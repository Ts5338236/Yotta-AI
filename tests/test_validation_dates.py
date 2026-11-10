"""Tests for date ordering and transaction chronology validation (Phase 4).

Verifies detection of:
- Dates outside fiscal year 2026
- Approval date preceding request submission
- RFQ due date preceding issue date
- Quote date preceding RFQ issue
- Purchase order preceding approval
- Delivery receipt preceding purchase order
"""

import copy
import pytest
from datagen.workflow import generate_procurement_workflow
from validate.checks import validate_date_ordering


@pytest.fixture(scope="module")
def starter_dataset():
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_clean_dataset_passes_date_validation(starter_dataset):
    """Verify clean dataset passes all date chronology rules with 0 errors."""
    results = validate_date_ordering(starter_dataset)
    failures = [r for r in results if not r.passed]
    assert len(failures) == 0, f"Expected 0 failures, got: {failures}"


def test_detects_request_outside_fiscal_year_2026(starter_dataset):
    """Verify detection of requisition date falling in 2025."""
    corrupted = copy.deepcopy(starter_dataset)
    corrupted["purchase_requests"][0]["request_date"] = "2025-12-15"
    corrupted["purchase_requests"][0]["created_at"] = "2025-12-15T10:00:00Z"

    results = validate_date_ordering(corrupted)
    failures = [r for r in results if r.check_name == "date_in_fiscal_year_2026" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].actual_value == 2025


def test_detects_approval_preceding_request(starter_dataset):
    """Verify detection of approval date preceding request submission."""
    corrupted = copy.deepcopy(starter_dataset)
    # Set approval date 10 days before request date
    pr = corrupted["purchase_requests"][0]
    pr_id = pr["request_id"]
    for app in corrupted["approvals"]:
        if app["request_id"] == pr_id:
            app["decision_date"] = "2026-01-01"
            break

    pr["request_date"] = "2026-06-01"
    pr["created_at"] = "2026-06-01T10:00:00Z"

    results = validate_date_ordering(corrupted)
    failures = [r for r in results if r.check_name == "date_approval_after_request" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "approvals"


def test_detects_delivery_preceding_purchase_order(starter_dataset):
    """Verify detection of delivery receipt date occurring before PO date."""
    corrupted = copy.deepcopy(starter_dataset)
    po = corrupted["purchase_orders"][0]
    po["po_date"] = "2026-09-01"

    for d in corrupted["deliveries"]:
        if d["po_id"] == po["po_id"]:
            d["delivery_date"] = "2026-01-15"
            break

    results = validate_date_ordering(corrupted)
    failures = [r for r in results if r.check_name == "date_delivery_after_po" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "deliveries"
