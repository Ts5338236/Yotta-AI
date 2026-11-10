"""Complete procurement workflow orchestration module (Phase 3).

Coordinates the end-to-end clean procurement lifecycle:
Requisitions -> Approvals -> Sourcing -> Quotations -> Scoring -> POs -> Deliveries -> Budget Ledger -> Status History.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional
import numpy as np

from datagen.approvals import generate_approvals
from datagen.budget import generate_budget_events
from datagen.config import load_config
from datagen.delivery import generate_deliveries
from datagen.events import generate_status_events
from datagen.ids import IDFactory
from datagen.masters import generate_all_masters
from datagen.orders import generate_orders
from datagen.requests import generate_all_requests
from datagen.sourcing import classify_sourcing_paths, generate_sourcing


def run_clean_path_validation(dataset: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate relational integrity and business rule consistency for Phase 3 dataset.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    prs = dataset["purchase_requests"]
    approvals = dataset["approvals"]
    rfqs = dataset["rfqs"]
    invites = dataset["rfq_supplier_invites"]
    quotes = dataset["supplier_quotes"]
    quote_lines = dataset["quote_lines"]
    pos = dataset["purchase_orders"]
    po_lines = dataset["purchase_order_lines"]
    deliveries = dataset["deliveries"]
    budgets = dataset["budgets"]
    budget_events = dataset["budget_events"]
    status_events = dataset["status_events"]

    pr_map = {p["request_id"]: p for p in prs}
    rfq_map = {r["rfq_id"]: r for r in rfqs}
    quote_map = {q["quote_id"]: q for q in quotes}
    po_map = {po["po_id"]: po for po in pos}

    # 1. Approvals completeness & integrity
    app_pr_ids = {a["request_id"] for a in approvals}
    for app in approvals:
        if app["request_id"] not in pr_map:
            errors.append(f"Approval {app['approval_id']} references missing PR {app['request_id']}")

    # 2. Only approved requests receive POs
    for po in pos:
        req_id = po["request_id"]
        if req_id not in pr_map:
            errors.append(f"PO {po['po_id']} references missing PR {req_id}")
        else:
            pr = pr_map[req_id]
            if pr["status"] == "REJECTED":
                errors.append(f"Rejected PR {req_id} erroneously received PO {po['po_id']}")

    # 3. Competitive POs must reference awarded quotes
    for po in pos:
        if po["sourcing_path"] == "competitive":
            qid = po["awarded_quote_id"]
            if not qid or qid not in quote_map:
                errors.append(f"Competitive PO {po['po_id']} missing valid awarded quote reference")
            else:
                q = quote_map[qid]
                if q["supplier_id"] != po["supplier_id"]:
                    errors.append(f"PO {po['po_id']} supplier does not match awarded quote supplier")
                if q["status"] != "AWARDED":
                    errors.append(f"PO {po['po_id']} awarded quote {qid} is not marked AWARDED")

    # 4. PO value equals sum of PO lines
    pol_sum = {}
    for pol in po_lines:
        pol_sum[pol["po_id"]] = pol_sum.get(pol["po_id"], 0) + pol["line_total"]
    for po in pos:
        poid = po["po_id"]
        if po["total_amount"] != pol_sum.get(poid, 0):
            errors.append(f"PO {poid} total {po['total_amount']} does not equal line sum {pol_sum.get(poid, 0)}")

    # 5. Deliveries reconcile with POs
    del_sum = {}
    for d in deliveries:
        del_sum[d["po_id"]] = del_sum.get(d["po_id"], 0) + d["items_delivered_count"]
    for po in pos:
        poid = po["po_id"]
        expected_qty = sum(l["quantity"] for l in po.get("_lines", []))
        delivered_qty = del_sum.get(poid, 0)
        if delivered_qty > expected_qty:
            errors.append(f"PO {poid} over-delivered: expected {expected_qty}, got {delivered_qty}")

    # 6. Budget balances: allocated >= reserved + committed + spent
    for b in budgets:
        alloc = b["allocated_amount"]
        res = b["reserved_amount"]
        com = b["committed_amount"]
        spent = b["spent_amount"]
        if alloc < (res + com + spent):
            errors.append(
                f"Budget {b['budget_id']} overrun: allocated ({alloc}) < sum({res} + {com} + {spent})"
            )

    return len(errors) == 0, errors


def generate_procurement_workflow(
    config_path: Optional[str] = None,
    scale: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute the complete Phase 3 end-to-end procurement workflow generation.

    Strictly adheres to:
    - Single NumPy RNG pass-through.
    - Centralized IDFactory instance.
    - Deterministic execution order.

    Args:
        config_path: Optional custom path to YAML config.
        scale: Optional scale tier ('starter' or 'full').
        seed: Optional custom integer seed.

    Returns:
        Dict[str, Any]: In-memory dictionary containing all procurement transaction datasets.
    """
    config = load_config(config_path)

    if scale is not None:
        if scale not in config["scale"]:
            raise ValueError(f"Unknown scale '{scale}'. Options: {list(config['scale'].keys())}")
        config["generation"]["default_scale"] = scale

    used_scale = config["generation"]["default_scale"]
    used_seed = seed if seed is not None else int(config["generation"]["default_seed"])
    fiscal_year = int(config["project"]["fiscal_year"])

    # Hard technical constraint: Exactly one RNG initialized at entry point
    rng = np.random.default_rng(used_seed)
    id_factory = IDFactory(fiscal_year=fiscal_year)

    # 1. Master Data Generation
    masters = generate_all_masters(config, rng, id_factory)

    # 2. Purchase Request & Line Generation
    requests_data = generate_all_requests(
        config,
        rng,
        id_factory,
        masters["departments"],
        masters["budgets"],
        masters["requesters"],
    )
    purchase_requests = requests_data["purchase_requests"]
    request_lines = requests_data["request_lines"]

    # 3. Approval Engine
    approval_data = generate_approvals(
        config,
        rng,
        id_factory,
        purchase_requests,
        masters["approvers"],
    )
    approvals = approval_data["approvals"]
    approved_requests = approval_data["approved_requests"]
    rejected_requests = approval_data["rejected_requests"]

    # 4. Sourcing Classification
    competitive_requests, non_competitive_requests = classify_sourcing_paths(
        config,
        rng,
        approved_requests,
    )

    # 5. RFQs, Invitations, Quotations, and Awards
    sourcing_data = generate_sourcing(
        config,
        rng,
        id_factory,
        competitive_requests,
        request_lines,
        masters["suppliers"],
    )
    rfqs = sourcing_data["rfqs"]
    invites = sourcing_data["rfq_supplier_invites"]
    quotes = sourcing_data["supplier_quotes"]
    quote_lines = sourcing_data["quote_lines"]
    awarded_quotes = sourcing_data["awarded_quotes"]

    # 6. Purchase Orders and Lines
    order_data = generate_orders(
        config,
        rng,
        id_factory,
        competitive_requests,
        non_competitive_requests,
        rfqs,
        awarded_quotes,
        request_lines,
        masters["suppliers"],
    )
    purchase_orders = order_data["purchase_orders"]
    purchase_order_lines = order_data["purchase_order_lines"]

    # 7. Deliveries
    delivery_data = generate_deliveries(
        config,
        rng,
        id_factory,
        purchase_orders,
    )
    deliveries = delivery_data["deliveries"]

    # 8. Budget Ledger Events & Reconciled Balances
    budget_data = generate_budget_events(
        config,
        rng,
        id_factory,
        masters["budgets"],
        purchase_requests,
        purchase_orders,
        deliveries,
    )
    budget_events = budget_data["budget_events"]
    reconciled_budgets = budget_data["reconciled_budgets"]

    # 9. Status Event History
    status_events = generate_status_events(
        id_factory,
        purchase_requests,
        approvals,
        rfqs,
        awarded_quotes,
        purchase_orders,
        deliveries,
    )

    dataset: Dict[str, Any] = {
        "departments": masters["departments"],
        "budgets": reconciled_budgets,
        "requesters": masters["requesters"],
        "suppliers": masters["suppliers"],
        "approvers": masters["approvers"],
        "purchase_requests": purchase_requests,
        "request_lines": request_lines,
        "approvals": approvals,
        "rfqs": rfqs,
        "rfq_supplier_invites": invites,
        "supplier_quotes": quotes,
        "quote_lines": quote_lines,
        "purchase_orders": purchase_orders,
        "purchase_order_lines": purchase_order_lines,
        "deliveries": deliveries,
        "budget_events": budget_events,
        "status_events": status_events,
        "metadata": {
            "scale": used_scale,
            "seed": used_seed,
            "fiscal_year": fiscal_year,
            "base_currency": config["project"]["base_currency"],
            "competitive_pos_count": len([p for p in purchase_orders if p["sourcing_path"] == "competitive"]),
            "non_competitive_pos_count": len([p for p in purchase_orders if p["sourcing_path"] != "competitive"]),
            "rejected_requests_count": len(rejected_requests),
            "approved_requests_count": len(approved_requests),
        },
    }

    # 10. Clean Path Validation
    is_valid, validation_errors = run_clean_path_validation(dataset)
    if not is_valid:
        error_msg = "\n".join(validation_errors[:10])
        raise ValueError(f"Clean-path validation failed ({len(validation_errors)} errors):\n{error_msg}")

    return dataset
