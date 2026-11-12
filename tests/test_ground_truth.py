"""Tests for Ground Truth Generation and Integrity (Phase 5).

Verifies that Ground Truth records conform strictly to the required schema,
possess valid unique IDs matching ANOM-######, resolve to real dataset records,
and are maintained in independent ground-truth structures.
"""

from __future__ import annotations

import json
import re
import numpy as np
import pytest

from datagen.anomalies import GroundTruthRecord, inject_anomalies
from datagen.config import load_config
from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def starter_anomaly_run():
    """Generate starter dataset with injected anomalies and ground truth."""
    config = load_config()
    clean = generate_procurement_workflow(scale="starter", seed=20261022)
    rng = np.random.default_rng(20261022)
    dataset, gt = inject_anomalies(clean, config, rng)
    return dataset, gt


def test_ground_truth_record_schema(starter_anomaly_run):
    """Verify all ground truth records have all mandatory schema fields."""
    _, gt_records = starter_anomaly_run
    required_keys = {
        "anomaly_id",
        "issue_type",
        "entity",
        "record_id",
        "expected_decision",
        "reason",
        "metadata",
    }
    for r in gt_records:
        assert isinstance(r, dict)
        assert set(r.keys()) == required_keys
        assert r["anomaly_id"].startswith("ANOM-")
        assert len(r["reason"]) > 0
        assert r["expected_decision"] in {"REJECT", "DISQUALIFY", "JUSTIFY_OR_REVERT", "BLOCK", "FLAG", "REVISE"}
        assert isinstance(r["metadata"], dict)


def test_anomaly_id_format_and_uniqueness(starter_anomaly_run):
    """Verify anomaly_id follows ANOM-###### format and is globally unique."""
    _, gt_records = starter_anomaly_run
    pattern = re.compile(r"^ANOM-\d{6}$")

    ids = [r["anomaly_id"] for r in gt_records]
    assert len(ids) == len(set(ids)), "Duplicate anomaly_id detected in ground truth"

    for aid in ids:
        assert pattern.match(aid), f"Anomaly ID '{aid}' does not match regex ^ANOM-\\d{{6}}$"


def test_ground_truth_record_resolution(starter_anomaly_run):
    """Verify each ground truth record_id resolves to an actual record in the dataset."""
    dataset, gt_records = starter_anomaly_run

    for r in gt_records:
        entity_table = r["entity"]
        target_id = r["record_id"]

        assert entity_table in dataset, f"Entity table '{entity_table}' not found in dataset"
        records = dataset[entity_table]

        # Determine primary key field name based on entity
        pk_field = {
            "purchase_orders": "po_id",
            "supplier_quotes": "quote_id",
            "budgets": "budget_id",
            "purchase_requests": "request_id",
        }.get(entity_table)

        assert pk_field is not None, f"Unrecognized entity table '{entity_table}' in ground truth"
        matching = [item for item in records if item.get(pk_field) == target_id]
        assert len(matching) == 1, f"Ground truth record_id '{target_id}' not found in {entity_table}"


def test_ground_truth_json_serialization(starter_anomaly_run):
    """Verify ground truth records serialize cleanly to JSON and deserialize back."""
    _, gt_records = starter_anomaly_run

    json_str = json.dumps(gt_records, indent=2)
    deserialized = json.loads(json_str)

    assert len(deserialized) == len(gt_records)
    assert deserialized[0]["anomaly_id"] == gt_records[0]["anomaly_id"]
    assert deserialized[0]["issue_type"] == gt_records[0]["issue_type"]


def test_ground_truth_storage_separation(starter_anomaly_run):
    """Verify operational tables do not contain injected ground truth flags or columns."""
    dataset, _ = starter_anomaly_run

    forbidden_keys = {"is_anomaly", "injected_anomaly", "ground_truth", "anomaly_id"}
    for table_name, rows in dataset.items():
        if isinstance(rows, list) and table_name != "ground_truth":
            for row in rows:
                if isinstance(row, dict):
                    overlap = set(row.keys()).intersection(forbidden_keys)
                    assert not overlap, f"Forbidden contamination key(s) {overlap} found in {table_name}"

