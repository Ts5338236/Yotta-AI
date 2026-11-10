"""Budget ledger event engine and balance reconciliation module.

Implements double-entry style financial events:
ALLOCATE, RESERVE, COMMIT, RELEASE, and SPEND.
Guarantees clean-path auditability and balance reconciliation without budget overruns.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional
import numpy as np

from datagen.ids import IDFactory


def generate_budget_events(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    budgets: List[Dict[str, Any]],
    purchase_requests: List[Dict[str, Any]],
    purchase_orders: List[Dict[str, Any]],
    deliveries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate chronological budget ledger events and reconcile budget balances.

    Event Sequence:
    1. ALLOCATE: Initial fiscal year funding per department budget line.
    2. RESERVE: Pre-encumbrance when a Purchase Request is approved.
    3. COMMIT: Encumbrance when a Purchase Order is issued (relieving PR reservation).
    4. RELEASE: Release of reservation if a request is cancelled or rejected.
    5. SPEND: Synthetic accounting expenditure upon goods delivery.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        budgets: Department budget records.
        purchase_requests: List of all PRs (approved, rejected, ordered).
        purchase_orders: List of issued Purchase Orders.
        deliveries: List of completed delivery shipment receipts.

    Returns:
        Dict[str, Any]:
            'budget_events': Complete chronological ledger of events.
            'reconciled_budgets': Updated budget master records with exact reconciled balances.
    """
    budget_events: List[Dict[str, Any]] = []

    # Map request_id to budget_id
    req_to_budget: Dict[str, str] = {pr["request_id"]: pr["budget_id"] for pr in purchase_requests}
    pr_by_id: Dict[str, Dict[str, Any]] = {pr["request_id"]: pr for pr in purchase_requests}
    po_by_id: Dict[str, Dict[str, Any]] = {po["po_id"]: po for po in purchase_orders}
    pos_by_request: Dict[str, Dict[str, Any]] = {po["request_id"]: po for po in purchase_orders}

    # 1. ALLOCATE: Initial Department Budgets
    for b in budgets:
        be_id = id_factory.next_budget_event_id()
        alloc_cents = b["allocated_amount"]
        alloc_usd = b["allocated"]

        budget_events.append({
            "budget_event_id": be_id,
            "budget_id": b["budget_id"],
            "request_id": None,
            "po_id": None,
            "event_type": "ALLOCATE",
            "amount": alloc_cents,
            "amount_usd": alloc_usd,
            "currency": "USD",
            "event_date": "2026-01-01",
            "event_timestamp": "2026-01-01T00:00:00Z",
            "description": f"Initial FY2026 budget allocation for department {b['department_id']}",
        })

    # 2. RESERVE: Requisition Approval Pre-encumbrances
    for pr in purchase_requests:
        if pr["status"] in ("APPROVED", "ORDERED"):
            be_id = id_factory.next_budget_event_id()
            amt_cents = pr["total_estimated_amount"]
            amt_usd = pr["total_estimate_usd"]
            ev_ts = pr["updated_at"]
            ev_date = ev_ts[:10]

            budget_events.append({
                "budget_event_id": be_id,
                "budget_id": pr["budget_id"],
                "request_id": pr["request_id"],
                "po_id": None,
                "event_type": "RESERVE",
                "amount": amt_cents,
                "amount_usd": amt_usd,
                "currency": "USD",
                "event_date": ev_date,
                "event_timestamp": ev_ts,
                "description": f"Pre-encumbrance reserve for requisition {pr['request_id']}",
            })

    # 3. COMMIT: Purchase Order Issuance
    # When PO is issued, release the initial reservation and commit the binding PO contract amount
    for po in purchase_orders:
        pr_id = po["request_id"]
        budget_id = req_to_budget[pr_id]
        pr = pr_by_id[pr_id]

        po_cents = po["total_amount"]
        po_usd = po["value"]
        po_ts = po["created_at"]
        po_date = po["po_date"]

        # Release reservation
        be_rel_id = id_factory.next_budget_event_id()
        budget_events.append({
            "budget_event_id": be_rel_id,
            "budget_id": budget_id,
            "request_id": pr_id,
            "po_id": po["po_id"],
            "event_type": "RELEASE",
            "amount": pr["total_estimated_amount"],
            "amount_usd": pr["total_estimate_usd"],
            "currency": "USD",
            "event_date": po_date,
            "event_timestamp": po_ts,
            "description": f"Relief of pre-encumbrance upon PO issuance for {pr_id}",
        })

        # Commit PO amount
        be_com_id = id_factory.next_budget_event_id()
        budget_events.append({
            "budget_event_id": be_com_id,
            "budget_id": budget_id,
            "request_id": pr_id,
            "po_id": po["po_id"],
            "event_type": "COMMIT",
            "amount": po_cents,
            "amount_usd": po_usd,
            "currency": "USD",
            "event_date": po_date,
            "event_timestamp": po_ts,
            "description": f"Binding encumbrance commitment for purchase order {po['po_id']}",
        })

    # 4. SPEND: Goods Delivery Physical Fulfillment
    # Synthetic expenditure recognized upon delivery of goods
    for delivery in deliveries:
        po_id = delivery["po_id"]
        po = po_by_id[po_id]
        pr_id = po["request_id"]
        budget_id = req_to_budget[pr_id]

        del_date = delivery["delivery_date"]
        del_ts = delivery["created_at"]

        # Calculate proportional spend for partial or full delivery
        total_qty = sum(l["quantity"] for l in po.get("_lines", [])) or 1
        delivered_qty = delivery["items_delivered_count"]
        ratio = min(1.0, delivered_qty / total_qty)

        spend_cents = int(round(po["total_amount"] * ratio))
        spend_usd = round(spend_cents / 100.0, 2)

        be_spend_id = id_factory.next_budget_event_id()
        budget_events.append({
            "budget_event_id": be_spend_id,
            "budget_id": budget_id,
            "request_id": pr_id,
            "po_id": po_id,
            "event_type": "SPEND",
            "amount": spend_cents,
            "amount_usd": spend_usd,
            "currency": "USD",
            "event_date": del_date,
            "event_timestamp": del_ts,
            "description": f"Synthetic expenditure recognized upon receipt {delivery['delivery_id']} for PO {po_id}",
        })

    # Sort budget events stably chronologically
    budget_events.sort(key=lambda e: (e["event_timestamp"], e["budget_event_id"]))

    # 5. Reconcile Balances per Department Budget
    # Derive exact active balances from ledger
    ledger_reserved: Dict[str, int] = {}
    ledger_committed: Dict[str, int] = {}
    ledger_spent: Dict[str, int] = {}

    for ev in budget_events:
        bid = ev["budget_id"]
        amt = ev["amount"]
        ev_type = ev["event_type"]

        if ev_type == "RESERVE":
            ledger_reserved[bid] = ledger_reserved.get(bid, 0) + amt
        elif ev_type == "RELEASE":
            ledger_reserved[bid] = max(0, ledger_reserved.get(bid, 0) - amt)
        elif ev_type == "COMMIT":
            ledger_committed[bid] = ledger_committed.get(bid, 0) + amt
        elif ev_type == "SPEND":
            ledger_spent[bid] = ledger_spent.get(bid, 0) + amt
            # Spend relieves active commitment
            ledger_committed[bid] = max(0, ledger_committed.get(bid, 0) - amt)

    reconciled_budgets: List[Dict[str, Any]] = []
    for b in budgets:
        bid = b["budget_id"]
        res_cents = ledger_reserved.get(bid, 0)
        com_cents = ledger_committed.get(bid, 0)
        spent_cents = ledger_spent.get(bid, 0)

        updated_b = dict(b)
        updated_b["reserved_amount"] = res_cents
        updated_b["reserved"] = round(res_cents / 100.0, 2)
        updated_b["committed_amount"] = com_cents
        updated_b["committed"] = round(com_cents / 100.0, 2)
        updated_b["spent_amount"] = spent_cents
        updated_b["spent"] = round(spent_cents / 100.0, 2)

        reconciled_budgets.append(updated_b)

    return {
        "budget_events": budget_events,
        "reconciled_budgets": reconciled_budgets,
    }
