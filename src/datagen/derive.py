"""Centralized Derived Fields Engine (Phase 4).

Responsible for pure, deterministic calculation and recalculation of all
derived metrics, aggregates, and financial summaries directly from source records.

Covers:
- RequestLine and PurchaseRequest financial totals
- QuoteLine and SupplierQuote landed costs and multi-currency conversions
- Multicriteria supplier scores and normalization
- PurchaseOrderLine and PurchaseOrder monetary totals
- Cumulative delivery receipts and fulfillment summaries
- Current lifecycle statuses from immutable StatusEvents
- Reconciled budget ledger balances from double-entry BudgetEvents
- Overall delivery performance metrics
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Tuple


def derive_request_line_totals(
    request_lines: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Recalculate exact line totals for purchase request lines.

    Formula:
        line_total_cents = quantity * estimated_unit_price (cents)
        line_total = round(line_total_cents / 100.0, 2)

    Args:
        request_lines: Raw or generated request line records.

    Returns:
        List[Dict[str, Any]]: Updated request lines with derived totals.
    """
    for line in request_lines:
        qty = int(line.get("quantity") or line.get("qty") or 0)
        # Unit price in cents
        unit_price_cents = line.get("estimated_unit_price")
        if unit_price_cents is None:
            unit_est = float(line.get("unit_estimate", 0.0))
            unit_price_cents = int(round(unit_est * 100))
            line["estimated_unit_price"] = unit_price_cents

        line_total_cents = qty * unit_price_cents
        line["estimated_line_total"] = line_total_cents
        line["line_total"] = round(line_total_cents / 100.0, 2)

    return request_lines


def derive_purchase_request_totals(
    request_lines: List[Dict[str, Any]],
    purchase_requests: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Recalculate Purchase Request financial totals directly from request lines.

    Formula:
        total_estimated_amount = SUM(estimated_line_total)
        total_estimate_usd = round(total_estimated_amount / 100.0, 2)

    Args:
        request_lines: Request line records.
        purchase_requests: Optional list of PR headers to update in-place.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of request_id to derived totals dict.
    """
    totals_by_req: Dict[str, Dict[str, Any]] = {}

    for line in request_lines:
        req_id = line["request_id"]
        if req_id not in totals_by_req:
            totals_by_req[req_id] = {
                "total_estimated_amount": 0,
                "total_estimate_usd": 0.0,
                "line_count": 0,
                "total_quantity": 0,
            }

        line_cents = line.get("estimated_line_total")
        if line_cents is None:
            line_cents = int(round(float(line.get("line_total", 0.0)) * 100))

        qty = int(line.get("quantity") or line.get("qty") or 0)

        totals_by_req[req_id]["total_estimated_amount"] += line_cents
        totals_by_req[req_id]["line_count"] += 1
        totals_by_req[req_id]["total_quantity"] += qty

    for req_id, data in totals_by_req.items():
        data["total_estimate_usd"] = round(data["total_estimated_amount"] / 100.0, 2)

    if purchase_requests:
        for pr in purchase_requests:
            req_id = pr["request_id"]
            if req_id in totals_by_req:
                derived = totals_by_req[req_id]
                pr["total_estimated_amount"] = derived["total_estimated_amount"]
                pr["total_estimate_usd"] = derived["total_estimate_usd"]

    return totals_by_req


def derive_quote_landed_costs(
    quotes: List[Dict[str, Any]],
    quote_lines: List[Dict[str, Any]],
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Recalculate supplier quotation merchandise totals and landed costs.

    Formula:
        total_quoted_amount = SUM(quote_line.line_total)  [native currency cents]
        total_quoted_amount_base = SUM(quote_line.line_total_base) [USD cents]
        landed_cost_base = merchandise_usd + freight + duty + tax_nonrecoverable

    Args:
        quotes: Supplier quote records.
        quote_lines: Itemized quote line records.
        config: Optional configuration dictionary.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of quote_id to derived cost metrics.
    """
    lines_by_quote: Dict[str, List[Dict[str, Any]]] = {}
    for ql in quote_lines:
        lines_by_quote.setdefault(ql["quote_id"], []).append(ql)

    derived_costs: Dict[str, Dict[str, Any]] = {}

    for q in quotes:
        qid = q["quote_id"]
        lines = lines_by_quote.get(qid, [])

        curr_cents = 0
        base_cents = 0

        for line in lines:
            line_curr = line.get("line_total")
            if line_curr is None:
                qty = int(line.get("quantity") or line.get("quoted_quantity") or 0)
                uprice = int(line.get("unit_price") or 0)
                line_curr = qty * uprice
                line["line_total"] = line_curr
            curr_cents += line_curr

            line_base = line.get("line_total_base")
            if line_base is None:
                fx = float(q.get("fx_rate_to_base", 1.0))
                line_base = int(round(line_curr * fx))
                line["line_total_base"] = line_base
            base_cents += line_base

        total_base_usd = round(base_cents / 100.0, 2)
        freight = float(q.get("freight", 0.0))
        duty = float(q.get("duty", 0.0))
        tax = float(q.get("tax_nonrecoverable", 0.0))
        landed_usd = round(total_base_usd + freight + duty + tax, 2)
        landed_cents = int(round(landed_usd * 100))

        derived = {
            "total_quoted_amount": curr_cents,
            "total_quoted_amount_base": base_cents,
            "total_quoted_amount_usd": total_base_usd,
            "freight": freight,
            "duty": duty,
            "tax_nonrecoverable": tax,
            "landed_cost_base": landed_usd,
            "landed_cost_cents": landed_cents,
        }
        derived_costs[qid] = derived

        # Update quote record
        q["total_quoted_amount"] = curr_cents
        q["total_quoted_amount_base"] = base_cents
        q["total_quoted_amount_usd"] = total_base_usd
        q["landed_cost_base"] = landed_usd

    return derived_costs


def derive_supplier_scores(
    quotes: List[Dict[str, Any]],
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, float]:
    """Calculate multicriteria scores across competing quotations for each RFQ.

    Formula:
        score = cost_w * cost_norm + lead_w * lead_norm + risk_w * risk_norm
        Where normalized = (val - min) / (max - min) if max > min else 0.0.

    Args:
        quotes: List of supplier quotes.
        config: Optional configuration dictionary.

    Returns:
        Dict[str, float]: Mapping of quote_id to derived composite score.
    """
    weights = (config or {}).get("supplier_scoring_weights", {})
    cost_w = float(weights.get("cost_weight", 0.60))
    lead_w = float(weights.get("lead_time_weight", 0.25))
    risk_w = float(weights.get("risk_rating_weight", 0.15))

    quotes_by_rfq: Dict[str, List[Dict[str, Any]]] = {}
    for q in quotes:
        quotes_by_rfq.setdefault(q["rfq_id"], []).append(q)

    derived_scores: Dict[str, float] = {}

    for rfq_id, rfq_quotes in quotes_by_rfq.items():
        costs = [float(q.get("landed_cost_base", 0.0)) for q in rfq_quotes]
        leads = [float(q.get("lead_time_days", 0)) for q in rfq_quotes]
        risks = [float(q.get("risk_score", 0.0)) for q in rfq_quotes]

        min_c, max_c = min(costs), max(costs)
        min_l, max_l = min(leads), max(leads)
        min_r, max_r = min(risks), max(risks)

        for q in rfq_quotes:
            c = float(q.get("landed_cost_base", 0.0))
            l = float(q.get("lead_time_days", 0))
            r = float(q.get("risk_score", 0.0))

            c_norm = (c - min_c) / (max_c - min_c) if max_c > min_c else 0.0
            l_norm = (l - min_l) / (max_l - min_l) if max_l > min_l else 0.0
            r_norm = (r - min_r) / (max_r - min_r) if max_r > min_r else 0.0

            # Bounds clamping [0.0, 1.0]
            c_norm = max(0.0, min(1.0, c_norm))
            l_norm = max(0.0, min(1.0, l_norm))
            r_norm = max(0.0, min(1.0, r_norm))

            score = round(cost_w * c_norm + lead_w * l_norm + risk_w * r_norm, 4)
            derived_scores[q["quote_id"]] = score
            q["score"] = score

    return derived_scores


def derive_purchase_order_line_totals(
    po_lines: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Recalculate Purchase Order line totals.

    Formula:
        line_total = quantity * unit_price (cents)
        line_total_usd = round(line_total / 100.0, 2)

    Args:
        po_lines: Purchase order line records.

    Returns:
        List[Dict[str, Any]]: Updated PO lines.
    """
    for pol in po_lines:
        qty = int(pol.get("quantity", 0))
        uprice = int(pol.get("unit_price", 0))
        line_total = qty * uprice
        pol["line_total"] = line_total
        pol["line_total_usd"] = round(line_total / 100.0, 2)

    return po_lines


def derive_purchase_order_totals(
    po_lines: List[Dict[str, Any]],
    purchase_orders: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Recalculate Purchase Order totals directly from itemized order lines.

    Formula:
        total_amount = SUM(po_line.line_total)  [cents]
        value = round(total_amount / 100.0, 2)  [USD]

    Args:
        po_lines: Purchase order line records.
        purchase_orders: Optional list of PO headers to update in-place.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of po_id to derived PO totals.
    """
    totals_by_po: Dict[str, Dict[str, Any]] = {}

    for line in po_lines:
        poid = line["po_id"]
        if poid not in totals_by_po:
            totals_by_po[poid] = {
                "total_amount": 0,
                "value": 0.0,
                "total_quantity": 0,
                "line_count": 0,
            }

        line_cents = line.get("line_total")
        if line_cents is None:
            qty = int(line.get("quantity", 0))
            uprice = int(line.get("unit_price", 0))
            line_cents = qty * uprice
            line["line_total"] = line_cents

        qty = int(line.get("quantity", 0))
        totals_by_po[poid]["total_amount"] += line_cents
        totals_by_po[poid]["total_quantity"] += qty
        totals_by_po[poid]["line_count"] += 1

    for poid, data in totals_by_po.items():
        data["value"] = round(data["total_amount"] / 100.0, 2)

    if purchase_orders:
        for po in purchase_orders:
            poid = po["po_id"]
            if poid in totals_by_po:
                derived = totals_by_po[poid]
                po["total_amount"] = derived["total_amount"]
                po["value"] = derived["value"]

    return totals_by_po


def derive_delivery_summaries(
    deliveries: List[Dict[str, Any]],
    purchase_orders: Optional[List[Dict[str, Any]]] = None,
    po_lines: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Recalculate cumulative delivery fulfillment metrics per purchase order.

    Formula:
        total_delivered_quantity = SUM(items_delivered_count)
        fulfillment_ratio = total_delivered_quantity / total_ordered_quantity

    Args:
        deliveries: Delivery shipment receipt records.
        purchase_orders: Optional list of PO headers.
        po_lines: Optional list of PO lines to compute total ordered quantity.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of po_id to delivery summary metrics.
    """
    deliveries_by_po: Dict[str, List[Dict[str, Any]]] = {}
    for d in deliveries:
        deliveries_by_po.setdefault(d["po_id"], []).append(d)

    po_ordered_qty: Dict[str, int] = {}
    if po_lines:
        for pol in po_lines:
            poid = pol["po_id"]
            po_ordered_qty[poid] = po_ordered_qty.get(poid, 0) + int(pol.get("quantity", 0))
    elif purchase_orders:
        for po in purchase_orders:
            poid = po["po_id"]
            lines = po.get("_lines", [])
            if lines:
                po_ordered_qty[poid] = sum(int(l.get("quantity", 0)) for l in lines)

    summaries: Dict[str, Dict[str, Any]] = {}

    all_po_ids = set(deliveries_by_po.keys())
    if purchase_orders:
        all_po_ids.update(po["po_id"] for po in purchase_orders)

    for poid in all_po_ids:
        del_list = deliveries_by_po.get(poid, [])
        delivered_qty = sum(int(d.get("items_delivered_count", 0)) for d in del_list)
        ordered_qty = po_ordered_qty.get(poid, delivered_qty)

        is_fully_delivered = (delivered_qty >= ordered_qty) and (ordered_qty > 0)
        has_late = any(d.get("delivery_status") == "LATE" for d in del_list)

        dates = [d["delivery_date"] for d in del_list if "delivery_date" in d]
        latest_date = max(dates) if dates else None

        summaries[poid] = {
            "po_id": poid,
            "shipment_count": len(del_list),
            "delivered_quantity": delivered_qty,
            "ordered_quantity": ordered_qty,
            "is_fully_delivered": is_fully_delivered,
            "is_partial": (0 < delivered_qty < ordered_qty),
            "has_late_delivery": has_late,
            "latest_delivery_date": latest_date,
        }

    return summaries


def derive_current_statuses(
    status_events: List[Dict[str, Any]],
) -> Dict[Tuple[str, str], str]:
    """Derive the current lifecycle status for every entity from its latest StatusEvent.

    Chronologically resolves the latest status by (event_timestamp, status_event_id).

    Args:
        status_events: Full list of StatusEvent records.

    Returns:
        Dict[Tuple[str, str], str]: Mapping of (entity_type, entity_id) -> current_status.
    """
    sorted_events = sorted(
        status_events,
        key=lambda e: (
            e.get("event_timestamp") or e.get("event_ts") or "",
            e.get("status_event_id") or e.get("event_id") or "",
        ),
    )

    current_statuses: Dict[Tuple[str, str], str] = {}
    for ev in sorted_events:
        ent_type = ev.get("entity_type") or ev.get("entity") or ""
        ent_id = ev.get("entity_id") or ""
        to_status = ev.get("to_status") or ev.get("new_status") or ""
        current_statuses[(ent_type, ent_id)] = to_status

    return current_statuses


def derive_budget_balances(
    budget_events: List[Dict[str, Any]],
    budgets: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Derive department budget balances strictly by processing the double-entry event ledger.

    Ledger Accounting Rules:
        - ALLOCATE: sets or increases allocated_amount
        - RESERVE: increases reserved_amount (pre-encumbrance)
        - RELEASE: decreases reserved_amount
        - COMMIT: increases committed_amount (encumbrance)
        - SPEND: increases spent_amount and decreases committed_amount

    Balance Invariant:
        available_amount = allocated_amount - (reserved_amount + committed_amount + spent_amount)

    Args:
        budget_events: Chronological budget ledger events.
        budgets: Optional list of budget master records.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of budget_id to derived balance dictionary.
    """
    sorted_events = sorted(
        budget_events,
        key=lambda e: (
            e.get("event_timestamp") or e.get("event_date") or "",
            e.get("budget_event_id") or "",
        ),
    )

    balances: Dict[str, Dict[str, Any]] = {}

    for ev in sorted_events:
        bid = ev["budget_id"]
        if bid not in balances:
            balances[bid] = {
                "budget_id": bid,
                "allocated_amount": 0,
                "reserved_amount": 0,
                "committed_amount": 0,
                "spent_amount": 0,
                "available_amount": 0,
            }

        amt = int(ev.get("amount", 0))
        ev_type = ev.get("event_type")

        if ev_type == "ALLOCATE":
            balances[bid]["allocated_amount"] += amt
        elif ev_type == "RESERVE":
            balances[bid]["reserved_amount"] += amt
        elif ev_type == "RELEASE":
            balances[bid]["reserved_amount"] = max(0, balances[bid]["reserved_amount"] - amt)
        elif ev_type == "COMMIT":
            balances[bid]["committed_amount"] += amt
        elif ev_type == "SPEND":
            balances[bid]["spent_amount"] += amt
            balances[bid]["committed_amount"] = max(0, balances[bid]["committed_amount"] - amt)

    for bid, bal in balances.items():
        bal["available_amount"] = bal["allocated_amount"] - (
            bal["reserved_amount"] + bal["committed_amount"] + bal["spent_amount"]
        )
        bal["allocated"] = round(bal["allocated_amount"] / 100.0, 2)
        bal["reserved"] = round(bal["reserved_amount"] / 100.0, 2)
        bal["committed"] = round(bal["committed_amount"] / 100.0, 2)
        bal["spent"] = round(bal["spent_amount"] / 100.0, 2)
        bal["available"] = round(bal["available_amount"] / 100.0, 2)

    if budgets:
        for b in budgets:
            bid = b["budget_id"]
            if bid in balances:
                derived = balances[bid]
                b["reserved_amount"] = derived["reserved_amount"]
                b["reserved"] = derived["reserved"]
                b["committed_amount"] = derived["committed_amount"]
                b["committed"] = derived["committed"]
                b["spent_amount"] = derived["spent_amount"]
                b["spent"] = derived["spent"]

    return balances


def derive_delivery_metrics(
    deliveries: List[Dict[str, Any]],
    purchase_orders: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate overall delivery performance and operational KPI metrics.

    Args:
        deliveries: All delivery receipt records.
        purchase_orders: All purchase order records.

    Returns:
        Dict[str, Any]: Comprehensive operational delivery KPIs.
    """
    total_deliveries = len(deliveries)
    on_time_count = sum(1 for d in deliveries if d.get("delivery_status") != "LATE")
    late_count = sum(1 for d in deliveries if d.get("delivery_status") == "LATE")
    partial_count = sum(1 for d in deliveries if d.get("delivery_status") == "PARTIAL")

    on_time_rate = round(on_time_count / total_deliveries, 4) if total_deliveries > 0 else 1.0

    po_by_id = {po["po_id"]: po for po in purchase_orders}
    lead_times = []
    delays = []

    for d in deliveries:
        poid = d.get("po_id")
        po = po_by_id.get(poid)
        if po and "po_date" in po and "delivery_date" in d:
            from datetime import date
            po_d = date.fromisoformat(po["po_date"][:10])
            del_d = date.fromisoformat(d["delivery_date"][:10])
            lead_times.append((del_d - po_d).days)

            exp_d = date.fromisoformat(po["expected_delivery_date"][:10])
            if del_d > exp_d:
                delays.append((del_d - exp_d).days)

    avg_lead_days = round(sum(lead_times) / len(lead_times), 2) if lead_times else 0.0
    avg_delay_days = round(sum(delays) / len(delays), 2) if delays else 0.0

    return {
        "total_deliveries": total_deliveries,
        "on_time_count": on_time_count,
        "late_count": late_count,
        "partial_count": partial_count,
        "on_time_rate": on_time_rate,
        "average_lead_days": avg_lead_days,
        "average_delay_days": avg_delay_days,
    }


def derive_all(
    dataset: Dict[str, Any],
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Central entry point to recalculate all derived fields across an entire dataset.

    Recalculates:
    - Request line and purchase request totals
    - Quote landed costs and supplier scores
    - PO line and PO totals
    - Delivery summaries and performance KPIs
    - Status event derived current statuses
    - Budget ledger balances

    Args:
        dataset: Dictionary containing all procurement entities.
        config: Central configuration dictionary.

    Returns:
        Dict[str, Any]: Dictionary containing all derived views and metrics.
    """
    req_lines = dataset.get("request_lines", [])
    prs = dataset.get("purchase_requests", [])
    quotes = dataset.get("supplier_quotes", [])
    quote_lines = dataset.get("quote_lines", [])
    pos = dataset.get("purchase_orders", [])
    po_lines = dataset.get("purchase_order_lines", [])
    deliveries = dataset.get("deliveries", [])
    status_events = dataset.get("status_events", [])
    budget_events = dataset.get("budget_events", [])
    budgets = dataset.get("budgets", [])

    # 1. Requisitions
    derive_request_line_totals(req_lines)
    pr_totals = derive_purchase_request_totals(req_lines, prs)

    # 2. Quotations & Scoring
    quote_costs = derive_quote_landed_costs(quotes, quote_lines, config)
    supplier_scores = derive_supplier_scores(quotes, config)

    # 3. Purchase Orders
    derive_purchase_order_line_totals(po_lines)
    po_totals = derive_purchase_order_totals(po_lines, pos)

    # 4. Deliveries
    delivery_summaries = derive_delivery_summaries(deliveries, pos, po_lines)
    delivery_metrics = derive_delivery_metrics(deliveries, pos)

    # 5. Statuses
    current_statuses = derive_current_statuses(status_events)

    # 6. Budget Balances
    budget_balances = derive_budget_balances(budget_events, budgets)

    return {
        "pr_totals": pr_totals,
        "quote_costs": quote_costs,
        "supplier_scores": supplier_scores,
        "po_totals": po_totals,
        "delivery_summaries": delivery_summaries,
        "delivery_metrics": delivery_metrics,
        "current_statuses": current_statuses,
        "budget_balances": budget_balances,
    }
