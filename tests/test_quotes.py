"""Unit tests for supplier quotations, landed costs, multicriteria scoring, and awards."""

import numpy as np
import pytest

from datagen.approvals import generate_approvals
from datagen.config import load_config
from datagen.ids import IDFactory
from datagen.masters import generate_all_masters
from datagen.requests import generate_all_requests
from datagen.sourcing import classify_sourcing_paths, generate_sourcing


@pytest.fixture
def sourcing_artifacts():
    """Setup sourcing artifacts for quote testing."""
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
    approval_data = generate_approvals(
        config,
        rng,
        id_factory,
        requests_data["purchase_requests"],
        masters["approvers"],
    )
    comp, _ = classify_sourcing_paths(config, rng, approval_data["approved_requests"])
    sourcing_data = generate_sourcing(
        config,
        rng,
        id_factory,
        comp,
        requests_data["request_lines"],
        masters["suppliers"],
    )
    return config, sourcing_data


def test_quote_lines_and_landed_cost_reconciliation(sourcing_artifacts):
    """Verify QuoteLine totals, multi-currency conversion, and landed cost formulas."""
    config, sourcing_data = sourcing_artifacts
    quotes = sourcing_data["supplier_quotes"]
    quote_lines = sourcing_data["quote_lines"]

    ql_by_quote = {}
    for ql in quote_lines:
        ql_by_quote.setdefault(ql["quote_id"], []).append(ql)

    for q in quotes:
        qid = q["quote_id"]
        assert qid in ql_by_quote
        lines = ql_by_quote[qid]

        # 1. Total quoted amount base equals sum of line_total_base
        sum_base = round(sum(l["line_total_base_float"] for l in lines), 2)
        assert abs(q["total_quoted_amount_usd"] - sum_base) < 0.05

        # 2. Landed cost formula verification
        expected_landed = round(
            q["total_quoted_amount_usd"] + q["freight"] + q["duty"] + q["tax_nonrecoverable"], 2
        )
        assert abs(q["landed_cost_base"] - expected_landed) < 0.01

        # 3. Validity date after quote date
        assert q["valid_until"] > q["quote_date"]


def test_multicriteria_scoring_and_lowest_score_award(sourcing_artifacts):
    """Verify that quote scores fall within [0, 1] and the lowest scoring quote is awarded."""
    config, sourcing_data = sourcing_artifacts
    quotes = sourcing_data["supplier_quotes"]
    rfqs = sourcing_data["rfqs"]
    awarded_quotes = sourcing_data["awarded_quotes"]

    quotes_by_rfq = {}
    for q in quotes:
        quotes_by_rfq.setdefault(q["rfq_id"], []).append(q)

    for rfq in rfqs:
        rfq_id = rfq["rfq_id"]
        rfq_quotes = quotes_by_rfq[rfq_id]

        assert rfq_id in awarded_quotes
        winner = awarded_quotes[rfq_id]

        # 1. Winner has lowest score
        min_score = min(q["score"] for q in rfq_quotes)
        assert winner["score"] == min_score
        assert winner["status"] == "AWARDED"

        # 2. All other quotes are marked REJECTED
        for q in rfq_quotes:
            assert 0.0 <= q["score"] <= 1.0
            if q["quote_id"] != winner["quote_id"]:
                assert q["status"] == "REJECTED"
