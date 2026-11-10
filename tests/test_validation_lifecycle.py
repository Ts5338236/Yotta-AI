"""Tests for lifecycle state machine and event sequence validation (Phase 4).

Verifies detection of:
- Discontinuous status sequences (from_status != previous event's to_status)
- Disallowed status transitions
- PO issued for rejected requisition
"""

import copy
import pytest
from datagen.workflow import generate_procurement_workflow
from validate.checks import validate_lifecycle_state_machine


@pytest.fixture(scope="module")
def starter_dataset():
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_clean_dataset_passes_lifecycle_validation(starter_dataset):
    """Verify clean dataset complies with all state transition rules with 0 errors."""
    results = validate_lifecycle_state_machine(starter_dataset)
    failures = [r for r in results if not r.passed]
    assert len(failures) == 0, f"Expected 0 failures, got: {failures}"


def test_detects_state_sequence_discontinuity(starter_dataset):
    """Verify detection when an event's from_status does not match preceding event's to_status."""
    corrupted = copy.deepcopy(starter_dataset)
    # Corrupt second event on first PR
    pr_events = [
        ev for ev in corrupted["status_events"]
        if (ev.get("entity_type") or ev.get("entity")) == "PURCHASE_REQUEST"
        and ev["entity_id"] == corrupted["purchase_requests"][0]["request_id"]
    ]
    assert len(pr_events) >= 2
    pr_events[1]["from_status"] = "CLOSED"  # Corrupt jump from CLOSED

    results = validate_lifecycle_state_machine(corrupted)
    failures = [r for r in results if r.check_name == "lifecycle_state_continuity" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "PURCHASE_REQUEST"


def test_detects_disallowed_state_transition(starter_dataset):
    """Verify detection of an illegal transition (e.g. DRAFT -> DELIVERED)."""
    corrupted = copy.deepcopy(starter_dataset)
    pr_events = [
        ev for ev in corrupted["status_events"]
        if (ev.get("entity_type") or ev.get("entity")) == "PURCHASE_REQUEST"
    ]
    pr_events[0]["from_status"] = "DRAFT"
    pr_events[0]["to_status"] = "DELIVERED"  # Illegal jump

    results = validate_lifecycle_state_machine(corrupted)
    failures = [r for r in results if r.check_name == "lifecycle_pr_valid_transition" and not r.passed]
    assert len(failures) >= 1


def test_detects_po_issued_for_rejected_requisition(starter_dataset):
    """Verify critical failure if a PO is issued against a REJECTED purchase request."""
    corrupted = copy.deepcopy(starter_dataset)
    # Mark first PR as REJECTED
    pr = corrupted["purchase_requests"][0]
    pr["status"] = "REJECTED"
    # Ensure there is a PO pointing to it
    corrupted["purchase_orders"][0]["request_id"] = pr["request_id"]

    results = validate_lifecycle_state_machine(corrupted)
    failures = [r for r in results if r.check_name == "lifecycle_rejected_pr_no_po" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].severity == "CRITICAL"
