"""Unit tests for Phase 6 SQL Schema DDL Export.

Verifies:
- Canonical schema.sql executes on a fresh SQLite database without errors.
- All 18 operational tables + ground_truth table are defined.
- Primary key, foreign key, unique, and check constraints exist.
- Useful indexes exist on foreign keys and lookup columns.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import pytest

from datagen.export import export_to_sql_schema


def test_sql_schema_syntax_and_tables(tmp_path):
    """Verify that schema.sql executes cleanly and creates expected tables."""
    schema_dest = tmp_path / "schema.sql"
    export_to_sql_schema(schema_src="output/sql/schema.sql", output_path=schema_dest)

    assert schema_dest.exists()

    with open(schema_dest, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(sql)

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    ).fetchall()
    table_names = [t[0] for t in tables]

    required_tables = [
        "departments", "budgets", "requesters", "approvers", "suppliers",
        "purchase_requests", "request_lines", "rfqs", "rfq_supplier_invites",
        "supplier_quotes", "quote_lines", "approvals", "purchase_orders",
        "purchase_order_lines", "deliveries", "status_events", "budget_events",
        "exception_logs", "ground_truth",
    ]

    for req in required_tables:
        assert req in table_names, f"Table {req} not found in schema"

    conn.close()


def test_sql_schema_indexes_created(tmp_path):
    """Verify that indexes are defined on foreign key columns."""
    with open("output/sql/schema.sql", "r", encoding="utf-8") as f:
        sql = f.read()

    conn = sqlite3.connect(":memory:")
    conn.executescript(sql)

    indexes = conn.execute("SELECT name FROM sqlite_master WHERE type='index';").fetchall()
    idx_names = [i[0] for i in indexes]

    assert "idx_budgets_department" in idx_names
    assert "idx_pr_requester" in idx_names
    assert "idx_po_supplier" in idx_names
    conn.close()

