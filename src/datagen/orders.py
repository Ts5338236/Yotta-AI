"""Purchase Order and Purchase Order Line generation engine.

Transforms awarded quotations (competitive sourcing) and approved direct requisitions
(non-competitive sourcing) into binding commercial purchase orders.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Mapping, Tuple
import numpy as np

from datagen.ids import IDFactory


def _add_days(iso_date: str, days: int) -> str:
    base = datetime.date.fromisoformat(iso_date[:10])
    target = base + datetime.timedelta(days=days)
    if target.year > 2026:
        target = datetime.date(2026, 12, 31)
    return target.isoformat()


def generate_orders(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    competitive_requests: List[Dict[str, Any]],
    non_competitive_requests: List[Dict[str, Any]],
    rfqs: List[Dict[str, Any]],
    awarded_quotes: Dict[str, Dict[str, Any]],
    request_lines: List[Dict[str, Any]],
    suppliers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate Purchase Orders and Purchase Order Lines for all eligible approved requests.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        competitive_requests: PRs sourced via competitive bidding.
        non_competitive_requests: PRs sourced via direct/single-source/contract paths.
        rfqs: Generated RFQ records.
        awarded_quotes: Mapping from rfq_id to winning quote.
        request_lines: Full list of request lines.
        suppliers: List of supplier master records.

    Returns:
        Dict[str, Any]:
            'purchase_orders': List of PO records.
            'purchase_order_lines': List of PO line records.
    """
    lines_by_request: Dict[str, List[Dict[str, Any]]] = {}
    for rl in request_lines:
        lines_by_request.setdefault(rl["request_id"], []).append(rl)

    # Map request_id to rfq_id for competitive requests
    rfq_by_request: Dict[str, str] = {r["request_id"]: r["rfq_id"] for r in rfqs}

    active_suppliers = [s for s in suppliers if s["status"] in ("ACTIVE", "PREFERRED")]
    if not active_suppliers:
        active_suppliers = list(suppliers)

    purchase_orders: List[Dict[str, Any]] = []
    purchase_order_lines: List[Dict[str, Any]] = []

    # 1. Competitive Purchase Orders
    for pr in competitive_requests:
        pr_id = pr["request_id"]
        rfq_id = rfq_by_request.get(pr_id)
        if not rfq_id or rfq_id not in awarded_quotes:
            continue

        winner_quote = awarded_quotes[rfq_id]
        supplier_id = winner_quote["supplier_id"]
        award_date = winner_quote.get("award_date", pr["updated_at"][:10])

        po_date = _add_days(award_date, int(rng.integers(1, 3)))
        lead_days = int(winner_quote.get("lead_time_days", 14))
        delivery_date = _add_days(po_date, lead_days)

        po_id = id_factory.next_purchase_order_id()
        po_lines: List[Dict[str, Any]] = []
        po_total_cents = 0

        # Lines derived from awarded quote lines
        quote_lines_list = winner_quote.get("_lines", [])
        for idx, ql in enumerate(quote_lines_list, start=1):
            pol_id = id_factory.next_purchase_order_line_id()
            qty = ql["quantity"]
            # Unit price in base currency (USD cents)
            unit_price_cents = int(round(ql["line_total_base"] / qty)) if qty > 0 else ql["line_total_base"]
            line_total_cents = ql["line_total_base"]
            po_total_cents += line_total_cents

            pol_rec = {
                "po_line_id": pol_id,
                "po_id": po_id,
                "line_number": idx,
                "request_line_id": ql["request_line_id"],
                "awarded_quote_line_id": ql["quote_line_id"],
                "quantity": qty,
                "unit_price": unit_price_cents,
                "unit_price_usd": round(unit_price_cents / 100.0, 2),
                "line_total": line_total_cents,
                "line_total_usd": round(line_total_cents / 100.0, 2),
                "created_at": f"{po_date}T10:00:00Z",
            }
            po_lines.append(pol_rec)
            purchase_order_lines.append(pol_rec)

        po_value_usd = round(po_total_cents / 100.0, 2)

        po_rec = {
            "po_id": po_id,
            "request_id": pr_id,
            "supplier_id": supplier_id,
            "awarded_quote_id": winner_quote["quote_id"],
            "quote_id": winner_quote["quote_id"],
            "sourcing_type": "COMPETITIVE",
            "sourcing_path": "competitive",
            "sourcing_justification": winner_quote.get("award_rationale", "Competitive award"),
            "single_source_reason_code": None,
            "award_rationale": winner_quote.get("award_rationale", "Competitive award"),
            "currency": "USD",
            "total_amount": po_total_cents,
            "value": po_value_usd,
            "status": "ISSUED",
            "po_date": po_date,
            "expected_delivery_date": delivery_date,
            "lead_time_days": lead_days,
            "created_at": f"{po_date}T10:00:00Z",
            "updated_at": f"{po_date}T10:00:00Z",
            "_lines": po_lines,
        }
        purchase_orders.append(po_rec)
        pr["status"] = "ORDERED"
        pr["updated_at"] = f"{po_date}T10:00:00Z"

    # 2. Non-Competitive Purchase Orders (Catalogue, Single Source, Contract)
    for pr in non_competitive_requests:
        pr_id = pr["request_id"]
        pr_lines = lines_by_request.get(pr_id, [])
        if not pr_lines:
            continue

        approval_date = pr["updated_at"][:10]
        po_date = _add_days(approval_date, int(rng.integers(1, 3)))

        # Assign an active supplier deterministically
        sup = active_suppliers[rng.integers(0, len(active_suppliers))]
        supplier_id = sup["supplier_id"]
        lead_days = int(sup.get("lead_time_mean", 14))
        delivery_date = _add_days(po_date, lead_days)

        po_id = id_factory.next_purchase_order_id()
        po_lines = []
        po_total_cents = 0

        # Lines derived directly from request lines
        for idx, rl in enumerate(pr_lines, start=1):
            pol_id = id_factory.next_purchase_order_line_id()
            qty = rl["quantity"]
            unit_price_cents = rl["estimated_unit_price"]
            line_total_cents = rl["estimated_line_total"]
            po_total_cents += line_total_cents

            pol_rec = {
                "po_line_id": pol_id,
                "po_id": po_id,
                "line_number": idx,
                "request_line_id": rl["request_line_id"],
                "awarded_quote_line_id": None,
                "quantity": qty,
                "unit_price": unit_price_cents,
                "unit_price_usd": round(unit_price_cents / 100.0, 2),
                "line_total": line_total_cents,
                "line_total_usd": round(line_total_cents / 100.0, 2),
                "created_at": f"{po_date}T10:00:00Z",
            }
            po_lines.append(pol_rec)
            purchase_order_lines.append(pol_rec)

        po_value_usd = round(po_total_cents / 100.0, 2)
        sourcing_path = pr.get("sourcing_path", "catalogue")
        sourcing_type = pr.get("sourcing_type", "SOLE_SOURCE")
        reason_code = pr.get("single_source_reason_code", "contract")

        po_rec = {
            "po_id": po_id,
            "request_id": pr_id,
            "supplier_id": supplier_id,
            "awarded_quote_id": None,
            "quote_id": None,
            "sourcing_type": sourcing_type,
            "sourcing_path": sourcing_path,
            "sourcing_justification": f"Direct procurement via {sourcing_path} ({reason_code})",
            "single_source_reason_code": reason_code,
            "award_rationale": f"Approved under {sourcing_path} path",
            "currency": "USD",
            "total_amount": po_total_cents,
            "value": po_value_usd,
            "status": "ISSUED",
            "po_date": po_date,
            "expected_delivery_date": delivery_date,
            "lead_time_days": lead_days,
            "created_at": f"{po_date}T10:00:00Z",
            "updated_at": f"{po_date}T10:00:00Z",
            "_lines": po_lines,
        }
        purchase_orders.append(po_rec)
        pr["status"] = "ORDERED"
        pr["updated_at"] = f"{po_date}T10:00:00Z"

    # Sort stably chronologically
    purchase_orders.sort(key=lambda p: (p["po_date"], p["po_id"]))
    return {
        "purchase_orders": purchase_orders,
        "purchase_order_lines": purchase_order_lines,
    }
