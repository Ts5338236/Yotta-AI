"""Unit tests for sourcing classification, RFQ generation, and supplier invitations."""

import numpy as np
import pytest

from datagen.approvals import generate_approvals
from datagen.config import load_config
from datagen.ids import IDFactory
from datagen.masters import generate_all_masters
from datagen.requests import generate_all_requests
from datagen.sourcing import classify_sourcing_paths, generate_sourcing


@pytest.fixture
def sourcing_setup():
    """Setup approved requisitions for sourcing tests."""
    config = load_config()
    rng = np.random.default_rng(20261022)
    id_factory = IDFactory()
    masters = generate_all_masters(config, rng, id_factory)
    requests_data = generate_all_requests(
        config,
        rng,
        id_factory,
        masters["departments"],
        masters["budgets"],
        masters["requesters"],
    )
    approval_data = generate_approvals(
        config,
        rng,
        id_factory,
        requests_data["purchase_requests"],
        masters["approvers"],
    )
    return config, rng, id_factory, masters, requests_data, approval_data


def test_sourcing_path_classification(sourcing_setup):
    """Verify classification into competitive and non-competitive paths with valid reasons."""
    config, rng, id_factory, masters, requests_data, approval_data = sourcing_setup
    approved = approval_data["approved_requests"]

    comp, non_comp = classify_sourcing_paths(config, rng, approved)
    assert len(comp) == 50  # Target RFQ count for starter scale
    assert len(non_comp) > 0

    valid_paths = {"competitive", "catalogue", "single_source", "contract"}
    valid_reasons = {"sole_supplier", "urgent", "contract"}

    for pr in comp:
        assert pr["sourcing_path"] == "competitive"
        assert pr["sourcing_type"] == "COMPETITIVE"

    for pr in non_comp:
        assert pr["sourcing_path"] in valid_paths
        assert pr["single_source_reason_code"] in valid_reasons


def test_rfq_and_supplier_invitations_integrity(sourcing_setup):
    """Verify RFQ constraints, 1:1 PR relationship, and supplier invitation uniqueness."""
    config, rng, id_factory, masters, requests_data, approval_data = sourcing_setup
    comp, _ = classify_sourcing_paths(config, rng, approval_data["approved_requests"])

    sourcing_data = generate_sourcing(
        config,
        rng,
        id_factory,
        comp,
        requests_data["request_lines"],
        masters["suppliers"],
    )

    rfqs = sourcing_data["rfqs"]
    invites = sourcing_data["rfq_supplier_invites"]

    assert len(rfqs) == len(comp)

    # 1. Exactly 1 RFQ per PR
    rfq_pr_ids = [r["request_id"] for r in rfqs]
    assert len(rfq_pr_ids) == len(set(rfq_pr_ids))

    # 2. Check invitation counts per RFQ
    invites_by_rfq = {}
    seen_pairs = set()
    for inv in invites:
        rfq_id = inv["rfq_id"]
        sup_id = inv["supplier_id"]
        pair = (rfq_id, sup_id)
        assert pair not in seen_pairs, f"Duplicate invite for RFQ {rfq_id} and supplier {sup_id}"
        seen_pairs.add(pair)
        invites_by_rfq.setdefault(rfq_id, []).append(inv)

    for rfq in rfqs:
        rfq_invites = invites_by_rfq.get(rfq["rfq_id"], [])
        assert len(rfq_invites) >= 3, f"RFQ {rfq['rfq_id']} has fewer than 3 supplier invitations"
        assert rfq["due_date"] > rfq["issue_date"]

