"""Tests for Data Export Engine (Phase 6).

Verifies export to CSV, JSON, SQLite database, SQL seed script, DDL schema,
integrity verification, and provenance source manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import pytest

from datagen.export import (
    export_all,
    export_to_csv,
    export_to_json,
    export_to_sqlite,
    export_to_sql_seed,
    export_to_sql_schema,
    generate_source_manifest,
    verify_export_integrity,
    generate_dataset_statistics,
)
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


def test_export_to_sql_seed_and_execution(starter_data, tmp_path):
    """Verify generated seed.sql executes cleanly against blank schema with zero FK violations."""
    seed_file = tmp_path / "test_seed.sql"
    exported_seed = export_to_sql_seed(starter_data, output_path=seed_file)

    assert exported_seed.exists()
    assert exported_seed.stat().st_size > 0

    # Execute schema.sql then seed.sql in a fresh in-memory database
    with open("output/sql/schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with open(exported_seed, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_sql)
    conn.executescript(seed_sql)

    fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
    assert len(fk_violations) == 0

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM departments;")
    assert cur.fetchone()[0] == len(starter_data["departments"])
    conn.close()


def test_source_manifest_generation(starter_data, tmp_path):
    """Verify source_manifest.json contains required provenance and reproducibility metadata."""
    manifest_file = tmp_path / "source_manifest.json"
    manifest = generate_source_manifest(starter_data, output_path=manifest_file)

    assert manifest_file.exists()
    assert manifest["manifest_version"] == "1.0.0"
    assert manifest["data_provenance"]["synthetic"] is True
    assert manifest["data_provenance"]["external_proprietary_data"] is False
    assert manifest["reproducibility"]["default_seed"] == 20261022
    assert "departments" in manifest["record_counts"]


def test_export_integrity_and_statistics(starter_data, tmp_path):
    """Verify verify_export_integrity passes and generate_dataset_statistics produces reports."""
    out_dir = tmp_path / "output_test"
    res = export_all(starter_data, output_dir=out_dir)

    assert Path(res["sqlite_db"]).exists()
    assert (out_dir / "sql" / "yotta_ai.db").exists()
    assert Path(res["schema_ddl"]).exists()
    assert Path(res["seed_sql"]).exists()
    assert res["integrity_report"]["status"] == "PASS"
    assert res["integrity_report"]["failed_checks"] == 0
    assert (out_dir / "reports" / "export_integrity_report.md").exists()
    assert (out_dir / "reports" / "dataset_statistics.md").exists()

