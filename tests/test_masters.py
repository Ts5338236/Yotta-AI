"""Tests for master data generation (departments, budgets, requesters, suppliers)."""

import numpy as np
import pytest

from datagen.config import load_config
from datagen.ids import IDFactory
from datagen.masters import (
    generate_all_masters,
    generate_budgets,
    generate_departments,
    generate_requesters,
    generate_suppliers,
)


@pytest.fixture
def base_config():
    """Load default configuration."""
    return load_config()


def test_generate_departments_starter_and_full(base_config):
    """Verify department counts and uniqueness for starter and full scales."""
    rng = np.random.default_rng(42)
    id_factory = IDFactory()

    # Starter scale
    depts_starter = generate_departments(base_config, rng, id_factory)
    assert len(depts_starter) == 10
    dept_ids = [d["department_id"] for d in depts_starter]
    dept_names = [d["name"] for d in depts_starter]
    cost_centers = [d["cost_center_code"] for d in depts_starter]

    assert len(set(dept_ids)) == 10
    assert len(set(dept_names)) == 10
    assert len(set(cost_centers)) == 10
    assert all(d["effective_from"] == "2026-01-01" for d in depts_starter)
    assert all(d["effective_to"] == "2026-12-31" for d in depts_starter)

    # Full scale
    id_factory.reset()
    config_full = dict(base_config)
    config_full["generation"] = dict(base_config["generation"], default_scale="full")
    depts_full = generate_departments(config_full, rng, id_factory)
    assert len(depts_full) == 12


def test_generate_budgets_integrity(base_config):
    """Verify budgets reference departments, have positive allocations, and zero initial encumbrance."""
    rng = np.random.default_rng(42)
    id_factory = IDFactory()
    depts = generate_departments(base_config, rng, id_factory)
    budgets = generate_budgets(base_config, rng, id_factory, depts)

    assert len(budgets) == len(depts)
    dept_ids = {d["department_id"] for d in depts}

    for b in budgets:
        assert b["department_id"] in dept_ids
        assert b["fiscal_year"] == 2026
        assert b["currency"] == "USD"
        assert b["allocated"] > 0
        assert b["allocated_amount"] > 0
        assert b["reserved"] == 0.0
        assert b["reserved_amount"] == 0
        assert b["committed"] == 0.0
        assert b["committed_amount"] == 0
        assert b["spent"] == 0.0
        assert b["spent_amount"] == 0

    # Ensure allocations vary across departments
    allocations = [b["allocated"] for b in budgets]
    assert len(set(allocations)) > 1


def test_generate_requesters_hierarchy_and_distribution(base_config):
    """Verify requester counts, department assignments, and strictly acyclic manager hierarchies."""
    rng = np.random.default_rng(42)
    id_factory = IDFactory()
    depts = generate_departments(base_config, rng, id_factory)
    requesters = generate_requesters(base_config, rng, id_factory, depts)

    assert len(requesters) == 30  # Starter scale count
    dept_ids = {d["department_id"] for d in depts}
    req_by_id = {r["requester_id"]: r for r in requesters}

    # 1. Every department has at least 1 requester
    dept_req_counts = {d: 0 for d in dept_ids}
    for r in requesters:
        assert r["department_id"] in dept_ids
        dept_req_counts[r["department_id"]] += 1
    assert all(count >= 1 for count in dept_req_counts.values())

    # 2. Departments do not all have the exact same count
    assert len(set(dept_req_counts.values())) > 1

    # 3. Hierarchy & circular reference check
    for r in requesters:
        manager_id = r["manager_id"]
        if manager_id is not None:
            # Manager must exist and be in the same department
            assert manager_id in req_by_id
            mgr = req_by_id[manager_id]
            assert mgr["department_id"] == r["department_id"]

            # Walk manager chain to ensure no circular loop
            visited = {r["requester_id"]}
            curr = mgr
            while curr["manager_id"] is not None:
                curr_mgr_id = curr["manager_id"]
                assert curr_mgr_id not in visited, f"Circular manager loop detected at {curr_mgr_id}"
                visited.add(curr_mgr_id)
                curr = req_by_id[curr_mgr_id]
        else:
            # Top-level leader should be DIRECTOR
            assert r["grade"] == "DIRECTOR"


def test_generate_suppliers_attributes_and_currencies(base_config):
    """Verify supplier counts, code uniqueness, status, risk scores, and valid currencies."""
    rng = np.random.default_rng(42)
    id_factory = IDFactory()
    suppliers = generate_suppliers(base_config, rng, id_factory)

    assert len(suppliers) == 12  # Starter scale
    supplier_ids = [s["supplier_id"] for s in suppliers]
    supplier_codes = [s["supplier_code"] for s in suppliers]
    supplier_names = [s["name"] for s in suppliers]

    assert len(set(supplier_ids)) == 12
    assert len(set(supplier_codes)) == 12
    assert len(set(supplier_names)) == 12

    valid_statuses = {"ACTIVE", "PREFERRED", "PROBATION", "INACTIVE"}
    valid_risks = {"LOW", "MEDIUM", "HIGH"}
    valid_currencies = set(base_config["fx_rates"].keys())

    for s in suppliers:
        assert s["status"] in valid_statuses
        assert s["risk_flag"] in valid_risks
        assert s["risk_classification"] in valid_risks
        assert 0.0 < s["risk_score"] < 1.0
        assert s["lead_time_mean"] > 0
        assert s["currency"] in valid_currencies


def test_generate_all_masters_integration(base_config):
    """Verify coordinating generate_all_masters returns all master datasets."""
    rng = np.random.default_rng(12345)
    id_factory = IDFactory()
    masters = generate_all_masters(base_config, rng, id_factory)

    assert "departments" in masters
    assert "budgets" in masters
    assert "requesters" in masters
    assert "suppliers" in masters
    assert len(masters["departments"]) == 10
    assert len(masters["budgets"]) == 10
    assert len(masters["requesters"]) == 30
    assert len(masters["suppliers"]) == 12

