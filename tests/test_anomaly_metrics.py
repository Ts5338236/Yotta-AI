"""Tests for Anomaly Detection Evaluation Metrics (Phase 5).

Verifies accuracy of True Positive, False Positive, False Negative, Precision,
Recall, and F1-score computations on synthetic benchmarks and empirical datasets.
"""

from __future__ import annotations

import numpy as np
import pytest

from datagen.anomalies import inject_anomalies
from datagen.config import load_config
from datagen.workflow import generate_procurement_workflow
from validate.anomaly_checks import AnomalyFinding, detect_all_anomalies, evaluate_detections


def test_evaluate_detections_perfect_match():
    """Verify evaluation metrics on a synthetic perfect match scenario."""
    gt = [
        {"issue_type": "po_without_approval", "entity": "purchase_orders", "record_id": "PO-001"},
        {"issue_type": "budget_overrun", "entity": "budgets", "record_id": "BUD-001"},
    ]
    findings = [
        AnomalyFinding(issue_type="po_without_approval", entity="purchase_orders", record_id="PO-001"),
        AnomalyFinding(issue_type="budget_overrun", entity="budgets", record_id="BUD-001"),
    ]

    metrics = evaluate_detections(findings, gt)
    assert metrics["true_positives"] == 2
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0


def test_evaluate_detections_with_false_positives_and_negatives():
    """Verify evaluation metric calculations when discrepancies occur."""
    gt = [
        {"issue_type": "po_without_approval", "entity": "purchase_orders", "record_id": "PO-001"},
        {"issue_type": "budget_overrun", "entity": "budgets", "record_id": "BUD-001"},
    ]
    findings = [
        AnomalyFinding(issue_type="po_without_approval", entity="purchase_orders", record_id="PO-001"),
        AnomalyFinding(issue_type="budget_overrun", entity="budgets", record_id="BUD-999"),  # FP
    ]

    metrics = evaluate_detections(findings, gt)
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1  # BUD-999
    assert metrics["false_negatives"] == 1  # BUD-001
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1_score"] == 0.5


def test_evaluate_detections_empty_cases():
    """Verify evaluation handles empty lists gracefully without division by zero."""
    # 0 GT, 0 findings -> 1.0 by convention
    metrics_empty = evaluate_detections([], [])
    assert metrics_empty["precision"] == 1.0
    assert metrics_empty["recall"] == 1.0
    assert metrics_empty["f1_score"] == 1.0

    # 1 GT, 0 findings -> precision 1.0, recall 0.0
    gt = [{"issue_type": "po_without_approval", "entity": "purchase_orders", "record_id": "PO-001"}]
    metrics_missed = evaluate_detections([], gt)
    assert metrics_missed["true_positives"] == 0
    assert metrics_missed["false_negatives"] == 1
    assert metrics_missed["recall"] == 0.0


def test_starter_scale_empirical_metrics():
    """Verify that starter scale dataset achieves 100% precision and 100% recall."""
    config = load_config()
    clean = generate_procurement_workflow(scale="starter", seed=20261022)
    rng = np.random.default_rng(20261022)

    dataset, gt = inject_anomalies(clean, config, rng)
    findings = detect_all_anomalies(dataset, config)
    metrics = evaluate_detections(findings, gt)

    assert metrics["total_ground_truth"] == 7
    assert metrics["total_detected"] == 7
    assert metrics["true_positives"] == 7
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0

    # Every category must be 100% precision and recall
    for cat, stats in metrics["by_category"].items():
        assert stats["precision"] == 1.0, f"Precision drop in {cat}"
        assert stats["recall"] == 1.0, f"Recall drop in {cat}"


def test_full_scale_empirical_metrics():
    """Verify that full scale dataset (35 anomalies) achieves 100% precision and 100% recall."""
    config = load_config()
    clean = generate_procurement_workflow(scale="full", seed=20261022)
    rng = np.random.default_rng(20261022)

    dataset, gt = inject_anomalies(clean, config, rng)
    findings = detect_all_anomalies(dataset, config)
    metrics = evaluate_detections(findings, gt)

    assert metrics["total_ground_truth"] == 35
    assert metrics["total_detected"] == 35
    assert metrics["true_positives"] == 35
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0

    for cat, stats in metrics["by_category"].items():
        assert stats["precision"] == 1.0, f"Precision drop in full scale {cat}"
        assert stats["recall"] == 1.0, f"Recall drop in full scale {cat}"

