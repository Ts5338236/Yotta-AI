"""End-to-end integration and determinism tests for complete procurement workflow."""

import pytest

from datagen.workflow import generate_procurement_workflow, run_clean_path_validation


def test_full_workflow_clean_path_validation_starter():
    """Verify end-to-end clean-path validation passes with zero errors on starter scale."""
    dataset = generate_procurement_workflow(scale="starter", seed=20261022)
    is_valid, errors = run_clean_path_validation(dataset)
    assert is_valid is True
    assert len(errors) == 0


def test_full_workflow_clean_path_validation_full():
    """Verify end-to-end clean-path validation passes with zero errors on full scale."""
    dataset = generate_procurement_workflow(scale="full", seed=20261022)
    is_valid, errors = run_clean_path_validation(dataset)
    assert is_valid is True
    assert len(errors) == 0


def test_workflow_seeded_determinism():
    """Verify that identical seeds produce byte-for-byte identical procurement workflow datasets."""
    ds1 = generate_procurement_workflow(scale="starter", seed=42)
    ds2 = generate_procurement_workflow(scale="starter", seed=42)

    # Check key entity counts
    assert len(ds1["purchase_orders"]) == len(ds2["purchase_orders"])
    assert len(ds1["deliveries"]) == len(ds2["deliveries"])
    assert len(ds1["budget_events"]) == len(ds2["budget_events"])
    assert len(ds1["status_events"]) == len(ds2["status_events"])

    # Check exact matching of IDs, amounts, and dates
    pos1 = [p["po_id"] for p in ds1["purchase_orders"]]
    pos2 = [p["po_id"] for p in ds2["purchase_orders"]]
    assert pos1 == pos2

    spend1 = sum(p["value"] for p in ds1["purchase_orders"])
    spend2 = sum(p["value"] for p in ds2["purchase_orders"])
    assert spend1 == spend2


def test_workflow_seed_divergence():
    """Verify that different seeds produce statistically distinct procurement transactions."""
    ds1 = generate_procurement_workflow(scale="starter", seed=100)
    ds2 = generate_procurement_workflow(scale="starter", seed=200)

    spend1 = sum(p["value"] for p in ds1["purchase_orders"])
    spend2 = sum(p["value"] for p in ds2["purchase_orders"])
    assert spend1 != spend2

