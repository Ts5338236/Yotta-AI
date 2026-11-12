"""Approval engine module for Procure-to-Pay Synthetic Data Generator.

Generates multi-tier approval events based on financial delegation of authority:
- <= $2,000: Line Manager approval (Level 1)
- $2,000 to $25,000: Department Head approval (Level 1)
- > $25,000: Department Head approval (Level 1) + Finance approval (Level 2)
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Mapping, Tuple
import numpy as np

from datagen.ids import IDFactory


def _add_days_to_iso(iso_date: str, days: int) -> tuple[str, str]:
    """Add days to a date string and return (YYYY-MM-DD, ISO 8601 UTC timestamp)."""
    base = datetime.date.fromisoformat(iso_date[:10])
    target = base + datetime.timedelta(days=days)
    if target.year > 2026:
        target = datetime.date(2026, 12, 31)
    date_str = target.isoformat()
    return date_str, f"{date_str}T11:00:00Z"


def generate_approvals(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    purchase_requests: List[Dict[str, Any]],
    approvers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Evaluate and generate approval events for eligible purchase requests.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        purchase_requests: List of purchase request records.
        approvers: List of approver master records.

    Returns:
        Dict[str, Any]:
            'approvals': List of generated approval records.
            'approved_requests': List of fully approved PR records.
            'rejected_requests': List of rejected PR records.
            'draft_requests': List of unsubmitted/draft PR records.
    """
    thresholds = config.get("approval_thresholds", {})
    mgr_limit = float(thresholds.get("manager_limit", 2000.0))
    dept_head_limit = float(thresholds.get("department_head_limit", 25000.0))

    # Index approvers by department and role
    mgr_by_dept: Dict[str, Dict[str, Any]] = {}
    head_by_dept: Dict[str, Dict[str, Any]] = {}
    finance_approvers: List[Dict[str, Any]] = []

    for app in approvers:
        dept_id = app.get("department_id")
        role = app["role"]
        if role == "LINE_MANAGER" and dept_id:
            mgr_by_dept[dept_id] = app
        elif role == "DEPARTMENT_HEAD" and dept_id:
            head_by_dept[dept_id] = app
        elif role == "FINANCE":
            finance_approvers.append(app)

    if not finance_approvers:
        # Fallback to any department head if finance approvers list empty
        finance_approvers = list(head_by_dept.values())

    approvals: List[Dict[str, Any]] = []
    approved_requests: List[Dict[str, Any]] = []
    rejected_requests: List[Dict[str, Any]] = []
    draft_requests: List[Dict[str, Any]] = []

    # Clean rejection rate: ~5% natural business rejection
    rejection_rate = 0.05

    for pr in purchase_requests:
        # Drafts are not yet submitted for approval
        if pr["status"] == "DRAFT":
            draft_requests.append(pr)
            continue

        dept_id = pr["department_id"]
        total_estimate = pr["total_estimate_usd"]
        req_date = pr["request_date"]

        # Determine approval tiers required
        requires_finance = total_estimate > dept_head_limit
        is_low_value = total_estimate <= mgr_limit

        # Level 1 Approver selection
        if is_low_value:
            level1_approver = mgr_by_dept.get(dept_id, head_by_dept[dept_id])
            l1_role = "LINE_MANAGER"
        else:
            level1_approver = head_by_dept.get(dept_id, mgr_by_dept[dept_id])
            l1_role = "DEPARTMENT_HEAD"

        l1_days = int(rng.integers(1, 3))
        l1_date, l1_ts = _add_days_to_iso(req_date, l1_days)

        # Decide Level 1
        l1_rejected = rng.uniform() < rejection_rate
        l1_decision = "REJECTED" if l1_rejected else "APPROVED"
        l1_comment = (
            "Rejected: Insufficient department budget allocation."
            if l1_rejected
            else "Approved: Valid operational expenditure."
        )

        app_id_1 = id_factory.next_approval_id()
        approvals.append({
            "approval_id": app_id_1,
            "request_id": pr["request_id"],
            "approver_id": level1_approver["approver_id"],
            "approver_role": l1_role,
            "approval_level": 1,
            "level": 1,
            "decision": l1_decision,
            "decision_date": l1_ts,
            "decided_at": l1_ts,
            "comments": l1_comment,
            "created_at": l1_ts,
        })

        if l1_rejected:
            pr["status"] = "REJECTED"
            pr["updated_at"] = l1_ts
            rejected_requests.append(pr)
            continue

        # Level 2 (Finance) if required
        if requires_finance:
            fin_approver = finance_approvers[rng.integers(0, len(finance_approvers))]
            l2_days = l1_days + int(rng.integers(1, 3))
            l2_date, l2_ts = _add_days_to_iso(req_date, l2_days)

            # Small chance of finance rejection
            l2_rejected = rng.uniform() < 0.03
            l2_decision = "REJECTED" if l2_rejected else "APPROVED"
            l2_comment = (
                "Rejected: Exceeds annual capital forecast."
                if l2_rejected
                else "Approved: Corporate finance review completed."
            )

            app_id_2 = id_factory.next_approval_id()
            approvals.append({
                "approval_id": app_id_2,
                "request_id": pr["request_id"],
                "approver_id": fin_approver["approver_id"],
                "approver_role": "FINANCE",
                "approval_level": 2,
                "level": 2,
                "decision": l2_decision,
                "decision_date": l2_ts,
                "decided_at": l2_ts,
                "comments": l2_comment,
                "created_at": l2_ts,
            })

            if l2_rejected:
                pr["status"] = "REJECTED"
                pr["updated_at"] = l2_ts
                rejected_requests.append(pr)
                continue

            pr["status"] = "APPROVED"
            pr["updated_at"] = l2_ts
            approved_requests.append(pr)
        else:
            pr["status"] = "APPROVED"
            pr["updated_at"] = l1_ts
            approved_requests.append(pr)

    return {
        "approvals": approvals,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
        "draft_requests": draft_requests,
    }

