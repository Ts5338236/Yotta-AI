"""Sourcing, RFQ, Supplier Quotation, and Scoring engine.

Implements competitive and non-competitive sourcing path classification,
supplier invitations, multi-currency quotation generation with landed costs,
and multicriteria supplier scoring for award decisions.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Tuple
import numpy as np

from datagen.fx import convert_to_base_currency, get_exchange_rate
from datagen.ids import IDFactory


def _add_days(iso_date: str, days: int) -> str:
    base = datetime.date.fromisoformat(iso_date[:10])
    target = base + datetime.timedelta(days=days)
    if target.year > 2026:
        target = datetime.date(2026, 12, 31)
    return target.isoformat()


def classify_sourcing_paths(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    approved_requests: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Classify approved purchase requests into competitive and non-competitive paths.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        approved_requests: List of fully approved purchase requests.

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
            (competitive_requests, non_competitive_requests).
    """
    scale_name = config.get("generation", {}).get("default_scale", "starter")
    target_rfqs = int(config.get("scale", {}).get(scale_name, {}).get("rfqs", 50))

    thresholds = config.get("approval_thresholds", {})
    mgr_limit = float(thresholds.get("manager_limit", 2000.0))

    eligible_for_competitive: List[Dict[str, Any]] = []
    direct_candidates: List[Dict[str, Any]] = []

    for pr in approved_requests:
        if pr["total_estimate_usd"] > mgr_limit:
            eligible_for_competitive.append(pr)
        else:
            direct_candidates.append(pr)

    # Sort stably by request_date and request_id
    eligible_for_competitive.sort(key=lambda r: (r["request_date"], r["request_id"]))
    direct_candidates.sort(key=lambda r: (r["request_date"], r["request_id"]))

    # Select target count of competitive RFQs
    num_competitive = min(target_rfqs, len(eligible_for_competitive))
    competitive_requests = eligible_for_competitive[:num_competitive]
    remaining_high_value = eligible_for_competitive[num_competitive:]

    for pr in competitive_requests:
        pr["sourcing_path"] = "competitive"
        pr["sourcing_type"] = "COMPETITIVE"
        pr["single_source_reason_code"] = None

    non_competitive_requests: List[Dict[str, Any]] = []

    # Direct catalogue purchases
    for pr in direct_candidates:
        pr["sourcing_path"] = "catalogue"
        pr["sourcing_type"] = "SOLE_SOURCE"
        pr["single_source_reason_code"] = "contract"
        non_competitive_requests.append(pr)

    # Remaining high-value purchases follow single-source or contract
    reason_codes = ["sole_supplier", "urgent", "contract"]
    for pr in remaining_high_value:
        reason = rng.choice(reason_codes)
        pr["sourcing_path"] = "single_source" if reason != "contract" else "contract"
        pr["sourcing_type"] = "SOLE_SOURCE" if reason != "contract" else "CONTRACT_RENEWAL"
        pr["single_source_reason_code"] = reason
        non_competitive_requests.append(pr)

    return competitive_requests, non_competitive_requests


def generate_sourcing(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    competitive_requests: List[Dict[str, Any]],
    request_lines: List[Dict[str, Any]],
    suppliers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate RFQs, supplier invites, multi-currency quotations, and award lowest scores.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        competitive_requests: List of PRs designated for competitive sourcing.
        request_lines: Full list of request lines.
        suppliers: List of supplier master records.

    Returns:
        Dict[str, Any]:
            'rfqs': List of RFQ records.
            'rfq_supplier_invites': List of supplier invite records.
            'supplier_quotes': List of quotation records.
            'quote_lines': List of itemized quotation line records.
            'awarded_quotes': Dict mapping rfq_id to winning quote record.
    """
    scoring_weights = config.get("supplier_scoring", {})
    cost_weight = float(scoring_weights.get("landed_cost_weight", 0.60))
    lead_weight = float(scoring_weights.get("lead_time_weight", 0.25))
    risk_weight = float(scoring_weights.get("risk_weight", 0.15))

    # Index request lines by request_id
    lines_by_request: Dict[str, List[Dict[str, Any]]] = {}
    for line in request_lines:
        lines_by_request.setdefault(line["request_id"], []).append(line)

    # Filter active and preferred suppliers
    eligible_suppliers = [
        s for s in suppliers if s["status"] in ("ACTIVE", "PREFERRED")
    ]
    if len(eligible_suppliers) < 3:
        eligible_suppliers = list(suppliers)

    rfqs: List[Dict[str, Any]] = []
    invites: List[Dict[str, Any]] = []
    quotes: List[Dict[str, Any]] = []
    quote_lines: List[Dict[str, Any]] = []
    awarded_quotes: Dict[str, Dict[str, Any]] = {}

    for pr in competitive_requests:
        pr_id = pr["request_id"]
        pr_lines = lines_by_request.get(pr_id, [])
        if not pr_lines:
            continue

        approval_date = pr["updated_at"][:10]
        issue_date = _add_days(approval_date, int(rng.integers(1, 3)))
        due_date = _add_days(issue_date, int(rng.integers(7, 14)))

        rfq_id = id_factory.next_rfq_id()
        rfq_record = {
            "rfq_id": rfq_id,
            "request_id": pr_id,
            "currency": "USD",
            "issue_date": issue_date,
            "due_date": due_date,
            "status": "AWARDED",
            "created_at": f"{issue_date}T09:00:00Z",
        }
        rfqs.append(rfq_record)

        # Invite 3 to 5 distinct suppliers
        invite_count = min(len(eligible_suppliers), int(rng.choice([3, 3, 3, 4, 5])))
        permuted_suppliers = list(rng.permutation(eligible_suppliers))[:invite_count]

        rfq_quotes: List[Dict[str, Any]] = []

        for sup in permuted_suppliers:
            sup_id = sup["supplier_id"]

            # 1. Invite record
            invite_id = id_factory.next_rfq_supplier_invite_id()
            invites.append({
                "invite_id": invite_id,
                "rfq_id": rfq_id,
                "supplier_id": sup_id,
                "invited_at": f"{issue_date}T09:00:00Z",
                "invitation_status": "ACCEPTED",
            })

            # 2. Quotation
            quote_id = id_factory.next_supplier_quote_id()
            quote_date = _add_days(issue_date, int(rng.integers(3, 7)))
            valid_until = _add_days(quote_date, int(rng.integers(30, 60)))

            curr = sup["currency"]
            # FX rate from config (units of base USD per 1 unit of quote currency)
            fx_rate = float(get_exchange_rate(curr, "USD", config))

            quote_line_records: List[Dict[str, Any]] = []
            quote_total_curr = 0.0
            quote_total_base = 0.0

            for rl in pr_lines:
                ql_id = id_factory.next_quote_line_id()
                qty = rl["quantity"]
                unit_est_usd = rl["unit_estimate"]

                # Variance between 90% and 115% of estimate
                price_variance = float(rng.uniform(0.90, 1.15))
                unit_price_usd = round(unit_est_usd * price_variance, 2)
                # Convert to supplier native currency
                unit_price_curr = round(unit_price_usd / fx_rate, 2) if fx_rate > 0 else unit_price_usd

                line_total_curr = round(qty * unit_price_curr, 2)
                line_total_base = round(line_total_curr * fx_rate, 2)

                quote_total_curr += line_total_curr
                quote_total_base += line_total_base

                ql_rec = {
                    "quote_line_id": ql_id,
                    "quote_id": quote_id,
                    "request_line_id": rl["request_line_id"],
                    "quantity": qty,
                    "quoted_quantity": qty,
                    "unit_price": int(round(unit_price_curr * 100)),
                    "unit_price_float": unit_price_curr,
                    "line_total": int(round(line_total_curr * 100)),
                    "line_total_float": line_total_curr,
                    "line_total_base": int(round(line_total_base * 100)),
                    "line_total_base_float": line_total_base,
                    "created_at": f"{quote_date}T14:00:00Z",
                }
                quote_line_records.append(ql_rec)
                quote_lines.append(ql_rec)

            quote_total_curr = round(quote_total_curr, 2)
            quote_total_base = round(quote_total_base, 2)

            # Landed cost elements
            freight = round(quote_total_base * float(rng.uniform(0.02, 0.04)), 2)
            duty = round(quote_total_base * (0.02 if curr != "USD" else 0.0), 2)
            tax = round(quote_total_base * float(rng.uniform(0.01, 0.03)), 2)
            landed_cost_base = round(quote_total_base + freight + duty + tax, 2)

            lead_days = max(1, int(round(sup["lead_time_mean"] + rng.integers(-2, 4))))

            quote_rec = {
                "quote_id": quote_id,
                "rfq_id": rfq_id,
                "supplier_id": sup_id,
                "quote_date": quote_date,
                "currency": curr,
                "fx_rate_to_base": fx_rate,
                "total_quoted_amount": int(round(quote_total_curr * 100)),
                "total_quoted_amount_base": int(round(quote_total_base * 100)),
                "total_quoted_amount_usd": quote_total_base,
                "freight": freight,
                "duty": duty,
                "tax_nonrecoverable": tax,
                "landed_cost_base": landed_cost_base,
                "lead_time_days": lead_days,
                "valid_until": valid_until,
                "risk_score": sup["risk_score"],
                "status": "UNDER_REVIEW",
                "score": 0.0,
                "created_at": f"{quote_date}T14:00:00Z",
                "_lines": quote_line_records,
                "_supplier": sup,
            }
            quotes.append(quote_rec)
            rfq_quotes.append(quote_rec)

        # 3. Multicriteria Scoring across competing quotes
        costs = [q["landed_cost_base"] for q in rfq_quotes]
        leads = [q["lead_time_days"] for q in rfq_quotes]
        risks = [q["risk_score"] for q in rfq_quotes]

        min_c, max_c = min(costs), max(costs)
        min_l, max_l = min(leads), max(leads)
        min_r, max_r = min(risks), max(risks)

        for q in rfq_quotes:
            c_norm = (q["landed_cost_base"] - min_c) / (max_c - min_c) if max_c > min_c else 0.0
            l_norm = (q["lead_time_days"] - min_l) / (max_l - min_l) if max_l > min_l else 0.0
            r_norm = (q["risk_score"] - min_r) / (max_r - min_r) if max_r > min_r else 0.0

            q["score"] = round(cost_weight * c_norm + lead_weight * l_norm + risk_weight * r_norm, 4)

        # 4. Award lowest scoring quote
        rfq_quotes.sort(key=lambda q: (q["score"], q["landed_cost_base"], q["quote_id"]))
        winner = rfq_quotes[0]
        award_date = _add_days(due_date, int(rng.integers(1, 3)))

        for q in rfq_quotes:
            if q["quote_id"] == winner["quote_id"]:
                q["status"] = "AWARDED"
            else:
                q["status"] = "REJECTED"

        winner["award_date"] = award_date
        winner["award_rationale"] = (
            f"Lowest evaluated score: {winner['score']:.4f} "
            f"(Landed cost: ${winner['landed_cost_base']:,.2f}, Lead time: {winner['lead_time_days']}d)"
        )
        awarded_quotes[rfq_id] = winner

    return {
        "rfqs": rfqs,
        "rfq_supplier_invites": invites,
        "supplier_quotes": quotes,
        "quote_lines": quote_lines,
        "awarded_quotes": awarded_quotes,
    }
