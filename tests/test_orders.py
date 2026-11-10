"""Unit tests for Purchase Order and Purchase Order Line generation."""

import numpy as np
import pytest

from datagen.approvals import generate_approvals
from datagen.config import load_config
from datagen.ids import IDFactory
from datagen.masters import generate_all_masters
from datagen.orders import generate_orders
from datagen.requests import generate_all_requests
from datagen.sourcing import classify_sourcing_paths, generate_sourcing


@pytest.fixture
def orders_setup():
    """Setup procurement orders."""
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
    comp, non_comp = classify_sourcing_paths(config, rng, approval_data["approved_requests"])
    sourcing_data = generate_sourcing(
        config,
        rng,
        id_factory,
        comp,
        requests_data["request_lines"],
        masters["suppliers"],
    )
    order_data = generate_orders(
        config,
        rng,
        id_factory,
        comp,
        non_comp,
        sourcing_data["rfqs"],
        sourcing_data["awarded_quotes"],
        requests_data["request_lines"],
        masters["suppliers"],
    )
    return config, order_data, sourcing_data, approval_data


def test_purchase_orders_counts_and_types(orders_setup):
    """Verify PO volume, competitive vs non-competitive routing, and rejection isolation."""
    config, order_data, sourcing_data, approval_data = orders_setup
    pos = order_data["purchase_orders"]
    rejected = {r["request_id"] for r in approval_data["rejected_requests"]}

    assert len(pos) >= 85  # Starter scale target: ~90 POs

    comp_pos = [p for p in pos if p["sourcing_path"] == "competitive"]
    non_comp_pos = [p for p in pos if p["sourcing_path"] != "competitive"]

    assert len(comp_pos) == 50  # Exactly matches 50 competitive RFQs

    # No rejected request ever received a PO
    for po in pos:
        assert po["request_id"] not in rejected
        assert po["status"] == "ISSUED"


def test_purchase_order_lines_reconciliation(orders_setup):
    """Verify that PO line totals sum to PO total amount and line quantities are positive."""
    config, order_data, sourcing_data, approval_data = orders_setup
    pos = order_data["purchase_orders"]
    po_lines = order_data["purchase_order_lines"]

    lines_by_po = {}
    for pol in po_lines:
        lines_by_po.setdefault(pol["po_id"], []).append(pol)

    for po in pos:
        poid = po["po_id"]
        assert poid in lines_by_po
        lines = lines_by_po[poid]
        assert len(lines) >= 1

        total_cents = sum(l["line_total"] for l in lines)
        assert po["total_amount"] == total_cents
        assert po["value"] == round(total_cents / 100.0, 2)
        assert all(l["quantity"] > 0 for l in lines)
