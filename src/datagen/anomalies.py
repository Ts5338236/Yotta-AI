"""Anomaly injection engine and ground truth generator (Phase 5).

Injects controlled procurement anomalies into clean synthetic datasets:
1. PO Without Approval (po_without_approval)
2. Expired Quote Before Award (expired_quote_before_award)
3. Non-Cheapest Quote Without Rationale (non_cheapest_quote_without_rationale)
4. Inactive Supplier Used (inactive_supplier_used)
5. Budget Overrun (budget_overrun)
6. Duplicate Purchase Request (duplicate_purchase_request)
7. Quote Currency Mismatch (quote_currency_mismatch)

Ground truth labels are maintained completely separately from operational records.
"""

from __future__ import annotations

import copy
import datetime
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple
import numpy as np

from datagen.derive import derive_budget_balances
from datagen.ids import IDFactory


ANOMALY_CATEGORIES = [
    "po_without_approval",
    "expired_quote_before_award",
    "non_cheapest_quote_without_rationale",
    "inactive_supplier_used",
    "budget_overrun",
    "duplicate_purchase_request",
    "quote_currency_mismatch",
]


@dataclass
class GroundTruthRecord:
    """Represents a single ground-truth anomaly label."""

    anomaly_id: str
    issue_type: str
    entity: str
    record_id: str
    expected_decision: str = "ANOMALY"
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching PRD specification."""
        return {
            "anomaly_id": self.anomaly_id,
            "issue_type": self.issue_type,
            "entity": self.entity,
            "record_id": self.record_id,
            "expected_decision": self.expected_decision,
            "reason": self.reason,
            "metadata": self.metadata,
        }


def _shift_days(iso_date: str, days: int) -> str:
    """Shift date string by days, bounded within 2026."""
    base = datetime.date.fromisoformat(iso_date[:10])
    target = base + datetime.timedelta(days=days)
    if target.year < 2026:
        target = datetime.date(2026, 1, 1)
    elif target.year > 2026:
        target = datetime.date(2026, 12, 31)
    return target.isoformat()


# ==============================================================================
# INDIVIDUAL ANOMALY INJECTORS
# ==============================================================================

def inject_po_without_approval(
    dataset: Dict[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    count: int = 1,
    excluded_po_ids: Optional[Set[str]] = None,
) -> List[GroundTruthRecord]:
    """Inject PO Without Approval anomalies.

    Removes all approval records for an issued purchase order's requisition.

    Args:
        dataset: Mutable dataset dictionary.
        rng: Deterministic random generator.
        id_factory: Centralized ID factory.
        count: Number of anomalies to inject.
        excluded_po_ids: Set of PO IDs to avoid mutating.

    Returns:
        List[GroundTruthRecord]: Ground truth records for injected anomalies.
    """
    sync_factory_counters(id_factory, dataset)
    excluded = excluded_po_ids or set()
    pos = dataset.get("purchase_orders", [])
    approvals = dataset.get("approvals", [])

    # Find POs that currently have approval records
    req_with_approvals = {app["request_id"] for app in approvals}
    candidates = [
        po for po in pos
        if po["po_id"] not in excluded and po["request_id"] in req_with_approvals
    ]

    if not candidates:
        return []

    chosen_indices = rng.choice(len(candidates), size=min(count, len(candidates)), replace=False)
    ground_truth: List[GroundTruthRecord] = []

    for idx in chosen_indices:
        target_po = candidates[idx]
        po_id = target_po["po_id"]
        req_id = target_po["request_id"]

        # Remove all approval records for this requisition
        dataset["approvals"] = [
            app for app in dataset.get("approvals", [])
            if app["request_id"] != req_id
        ]

        # Record ground truth
        gt = GroundTruthRecord(
            anomaly_id=id_factory.next_anomaly_id(),
            issue_type="po_without_approval",
            entity="purchase_orders",
            record_id=po_id,
            expected_decision="REJECT",
            reason=f"Purchase order {po_id} issued for requisition {req_id} lacking required approval records",
            metadata={"request_id": req_id},
        )
        ground_truth.append(gt)

    return ground_truth


def inject_expired_quote_before_award(
    dataset: Dict[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    count: int = 1,
    excluded_quote_ids: Optional[Set[str]] = None,
) -> List[GroundTruthRecord]:
    """Inject Expired Quote Before Award anomalies.

    Mutates an awarded quote's valid_until date so that it expires prior to award date.
    """
    excluded = excluded_quote_ids or set()
    quotes = dataset.get("supplier_quotes", [])

    candidates = [
        q for q in quotes
        if q["quote_id"] not in excluded
        and q.get("status") == "AWARDED"
        and "award_date" in q
    ]

    if not candidates:
        return []

    chosen_indices = rng.choice(len(candidates), size=min(count, len(candidates)), replace=False)
    ground_truth: List[GroundTruthRecord] = []

    for idx in chosen_indices:
        target_quote = candidates[idx]
        qid = target_quote["quote_id"]
        award_date = target_quote["award_date"][:10]

        # Set valid_until to 3 to 7 days before award date
        expired_date = _shift_days(award_date, -int(rng.integers(3, 8)))
        target_quote["valid_until"] = expired_date

        gt = GroundTruthRecord(
            anomaly_id=id_factory.next_anomaly_id(),
            issue_type="expired_quote_before_award",
            entity="supplier_quotes",
            record_id=qid,
            expected_decision="DISQUALIFY",
            reason=f"Quote {qid} validity expired on {expired_date} prior to award on {award_date}",
            metadata={"award_date": award_date, "expired_date": expired_date},
        )
        ground_truth.append(gt)

    return ground_truth


def inject_non_cheapest_quote_without_rationale(
    dataset: Dict[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    count: int = 1,
    excluded_quote_ids: Optional[Set[str]] = None,
) -> List[GroundTruthRecord]:
    """Inject Non-Cheapest Quote Without Rationale anomalies.

    Awards an eligible quotation that is not the cheapest/lowest score, with rationale missing.
    """
    excluded = excluded_quote_ids or set()
    quotes = dataset.get("supplier_quotes", [])
    rfqs = dataset.get("rfqs", [])
    pos = dataset.get("purchase_orders", [])

    quotes_by_rfq: Dict[str, List[Dict[str, Any]]] = {}
    for q in quotes:
        quotes_by_rfq.setdefault(q["rfq_id"], []).append(q)

    # Find RFQs with >= 3 quotes where multiple quotes have distinct scores
    eligible_rfqs = []
    for rfq in rfqs:
        rfq_id = rfq["rfq_id"]
        q_list = [q for q in quotes_by_rfq.get(rfq_id, []) if q["quote_id"] not in excluded]
        if len(q_list) >= 3:
            costs = [q.get("landed_cost_base", 0.0) for q in q_list]
            if len(set(costs)) > 1:
                eligible_rfqs.append((rfq_id, q_list))

    if not eligible_rfqs:
        return []

    chosen_indices = rng.choice(len(eligible_rfqs), size=min(count, len(eligible_rfqs)), replace=False)
    ground_truth: List[GroundTruthRecord] = []

    for idx in chosen_indices:
        rfq_id, q_list = eligible_rfqs[idx]

        # Sort quotes by landed cost ascending
        sorted_quotes = sorted(q_list, key=lambda q: (q.get("landed_cost_base", 0.0), q["quote_id"]))
        cheapest_quote = sorted_quotes[0]
        # Pick 2nd or 3rd quote (more expensive)
        expensive_quote = sorted_quotes[-1]

        award_date = cheapest_quote.get("award_date") or rfq_id

        # Update previous winner to REJECTED
        for q in q_list:
            if q["quote_id"] == expensive_quote["quote_id"]:
                q["status"] = "AWARDED"
                q["award_date"] = award_date if isinstance(award_date, str) else "2026-06-01"
                q["award_rationale"] = None  # Missing justification!
            else:
                q["status"] = "REJECTED"

        # Update competitive PO reference if applicable
        for po in pos:
            if po.get("sourcing_path") == "competitive" and po.get("awarded_quote_id") == cheapest_quote["quote_id"]:
                po["awarded_quote_id"] = expensive_quote["quote_id"]
                po["supplier_id"] = expensive_quote["supplier_id"]

        gt = GroundTruthRecord(
            anomaly_id=id_factory.next_anomaly_id(),
            issue_type="non_cheapest_quote_without_rationale",
            entity="supplier_quotes",
            record_id=expensive_quote["quote_id"],
            expected_decision="JUSTIFY_OR_REVERT",
            reason=(
                f"Quotation {expensive_quote['quote_id']} awarded at landed cost ${expensive_quote.get('landed_cost_base', 0):,.2f} "
                f"over cheaper quote {cheapest_quote['quote_id']} (${cheapest_quote.get('landed_cost_base', 0):,.2f}) "
                f"without documented justification rationale"
            ),
            metadata={
                "rfq_id": rfq_id,
                "awarded_quote_id": expensive_quote["quote_id"],
                "cheapest_quote_id": cheapest_quote["quote_id"],
            },
        )
        ground_truth.append(gt)

    return ground_truth


def sync_factory_counters(id_factory: IDFactory, dataset: Dict[str, Any]) -> None:
    """Synchronize IDFactory sequence counters with highest sequence numbers in dataset."""
    for pr in dataset.get("purchase_requests", []):
        pid = str(pr.get("request_id", ""))
        parts = pid.split("-")
        if len(parts) == 3 and parts[2].isdigit():
            id_factory._counters["purchase_request"] = max(id_factory._counters["purchase_request"], int(parts[2]))

    for rl in dataset.get("request_lines", []):
        rid = str(rl.get("request_line_id", ""))
        parts = rid.split("-")
        if len(parts) == 2 and parts[1].isdigit():
            id_factory._counters["request_line"] = max(id_factory._counters["request_line"], int(parts[1]))

    for s in dataset.get("suppliers", []):
        sid = str(s.get("supplier_id", ""))
        parts = sid.split("-")
        if len(parts) == 2 and parts[1].isdigit():
            id_factory._counters["supplier"] = max(id_factory._counters["supplier"], int(parts[1]))


def inject_inactive_supplier_used(
    dataset: Dict[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    count: int = 1,
    excluded_po_ids: Optional[Set[str]] = None,
) -> List[GroundTruthRecord]:
    """Inject Inactive Supplier Used anomalies.

    Creates an inactive supplier in the supplier master and associates a targeted PO with it,
    ensuring other POs remain uncorrupted.
    """
    sync_factory_counters(id_factory, dataset)
    excluded = excluded_po_ids or set()
    pos = dataset.get("purchase_orders", [])

    candidates = [po for po in pos if po["po_id"] not in excluded]
    if not candidates:
        return []

    chosen_indices = rng.choice(len(candidates), size=min(count, len(candidates)), replace=False)
    ground_truth: List[GroundTruthRecord] = []

    for idx in chosen_indices:
        target_po = candidates[idx]
        po_id = target_po["po_id"]

        # Create a new inactive supplier
        inactive_sup_id = id_factory.next_supplier_id()
        inactive_sup = {
            "supplier_id": inactive_sup_id,
            "name": f"Decommissioned Supplier {inactive_sup_id}",
            "supplier_code": f"SUP-D-{rng.integers(1000, 9999)}",
            "country": "US",
            "currency": "USD",
            "contact_email": f"support@{inactive_sup_id.lower()}.example.com",
            "risk_score": 0.85,
            "lead_time_mean": 21.0,
            "lead_time_variance": 4.0,
            "status": "INACTIVE",
            "active": False,
            "created_at": "2025-01-01T00:00:00Z",
            "notes": "Vendor de-registered due to commercial bankruptcy",
        }
        dataset["suppliers"].append(inactive_sup)

        # Reassign target PO to inactive supplier
        target_po["supplier_id"] = inactive_sup_id

        gt = GroundTruthRecord(
            anomaly_id=id_factory.next_anomaly_id(),
            issue_type="inactive_supplier_used",
            entity="purchase_orders",
            record_id=po_id,
            expected_decision="BLOCK",
            reason=f"Purchase order {po_id} issued to inactive/debarred vendor {inactive_sup_id}",
            metadata={"supplier_id": inactive_sup_id},
        )
        ground_truth.append(gt)

    return ground_truth


def inject_budget_overrun(
    dataset: Dict[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    count: int = 1,
    excluded_budget_ids: Optional[Set[str]] = None,
) -> List[GroundTruthRecord]:
    """Inject Budget Overrun anomalies.

    Adjusts department budget allocation below total active commitments/spend,
    keeping ledger events arithmetically consistent.
    """
    excluded = excluded_budget_ids or set()
    budgets = dataset.get("budgets", [])
    budget_events = dataset.get("budget_events", [])

    # Find budgets with positive commitments/spend
    candidates = [
        b for b in budgets
        if b["budget_id"] not in excluded
        and (int(b.get("committed_amount", 0)) + int(b.get("spent_amount", 0))) > 0
    ]

    if not candidates:
        return []

    chosen_indices = rng.choice(len(candidates), size=min(count, len(candidates)), replace=False)
    ground_truth: List[GroundTruthRecord] = []

    for idx in chosen_indices:
        target_b = candidates[idx]
        bid = target_b["budget_id"]

        used_cents = (
            int(target_b.get("committed_amount", 0))
            + int(target_b.get("spent_amount", 0))
            + int(target_b.get("reserved_amount", 0))
        )

        # Set allocation to 60% of used amount (guaranteeing a deficit)
        reduced_alloc_cents = max(100, int(used_cents * 0.60))
        target_b["allocated_amount"] = reduced_alloc_cents
        target_b["allocated"] = round(reduced_alloc_cents / 100.0, 2)

        # Update initial ALLOCATE event in budget_events to keep ledger arithmetic consistent
        for ev in budget_events:
            if ev["budget_id"] == bid and ev["event_type"] == "ALLOCATE":
                ev["amount"] = reduced_alloc_cents
                ev["amount_usd"] = round(reduced_alloc_cents / 100.0, 2)

        # Re-derive budget balances so that available_amount is accurately negative
        derive_budget_balances(budget_events, [target_b])

        gt = GroundTruthRecord(
            anomaly_id=id_factory.next_anomaly_id(),
            issue_type="budget_overrun",
            entity="budgets",
            record_id=bid,
            expected_decision="REJECT",
            reason=(
                f"Department budget {bid} total encumbrances (${round(used_cents/100, 2):,.2f}) "
                f"exceed allocated budget limit (${round(reduced_alloc_cents/100, 2):,.2f})"
            ),
            metadata={
                "allocated_amount": reduced_alloc_cents,
                "encumbered_amount": used_cents,
                "deficit_cents": used_cents - reduced_alloc_cents,
            },
        )
        ground_truth.append(gt)

    return ground_truth


def inject_duplicate_purchase_request(
    dataset: Dict[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    count: int = 1,
    excluded_pr_ids: Optional[Set[str]] = None,
) -> List[GroundTruthRecord]:
    """Inject Duplicate Purchase Request anomalies.

    Creates an identical requisition with same requester and item lines within a short window.
    """
    sync_factory_counters(id_factory, dataset)
    excluded = excluded_pr_ids or set()
    prs = dataset.get("purchase_requests", [])
    req_lines = dataset.get("request_lines", [])

    lines_by_pr: Dict[str, List[Dict[str, Any]]] = {}
    for rl in req_lines:
        lines_by_pr.setdefault(rl["request_id"], []).append(rl)

    candidates = [
        pr for pr in prs
        if pr["request_id"] not in excluded and pr["request_id"] in lines_by_pr
    ]

    if not candidates:
        return []

    chosen_indices = rng.choice(len(candidates), size=min(count, len(candidates)), replace=False)
    ground_truth: List[GroundTruthRecord] = []

    for idx in chosen_indices:
        orig_pr = candidates[idx]
        orig_lines = lines_by_pr[orig_pr["request_id"]]

        dup_pr_id = id_factory.next_purchase_request_id()
        orig_date = orig_pr.get("request_date") or orig_pr["created_at"][:10]
        dup_date = _shift_days(orig_date, int(rng.integers(1, 4)))

        # Create duplicate PR record
        dup_pr = dict(orig_pr)
        dup_pr["request_id"] = dup_pr_id
        dup_pr["request_date"] = dup_date
        dup_pr["created_at"] = f"{dup_date}T10:00:00Z"
        dup_pr["updated_at"] = f"{dup_date}T10:00:00Z"
        dup_pr["status"] = "SUBMITTED"
        dataset["purchase_requests"].append(dup_pr)

        # Clone request lines
        for rl in orig_lines:
            dup_rl = dict(rl)
            dup_rl["request_line_id"] = id_factory.next_request_line_id()
            dup_rl["request_id"] = dup_pr_id
            dup_rl["created_at"] = f"{dup_date}T10:00:00Z"
            dataset["request_lines"].append(dup_rl)

        gt = GroundTruthRecord(
            anomaly_id=id_factory.next_anomaly_id(),
            issue_type="duplicate_purchase_request",
            entity="purchase_requests",
            record_id=dup_pr_id,
            expected_decision="FLAG",
            reason=(
                f"Duplicate requisition {dup_pr_id} submitted for identical items within short "
                f"time window of original request {orig_pr['request_id']}"
            ),
            metadata={
                "original_request_id": orig_pr["request_id"],
                "duplicate_request_id": dup_pr_id,
                "requester_id": orig_pr["requester_id"],
            },
        )
        ground_truth.append(gt)

    return ground_truth


def inject_quote_currency_mismatch(
    dataset: Dict[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    count: int = 1,
    excluded_quote_ids: Optional[Set[str]] = None,
) -> List[GroundTruthRecord]:
    """Inject Quote Currency Mismatch anomalies.

    Changes quote currency to an unsupported foreign code without valid exchange rate conversion.
    """
    excluded = excluded_quote_ids or set()
    quotes = dataset.get("supplier_quotes", [])

    candidates = [
        q for q in quotes
        if q["quote_id"] not in excluded and q.get("status") != "AWARDED"
    ]

    if not candidates:
        return []

    chosen_indices = rng.choice(len(candidates), size=min(count, len(candidates)), replace=False)
    ground_truth: List[GroundTruthRecord] = []

    for idx in chosen_indices:
        target_quote = candidates[idx]
        qid = target_quote["quote_id"]

        # Set to an unmapped unsupported currency code
        target_quote["currency"] = "XYZ"
        target_quote["fx_rate_to_base"] = None

        gt = GroundTruthRecord(
            anomaly_id=id_factory.next_anomaly_id(),
            issue_type="quote_currency_mismatch",
            entity="supplier_quotes",
            record_id=qid,
            expected_decision="REVISE",
            reason=f"Quote {qid} submitted in unsupported currency XYZ lacking valid FX conversion rate",
            metadata={"currency": "XYZ"},
        )
        ground_truth.append(gt)

    return ground_truth


# ==============================================================================
# MASTER ANOMALY INJECTION ORCHESTRATOR
# ==============================================================================

def inject_anomalies(
    clean_dataset: Dict[str, Any],
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: Optional[IDFactory] = None,
    counts_per_category: Optional[Dict[str, int]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Inject controlled anomalies into a deep copy of the clean dataset.

    Preserves the clean input dataset without side effects.
    Emits separate ground-truth labels for all injected anomalies.

    Args:
        clean_dataset: The pristine synthetic dataset from Phase 3/4.
        config: Central configuration dictionary.
        rng: Deterministic NumPy random generator.
        id_factory: Central IDFactory instance.
        counts_per_category: Optional explicit counts per anomaly category.

    Returns:
        Tuple[Dict[str, Any], List[Dict[str, Any]]]:
            (anomaly_injected_dataset, ground_truth_records).
    """
    dataset = copy.deepcopy(clean_dataset)
    factory = id_factory or IDFactory(fiscal_year=int(config.get("project", {}).get("fiscal_year", 2026)))
    sync_factory_counters(factory, dataset)

    scale_name = dataset.get("metadata", {}).get("scale") or config.get("generation", {}).get("default_scale", "starter")
    default_count = 1 if scale_name == "starter" else 5

    counts = counts_per_category or {
        cat: default_count for cat in ANOMALY_CATEGORIES
    }

    all_ground_truth: List[GroundTruthRecord] = []
    mutated_po_ids: Set[str] = set()
    mutated_quote_ids: Set[str] = set()
    mutated_pr_ids: Set[str] = set()
    mutated_budget_ids: Set[str] = set()

    # 1. PO Without Approval
    gt_po_no_app = inject_po_without_approval(
        dataset, rng, factory, count=counts.get("po_without_approval", default_count), excluded_po_ids=mutated_po_ids
    )
    for g in gt_po_no_app:
        mutated_po_ids.add(g.record_id)
    all_ground_truth.extend(gt_po_no_app)

    # 2. Expired Quote Before Award
    gt_exp_quote = inject_expired_quote_before_award(
        dataset, rng, factory, count=counts.get("expired_quote_before_award", default_count), excluded_quote_ids=mutated_quote_ids
    )
    for g in gt_exp_quote:
        mutated_quote_ids.add(g.record_id)
    all_ground_truth.extend(gt_exp_quote)

    # 3. Non-Cheapest Quote Without Rationale
    gt_non_cheap = inject_non_cheapest_quote_without_rationale(
        dataset, rng, factory, count=counts.get("non_cheapest_quote_without_rationale", default_count), excluded_quote_ids=mutated_quote_ids
    )
    for g in gt_non_cheap:
        mutated_quote_ids.add(g.record_id)
    all_ground_truth.extend(gt_non_cheap)

    # 4. Inactive Supplier Used
    gt_inactive_sup = inject_inactive_supplier_used(
        dataset, rng, factory, count=counts.get("inactive_supplier_used", default_count), excluded_po_ids=mutated_po_ids
    )
    for g in gt_inactive_sup:
        mutated_po_ids.add(g.record_id)
    all_ground_truth.extend(gt_inactive_sup)

    # 5. Budget Overrun
    gt_budget_over = inject_budget_overrun(
        dataset, rng, factory, count=counts.get("budget_overrun", default_count), excluded_budget_ids=mutated_budget_ids
    )
    for g in gt_budget_over:
        mutated_budget_ids.add(g.record_id)
    all_ground_truth.extend(gt_budget_over)

    # 6. Duplicate Purchase Request
    gt_dup_pr = inject_duplicate_purchase_request(
        dataset, rng, factory, count=counts.get("duplicate_purchase_request", default_count), excluded_pr_ids=mutated_pr_ids
    )
    for g in gt_dup_pr:
        mutated_pr_ids.add(g.record_id)
    all_ground_truth.extend(gt_dup_pr)

    # 7. Quote Currency Mismatch
    gt_curr_mismatch = inject_quote_currency_mismatch(
        dataset, rng, factory, count=counts.get("quote_currency_mismatch", default_count), excluded_quote_ids=mutated_quote_ids
    )
    for g in gt_curr_mismatch:
        mutated_quote_ids.add(g.record_id)
    all_ground_truth.extend(gt_curr_mismatch)

    # Convert ground truth to dictionaries
    gt_dicts = [gt.to_dict() for gt in all_ground_truth]

    # Calculate and store anomaly summary in dataset metadata
    total_anomalies = len(gt_dicts)
    total_transactions = (
        len(dataset.get("purchase_orders", []))
        + len(dataset.get("purchase_requests", []))
        + len(dataset.get("rfqs", []))
    )
    anomaly_rate = round(total_anomalies / total_transactions, 4) if total_transactions > 0 else 0.0

    if "metadata" not in dataset:
        dataset["metadata"] = {}
    dataset["metadata"]["anomalies_injected"] = total_anomalies
    dataset["metadata"]["anomaly_rate"] = anomaly_rate
    dataset["metadata"]["anomaly_categories_count"] = len(set(g["issue_type"] for g in gt_dicts))

    return dataset, gt_dicts
