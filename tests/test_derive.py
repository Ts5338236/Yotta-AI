"""Unit tests for centralized derived fields engine (Phase 4).

Verifies exact calculation and recalculation of:
- Request line and purchase request totals
- Quote landed costs and multicriteria supplier scores
- PO line and PO totals
- Delivery fulfillment summaries and operational KPIs
- Current lifecycle statuses from StatusEvents
- Reconciled budget ledger balances
"""

import copy
import pytest
from datagen.derive import (
    derive_all,
    derive_budget_balances,
    derive_current_statuses,
    derive_delivery_metrics,
    derive_delivery_summaries,
    derive_purchase_order_line_totals,
    derive_purchase_order_totals,
    derive_purchase_request_totals,
    derive_quote_landed_costs,
    derive_request_line_totals,
    derive_supplier_scores,
)
from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def starter_dataset():
    """Shared deterministic starter-scale dataset for testing derivations."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_derive_request_line_totals():
    """Verify line total recalculation from quantity and unit price."""
    lines = [
        {"quantity": 5, "estimated_unit_price": 2000, "item": "Widget A"},  # $20.00 each -> $100.00
        {"quantity": 2, "estimated_unit_price": 15050, "item": "Tool B"},  # $150.50 each -> $301.00
    ]
    derived = derive_request_line_totals(lines)
    assert derived[0]["estimated_line_total"] == 10000
    assert derived[0]["line_total"] == 100.0
    assert derived[1]["estimated_line_total"] == 30100
    assert derived[1]["line_total"] == 301.0


def test_derive_purchase_request_totals():
    """Verify purchase request total is strictly the sum of its request lines."""
    lines = [
        {"request_id": "PR-2026-000001", "estimated_line_total": 50000, "line_total": 500.0, "quantity": 5},
        {"request_id": "PR-2026-000001", "estimated_line_total": 25000, "line_total": 250.0, "quantity": 2},
        {"request_id": "PR-2026-000002", "estimated_line_total": 10000, "line_total": 100.0, "quantity": 1},
    ]
    prs = [
        {"request_id": "PR-2026-000001", "total_estimated_amount": 0, "total_estimate_usd": 0.0},
        {"request_id": "PR-2026-000002", "total_estimated_amount": 0, "total_estimate_usd": 0.0},
    ]
    totals = derive_purchase_request_totals(lines, prs)

    assert totals["PR-2026-000001"]["total_estimated_amount"] == 75000
    assert totals["PR-2026-000001"]["total_estimate_usd"] == 750.0
    assert totals["PR-2026-000001"]["line_count"] == 2
    assert prs[0]["total_estimated_amount"] == 75000
    assert prs[0]["total_estimate_usd"] == 750.0

    assert totals["PR-2026-000002"]["total_estimated_amount"] == 10000
    assert totals["PR-2026-000002"]["total_estimate_usd"] == 100.0
    assert prs[1]["total_estimated_amount"] == 10000


def test_derive_quote_landed_costs():
    """Verify quote landed cost calculation includes freight, duty, and taxes."""
    quotes = [{
        "quote_id": "QUO-2026-000001",
        "currency": "USD",
        "fx_rate_to_base": 1.0,
        "freight": 50.0,
        "duty": 25.0,
        "tax_nonrecoverable": 30.0,
    }]
    lines = [
        {"quote_id": "QUO-2026-000001", "line_total": 100000, "line_total_base": 100000},  # $1,000.00
    ]
    derived = derive_quote_landed_costs(quotes, lines)
    quo_res = derived["QUO-2026-000001"]

    # Merchandise = $1,000.00, Landed = 1000 + 50 + 25 + 30 = $1,105.00
    assert quo_res["total_quoted_amount_usd"] == 1000.0
    assert quo_res["landed_cost_base"] == 1105.0
    assert quo_res["landed_cost_cents"] == 110500


def test_derive_supplier_scores():
    """Verify multicriteria supplier scoring normalization and weighting."""
    config = {
        "supplier_scoring_weights": {
            "cost_weight": 0.60,
            "lead_time_weight": 0.25,
            "risk_rating_weight": 0.15,
        }
    }
    quotes = [
        {"quote_id": "Q1", "rfq_id": "RFQ-1", "landed_cost_base": 1000.0, "lead_time_days": 10, "risk_score": 0.10},
        {"quote_id": "Q2", "rfq_id": "RFQ-1", "landed_cost_base": 2000.0, "lead_time_days": 20, "risk_score": 0.90},
    ]
    scores = derive_supplier_scores(quotes, config)

    # Q1 is minimum in all 3 dimensions -> normalized factors are 0.0 -> score = 0.0
    assert scores["Q1"] == 0.0
    # Q2 is maximum in all 3 dimensions -> normalized factors are 1.0 -> score = 0.60 + 0.25 + 0.15 = 1.0
    assert scores["Q2"] == 1.0


def test_derive_purchase_order_totals():
    """Verify PO totals reconcile with PO lines."""
    po_lines = [
        {"po_id": "PO-1", "quantity": 10, "unit_price": 500},   # $50.00
        {"po_id": "PO-1", "quantity": 2, "unit_price": 2500},   # $50.00
    ]
    pos = [{"po_id": "PO-1", "total_amount": 0, "value": 0.0}]
    derive_purchase_order_line_totals(po_lines)
    totals = derive_purchase_order_totals(po_lines, pos)

    assert totals["PO-1"]["total_amount"] == 10000
    assert totals["PO-1"]["value"] == 100.0
    assert pos[0]["total_amount"] == 10000
    assert pos[0]["value"] == 100.0


def test_derive_delivery_summaries():
    """Verify cumulative delivered quantities and fulfillment status."""
    pos = [{"po_id": "PO-1", "value": 100.0}]
    po_lines = [{"po_id": "PO-1", "quantity": 10}]
    deliveries = [
        {"po_id": "PO-1", "items_delivered_count": 6, "delivery_status": "PARTIAL", "delivery_date": "2026-03-01"},
        {"po_id": "PO-1", "items_delivered_count": 4, "delivery_status": "DELIVERED", "delivery_date": "2026-03-05"},
    ]
    summaries = derive_delivery_summaries(deliveries, pos, po_lines)
    summary = summaries["PO-1"]

    assert summary["shipment_count"] == 2
    assert summary["delivered_quantity"] == 10
    assert summary["ordered_quantity"] == 10
    assert summary["is_fully_delivered"] is True
    assert summary["latest_delivery_date"] == "2026-03-05"


def test_derive_current_statuses():
    """Verify latest StatusEvent determines current entity status."""
    events = [
        {"entity_type": "PURCHASE_REQUEST", "entity_id": "PR-1", "to_status": "DRAFT", "event_timestamp": "2026-01-01T10:00:00Z", "status_event_id": "SE-01"},
        {"entity_type": "PURCHASE_REQUEST", "entity_id": "PR-1", "to_status": "SUBMITTED", "event_timestamp": "2026-01-01T10:05:00Z", "status_event_id": "SE-02"},
        {"entity_type": "PURCHASE_REQUEST", "entity_id": "PR-1", "to_status": "APPROVED", "event_timestamp": "2026-01-02T14:00:00Z", "status_event_id": "SE-03"},
    ]
    statuses = derive_current_statuses(events)
    assert statuses[("PURCHASE_REQUEST", "PR-1")] == "APPROVED"


def test_derive_budget_balances():
    """Verify double-entry budget ledger event processing and balance equation."""
    events = [
        {"budget_id": "BUD-01", "event_type": "ALLOCATE", "amount": 1000000, "event_timestamp": "2026-01-01T00:00:00Z", "budget_event_id": "BE-1"},
        {"budget_id": "BUD-01", "event_type": "RESERVE", "amount": 200000, "event_timestamp": "2026-01-05T09:00:00Z", "budget_event_id": "BE-2"},
        {"budget_id": "BUD-01", "event_type": "RELEASE", "amount": 200000, "event_timestamp": "2026-01-10T09:00:00Z", "budget_event_id": "BE-3"},
        {"budget_id": "BUD-01", "event_type": "COMMIT", "amount": 150000, "event_timestamp": "2026-01-10T10:00:00Z", "budget_event_id": "BE-4"},
        {"budget_id": "BUD-01", "event_type": "SPEND", "amount": 150000, "event_timestamp": "2026-01-20T10:00:00Z", "budget_event_id": "BE-5"},
    ]
    balances = derive_budget_balances(events)
    b = balances["BUD-01"]

    assert b["allocated_amount"] == 1000000
    assert b["reserved_amount"] == 0
    assert b["committed_amount"] == 0
    assert b["spent_amount"] == 150000
    assert b["available_amount"] == 850000
    assert b["allocated"] == 10000.0
    assert b["available"] == 8500.0


def test_derive_all_integration(starter_dataset):
    """Verify derive_all runs cleanly against a complete dataset."""
    derived = derive_all(starter_dataset)
    assert "pr_totals" in derived
    assert "quote_costs" in derived
    assert "supplier_scores" in derived
    assert "po_totals" in derived
    assert "delivery_summaries" in derived
    assert "delivery_metrics" in derived
    assert "current_statuses" in derived
    assert "budget_balances" in derived
    assert derived["delivery_metrics"]["on_time_rate"] > 0.70

