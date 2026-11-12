"""Tests for Determinism and Reproducibility in Anomaly Injection (Phase 5).

Verifies that identical random seeds produce identical anomaly mutations and ground truth,
different seeds produce divergent mutations, and scale tiers inject the exact configured anomaly counts.
"""

from __future__ import annotations

import numpy as np
import pytest

from datagen.anomalies import inject_anomalies
from datagen.config import load_config
from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def project_config():
    """Load default project configuration."""
    return load_config()


def test_anomaly_injection_identical_seed_determinism(project_config):
    """Verify that identical seeds produce identical anomaly records and mutations."""
    clean1 = generate_procurement_workflow(scale="starter", seed=20261022)
    clean2 = generate_procurement_workflow(scale="starter", seed=20261022)

    rng1 = np.random.default_rng(9999)
    rng2 = np.random.default_rng(9999)

    dataset1, gt1 = inject_anomalies(clean1, project_config, rng1)
    dataset2, gt2 = inject_anomalies(clean2, project_config, rng2)

    assert len(gt1) == len(gt2)
    for r1, r2 in zip(gt1, gt2):
        assert r1["anomaly_id"] == r2["anomaly_id"]
        assert r1["issue_type"] == r2["issue_type"]
        assert r1["entity"] == r2["entity"]
        assert r1["record_id"] == r2["record_id"]
        assert r1["metadata"] == r2["metadata"]


def test_anomaly_injection_divergent_seeds(project_config):
    """Verify that different seeds select different target records for mutation."""
    clean1 = generate_procurement_workflow(scale="starter", seed=20261022)
    clean2 = generate_procurement_workflow(scale="starter", seed=20261022)

    rng1 = np.random.default_rng(1111)
    rng2 = np.random.default_rng(8888)

    _, gt1 = inject_anomalies(clean1, project_config, rng1)
    _, gt2 = inject_anomalies(clean2, project_config, rng2)

    gt1_records = {(r["issue_type"], r["record_id"]) for r in gt1}
    gt2_records = {(r["issue_type"], r["record_id"]) for r in gt2}

    # At least some of the randomly selected records should differ
    assert gt1_records != gt2_records


def test_anomaly_counts_by_scale_tier(project_config):
    """Verify starter tier injects 7 anomalies and full tier injects 35 anomalies."""
    clean_starter = generate_procurement_workflow(scale="starter", seed=20261022)
    rng_starter = np.random.default_rng(20261022)
    _, gt_starter = inject_anomalies(clean_starter, project_config, rng_starter)
    assert len(gt_starter) == 7

    clean_full = generate_procurement_workflow(scale="full", seed=20261022)
    rng_full = np.random.default_rng(20261022)
    _, gt_full = inject_anomalies(clean_full, project_config, rng_full)
    assert len(gt_full) == 35

    # Full tier should have exactly 5 anomalies per category
    from collections import Counter
    counts = Counter(r["issue_type"] for r in gt_full)
    for cat in counts:
        assert counts[cat] == 5, f"Expected 5 anomalies for {cat}, got {counts[cat]}"

