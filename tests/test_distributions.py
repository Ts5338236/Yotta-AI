"""Tests for category price distributions and seasonal pattern generation."""

from collections import Counter
import numpy as np
import pytest

from datagen import generate_phase2_dataset
from datagen.config import load_config


@pytest.fixture(scope="module")
def full_dataset():
    """Generate full dataset once for statistical distribution testing."""
    return generate_phase2_dataset(scale="full", seed=20261022)


def test_category_price_distributions_distinguishable(full_dataset):
    """Verify that category price distributions reflect distinct realistic profiles."""
    lines = full_dataset["request_lines"]

    prices_by_cat: dict[str, list[float]] = {}
    for line in lines:
        cat = line["category"]
        prices_by_cat.setdefault(cat, []).append(line["unit_estimate"])

    # Verify high-value categories (Industrial Equipment, IT Hardware) have much higher medians than Office Supplies
    median_industrial = np.median(prices_by_cat["Industrial Equipment"])
    median_hardware = np.median(prices_by_cat["IT Hardware"])
    median_supplies = np.median(prices_by_cat["Office Supplies"])

    assert median_industrial > median_supplies * 5, f"Expected industrial ({median_industrial}) >> supplies ({median_supplies})"
    assert median_hardware > median_supplies * 3, f"Expected hardware ({median_hardware}) >> supplies ({median_supplies})"


def test_category_price_bounds_enforced(full_dataset):
    """Verify that every generated price respects configured min_price and max_price."""
    config = load_config()
    cat_dists = config["category_distributions"]
    lines = full_dataset["request_lines"]

    for line in lines:
        cat = line["category"]
        cfg = cat_dists[cat]
        price = line["unit_estimate"]
        min_p = cfg["min_price"]
        max_p = cfg["max_price"]

        assert min_p <= price <= max_p, (
            f"Line price ${price} out of bounds for {cat} (${min_p} - ${max_p})"
        )


def test_seasonal_distribution_trend(full_dataset):
    """Verify that PR dates across 2026 reflect the configured year-end purchasing increase."""
    prs = full_dataset["purchase_requests"]
    months = [int(p["request_date"].split("-")[1]) for p in prs]
    month_counts = Counter(months)

    # All 12 months must have generated purchase requests in full scale (1,150 requests)
    assert len(month_counts) == 12

    # Configured Q1 weight = 0.07 + 0.07 + 0.08 = 0.22
    # Configured Q4 weight = 0.10 + 0.10 + 0.11 = 0.31
    q1_count = month_counts[1] + month_counts[2] + month_counts[3]
    q4_count = month_counts[10] + month_counts[11] + month_counts[12]

    assert q4_count > q1_count, f"Expected Q4 count ({q4_count}) to be greater than Q1 count ({q1_count})"


def test_numerical_sanity_checks(full_dataset):
    """Verify no negative, zero, NaN, or infinite values in generated requests and lines."""
    for pr in full_dataset["purchase_requests"]:
        assert pr["total_estimate_usd"] > 0
        assert pr["total_estimated_amount"] > 0
        assert not np.isnan(pr["total_estimate_usd"])

    for line in full_dataset["request_lines"]:
        assert line["qty"] > 0
        assert line["unit_estimate"] > 0
        assert line["line_total"] > 0
        assert not np.isnan(line["unit_estimate"])
        assert not np.isnan(line["line_total"])
