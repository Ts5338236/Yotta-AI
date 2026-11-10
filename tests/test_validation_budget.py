"""Tests for budget ledger event and balance reconciliation validation (Phase 4).

Verifies detection of:
- Missing initial budget allocations
- Negative ledger event amounts
- Discrepancies between event ledger reconstruction and Budget master table
"""

import copy
import pytest
from datagen.workflow import generate_procurement_workflow
from validate.checks import validate_budget_ledger


@pytest.fixture(scope="module")
def starter_dataset():
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_clean_dataset_passes_budget_ledger_validation(starter_dataset):
    """Verify clean dataset complies with all double-entry ledger rules with 0 errors."""
    results = validate_budget_ledger(starter_dataset)
    failures = [r for r in results if not r.passed]
    assert len(failures) == 0, f"Expected 0 failures, got: {failures}"


def test_detects_negative_budget_event_amount(starter_dataset):
    """Verify detection of negative amount in budget ledger events."""
    corrupted = copy.deepcopy(starter_dataset)
    corrupted["budget_events"][0]["amount"] = -50000

    results = validate_budget_ledger(corrupted)
    failures = [r for r in results if r.check_name == "budget_event_amount_positive" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "budget_events"


def test_detects_missing_initial_budget_allocation(starter_dataset):
    """Verify detection when a department budget lacks an initial ALLOCATE event."""
    corrupted = copy.deepcopy(starter_dataset)
    bid = corrupted["budgets"][0]["budget_id"]
    # Remove all ALLOCATE events for this budget
    corrupted["budget_events"] = [
        ev for ev in corrupted["budget_events"]
        if not (ev["budget_id"] == bid and ev["event_type"] == "ALLOCATE")
    ]

    results = validate_budget_ledger(corrupted)
    failures = [
        r for r in results
        if r.check_name == "budget_has_initial_allocation" and r.record_id == bid and not r.passed
    ]
    assert len(failures) >= 1
    assert failures[0].severity == "CRITICAL"


def test_detects_reconciled_balance_mismatch(starter_dataset):
    """Verify detection when Budget table balance differs from event ledger."""
    corrupted = copy.deepcopy(starter_dataset)
    # Tamper with committed amount on first budget
    corrupted["budgets"][0]["committed_amount"] = 99999999

    results = validate_budget_ledger(corrupted)
    failures = [
        r for r in results
        if r.check_name == "budget_committed_reconciliation" and not r.passed
    ]
    assert len(failures) >= 1
    assert failures[0].entity == "budgets"
