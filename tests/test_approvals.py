"""Unit tests for multi-tier approval generation and delegation of authority."""

import numpy as np
import pytest

from datagen.approvals import generate_approvals
from datagen.config import load_config
from datagen.ids import IDFactory
from datagen.masters import generate_all_masters
from datagen.requests import generate_all_requests


@pytest.fixture
def workflow_setup():
    """Setup base masters and requests for approval testing."""
    config = load_config()
    rng = np.random.default_rng(20261022)
    id_factory = IDFactory()
    masters = generate_all_masters(config, rng, id_factory)
    requests_data = generate_all_requests(
        config,
        rng,
        id_factory,
        masters["departments"],
        masters["budgets"],
        masters["requesters"],
    )
    return config, rng, id_factory, masters, requests_data


def test_approval_thresholds_and_tiers(workflow_setup):
    """Verify that requests receive the correct approval level based on monetary thresholds."""
    config, rng, id_factory, masters, requests_data = workflow_setup
    prs = requests_data["purchase_requests"]
    approvers = masters["approvers"]

    approval_data = generate_approvals(config, rng, id_factory, prs, approvers)
    approvals = approval_data["approvals"]

    apps_by_request = {}
    for app in approvals:
        apps_by_request.setdefault(app["request_id"], []).append(app)

    mgr_limit = float(config["approval_thresholds"]["manager_limit"])
    dept_head_limit = float(config["approval_thresholds"]["department_head_limit"])

    for pr in prs:
        req_id = pr["request_id"]
        if pr["status"] == "DRAFT":
            assert req_id not in apps_by_request
            continue

        req_apps = apps_by_request.get(req_id, [])
        assert len(req_apps) >= 1
        est = pr["total_estimate_usd"]

        l1 = req_apps[0]
        assert l1["approval_level"] == 1
        assert l1["decision"] in ("APPROVED", "REJECTED")

        if est <= mgr_limit:
            assert l1["approver_role"] == "LINE_MANAGER"
            assert len(req_apps) == 1
        elif est <= dept_head_limit:
            assert l1["approver_role"] == "DEPARTMENT_HEAD"
            assert len(req_apps) == 1
        else:
            # Over 25,000 requires Dept Head + Finance (if L1 approved)
            assert l1["approver_role"] == "DEPARTMENT_HEAD"
            if l1["decision"] == "APPROVED":
                assert len(req_apps) == 2
                l2 = req_apps[1]
                assert l2["approval_level"] == 2
                assert l2["approver_role"] == "FINANCE"


def test_rejected_requests_cannot_proceed(workflow_setup):
    """Verify rejected requests are marked REJECTED and isolated from approved workflow."""
    config, rng, id_factory, masters, requests_data = workflow_setup
    prs = requests_data["purchase_requests"]
    approvers = masters["approvers"]

    approval_data = generate_approvals(config, rng, id_factory, prs, approvers)
    rejected = approval_data["rejected_requests"]
    approved = approval_data["approved_requests"]

    assert len(rejected) > 0  # Some natural business rejections exist
    assert len(approved) > 0

    rejected_ids = {r["request_id"] for r in rejected}
    approved_ids = {a["request_id"] for a in approved}

    assert rejected_ids.isdisjoint(approved_ids)
    for r in rejected:
        assert r["status"] == "REJECTED"


def test_approval_chronological_ordering(workflow_setup):
    """Verify approval timestamps occur on or after requisition dates."""
    config, rng, id_factory, masters, requests_data = workflow_setup
    prs = requests_data["purchase_requests"]
    approvers = masters["approvers"]
    pr_map = {p["request_id"]: p for p in prs}

    approval_data = generate_approvals(config, rng, id_factory, prs, approvers)
    for app in approval_data["approvals"]:
        pr = pr_map[app["request_id"]]
        assert app["decision_date"][:10] >= pr["request_date"]

