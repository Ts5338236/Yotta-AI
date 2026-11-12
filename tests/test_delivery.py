"""Unit tests for delivery fulfillment, partial shipments, and goods receipt."""

import numpy as np
import pytest

from datagen.approvals import generate_approvals
from datagen.config import load_config
from datagen.delivery import generate_deliveries
from datagen.ids import IDFactory
from datagen.masters import generate_all_masters
from datagen.orders import generate_orders
from datagen.requests import generate_all_requests
from datagen.sourcing import classify_sourcing_paths, generate_sourcing


@pytest.fixture
def delivery_setup():
    """Setup purchase orders for delivery testing."""
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
    deliveries_data = generate_deliveries(
        config,
        rng,
        id_factory,
        order_data["purchase_orders"],
    )
    return config, order_data["purchase_orders"], deliveries_data["deliveries"]


def test_delivery_chronology_and_fulfillment(delivery_setup):
    """Verify delivery dates follow PO dates and cumulative quantities match PO contracted amounts."""
    config, pos, deliveries = delivery_setup

    po_map = {p["po_id"]: p for p in pos}
    del_by_po = {}
    for d in deliveries:
        assert d["po_id"] in po_map
        del_by_po.setdefault(d["po_id"], []).append(d)

    has_partial = False

    for po in pos:
        poid = po["po_id"]
        assert poid in del_by_po
        po_deliveries = del_by_po[poid]

        total_po_qty = sum(l["quantity"] for l in po.get("_lines", [])) or 1
        cum_qty = sum(d["items_delivered_count"] for d in po_deliveries)

        # 1. Cumulative quantity matches
        assert cum_qty == total_po_qty

        # 2. Chronological check: delivery on or after PO date
        for d in po_deliveries:
            assert d["delivery_date"] >= po["po_date"]
            assert d["items_delivered_count"] > 0

        # 3. Multi-shipment check
        if len(po_deliveries) > 1:
            has_partial = True
            assert po_deliveries[0]["delivery_status"] == "PARTIAL"
            assert po_deliveries[1]["delivery_status"] == "FULL"
            assert po_deliveries[1]["delivery_date"] >= po_deliveries[0]["delivery_date"]

        assert po["status"] == "COMPLETED"

    assert has_partial, "Expected at least one multi-shipment partial delivery scenario in dataset"

