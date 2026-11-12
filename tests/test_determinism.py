"""Tests for strict deterministic generation behavior."""

import pytest

from datagen import generate_phase2_dataset


def test_identical_seed_produces_identical_data():
    """Verify that running generation with the same seed and scale produces identical output."""
    dataset_1 = generate_phase2_dataset(scale="starter", seed=20261022)
    dataset_2 = generate_phase2_dataset(scale="starter", seed=20261022)

    # Check entity counts match exactly
    assert len(dataset_1["departments"]) == len(dataset_2["departments"])
    assert len(dataset_1["budgets"]) == len(dataset_2["budgets"])
    assert len(dataset_1["requesters"]) == len(dataset_2["requesters"])
    assert len(dataset_1["suppliers"]) == len(dataset_2["suppliers"])
    assert len(dataset_1["purchase_requests"]) == len(dataset_2["purchase_requests"])
    assert len(dataset_1["request_lines"]) == len(dataset_2["request_lines"])

    # Check exact record-for-record identity
    assert dataset_1["departments"] == dataset_2["departments"]
    assert dataset_1["budgets"] == dataset_2["budgets"]
    assert dataset_1["requesters"] == dataset_2["requesters"]
    assert dataset_1["suppliers"] == dataset_2["suppliers"]
    assert dataset_1["purchase_requests"] == dataset_2["purchase_requests"]
    assert dataset_1["request_lines"] == dataset_2["request_lines"]


def test_different_seeds_produce_different_data():
    """Verify that running generation with different seeds produces statistically distinct data."""
    dataset_a = generate_phase2_dataset(scale="starter", seed=11111)
    dataset_b = generate_phase2_dataset(scale="starter", seed=99999)

    # Identifiers may align in pattern but values, prices, names, and totals should differ
    names_a = [r["name"] for r in dataset_a["requesters"]]
    names_b = [r["name"] for r in dataset_b["requesters"]]
    assert names_a != names_b

    spend_a = sum(pr["total_estimate_usd"] for pr in dataset_a["purchase_requests"])
    spend_b = sum(pr["total_estimate_usd"] for pr in dataset_b["purchase_requests"])
    assert spend_a != spend_b

    dates_a = [pr["request_date"] for pr in dataset_a["purchase_requests"]]
    dates_b = [pr["request_date"] for pr in dataset_b["purchase_requests"]]
    assert dates_a != dates_b


def test_scale_tier_differentiation():
    """Verify starter and full scales generate the configured counts."""
    starter = generate_phase2_dataset(scale="starter", seed=42)
    full = generate_phase2_dataset(scale="full", seed=42)

    assert len(starter["departments"]) == 10
    assert len(full["departments"]) == 12

    assert len(starter["requesters"]) == 30
    assert len(full["requesters"]) == 300

    assert len(starter["suppliers"]) == 12
    assert len(full["suppliers"]) == 120

    assert len(starter["purchase_requests"]) == 115
    assert len(full["purchase_requests"]) == 1200


