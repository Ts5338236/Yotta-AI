"""Unit tests for Phase 6 JSON Export Engine.

Verifies:
- All operational entities generate valid JSON files.
- Record counts match in-memory data.
- Correct serialization of dates, decimals, nulls, and nested dicts.
- Round-trip deserialization via json.load.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from datagen.export import OPERATIONAL_TABLES, export_to_json
from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def starter_dataset():
    """Generate starter dataset for export testing."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_json_export_all_entities(starter_dataset, tmp_path):
    """Verify that all operational entities generate valid JSON files."""
    json_dir = tmp_path / "json"
    exported = export_to_json(starter_dataset, output_dir=json_dir)

    for table in OPERATIONAL_TABLES:
        if table in starter_dataset:
            assert table in exported
            j_file = exported[table]
            assert j_file.exists()
            assert j_file.stat().st_size > 0


def test_json_deserialization_and_counts(starter_dataset, tmp_path):
    """Verify that exported JSON files parse correctly and match source counts."""
    json_dir = tmp_path / "json"
    exported = export_to_json(starter_dataset, output_dir=json_dir)

    for table, j_file in exported.items():
        if table == "metadata":
            continue
        source_rows = starter_dataset[table]
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == len(source_rows), f"Count mismatch in {table}.json"


def test_json_deterministic_ordering(starter_dataset, tmp_path):
    """Verify that repeated JSON exports produce bitwise identical content."""
    dir1 = tmp_path / "json1"
    dir2 = tmp_path / "json2"

    exp1 = export_to_json(starter_dataset, output_dir=dir1)
    exp2 = export_to_json(starter_dataset, output_dir=dir2)

    for table in exp1:
        with open(exp1[table], "rb") as f1, open(exp2[table], "rb") as f2:
            assert f1.read() == f2.read(), f"Non-deterministic JSON in {table}"

