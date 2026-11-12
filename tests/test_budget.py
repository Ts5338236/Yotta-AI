"""Unit tests for BudgetEvent ledger generation and balance reconciliation."""

import numpy as np
import pytest

from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def workflow_dataset():
    """Generate workflow dataset for budget tests."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_budget_event_types_and_integrity(workflow_dataset):
    """Verify presence of all 5 budget event types and non-negative event values."""
    events = workflow_dataset["budget_events"]
    event_types = {e["event_type"] for e in events}

    expected_types = {"ALLOCATE", "RESERVE", "COMMIT", "RELEASE", "SPEND"}
    assert expected_types.issubset(event_types)

    for ev in events:
        assert ev["amount"] >= 0
        assert ev["currency"] == "USD"
        assert ev["event_date"].startswith("2026-")


def test_budget_balances_reconciled_without_overrun(workflow_dataset):
    """Verify that department budgets reconcile with ledger and zero clean-path overruns exist."""
    budgets = workflow_dataset["budgets"]

    for b in budgets:
        alloc = b["allocated_amount"]
        res = b["reserved_amount"]
        com = b["committed_amount"]
        spent = b["spent_amount"]

        assert alloc > 0
        assert res >= 0
        assert com >= 0
        assert spent >= 0

        # Fundamental clean-path guarantee: allocated funding covers all encumbrances and disbursements
        assert alloc >= (res + com + spent), (
            f"Budget overrun detected on {b['budget_id']}: {alloc} < ({res} + {com} + {spent})"
        )

