"""Tests for Data Export Engine (Phase 6).

Verifies export to CSV, JSON, and SQLite database with full schema compliance.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import pytest

from datagen.export import export_all, export_to_csv, export_to_json, export_to_sqlite
from datagen.workflow import generate_procurement_workflow
from validate.checks import run_foundational_checks


@pytest.fixture(scope="module")
def starter_data():
    """Generate starter dataset for export testing."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_export_to_csv(starter_data, tmp_path):
    """Verify CSV export writes valid non-empty files for all tables."""
    csv_dir = tmp_path / "csv"
    exported = export_to_csv(starter_data, output_dir=csv_dir)

    assert len(exported) >= 15
    assert "departments" in exported
    assert "purchase_orders" in exported

    dept_csv = exported["departments"]
    assert dept_csv.exists()
    assert dept_csv.stat().st_size > 0


def test_export_to_json(starter_data, tmp_path):
    """Verify JSON export writes valid serializable JSON files."""
    json_dir = tmp_path / "json"
    exported = export_to_json(starter_data, output_dir=json_dir)

    assert len(exported) >= 15
    assert "suppliers" in exported

    supp_json = exported["suppliers"]
    assert supp_json.exists()
    with open(supp_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == len(starter_data["suppliers"])


def test_export_to_sqlite(starter_data, tmp_path):
    """Verify SQLite export populates physical DB with zero FK violations."""
    db_file = tmp_path / "test_p2p.db"
    exported_db = export_to_sqlite(starter_data, db_path=db_file)

    assert exported_db.exists()
    checks = run_foundational_checks(exported_db)
    assert checks["foreign_keys_enabled"] is True
    assert checks["integrity_ok"] is True
    assert checks["tables_ok"] is True
    assert checks["fk_violations_count"] == 0
    assert checks["all_passed"] is True


def test_export_all_integration(starter_data, tmp_path):
    """Verify export_all orchestrates CSV, JSON, and SQLite generation."""
    csv_dir = tmp_path / "csv_all"
    json_dir = tmp_path / "json_all"
    db_path = tmp_path / "p2p_all.db"

    res = export_all(
        starter_data,
        csv_dir=csv_dir,
        json_dir=json_dir,
        db_path=db_path,
    )

    assert res["total_tables_exported"] >= 15
    assert Path(res["sqlite_db"]).exists()
    assert len(res["csv_files"]) >= 15
    assert len(res["json_files"]) >= 15
