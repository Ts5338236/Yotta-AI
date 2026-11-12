"""Tests for SQLite database schema, constraints, and relational integrity."""

import sqlite3
from pathlib import Path
import pytest

from validate.checks import (
    check_foreign_keys_enabled,
    check_required_tables_exist,
    check_schema_integrity,
    EXPECTED_TABLES,
)


@pytest.fixture
def db_conn():
    """Create an in-memory SQLite database initialized with schema.sql."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_path = Path(__file__).resolve().parent.parent / "output" / "sql" / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    yield conn
    conn.close()


def test_schema_initialization_and_tables(db_conn):
    """Verify that schema executes successfully and all 18 tables exist."""
    assert check_foreign_keys_enabled(db_conn) is True

    integrity_ok, messages = check_schema_integrity(db_conn)
    assert integrity_ok is True
    assert messages == ["ok"]

    tables_ok, missing = check_required_tables_exist(db_conn)
    assert tables_ok is True
    assert len(missing) == 0


def test_foreign_key_enforcement_rejects_orphans(db_conn):
    """Verify that inserting a child record with a non-existent parent foreign key is rejected."""
    # Attempt inserting requester referencing a non-existent department
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO requesters (requester_id, name, email, department_id, job_title, created_at)
            VALUES ('REQ-0001', 'Alice User', 'alice@company.com', 'DEPT-99', 'Analyst', '2026-01-01T00:00:00Z');
            """
        )


def test_unique_constraints(db_conn):
    """Verify that unique constraints on department name and code are enforced."""
    db_conn.execute(
        """
        INSERT INTO departments (department_id, name, cost_center_code, created_at)
        VALUES ('DEPT-01', 'Engineering', 'CC-100', '2026-01-01T00:00:00Z');
        """
    )

    # Duplicate name
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO departments (department_id, name, cost_center_code, created_at)
            VALUES ('DEPT-02', 'Engineering', 'CC-101', '2026-01-01T00:00:00Z');
            """
        )

    # Duplicate cost center code
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO departments (department_id, name, cost_center_code, created_at)
            VALUES ('DEPT-03', 'R&D', 'CC-100', '2026-01-01T00:00:00Z');
            """
        )


def test_check_constraints_monetary_and_enums(db_conn):
    """Verify that CHECK constraints prevent negative amounts and invalid enum values."""
    db_conn.execute(
        """
        INSERT INTO departments (department_id, name, cost_center_code, created_at)
        VALUES ('DEPT-01', 'Operations', 'CC-200', '2026-01-01T00:00:00Z');
        """
    )

    # Negative allocated budget amount
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO budgets (budget_id, department_id, fiscal_year, currency, allocated_amount, created_at)
            VALUES ('BUD-0001', 'DEPT-01', 2026, 'USD', -5000, '2026-01-01T00:00:00Z');
            """
        )

    # Invalid approver role
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO approvers (approver_id, name, email, department_id, role, approval_limit, created_at)
            VALUES ('APP-0001', 'Bob Manager', 'bob@company.com', 'DEPT-01', 'SUPER_ADMIN', 100000, '2026-01-01T00:00:00Z');
            """
        )


def test_single_rfq_per_purchase_request(db_conn):
    """Verify that only one RFQ can exist per Purchase Request."""
    # Seed Department, Budget, Requester, PurchaseRequest
    db_conn.execute(
        "INSERT INTO departments VALUES ('DEPT-01', 'Finance', 'CC-300', '2026-01-01T00:00:00Z');"
    )
    db_conn.execute(
        "INSERT INTO budgets VALUES ('BUD-0001', 'DEPT-01', 2026, 'USD', 10000000, 0, 0, 0, '2026-01-01T00:00:00Z');"
    )
    db_conn.execute(
        "INSERT INTO requesters VALUES ('REQ-0001', 'Charlie', 'charlie@company.com', 'DEPT-01', 'Lead', '2026-01-01T00:00:00Z');"
    )
    db_conn.execute(
        """
        INSERT INTO purchase_requests VALUES (
            'PR-2026-000001', 'REQ-0001', 'DEPT-01', 'BUD-0001', 'USD', 50000, 'APPROVED',
            '2026-01-02', 'Laptops for engineers', '2026-01-02T00:00:00Z', '2026-01-02T00:00:00Z'
        );
        """
    )

    # First RFQ succeeds
    db_conn.execute(
        "INSERT INTO rfqs VALUES ('RFQ-2026-000001', 'PR-2026-000001', '2026-01-03', '2026-01-10', 'ISSUED', '2026-01-03T00:00:00Z');"
    )

    # Second RFQ for the same PR-2026-000001 must fail unique constraint
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "INSERT INTO rfqs VALUES ('RFQ-2026-000002', 'PR-2026-000001', '2026-01-04', '2026-01-11', 'ISSUED', '2026-01-04T00:00:00Z');"
        )


def test_quote_requires_rfq_supplier_invitation(db_conn):
    """Verify that a supplier cannot submit a quote without having an RFQ invitation."""
    # Setup hierarchy
    db_conn.execute("INSERT INTO departments VALUES ('DEPT-01', 'IT', 'CC-400', '2026-01-01T00:00:00Z');")
    db_conn.execute("INSERT INTO budgets VALUES ('BUD-0001', 'DEPT-01', 2026, 'USD', 5000000, 0, 0, 0, '2026-01-01T00:00:00Z');")
    db_conn.execute("INSERT INTO requesters VALUES ('REQ-0001', 'Dana', 'dana@company.com', 'DEPT-01', 'IT Admin', '2026-01-01T00:00:00Z');")
    db_conn.execute(
        "INSERT INTO purchase_requests VALUES ('PR-2026-000001', 'REQ-0001', 'DEPT-01', 'BUD-0001', 'USD', 20000, 'IN_SOURCING', '2026-01-02', 'Monitors', '2026-01-02T00:00:00Z', '2026-01-02T00:00:00Z');"
    )
    db_conn.execute("INSERT INTO rfqs VALUES ('RFQ-2026-000001', 'PR-2026-000001', '2026-01-03', '2026-01-10', 'ISSUED', '2026-01-03T00:00:00Z');")
    db_conn.execute("INSERT INTO suppliers VALUES ('SUP-0001', 'Tech Corp', 'sales@tech.com', 'USA', 'USD', 'ACTIVE', 'LOW', '2026-01-01T00:00:00Z');")

    # Supplier SUP-0001 has NOT been invited to RFQ-2026-000001 yet.
    # Inserting quote directly must fail due to compound foreign key (rfq_id, supplier_id) referencing rfq_supplier_invites
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO supplier_quotes VALUES (
                'QUO-SUP-C-0001-2026-000001', 'RFQ-2026-000001', 'SUP-0001', '2026-01-05', 'USD', 1.0,
                19500, 19500, 5, 'SUBMITTED', '2026-01-05T00:00:00Z'
            );
            """
        )

    # Now invite supplier
    db_conn.execute(
        "INSERT INTO rfq_supplier_invites VALUES ('INV-000001', 'RFQ-2026-000001', 'SUP-0001', '2026-01-04T00:00:00Z', 'SENT');"
    )

    # Submitting quote should now succeed
    db_conn.execute(
        """
        INSERT INTO supplier_quotes VALUES (
            'QUO-SUP-C-0001-2026-000001', 'RFQ-2026-000001', 'SUP-0001', '2026-01-05', 'USD', 1.0,
            19500, 19500, 5, 'SUBMITTED', '2026-01-05T00:00:00Z'
        );
        """
    )
    cursor = db_conn.cursor()
    cursor.execute("SELECT quote_id FROM supplier_quotes WHERE quote_id = 'QUO-SUP-C-0001-2026-000001';")
    assert cursor.fetchone()[0] == "QUO-SUP-C-0001-2026-000001"
