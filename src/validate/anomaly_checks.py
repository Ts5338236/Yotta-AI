"""Independent anomaly detection engine and ground truth evaluation module (Phase 5).

Critical Design Rules:
- Detectors inspect procurement data and business rules independently.
- Detectors NEVER read ground_truth, anomaly-injector metadata, or injection flags.
- Distinguishes genuine business rule violations from legitimate procurement edge cases.
- Evaluates detection precision, recall, and detection rates against ground truth.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple


@dataclass
class AnomalyFinding:
    """Represents an independently detected anomaly finding."""

    issue_type: str
    entity: str
    record_id: str
    detected: bool = True
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def description(self) -> str:
        return self.reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary representation."""
        return {
            "issue_type": self.issue_type,
            "entity": self.entity,
            "record_id": self.record_id,
            "detected": self.detected,
            "reason": self.reason,
            "metadata": self.metadata,
        }


# ==============================================================================
# INDEPENDENT ANOMALY DETECTORS
# ==============================================================================

def detect_po_without_approval(dataset: Dict[str, Any]) -> List[AnomalyFinding]:
    """Detect Purchase Orders issued without required approval authorization.

    Rule: Every issued purchase order must link to a requisition that has at
    least one recorded 'APPROVED' decision in the approvals table.
    """
    pos = dataset.get("purchase_orders", [])
    approvals = dataset.get("approvals", [])

    approved_requests = {
        app["request_id"]
        for app in approvals
        if app.get("decision") == "APPROVED"
    }

    findings: List[AnomalyFinding] = []
    for po in pos:
        req_id = po.get("request_id")
        if req_id not in approved_requests:
            findings.append(AnomalyFinding(
                issue_type="po_without_approval",
                entity="purchase_orders",
                record_id=po["po_id"],
                detected=True,
                reason=f"Purchase order {po['po_id']} issued for requisition {req_id} lacking approved authorization",
                metadata={"request_id": req_id},
            ))

    return findings


def detect_expired_quote_before_award(dataset: Dict[str, Any]) -> List[AnomalyFinding]:
    """Detect Supplier Quotations awarded after their validity period expired.

    Rule: An awarded quote's valid_until date must be on or after its award date.
    """
    quotes = dataset.get("supplier_quotes", [])
    findings: List[AnomalyFinding] = []

    for q in quotes:
        if q.get("status") == "AWARDED" and "award_date" in q and "valid_until" in q:
            award_d_str = str(q["award_date"])[:10]
            valid_d_str = str(q["valid_until"])[:10]
            try:
                award_d = datetime.date.fromisoformat(award_d_str)
                valid_d = datetime.date.fromisoformat(valid_d_str)
                if valid_d < award_d:
                    findings.append(AnomalyFinding(
                        issue_type="expired_quote_before_award",
                        entity="supplier_quotes",
                        record_id=q["quote_id"],
                        detected=True,
                        reason=f"Quote {q['quote_id']} validity expired on {valid_d_str} before award date {award_d_str}",
                        metadata={"award_date": award_d_str, "valid_until": valid_d_str},
                    ))
            except ValueError:
                continue

    return findings


def detect_non_cheapest_quote_without_rationale(dataset: Dict[str, Any]) -> List[AnomalyFinding]:
    """Detect non-cheapest quotation awards lacking documented justification rationale.

    Rule: If an awarded quote in an RFQ is not the lowest landed cost / lowest score,
    an explicit non-empty award rationale must be provided.
    """
    quotes = dataset.get("supplier_quotes", [])
    rfqs = dataset.get("rfqs", [])

    quotes_by_rfq: Dict[str, List[Dict[str, Any]]] = {}
    for q in quotes:
        quotes_by_rfq.setdefault(q.get("rfq_id", ""), []).append(q)

    findings: List[AnomalyFinding] = []

    for rfq in rfqs:
        rfq_id = rfq.get("rfq_id")
        q_list = quotes_by_rfq.get(rfq_id, [])
        if len(q_list) < 2:
            continue

        min_cost = min(float(q.get("landed_cost_base", 0.0)) for q in q_list)

        for q in q_list:
            if q.get("status") == "AWARDED":
                cost = float(q.get("landed_cost_base", 0.0))
                # If quote is more expensive than the cheapest competitor
                if cost > min_cost + 0.01:
                    rationale = q.get("award_rationale")
                    # Check if justification rationale is missing or blank
                    if not rationale or not str(rationale).strip():
                        findings.append(AnomalyFinding(
                            issue_type="non_cheapest_quote_without_rationale",
                            entity="supplier_quotes",
                            record_id=q["quote_id"],
                            detected=True,
                            reason=(
                                f"Quote {q['quote_id']} awarded at ${cost:,.2f} exceeding minimum "
                                f"available cost (${min_cost:,.2f}) without documented justification"
                            ),
                            metadata={"cost": cost, "min_cost": min_cost, "rfq_id": rfq_id},
                        ))

    return findings


def detect_inactive_supplier_used(dataset: Dict[str, Any]) -> List[AnomalyFinding]:
    """Detect Purchase Orders issued to inactive or suspended vendors.

    Rule: Commercial purchase orders must only be issued to active suppliers.
    """
    pos = dataset.get("purchase_orders", [])
    suppliers = dataset.get("suppliers", [])
    sup_map = {s["supplier_id"]: s for s in suppliers}

    findings: List[AnomalyFinding] = []
    for po in pos:
        sup_id = po.get("supplier_id")
        sup = sup_map.get(sup_id)
        if sup:
            status = str(sup.get("status", "")).upper()
            is_active = sup.get("active", True)
            if status in ("INACTIVE", "SUSPENDED", "DEBARRED") or not is_active:
                findings.append(AnomalyFinding(
                    issue_type="inactive_supplier_used",
                    entity="purchase_orders",
                    record_id=po["po_id"],
                    detected=True,
                    reason=f"Purchase order {po['po_id']} issued to inactive/suspended vendor {sup_id}",
                    metadata={"supplier_id": sup_id, "supplier_status": status},
                ))

    return findings


def detect_budget_overrun(dataset: Dict[str, Any]) -> List[AnomalyFinding]:
    """Detect department budgets where active encumbrances and spending exceed allocation.

    Rule: Department allocated funding must be greater than or equal to total encumbrances
    (reserved + committed + spent), meaning available_amount >= 0.
    """
    budgets = dataset.get("budgets", [])
    findings: List[AnomalyFinding] = []

    for b in budgets:
        alloc = int(b.get("allocated_amount", 0))
        res = int(b.get("reserved_amount", 0))
        com = int(b.get("committed_amount", 0))
        spent = int(b.get("spent_amount", 0))
        total_used = res + com + spent

        avail = int(b.get("available_amount", alloc - total_used))

        if total_used > alloc or avail < 0:
            deficit_cents = total_used - alloc
            findings.append(AnomalyFinding(
                issue_type="budget_overrun",
                entity="budgets",
                record_id=b["budget_id"],
                detected=True,
                reason=(
                    f"Department budget {b['budget_id']} total commitments (${round(total_used/100, 2):,.2f}) "
                    f"exceed allocated budget (${round(alloc/100, 2):,.2f}) by ${round(deficit_cents/100, 2):,.2f}"
                ),
                metadata={
                    "allocated_cents": alloc,
                    "encumbered_cents": total_used,
                    "deficit_cents": deficit_cents,
                },
            ))

    return findings


def detect_duplicate_purchase_requests(dataset: Dict[str, Any], window_days: int = 7) -> List[AnomalyFinding]:
    """Detect duplicate purchase requests raised by the same requester within a short window.

    Rule: Identical requisitions for the same items, quantities, and estimates
    submitted within 7 calendar days are flagged as unauthorized duplicates.
    """
    prs = dataset.get("purchase_requests", [])
    lines = dataset.get("request_lines", [])

    lines_by_pr: Dict[str, List[Dict[str, Any]]] = {}
    for rl in lines:
        lines_by_pr.setdefault(rl.get("request_id", ""), []).append(rl)

    prs_by_requester: Dict[str, List[Dict[str, Any]]] = {}
    for pr in prs:
        prs_by_requester.setdefault(pr.get("requester_id", ""), []).append(pr)

    findings: List[AnomalyFinding] = []
    seen_flagged_ids: Set[str] = set()

    for req_id, req_prs in prs_by_requester.items():
        if len(req_prs) < 2:
            continue

        # Sort chronologically
        sorted_prs = sorted(
            req_prs,
            key=lambda p: (str(p.get("request_date") or p.get("created_at") or "")[:10], p["request_id"])
        )

        for i in range(len(sorted_prs)):
            pr_a = sorted_prs[i]
            date_a_str = str(pr_a.get("request_date") or pr_a["created_at"])[:10]
            try:
                date_a = datetime.date.fromisoformat(date_a_str)
            except ValueError:
                continue

            lines_a = lines_by_pr.get(pr_a["request_id"], [])
            items_a = tuple(sorted((l.get("item") or l.get("item_description", ""), int(l.get("quantity", 0))) for l in lines_a))

            if not items_a:
                continue

            for j in range(i + 1, len(sorted_prs)):
                pr_b = sorted_prs[j]
                if pr_b["request_id"] in seen_flagged_ids:
                    continue

                date_b_str = str(pr_b.get("request_date") or pr_b["created_at"])[:10]
                try:
                    date_b = datetime.date.fromisoformat(date_b_str)
                except ValueError:
                    continue

                # Must fall within the duplicate window
                days_diff = abs((date_b - date_a).days)
                if days_diff <= window_days:
                    lines_b = lines_by_pr.get(pr_b["request_id"], [])
                    items_b = tuple(sorted((l.get("item") or l.get("item_description", ""), int(l.get("quantity", 0))) for l in lines_b))

                    if items_a == items_b and int(pr_a.get("total_estimated_amount", 0)) == int(pr_b.get("total_estimated_amount", 0)):
                        findings.append(AnomalyFinding(
                            issue_type="duplicate_purchase_request",
                            entity="purchase_requests",
                            record_id=pr_b["request_id"],
                            detected=True,
                            reason=(
                                f"Requisition {pr_b['request_id']} is an identical duplicate of {pr_a['request_id']} "
                                f"submitted within {days_diff} days for identical item lines"
                            ),
                            metadata={"original_request_id": pr_a["request_id"], "days_difference": days_diff},
                        ))
                        seen_flagged_ids.add(pr_b["request_id"])

    return findings


def detect_quote_currency_mismatch(dataset: Dict[str, Any], config: Optional[Mapping[str, Any]] = None) -> List[AnomalyFinding]:
    """Detect supplier quotations submitted in unsupported currencies without valid FX conversion.

    Rule: All quotations must use authorized system currencies with positive, defined exchange rates.
    """
    quotes = dataset.get("supplier_quotes", [])
    fx_rates = (config or {}).get("fx_rates", {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "INR": 0.012, "JPY": 0.0067})

    findings: List[AnomalyFinding] = []

    for q in quotes:
        curr = q.get("currency")
        fx = q.get("fx_rate_to_base")

        is_unsupported_currency = (curr not in fx_rates)
        is_missing_conversion = (fx is None or float(fx) <= 0)

        if is_unsupported_currency or is_missing_conversion:
            findings.append(AnomalyFinding(
                issue_type="quote_currency_mismatch",
                entity="supplier_quotes",
                record_id=q["quote_id"],
                detected=True,
                reason=f"Quote {q['quote_id']} submitted in invalid/unsupported currency '{curr}' lacking valid conversion rate",
                metadata={"currency": curr, "fx_rate": fx},
            ))

    return findings


# ==============================================================================
# MASTER DETECTOR ORCHESTRATOR
# ==============================================================================

def detect_all_anomalies(dataset: Dict[str, Any], config: Optional[Mapping[str, Any]] = None) -> List[AnomalyFinding]:
    """Execute all 7 independent anomaly detectors against a procurement dataset.

    Inspects dataset strictly without reading ground_truth or injection flags.

    Args:
        dataset: The procurement dataset to inspect.
        config: Optional system configuration.

    Returns:
        List[AnomalyFinding]: All independently identified anomaly findings.
    """
    all_findings: List[AnomalyFinding] = []

    all_findings.extend(detect_po_without_approval(dataset))
    all_findings.extend(detect_expired_quote_before_award(dataset))
    all_findings.extend(detect_non_cheapest_quote_without_rationale(dataset))
    all_findings.extend(detect_inactive_supplier_used(dataset))
    all_findings.extend(detect_budget_overrun(dataset))
    all_findings.extend(detect_duplicate_purchase_requests(dataset))
    all_findings.extend(detect_quote_currency_mismatch(dataset, config))

    return all_findings


# ==============================================================================
# EVALUATION & METRICS ENGINE
# ==============================================================================

def evaluate_detections(
    findings: List[AnomalyFinding],
    ground_truth: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Evaluate detector findings against ground truth labels.

    Calculates True Positives, False Positives, False Negatives, Precision,
    Recall, and Detection Rates overall and per anomaly category.

    Args:
        findings: Findings output by independent anomaly detectors.
        ground_truth: True anomaly labels recorded during injection.

    Returns:
        Dict[str, Any]: Comprehensive precision, recall, and evaluation breakdown.
    """
    # Ground truth lookup keys: (issue_type, entity, record_id)
    gt_keys: Set[Tuple[str, str, str]] = {
        (g["issue_type"], g["entity"], g["record_id"]) for g in ground_truth
    }

    # Finding lookup keys: (issue_type, entity, record_id)
    detected_keys: Set[Tuple[str, str, str]] = {
        (f.issue_type, f.entity, f.record_id) for f in findings
    }

    # Overall Metrics
    tp_keys = gt_keys.intersection(detected_keys)
    fp_keys = detected_keys - gt_keys
    fn_keys = gt_keys - detected_keys

    tp = len(tp_keys)
    fp = len(fp_keys)
    fn = len(fn_keys)

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 1.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 1.0
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 1.0

    # Per-category metrics
    all_categories = sorted(list({g["issue_type"] for g in ground_truth}.union({f.issue_type for f in findings})))
    per_category: Dict[str, Dict[str, Any]] = {}

    for cat in all_categories:
        cat_gt = {k for k in gt_keys if k[0] == cat}
        cat_detected = {k for k in detected_keys if k[0] == cat}

        cat_tp = len(cat_gt.intersection(cat_detected))
        cat_fp = len(cat_detected - cat_gt)
        cat_fn = len(cat_gt - cat_detected)

        cat_prec = round(cat_tp / (cat_tp + cat_fp), 4) if (cat_tp + cat_fp) > 0 else 1.0
        cat_rec = round(cat_tp / (cat_tp + cat_fn), 4) if (cat_tp + cat_fn) > 0 else 1.0
        cat_f1 = round(2 * cat_prec * cat_rec / (cat_prec + cat_rec), 4) if (cat_prec + cat_rec) > 0 else 1.0

        per_category[cat] = {
            "ground_truth": len(cat_gt),
            "detected": len(cat_detected),
            "ground_truth_count": len(cat_gt),
            "detected_count": len(cat_detected),
            "true_positives": cat_tp,
            "false_positives": cat_fp,
            "false_negatives": cat_fn,
            "precision": cat_prec,
            "recall": cat_rec,
            "f1_score": cat_f1,
            "detection_rate": cat_rec,
        }

    return {
        "total_ground_truth": len(gt_keys),
        "total_detected": len(detected_keys),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "detection_rate": recall,
        "overall": {
            "ground_truth_count": len(gt_keys),
            "detected_count": len(detected_keys),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "detection_rate": recall,
        },
        "per_category": per_category,
        "by_category": per_category,
        "false_positive_records": [{"issue_type": k[0], "entity": k[1], "record_id": k[2]} for k in fp_keys],
        "false_negative_records": [{"issue_type": k[0], "entity": k[1], "record_id": k[2]} for k in fn_keys],
    }


detect_duplicate_purchase_request = detect_duplicate_purchase_requests

__all__ = [
    "AnomalyFinding",
    "detect_po_without_approval",
    "detect_expired_quote_before_award",
    "detect_non_cheapest_quote_without_rationale",
    "detect_inactive_supplier_used",
    "detect_budget_overrun",
    "detect_duplicate_purchase_requests",
    "detect_duplicate_purchase_request",
    "detect_quote_currency_mismatch",
    "detect_all_anomalies",
    "evaluate_detections",
]
