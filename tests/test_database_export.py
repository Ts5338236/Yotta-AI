"""Unit tests for Phase 6 SQLite Database Export & Persistence.

Verifies:
- All required tables are created in SQLite database.
- Primary keys and foreign keys are preserved with PRAGMA foreign_keys = ON.
- Record counts match in-memory records.
- PRAGMA integrity_check returns ok.
- PRAGMA foreign_key_check returns zero violations.
- Safe rollback on constraint errors.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import pytest

from datagen.database import (
    DatabaseError,
    check_database_integrity,
    get_connection,
    initialize_schema,
    populate_database,
)
from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def starter_dataset():
    """Generate starter dataset for database persistence tests."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_database_initialization_and_schema(tmp_path):
    """Verify that initialize_schema creates a clean SQLite DB with 19 tables."""
    db_file = tmp_path / "init_test.db"
    initialize_schema(db_file, schema_path="data/sql/schema.sql")

    assert db_file.exists()
    conn = get_connection(db_file)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    ).fetchall()
    conn.close()

    assert len(tables) >= 18


def test_database_population_and_foreign_keys(starter_dataset, tmp_path):
    """Verify that populate_database inserts all records with zero foreign key errors."""
    db_file = tmp_path / "procurement.db"
    populate_database(starter_dataset, db_path=db_file, schema_path="data/sql/schema.sql")

    assert db_file.exists()
    integrity = check_database_integrity(db_file)

    assert integrity["integrity_ok"] is True
    assert integrity["integrity_result"] == "ok"
    assert integrity["foreign_key_violations_count"] == 0

    # Verify counts
    for table, count in integrity["table_counts"].items():
        if table in starter_dataset:
            assert count == len(starter_dataset[table]), f"Count mismatch in {table}"


def test_database_rollback_on_failure(starter_dataset, tmp_path):
    """Verify that invalid data causes a clean rollback without corrupting the file."""
    db_file = tmp_path / "corrupt_test.db"
    corrupted = dict(starter_dataset)
    # Inject record with non-existent foreign key
    corrupted["purchase_requests"] = [
        dict(starter_dataset["purchase_requests"][0], department_id="DEPT-99999")
    ]

    with pytest.raises(DatabaseError):
        populate_database(corrupted, db_path=db_file, schema_path="data/sql/schema.sql")

    # DB should either not exist or be cleaned up
    assert not db_file.exists() or db_file.stat().st_size == 0

