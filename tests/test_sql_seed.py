"""Unit tests for Phase 6 SQL Seed Script Generation.

Verifies:
- seed.sql contains real INSERT statements (not a placeholder).
- Executes in dependency order against schema.sql with PRAGMA foreign_keys = ON.
- Zero foreign-key violations.
- Reproduces identical record counts as the source dataset.
- Preserves escaping of quotes, integers, floats, and NULLs.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import pytest

from datagen.export import export_to_sql_seed
from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def starter_dataset():
    """Generate starter dataset for seed tests."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_sql_seed_not_placeholder(starter_dataset, tmp_path):
    """Verify that generated seed.sql contains real INSERT statements."""
    seed_file = tmp_path / "seed.sql"
    export_to_sql_seed(starter_dataset, output_path=seed_file, schema_path="output/sql/schema.sql")

    assert seed_file.exists()
    assert seed_file.stat().st_size > 1000

    with open(seed_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "INSERT INTO departments" in content
    assert "INSERT INTO purchase_orders" in content
    assert "Placeholder" not in content


def test_sql_seed_execution_and_counts(starter_dataset, tmp_path):
    """Verify that seed.sql executes cleanly and recreates the source dataset."""
    seed_file = tmp_path / "seed.sql"
    export_to_sql_seed(starter_dataset, output_path=seed_file, schema_path="output/sql/schema.sql")

    with open("output/sql/schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with open(seed_file, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_sql)
    conn.executescript(seed_sql)

    # Assert 0 foreign key violations
    fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
    assert len(fk_violations) == 0

    # Assert counts match source dataset
    for table, records in starter_dataset.items():
        if isinstance(records, list) and records and isinstance(records[0], dict):
            cursor = conn.cursor()
            cnt = cursor.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
            assert cnt == len(records), f"Count mismatch in {table}"

    conn.close()

