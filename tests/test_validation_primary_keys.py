"""Tests for primary key and identifier format validation (Phase 4).

Verifies detection of:
- Duplicate primary keys
- Null or empty primary keys
- Malformed IDs violating canonical regex patterns
- Duplicate compound business identifiers
"""

import copy
import pytest
from datagen.workflow import generate_procurement_workflow
from validate.checks import validate_primary_keys_and_ids


@pytest.fixture(scope="module")
def starter_dataset():
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_clean_dataset_passes_primary_key_validation(starter_dataset):
    """Verify clean dataset passes all primary key checks with zero failures."""
    results = validate_primary_keys_and_ids(starter_dataset)
    failures = [r for r in results if not r.passed]
    assert len(failures) == 0, f"Expected 0 failures, got: {failures}"


def test_detects_duplicate_primary_key(starter_dataset):
    """Verify validator detects an intentionally injected duplicate primary key."""
    corrupted = copy.deepcopy(starter_dataset)
    # Duplicate first department ID onto the second department
    first_id = corrupted["departments"][0]["department_id"]
    corrupted["departments"][1]["department_id"] = first_id

    results = validate_primary_keys_and_ids(corrupted)
    failures = [r for r in results if r.check_name == "pk_uniqueness" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "departments"
    assert failures[0].record_id == first_id
    assert failures[0].severity == "CRITICAL"


def test_detects_null_or_empty_primary_key(starter_dataset):
    """Verify validator detects null or empty primary keys."""
    corrupted = copy.deepcopy(starter_dataset)
    corrupted["purchase_requests"][0]["request_id"] = ""

    results = validate_primary_keys_and_ids(corrupted)
    failures = [r for r in results if r.check_name == "pk_not_null" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "purchase_requests"
    assert failures[0].severity == "CRITICAL"


def test_detects_malformed_id_regex_violation(starter_dataset):
    """Verify validator detects an invalid ID format."""
    corrupted = copy.deepcopy(starter_dataset)
    # Valid format: PO-2026-XXXXXX; Inject invalid format
    corrupted["purchase_orders"][0]["po_id"] = "PURCHASE-ORDER-999"

    results = validate_primary_keys_and_ids(corrupted)
    failures = [r for r in results if r.check_name == "pk_id_format" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].record_id == "PURCHASE-ORDER-999"
    assert failures[0].entity == "purchase_orders"


def test_detects_duplicate_rfq_supplier_invitation(starter_dataset):
    """Verify validator detects duplicate (rfq_id, supplier_id) invitation combinations."""
    corrupted = copy.deepcopy(starter_dataset)
    # Duplicate first invite
    first_inv = corrupted["rfq_supplier_invites"][0]
    corrupted["rfq_supplier_invites"].append({
        "invite_id": "INV-2026-999999",
        "rfq_id": first_inv["rfq_id"],
        "supplier_id": first_inv["supplier_id"],
    })

    results = validate_primary_keys_and_ids(corrupted)
    failures = [r for r in results if r.check_name == "rfq_invite_uniqueness" and not r.passed]
    assert len(failures) >= 1
    assert failures[0].entity == "rfq_supplier_invites"
