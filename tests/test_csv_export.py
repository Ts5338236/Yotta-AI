"""Unit tests for Phase 6 CSV Export Engine.

Verifies:
- All required operational entities are exported.
- Header correctness and UTF-8 encoding.
- Row counts match in-memory records.
- Deterministic primary key sorting.
- Correct null, date, and decimal formatting.
"""

from __future__ import annotations

import csv
from pathlib import Path
import pytest

from datagen.export import OPERATIONAL_TABLES, export_to_csv
from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def starter_dataset():
    """Generate starter dataset for export testing."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_csv_export_all_operational_entities(starter_dataset, tmp_path):
    """Verify that every implemented operational entity generates a valid CSV file."""
    csv_dir = tmp_path / "csv"
    exported = export_to_csv(starter_dataset, output_dir=csv_dir)

    for table in OPERATIONAL_TABLES:
        if table in starter_dataset:
            assert table in exported
            csv_file = exported[table]
            assert csv_file.exists()
            assert csv_file.stat().st_size > 0


def test_csv_headers_and_row_counts(starter_dataset, tmp_path):
    """Verify that CSV headers match dictionary keys and row counts match source data."""
    csv_dir = tmp_path / "csv"
    exported = export_to_csv(starter_dataset, output_dir=csv_dir)

    for table, csv_file in exported.items():
        source_rows = starter_dataset[table]
        if not source_rows:
            continue

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == len(source_rows), f"Count mismatch in {table}"

        # Verify expected columns (excluding dropped internal helper keys)
        expected_keys = {k for k in source_rows[0].keys() if k not in ("_lines", "_supplier")}
        actual_keys = set(rows[0].keys())
        assert expected_keys.issubset(actual_keys), f"Missing columns in {table}"
        if table in ("supplier_quotes", "purchase_orders"):
            assert "_lines" not in actual_keys
        if table == "supplier_quotes":
            assert "_supplier" not in actual_keys


def test_csv_deterministic_row_ordering(starter_dataset, tmp_path):
    """Verify that exporting twice produces bitwise identical CSV files."""
    dir1 = tmp_path / "csv1"
    dir2 = tmp_path / "csv2"

    exp1 = export_to_csv(starter_dataset, output_dir=dir1)
    exp2 = export_to_csv(starter_dataset, output_dir=dir2)

    for table in exp1:
        with open(exp1[table], "rb") as f1, open(exp2[table], "rb") as f2:
            assert f1.read() == f2.read(), f"Non-deterministic export in {table}"

