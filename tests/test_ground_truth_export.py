"""Unit tests for Phase 6 Ground Truth Export.

Verifies:
- Ground truth is exported to data/ground_truth/ground_truth.csv and ground_truth.json.
- Ground truth remains isolated and is NOT written into operational CSV or JSON tables.
- Contains required fields: anomaly_id, issue_type, entity, record_id, expected_decision, reason.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import numpy as np
import pytest

from datagen.anomalies import inject_anomalies
from datagen.config import load_config
from datagen.export import export_all, export_ground_truth
from datagen.workflow import generate_procurement_workflow
from validate.export_checks import validate_ground_truth_isolation


@pytest.fixture(scope="module")
def anomaly_dataset():
    """Generate starter dataset with controlled anomalies."""
    cfg = load_config()
    seed = 20261022
    ds = generate_procurement_workflow(scale="starter", seed=seed)
    rng = np.random.default_rng(seed)
    ds, gt = inject_anomalies(ds, cfg, rng)
    return ds, gt


def test_ground_truth_export_standalone(anomaly_dataset, tmp_path):
    """Verify that export_ground_truth creates valid isolated CSV and JSON files."""
    _, gt_records = anomaly_dataset
    gt_dir = tmp_path / "ground_truth"
    exported = export_ground_truth(gt_records, output_dir=gt_dir)

    assert "csv" in exported
    assert "json" in exported

    csv_path = exported["csv"]
    json_path = exported["json"]

    assert csv_path.exists()
    assert json_path.exists()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == len(gt_records)
    required_fields = {"anomaly_id", "issue_type", "entity", "record_id", "expected_decision", "reason"}
    assert required_fields.issubset(set(rows[0].keys()))


def test_ground_truth_isolation_in_export_all(anomaly_dataset, tmp_path):
    """Verify that export_all separates ground truth from operational tables."""
    dataset, gt_records = anomaly_dataset
    data_dir = tmp_path / "data"

    export_all(dataset, base_dir=data_dir, ground_truth=gt_records)

    audit = validate_ground_truth_isolation(
        ground_truth_dir=data_dir / "ground_truth",
        csv_dir=data_dir / "csv",
        json_dir=data_dir / "json",
    )

    assert audit["passed"] is True
    assert audit["files_exist"] is True
    assert audit["isolated_from_operational_csv"] is True
    assert audit["isolated_from_operational_json"] is True

