"""Tests for Independent Anomaly Detection Engine (Phase 5).

Verifies that detectors accurately identify business rule violations without reading
ground truth or injection flags, while discriminating against legitimate edge cases.
"""

from __future__ import annotations

import copy
import numpy as np
import pytest

from datagen.anomalies import (
    inject_budget_overrun,
    inject_duplicate_purchase_request,
    inject_expired_quote_before_award,
    inject_inactive_supplier_used,
    inject_non_cheapest_quote_without_rationale,
    inject_po_without_approval,
    inject_quote_currency_mismatch,
)
from datagen.ids import IDFactory
from datagen.workflow import generate_procurement_workflow
from validate.anomaly_checks import (
    detect_all_anomalies,
    detect_budget_overrun,
    detect_duplicate_purchase_requests,
    detect_expired_quote_before_award,
    detect_inactive_supplier_used,
    detect_non_cheapest_quote_without_rationale,
    detect_po_without_approval,
    detect_quote_currency_mismatch,
)


@pytest.fixture(scope="module")
def clean_starter():
    """Generate clean starter dataset for baseline testing."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_clean_dataset_produces_zero_findings(clean_starter):
    """Verify that a clean generated dataset triggers zero anomaly detections."""
    findings = detect_all_anomalies(clean_starter)
    assert len(findings) == 0, f"Clean dataset produced unexpected findings: {findings}"


def test_detect_po_without_approval_targeted(clean_starter):
    """Verify detector catches PO without approval and ignores valid approved POs."""
    dataset = copy.deepcopy(clean_starter)
    rng = np.random.default_rng(101)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_po_without_approval(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    findings = detect_po_without_approval(dataset)

    assert len(findings) == 1
    assert findings[0].issue_type == "po_without_approval"
    assert findings[0].record_id == gt.record_id
    assert findings[0].entity == "purchase_orders"


def test_detect_expired_quote_before_award_targeted(clean_starter):
    """Verify detector catches expired quote and allows unexpired quotes."""
    dataset = copy.deepcopy(clean_starter)
    rng = np.random.default_rng(101)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_expired_quote_before_award(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    findings = detect_expired_quote_before_award(dataset)

    assert len(findings) == 1
    assert findings[0].issue_type == "expired_quote_before_award"
    assert findings[0].record_id == gt.record_id


def test_detect_non_cheapest_quote_without_rationale_discrimination(clean_starter):
    """Verify non-cheapest award with valid rationale is NOT flagged, but without rationale IS flagged."""
    dataset = copy.deepcopy(clean_starter)
    rng = np.random.default_rng(101)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_non_cheapest_quote_without_rationale(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    findings = detect_non_cheapest_quote_without_rationale(dataset)

    assert len(findings) == 1
    assert findings[0].record_id == gt.record_id

    # Add a documented business justification to the awarded quote
    target_quote = next(q for q in dataset["supplier_quotes"] if q["quote_id"] == gt.record_id)
    target_quote["award_rationale"] = "Superior delivery lead time and comprehensive SLA."

    # Now the detector must not flag it as an anomaly!
    re_findings = detect_non_cheapest_quote_without_rationale(dataset)
    assert len(re_findings) == 0


def test_detect_inactive_supplier_used_targeted(clean_starter):
    """Verify detector catches PO issued to inactive supplier and ignores active suppliers."""
    dataset = copy.deepcopy(clean_starter)
    rng = np.random.default_rng(101)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_inactive_supplier_used(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    findings = detect_inactive_supplier_used(dataset)

    assert len(findings) == 1
    assert findings[0].record_id == gt.record_id
    assert findings[0].metadata["supplier_id"] == gt.metadata["supplier_id"]


def test_detect_budget_overrun_targeted(clean_starter):
    """Verify detector catches budget overrun and ignores healthy budgets."""
    dataset = copy.deepcopy(clean_starter)
    rng = np.random.default_rng(101)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_budget_overrun(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    findings = detect_budget_overrun(dataset)

    assert len(findings) == 1
    assert findings[0].record_id == gt.record_id


def test_detect_duplicate_purchase_requests_targeted(clean_starter):
    """Verify detector catches duplicate PRs within 7 days with identical items."""
    dataset = copy.deepcopy(clean_starter)
    rng = np.random.default_rng(101)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_duplicate_purchase_request(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    findings = detect_duplicate_purchase_requests(dataset)

    assert len(findings) == 1
    assert findings[0].record_id == gt.record_id


def test_detect_quote_currency_mismatch_targeted(clean_starter):
    """Verify detector catches mismatch between quote and supplier billing currency."""
    dataset = copy.deepcopy(clean_starter)
    rng = np.random.default_rng(101)
    id_factory = IDFactory(fiscal_year=2026)

    gt_list = inject_quote_currency_mismatch(dataset, rng, id_factory)
    assert len(gt_list) == 1
    gt = gt_list[0]
    findings = detect_quote_currency_mismatch(dataset)

    assert len(findings) == 1
    assert findings[0].record_id == gt.record_id
