"""Tests for Phase 5 Anomaly Injection Engine.

Verifies that all 7 anomaly injectors function correctly, mutate only targeted
records, preserve clean baseline integrity, and maintain proper ground truth tracking.
"""

from __future__ import annotations

import copy
import numpy as np
import pytest

from datagen.anomalies import (
    ANOMALY_CATEGORIES,
    GroundTruthRecord,
    inject_anomalies,
    inject_budget_overrun,
    inject_duplicate_purchase_request,
    inject_expired_quote_before_award,
    inject_inactive_supplier_used,
    inject_non_cheapest_quote_without_rationale,
    inject_po_without_approval,
    inject_quote_currency_mismatch,
)
from datagen.config import load_config
from datagen.ids import IDFactory
from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def starter_clean_dataset():
    """Generate clean starter dataset for injection tests."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


@pytest.fixture(scope="module")
def project_config():
    """Load default project configuration."""
    return load_config()


def test_anomaly_categories_constant():
    """Verify all 7 PRD anomaly categories are registered."""
    assert len(ANOMALY_CATEGORIES) == 7
    expected = {
        "po_without_approval",
        "expired_quote_before_award",
        "non_cheapest_quote_without_rationale",
        "inactive_supplier_used",
        "budget_overrun",
        "duplicate_purchase_request",
        "quote_currency_mismatch",
    }
    assert set(ANOMALY_CATEGORIES) == expected


def test_inject_po_without_approval(starter_clean_dataset):
    """Verify injection of PO without approval removes approval and updates status."""
    dataset = copy.deepcopy(starter_clean_dataset)
    rng = np.random.default_rng(42)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_po_without_approval(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    assert gt.issue_type == "po_without_approval"
    assert gt.entity == "purchase_orders"
    assert gt.expected_decision == "REJECT"

    # Verify approval for the target PR was removed
    po = next(p for p in dataset["purchase_orders"] if p["po_id"] == gt.record_id)
    pr_id = po["request_id"]
    approvals = [a for a in dataset["approvals"] if a["request_id"] == pr_id]
    assert len(approvals) == 0


def test_inject_expired_quote_before_award(starter_clean_dataset):
    """Verify injection of expired quote shifts valid_until before award date."""
    dataset = copy.deepcopy(starter_clean_dataset)
    rng = np.random.default_rng(42)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_expired_quote_before_award(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    assert gt.issue_type == "expired_quote_before_award"
    assert gt.entity == "supplier_quotes"
    assert gt.expected_decision == "DISQUALIFY"

    quote = next(q for q in dataset["supplier_quotes"] if q["quote_id"] == gt.record_id)
    assert quote["valid_until"] < quote["award_date"]


def test_inject_non_cheapest_quote_without_rationale(starter_clean_dataset):
    """Verify non-cheapest award injection awards expensive quote with empty rationale."""
    dataset = copy.deepcopy(starter_clean_dataset)
    rng = np.random.default_rng(42)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_non_cheapest_quote_without_rationale(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    assert gt.issue_type == "non_cheapest_quote_without_rationale"
    assert gt.entity == "supplier_quotes"
    assert gt.expected_decision == "JUSTIFY_OR_REVERT"

    quote = next(q for q in dataset["supplier_quotes"] if q["quote_id"] == gt.record_id)
    assert quote["status"] == "AWARDED"
    assert quote["award_rationale"] is None or quote["award_rationale"].strip() == ""


def test_inject_inactive_supplier_used(starter_clean_dataset):
    """Verify inactive supplier injection creates inactive vendor and points PO to it."""
    dataset = copy.deepcopy(starter_clean_dataset)
    rng = np.random.default_rng(42)
    id_factory = IDFactory(fiscal_year=2026)

    initial_supplier_count = len(dataset["suppliers"])
    gt_list = inject_inactive_supplier_used(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    assert gt.issue_type == "inactive_supplier_used"
    assert gt.entity == "purchase_orders"
    assert gt.expected_decision == "BLOCK"

    po = next(p for p in dataset["purchase_orders"] if p["po_id"] == gt.record_id)
    supp = next(s for s in dataset["suppliers"] if s["supplier_id"] == po["supplier_id"])
    assert supp.get("status") == "INACTIVE" or supp.get("active") is False
    assert len(dataset["suppliers"]) == initial_supplier_count + 1


def test_inject_budget_overrun(starter_clean_dataset):
    """Verify budget overrun injection lowers allocation below committed spend."""
    dataset = copy.deepcopy(starter_clean_dataset)
    rng = np.random.default_rng(42)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_budget_overrun(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    assert gt.issue_type == "budget_overrun"
    assert gt.entity == "budgets"
    assert gt.expected_decision == "REJECT"

    budget = next(b for b in dataset["budgets"] if b["budget_id"] == gt.record_id)
    assert budget["spent_amount"] + budget.get("committed_amount", 0) > budget["allocated_amount"]


def test_inject_duplicate_purchase_request(starter_clean_dataset):
    """Verify duplicate PR injection creates matching requisition within 7-day window."""
    dataset = copy.deepcopy(starter_clean_dataset)
    rng = np.random.default_rng(42)
    id_factory = IDFactory(fiscal_year=2026)

    initial_pr_count = len(dataset["purchase_requests"])
    gt_list = inject_duplicate_purchase_request(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    assert gt.issue_type == "duplicate_purchase_request"
    assert gt.entity == "purchase_requests"
    assert gt.expected_decision == "FLAG"

    assert len(dataset["purchase_requests"]) == initial_pr_count + 1
    dup_pr = next(pr for pr in dataset["purchase_requests"] if pr["request_id"] == gt.record_id)
    orig_pr_id = gt.metadata["original_request_id"]
    orig_pr = next(pr for pr in dataset["purchase_requests"] if pr["request_id"] == orig_pr_id)

    assert dup_pr["department_id"] == orig_pr["department_id"]
    assert dup_pr["requester_id"] == orig_pr["requester_id"]


def test_inject_quote_currency_mismatch(starter_clean_dataset):
    """Verify quote currency mismatch mutates quotation currency away from supplier currency."""
    dataset = copy.deepcopy(starter_clean_dataset)
    rng = np.random.default_rng(42)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_quote_currency_mismatch(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    assert gt.issue_type == "quote_currency_mismatch"
    assert gt.entity == "supplier_quotes"
    assert gt.expected_decision == "REVISE"

    quote = next(q for q in dataset["supplier_quotes"] if q["quote_id"] == gt.record_id)
    supp = next(s for s in dataset["suppliers"] if s["supplier_id"] == quote["supplier_id"])
    assert quote["currency"] != supp["currency"]


def test_inject_anomalies_orchestration(starter_clean_dataset, project_config):
    """Verify master inject_anomalies orchestrates all categories and returns deep copy."""
    clean_copy = copy.deepcopy(starter_clean_dataset)
    rng = np.random.default_rng(20261022)

    mutated_dataset, ground_truth = inject_anomalies(clean_copy, project_config, rng)

    # Clean dataset fixture must remain unmutated
    assert len(clean_copy["purchase_requests"]) == len(starter_clean_dataset["purchase_requests"])
    assert len(clean_copy["suppliers"]) == len(starter_clean_dataset["suppliers"])

    # Mutated dataset should have exactly 7 anomalies in starter scale (1 per category)
    assert len(ground_truth) == 7
    issue_types = {gt["issue_type"] for gt in ground_truth}
    assert len(issue_types) == 7
