"""Tests for financial arithmetic and monetary reconciliation validation (Phase 4).

Verifies detection of:
- Request line arithmetic errors (qty * unit_price != line_total)
- Requisition total mismatch (sum(lines) != PR total)
- Quote landed cost calculation discrepancies
- Purchase order header vs line total discrepancies
- Delivery quantity over-fulfillment
- Budget overruns
"""

import copy
import pytest
from datagen.workflow import generate_procurement_workflow
from validate.checks import validate_financial_reconciliation


@pytest.fixture(scope="module")
def starter_dataset():
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_clean_dataset_passes_financial_reconciliation(starter_dataset):
    """Verify clean dataset has zero financial reconciliation discrepancies."""
    results = validate_financial_reconciliation(starter_dataset)
    failures = [r for r in results if not r.passed]
    assert len(failures) == 0, f"Expected 0 failures, got: {failures}"


def test_detects_request_line_arithmetic_error(starter_dataset):
    """Verify detection of line_total != quantity * unit_price."""
    corrupted = copy.deepcopy(starter_dataset)
    # Inject corrupt line total
    corrupted["request_lines"][0]["estimated_line_total"] = 99999999

    results = validate_financial_reconciliation(corrupted)
    failures = [r for r in results if r.check_name == "financial_request_line_total" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "request_lines"


def test_detects_purchase_request_header_sum_mismatch(starter_dataset):
    """Verify detection of PR total not matching sum of lines."""
    corrupted = copy.deepcopy(starter_dataset)
    corrupted["purchase_requests"][0]["total_estimated_amount"] = 1234567

    results = validate_financial_reconciliation(corrupted)
    failures = [r for r in results if r.check_name == "financial_pr_total_estimate" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "purchase_requests"
    assert failures[0].actual_value == 1234567


def test_detects_quote_landed_cost_discrepancy(starter_dataset):
    """Verify detection of quote landed cost differing from merchandise + freight + duty + tax."""
    corrupted = copy.deepcopy(starter_dataset)
    corrupted["supplier_quotes"][0]["landed_cost_base"] = 99999.99

    results = validate_financial_reconciliation(corrupted)
    failures = [r for r in results if r.check_name == "financial_quote_landed_cost" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "supplier_quotes"


def test_detects_purchase_order_line_sum_mismatch(starter_dataset):
    """Verify detection of PO total amount != sum of PO lines."""
    corrupted = copy.deepcopy(starter_dataset)
    corrupted["purchase_orders"][0]["total_amount"] = 88888888

    results = validate_financial_reconciliation(corrupted)
    failures = [r for r in results if r.check_name == "financial_po_total_reconciliation" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "purchase_orders"


def test_detects_delivery_quantity_overrun(starter_dataset):
    """Verify detection of received quantities exceeding ordered quantity."""
    corrupted = copy.deepcopy(starter_dataset)
    # Inflate delivered items count on first delivery
    corrupted["deliveries"][0]["items_delivered_count"] = 999999

    results = validate_financial_reconciliation(corrupted)
    failures = [r for r in results if r.check_name == "delivery_quantity_bounds" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].severity == "CRITICAL"


def test_detects_budget_overrun(starter_dataset):
    """Verify detection of department encumbrances exceeding allocated budget."""
    corrupted = copy.deepcopy(starter_dataset)
    # Reduce allocation on first budget to $1.00 (100 cents)
    corrupted["budgets"][0]["allocated_amount"] = 100

    results = validate_financial_reconciliation(corrupted)
    failures = [r for r in results if r.check_name == "financial_budget_no_overrun" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "budgets"
    assert failures[0].severity == "CRITICAL"
