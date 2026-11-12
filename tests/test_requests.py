"""Tests for Purchase Request and Request Line generation."""

from collections import defaultdict
import numpy as np
import pytest

from datagen.config import load_config
from datagen.ids import IDFactory
from datagen.masters import generate_all_masters
from datagen.requests import generate_all_requests, CATEGORY_ITEM_CATALOG


@pytest.fixture
def master_data():
    """Generate in-memory masters fixture for requests testing."""
    config = load_config()
    rng = np.random.default_rng(20261022)
    id_factory = IDFactory()
    masters = generate_all_masters(config, rng, id_factory)
    return config, rng, id_factory, masters


def test_purchase_requests_counts_and_relationships(master_data):
    """Verify purchase request counts, departmental consistency, and pre-approval workflow status."""
    config, rng, id_factory, masters = master_data
    requests_data = generate_all_requests(
        config,
        rng,
        id_factory,
        masters["departments"],
        masters["budgets"],
        masters["requesters"],
    )

    prs = requests_data["purchase_requests"]
    assert len(prs) == 115  # Starter scale count

    req_map = {r["requester_id"]: r for r in masters["requesters"]}
    dept_budget_map = {b["department_id"]: b["budget_id"] for b in masters["budgets"]}

    valid_statuses = {"DRAFT", "SUBMITTED"}
    valid_priorities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    for pr in prs:
        # 1. Requester relationship
        assert pr["requester_id"] in req_map
        req = req_map[pr["requester_id"]]

        # 2. Department consistency
        assert pr["department_id"] == req["department_id"]

        # 3. Budget consistency
        assert pr["budget_id"] == dept_budget_map[pr["department_id"]]

        # 4. Temporal constraints: within fiscal year 2026
        assert pr["request_date"].startswith("2026-")
        assert pr["created_at"].startswith("2026-")

        # 5. Pre-approval statuses only (No APPROVED or REJECTED in Phase 2)
        assert pr["status"] in valid_statuses
        assert pr["status"] not in {"APPROVED", "REJECTED"}

        # 6. Valid priority
        assert pr["priority"] in valid_priorities


def test_request_lines_integrity_and_categories(master_data):
    """Verify request lines have positive quantities, valid categories, and exact line totals."""
    config, rng, id_factory, masters = master_data
    requests_data = generate_all_requests(
        config,
        rng,
        id_factory,
        masters["departments"],
        masters["budgets"],
        masters["requesters"],
    )

    prs = requests_data["purchase_requests"]
    lines = requests_data["request_lines"]
    pr_ids = {p["request_id"] for p in prs}
    approved_categories = set(CATEGORY_ITEM_CATALOG.keys())

    assert len(lines) >= len(prs)  # At least one line per PR

    lines_by_pr = defaultdict(list)
    for line in lines:
        assert line["request_id"] in pr_ids
        assert line["category"] in approved_categories
        assert line["qty"] > 0
        assert line["unit_estimate"] > 0.0

        # Exact line total calculation
        expected_line_total = round(line["qty"] * line["unit_estimate"], 2)
        assert line["line_total"] == expected_line_total
        assert line["estimated_line_total"] == int(round(expected_line_total * 100))

        lines_by_pr[line["request_id"]].append(line)

    # Every PR must have at least one line
    assert all(len(lines_by_pr[pid]) >= 1 for pid in pr_ids)


def test_exact_financial_reconciliation(master_data):
    """Verify that every PR total_estimate_usd equals exactly the sum of its request line totals."""
    config, rng, id_factory, masters = master_data
    requests_data = generate_all_requests(
        config,
        rng,
        id_factory,
        masters["departments"],
        masters["budgets"],
        masters["requesters"],
    )

    prs = requests_data["purchase_requests"]
    lines = requests_data["request_lines"]

    lines_sum_usd = defaultdict(float)
    lines_sum_cents = defaultdict(int)
    for line in lines:
        pid = line["request_id"]
        lines_sum_usd[pid] = round(lines_sum_usd[pid] + line["line_total"], 2)
        lines_sum_cents[pid] += line["estimated_line_total"]

    for pr in prs:
        pid = pr["request_id"]
        assert pr["total_estimate_usd"] == lines_sum_usd[pid]
        assert pr["total_estimated_amount"] == lines_sum_cents[pid]
        assert pr["total_estimate_usd"] > 0.0

