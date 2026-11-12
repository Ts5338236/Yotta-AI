"""Tests for foreign key and cross-entity relationship validation (Phase 4).

Verifies detection of:
- Missing department references
- Mismatched requester and PR department assignments
- Orphaned request lines and purchase orders
- Quotations from uninvited suppliers
"""

import copy
import pytest
from datagen.workflow import generate_procurement_workflow
from validate.checks import validate_foreign_keys


@pytest.fixture(scope="module")
def starter_dataset():
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_clean_dataset_passes_foreign_key_validation(starter_dataset):
    """Verify clean dataset passes all foreign key checks with 0 failures."""
    results = validate_foreign_keys(starter_dataset)
    failures = [r for r in results if not r.passed]
    assert len(failures) == 0, f"Expected 0 failures, got: {failures}"


def test_detects_missing_budget_department_reference(starter_dataset):
    """Verify detection of budget referencing non-existent department."""
    corrupted = copy.deepcopy(starter_dataset)
    corrupted["budgets"][0]["department_id"] = "DEPT-99"

    results = validate_foreign_keys(corrupted)
    failures = [r for r in results if r.check_name == "fk_budget_department" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].actual_value == "DEPT-99"
    assert failures[0].severity == "CRITICAL"


def test_detects_pr_requester_department_mismatch(starter_dataset):
    """Verify detection of PR department differing from requester department."""
    corrupted = copy.deepcopy(starter_dataset)
    # PR has department different from its requester's department
    pr = corrupted["purchase_requests"][0]
    pr["department_id"] = "DEPT-99"

    results = validate_foreign_keys(corrupted)
    failures = [r for r in results if r.check_name == "fk_pr_department_match" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "purchase_requests"
    assert failures[0].record_id == pr["request_id"]


def test_detects_uninvited_quoting_supplier(starter_dataset):
    """Verify detection of supplier quote from an uninvited supplier."""
    corrupted = copy.deepcopy(starter_dataset)
    # Change supplier_id on first quote to a supplier not invited to that RFQ
    quote = corrupted["supplier_quotes"][0]
    quote["supplier_id"] = "SUP-9999"

    results = validate_foreign_keys(corrupted)
    failures = [r for r in results if r.check_name == "fk_quote_supplier_was_invited" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "supplier_quotes"
    assert failures[0].record_id == quote["quote_id"]


def test_detects_competitive_po_missing_awarded_quote(starter_dataset):
    """Verify detection of competitive PO missing valid awarded quote reference."""
    corrupted = copy.deepcopy(starter_dataset)
    comp_pos = [p for p in corrupted["purchase_orders"] if p["sourcing_path"] == "competitive"]
    assert len(comp_pos) > 0
    comp_pos[0]["awarded_quote_id"] = "QUO-2026-999999"

    results = validate_foreign_keys(corrupted)
    failures = [r for r in results if r.check_name == "fk_competitive_po_awarded_quote" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].actual_value == "QUO-2026-999999"

