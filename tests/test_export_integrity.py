"""Unit tests for Phase 6 Export Integrity and Cross-Format Consistency.

Verifies:
- validate_all_exports validates CSV, JSON, SQLite, and SQL seed.
- Detects missing files or record count mismatches.
- Cross-format checks confirm logical record equivalence between CSV, JSON, and SQLite.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from datagen.export import export_all
from datagen.workflow import generate_procurement_workflow
from validate.export_checks import (
    validate_all_exports,
    validate_csv_exports,
    validate_json_exports,
    validate_sqlite_database,
    validate_sql_seed_execution,
)


@pytest.fixture(scope="module")
def starter_dataset():
    """Generate starter dataset for integrity audit."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_full_export_integrity_passes(starter_dataset, tmp_path):
    """Verify that export_all generates artifacts that achieve 100% PASS across all integrity audits."""
    data_dir = tmp_path / "data"
    export_all(starter_dataset, base_dir=data_dir, schema_path="output/sql/schema.sql")

    audit = validate_all_exports(starter_dataset, base_dir=data_dir, schema_path="output/sql/schema.sql")

    assert audit["status"] == "PASS"
    assert audit["csv_validation"]["passed"] is True
    assert audit["json_validation"]["passed"] is True
    assert audit["sqlite_validation"]["passed"] is True
    assert audit["seed_validation"]["passed"] is True


def test_integrity_audit_detects_corrupted_csv(starter_dataset, tmp_path):
    """Verify that a corrupted CSV file triggers audit failure."""
    data_dir = tmp_path / "data"
    export_all(starter_dataset, base_dir=data_dir, schema_path="output/sql/schema.sql")

    # Corrupt a CSV by removing records
    dept_csv = data_dir / "csv" / "departments.csv"
    with open(dept_csv, "w", encoding="utf-8") as f:
        f.write("department_id,name\nDEPT-01,Test\n")

    audit = validate_csv_exports(starter_dataset, csv_dir=data_dir / "csv")
    assert audit["passed"] is False

