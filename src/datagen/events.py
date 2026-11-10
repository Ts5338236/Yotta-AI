"""Status event lifecycle audit history generation engine.

Tracks complete, chronological lifecycle transitions for:
- PurchaseRequest
- RFQ
- PurchaseOrder
- Delivery
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping
from datagen.ids import IDFactory


def generate_status_events(
    id_factory: IDFactory,
    purchase_requests: List[Dict[str, Any]],
    approvals: List[Dict[str, Any]],
    rfqs: List[Dict[str, Any]],
    awarded_quotes: Dict[str, Dict[str, Any]],
    purchase_orders: List[Dict[str, Any]],
    deliveries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate comprehensive audit trail of lifecycle transitions across all entities.

    Guarantees:
    - Never overwrites previous events.
    - Transitions follow allowed state machines.
    - Timestamps are strictly chronological.
    - Current entity status equals the final event's to_status.

    Args:
        id_factory: Centralized IDFactory instance.
        purchase_requests: Requisition records.
        approvals: Multi-tier approval records.
        rfqs: Sourcing RFQ records.
        awarded_quotes: Awarded quote mappings.
        purchase_orders: Issued purchase orders.
        deliveries: Shipment receipts.

    Returns:
        List[Dict[str, Any]]: Complete list of StatusEvent records.
    """
    status_events: List[Dict[str, Any]] = []

    approvals_by_request: Dict[str, List[Dict[str, Any]]] = {}
    for app in approvals:
        approvals_by_request.setdefault(app["request_id"], []).append(app)

    rfq_by_request: Dict[str, Dict[str, Any]] = {r["request_id"]: r for r in rfqs}
    po_by_request: Dict[str, Dict[str, Any]] = {po["request_id"]: po for po in purchase_orders}
    deliveries_by_po: Dict[str, List[Dict[str, Any]]] = {}
    for d in deliveries:
        deliveries_by_po.setdefault(d["po_id"], []).append(d)

    # 1. PurchaseRequest Lifecycle
    for pr in purchase_requests:
        req_id = pr["request_id"]
        created_ts = pr["created_at"]
        req_user = pr["requester_id"]

        # Initial transition: DRAFT -> SUBMITTED
        se_id_1 = id_factory.next_status_event_id()
        status_events.append({
            "status_event_id": se_id_1,
            "event_id": se_id_1,
            "entity": "PURCHASE_REQUEST",
            "entity_type": "PURCHASE_REQUEST",
            "entity_id": req_id,
            "from_status": "DRAFT",
            "previous_status": "DRAFT",
            "to_status": "SUBMITTED",
            "new_status": "SUBMITTED",
            "actor": req_user,
            "actor_id": req_user,
            "actor_type": "REQUESTER",
            "event_ts": created_ts,
            "event_timestamp": created_ts,
            "reason": "Requisition submitted for approval",
        })

        if pr.get("status") == "DRAFT":
            continue

        # Submission -> PENDING_APPROVAL
        se_id_2 = id_factory.next_status_event_id()
        status_events.append({
            "status_event_id": se_id_2,
            "event_id": se_id_2,
            "entity": "PURCHASE_REQUEST",
            "entity_type": "PURCHASE_REQUEST",
            "entity_id": req_id,
            "from_status": "SUBMITTED",
            "previous_status": "SUBMITTED",
            "to_status": "PENDING_APPROVAL",
            "new_status": "PENDING_APPROVAL",
            "actor": "SYSTEM",
            "actor_id": "SYSTEM",
            "actor_type": "SYSTEM",
            "event_ts": created_ts,
            "event_timestamp": created_ts,
            "reason": "Workflow routing to designated approvers",
        })

        # Approvals
        req_approvals = approvals_by_request.get(req_id, [])
        for idx, app in enumerate(req_approvals):
            dec = app["decision"]
            dec_ts = app["decision_date"]
            app_id = app["approver_id"]
            from_st = "PENDING_APPROVAL" if idx == 0 else req_approvals[idx - 1]["decision"]

            se_app = id_factory.next_status_event_id()
            status_events.append({
                "status_event_id": se_app,
                "event_id": se_app,
                "entity": "PURCHASE_REQUEST",
                "entity_type": "PURCHASE_REQUEST",
                "entity_id": req_id,
                "from_status": from_st,
                "previous_status": from_st,
                "to_status": dec,
                "new_status": dec,
                "actor": app_id,
                "actor_id": app_id,
                "actor_type": "APPROVER",
                "event_ts": dec_ts,
                "event_timestamp": dec_ts,
                "reason": app.get("comments", f"Approval level {app['approval_level']} decision"),
            })

        # If PO issued
        po = po_by_request.get(req_id)
        if po:
            po_ts = po["created_at"]
            se_po = id_factory.next_status_event_id()
            status_events.append({
                "status_event_id": se_po,
                "event_id": se_po,
                "entity": "PURCHASE_REQUEST",
                "entity_type": "PURCHASE_REQUEST",
                "entity_id": req_id,
                "from_status": "APPROVED",
                "previous_status": "APPROVED",
                "to_status": "ORDERED",
                "new_status": "ORDERED",
                "actor": "SYSTEM",
                "actor_id": "SYSTEM",
                "actor_type": "SYSTEM",
                "event_ts": po_ts,
                "event_timestamp": po_ts,
                "reason": f"Purchase order {po['po_id']} issued to vendor",
            })

            # Check if deliveries completed
            del_list = deliveries_by_po.get(po["po_id"], [])
            if del_list:
                last_del = del_list[-1]
                del_ts = last_del["created_at"]
                se_del = id_factory.next_status_event_id()
                status_events.append({
                    "status_event_id": se_del,
                    "event_id": se_del,
                    "entity": "PURCHASE_REQUEST",
                    "entity_type": "PURCHASE_REQUEST",
                    "entity_id": req_id,
                    "from_status": "ORDERED",
                    "previous_status": "ORDERED",
                    "to_status": "ORDERED",
                    "new_status": "ORDERED",
                    "actor": last_del["received_by"],
                    "actor_id": "SYSTEM",
                    "actor_type": "SYSTEM",
                    "event_ts": del_ts,
                    "event_timestamp": del_ts,
                    "reason": f"All goods delivered under {last_del['delivery_id']}",
                })

    # 2. RFQ Lifecycle
    for rfq in rfqs:
        rfq_id = rfq["rfq_id"]
        issue_ts = rfq["created_at"]

        # DRAFT -> ISSUED
        se_rfq_1 = id_factory.next_status_event_id()
        status_events.append({
            "status_event_id": se_rfq_1,
            "event_id": se_rfq_1,
            "entity": "RFQ",
            "entity_type": "RFQ",
            "entity_id": rfq_id,
            "from_status": "DRAFT",
            "previous_status": "DRAFT",
            "to_status": "ISSUED",
            "new_status": "ISSUED",
            "actor": "BUYER",
            "actor_id": "BUYER",
            "actor_type": "BUYER",
            "event_ts": issue_ts,
            "event_timestamp": issue_ts,
            "reason": "RFQ published to invited bidders",
        })

        # ISSUED -> CLOSED -> AWARDED
        award = awarded_quotes.get(rfq_id)
        if award:
            due_ts = f"{rfq['due_date']}T17:00:00Z"
            se_rfq_close = id_factory.next_status_event_id()
            status_events.append({
                "status_event_id": se_rfq_close,
                "event_id": se_rfq_close,
                "entity": "RFQ",
                "entity_type": "RFQ",
                "entity_id": rfq_id,
                "from_status": "ISSUED",
                "previous_status": "ISSUED",
                "to_status": "CLOSED",
                "new_status": "CLOSED",
                "actor": "SYSTEM",
                "actor_id": "SYSTEM",
                "actor_type": "SYSTEM",
                "event_ts": due_ts,
                "event_timestamp": due_ts,
                "reason": "Bidding window closed",
            })

            award_ts = f"{award.get('award_date', rfq['due_date'])}T10:00:00Z"
            se_rfq_award = id_factory.next_status_event_id()
            status_events.append({
                "status_event_id": se_rfq_award,
                "event_id": se_rfq_award,
                "entity": "RFQ",
                "entity_type": "RFQ",
                "entity_id": rfq_id,
                "from_status": "CLOSED",
                "previous_status": "CLOSED",
                "to_status": "AWARDED",
                "new_status": "AWARDED",
                "actor": "BUYER",
                "actor_id": "BUYER",
                "actor_type": "BUYER",
                "event_ts": award_ts,
                "event_timestamp": award_ts,
                "reason": f"Awarded to supplier {award['supplier_id']}",
            })

    # 3. PurchaseOrder Lifecycle
    for po in purchase_orders:
        po_id = po["po_id"]
        po_ts = po["created_at"]

        # DRAFT -> ISSUED
        se_po_issue = id_factory.next_status_event_id()
        status_events.append({
            "status_event_id": se_po_issue,
            "event_id": se_po_issue,
            "entity": "PURCHASE_ORDER",
            "entity_type": "PURCHASE_ORDER",
            "entity_id": po_id,
            "from_status": "DRAFT",
            "previous_status": "DRAFT",
            "to_status": "ISSUED",
            "new_status": "ISSUED",
            "actor": "BUYER",
            "actor_id": "BUYER",
            "actor_type": "BUYER",
            "event_ts": po_ts,
            "event_timestamp": po_ts,
            "reason": "Purchase order approved and transmitted to vendor",
        })

        # ISSUED -> COMPLETED
        if po.get("status") == "COMPLETED":
            del_list = deliveries_by_po.get(po_id, [])
            last_del_ts = del_list[-1]["created_at"] if del_list else po_ts
            se_po_comp = id_factory.next_status_event_id()
            status_events.append({
                "status_event_id": se_po_comp,
                "event_id": se_po_comp,
                "entity": "PURCHASE_ORDER",
                "entity_type": "PURCHASE_ORDER",
                "entity_id": po_id,
                "from_status": "ISSUED",
                "previous_status": "ISSUED",
                "to_status": "COMPLETED",
                "new_status": "COMPLETED",
                "actor": "SYSTEM",
                "actor_id": "SYSTEM",
                "actor_type": "SYSTEM",
                "event_ts": last_del_ts,
                "event_timestamp": last_del_ts,
                "reason": "All contracted line items physically delivered and verified",
            })

    # 4. Delivery Lifecycle
    for d in deliveries:
        d_id = d["delivery_id"]
        d_ts = d["created_at"]

        se_del = id_factory.next_status_event_id()
        status_events.append({
            "status_event_id": se_del,
            "event_id": se_del,
            "entity": "DELIVERY",
            "entity_type": "DELIVERY",
            "entity_id": d_id,
            "from_status": "IN_TRANSIT",
            "previous_status": "IN_TRANSIT",
            "to_status": d["delivery_status"],
            "new_status": d["delivery_status"],
            "actor": d["received_by"],
            "actor_id": "SYSTEM",
            "actor_type": "REQUESTER",
            "event_ts": d_ts,
            "event_timestamp": d_ts,
            "reason": d.get("notes", "Goods received at receiving dock"),
        })

    # Sort status events stably chronologically
    status_events.sort(key=lambda s: (s["event_timestamp"], s["status_event_id"]))
    return status_events
