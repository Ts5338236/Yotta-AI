"""Tests for approval threshold, approver role, and sourcing award rule validation (Phase 4).

Verifies detection of:
- Missing approval levels based on monetary thresholds
- Insufficient quotation counts in competitive RFQs (< 3 quotes)
- Non-lowest evaluated score awarded in clean path
"""

import copy
import pytest
from datagen.workflow import generate_procurement_workflow
from validate.checks import validate_approvals_and_business_rules, validate_split_purchases


@pytest.fixture(scope="module")
def starter_dataset():
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_clean_dataset_passes_approvals_and_rules_validation(starter_dataset):
    """Verify clean dataset passes all business rule and approval checks with 0 errors."""
    results = validate_approvals_and_business_rules(starter_dataset)
    failures = [r for r in results if not r.passed]
    assert len(failures) == 0, f"Expected 0 failures, got: {failures}"


def test_detects_missing_approval_tier(starter_dataset):
    """Verify detection when a high-value PR lacks required approval levels."""
    corrupted = copy.deepcopy(starter_dataset)
    # Find a PR with > $25,000 estimate
    high_value_prs = [
        pr for pr in corrupted["purchase_requests"]
        if pr["total_estimate_usd"] > 25000 and pr["status"] != "REJECTED"
    ]
    assert len(high_value_prs) > 0
    target_pr = high_value_prs[0]
    pr_id = target_pr["request_id"]

    # Delete all but 1 approval for this PR
    kept = False
    new_approvals = []
    for app in corrupted["approvals"]:
        if app["request_id"] == pr_id:
            if not kept:
                new_approvals.append(app)
                kept = True
        else:
            new_approvals.append(app)
    corrupted["approvals"] = new_approvals

    results = validate_approvals_and_business_rules(corrupted)
    failures = [
        r for r in results
        if r.check_name == "approval_required_levels" and r.record_id == pr_id and not r.passed
    ]
    assert len(failures) >= 1
    assert failures[0].actual_value == 1


def test_detects_insufficient_competitive_quotes(starter_dataset):
    """Verify detection when an RFQ receives fewer than 3 supplier quotations."""
    corrupted = copy.deepcopy(starter_dataset)
    rfq_id = corrupted["rfqs"][0]["rfq_id"]

    # Remove quotes for this RFQ until only 2 remain
    kept_count = 0
    new_quotes = []
    for q in corrupted["supplier_quotes"]:
        if q["rfq_id"] == rfq_id:
            if kept_count < 2:
                new_quotes.append(q)
                kept_count += 1
        else:
            new_quotes.append(q)
    corrupted["supplier_quotes"] = new_quotes

    results = validate_approvals_and_business_rules(corrupted)
    failures = [
        r for r in results
        if r.check_name == "sourcing_competitive_quote_count" and r.record_id == rfq_id and not r.passed
    ]
    assert len(failures) >= 1
    assert failures[0].actual_value == 2


def test_detects_non_lowest_score_awarded(starter_dataset):
    """Verify detection when awarded quote is not the lowest composite score."""
    corrupted = copy.deepcopy(starter_dataset)
    # Find an awarded quote and artificially increase its score to 99.99
    for q in corrupted["supplier_quotes"]:
        if q.get("status") == "AWARDED":
            q["score"] = 99.99
            target_qid = q["quote_id"]
            break

    results = validate_approvals_and_business_rules(corrupted)
    failures = [
        r for r in results
        if r.check_name == "award_lowest_composite_score" and r.record_id == target_qid and not r.passed
    ]
    assert len(failures) >= 1
    assert failures[0].severity == "CRITICAL"


def test_validate_split_purchases_auditing(starter_dataset):
    """Verify split purchase detection identifies requisitions aggregating over threshold."""
    corrupted = copy.deepcopy(starter_dataset)
    # Inject two PRs for same requester on same date, each $1,500 (total $3,000 > $2,000)
    req_id = corrupted["requesters"][0]["requester_id"]
    corrupted["purchase_requests"].append({
        "request_id": "PR-2026-999001",
        "requester_id": req_id,
        "department_id": corrupted["requesters"][0]["department_id"],
        "budget_id": corrupted["budgets"][0]["budget_id"],
        "request_date": "2026-05-10",
        "status": "APPROVED",
        "priority": "MEDIUM",
        "total_estimate_usd": 1500.0,
    })
    corrupted["purchase_requests"].append({
        "request_id": "PR-2026-999002",
        "requester_id": req_id,
        "department_id": corrupted["requesters"][0]["department_id"],
        "budget_id": corrupted["budgets"][0]["budget_id"],
        "request_date": "2026-05-11",
        "status": "APPROVED",
        "priority": "MEDIUM",
        "total_estimate_usd": 1600.0,
    })

    results = validate_split_purchases(corrupted, window_days=3)
    audited = [r for r in results if r.check_name == "split_purchase_threshold_audit"]
    assert len(audited) >= 1
    found = any("PR-2026-999001+PR-2026-999002" == r.record_id for r in audited)
    assert found


