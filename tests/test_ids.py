"""Tests for centralized ID generation module."""

import re
import pytest

from datagen.ids import COMPILED_ID_PATTERNS, IDFactory, ID_REGEX_MAP


def test_all_id_patterns_format():
    """Verify that every generated entity ID matches its canonical regex pattern."""
    factory = IDFactory(fiscal_year=2026)

    # Core entities
    dept_id = factory.next_department_id()
    assert re.match(r"^DEPT-\d{2}$", dept_id)
    assert dept_id == "DEPT-01"

    bud_id = factory.next_budget_id()
    assert re.match(r"^BUD-\d{4}$", bud_id)
    assert bud_id == "BUD-0001"

    req_id = factory.next_requester_id()
    assert re.match(r"^REQ-\d{4}$", req_id)
    assert req_id == "REQ-0001"

    sup_id = factory.next_supplier_id()
    assert re.match(r"^SUP-\d{4}$", sup_id)
    assert sup_id == "SUP-0001"

    app_id = factory.next_approver_id()
    assert re.match(r"^APP-\d{4}$", app_id)
    assert app_id == "APP-0001"

    # Fiscal scoped entities
    pr_id = factory.next_purchase_request_id()
    assert re.match(r"^PR-2026-\d{6}$", pr_id)
    assert pr_id == "PR-2026-000001"

    rfq_id = factory.next_rfq_id()
    assert re.match(r"^RFQ-2026-\d{6}$", rfq_id)
    assert rfq_id == "RFQ-2026-000001"

    quo_id = factory.next_supplier_quote_id(supplier_code="SUP-C-0001")
    assert re.match(r"^QUO-[A-Za-z0-9_-]+-2026-\d{6}$", quo_id)
    assert quo_id == "QUO-SUP-C-0001-2026-000001"

    po_id = factory.next_purchase_order_id()
    assert re.match(r"^PO-2026-\d{6}$", po_id)
    assert po_id == "PO-2026-000001"

    del_id = factory.next_delivery_id(po_id)
    assert re.match(r"^DEL-PO-2026-\d{6}-\d{2}$", del_id)
    assert del_id == "DEL-PO-2026-000001-01"

    # Lines, events, and logs
    rl_id = factory.next_request_line_id()
    assert re.match(r"^RL-\d{6}$", rl_id)
    assert rl_id == "RL-000001"

    ql_id = factory.next_quote_line_id()
    assert re.match(r"^QL-\d{6}$", ql_id)
    assert ql_id == "QL-000001"

    apr_id = factory.next_approval_id()
    assert re.match(r"^APR-\d{6}$", apr_id)
    assert apr_id == "APR-000001"

    pol_id = factory.next_purchase_order_line_id()
    assert re.match(r"^POL-\d{6}$", pol_id)
    assert pol_id == "POL-000001"

    be_id = factory.next_budget_event_id()
    assert re.match(r"^BE-\d{6}$", be_id)
    assert be_id == "BE-000001"

    se_id = factory.next_status_event_id()
    assert re.match(r"^SE-\d{6}$", se_id)
    assert se_id == "SE-000001"

    inv_id = factory.next_rfq_supplier_invite_id()
    assert re.match(r"^INV-\d{6}$", inv_id)
    assert inv_id == "INV-000001"

    exc_id = factory.next_exception_log_id()
    assert re.match(r"^EXC-\d{6}$", exc_id)
    assert exc_id == "EXC-000001"


def test_independent_entity_counters():
    """Verify that incrementing one entity counter does not advance other entity counters."""
    factory = IDFactory(fiscal_year=2026)

    factory.next_requester_id()  # REQ-0001
    factory.next_requester_id()  # REQ-0002
    req_3 = factory.next_requester_id()  # REQ-0003

    sup_1 = factory.next_supplier_id()  # SUP-0001
    dept_1 = factory.next_department_id()  # DEPT-01

    assert req_3 == "REQ-0003"
    assert sup_1 == "SUP-0001"
    assert dept_1 == "DEPT-01"


def test_multiple_delivery_ids_for_po():
    """Verify that multiple deliveries for a PO increment sequential suffix per PO independently."""
    factory = IDFactory(fiscal_year=2026)

    po1 = factory.next_purchase_order_id()  # PO-2026-000001
    po2 = factory.next_purchase_order_id()  # PO-2026-000002

    del1_po1 = factory.next_delivery_id(po1)
    del2_po1 = factory.next_delivery_id(po1)
    del1_po2 = factory.next_delivery_id(po2)

    assert del1_po1 == "DEL-PO-2026-000001-01"
    assert del2_po1 == "DEL-PO-2026-000001-02"
    assert del1_po2 == "DEL-PO-2026-000002-01"


def test_invalid_po_for_delivery_raises_value_error():
    """Verify that an invalid PO ID raises ValueError when generating delivery ID."""
    factory = IDFactory()
    with pytest.raises(ValueError, match="Invalid purchase order ID format"):
        factory.next_delivery_id("INVALID-PO-ID")


def test_reset_functionality():
    """Verify that reset restores all counters and clears duplicate tracking."""
    factory = IDFactory(fiscal_year=2026)

    assert factory.next_department_id() == "DEPT-01"
    assert factory.next_department_id() == "DEPT-02"

    factory.reset(fiscal_year=2027)

    assert factory.fiscal_year == 2027
    assert factory.next_department_id() == "DEPT-01"
    assert factory.next_purchase_request_id() == "PR-2027-000001"


def test_no_duplicate_ids():
    """Verify that factory generates unique IDs across repeated calls."""
    factory = IDFactory()
    ids = [factory.next_request_line_id() for _ in range(100)]
    assert len(ids) == len(set(ids))
    assert ids[0] == "RL-000001"
    assert ids[-1] == "RL-000100"


def test_validate_id_utility():
    """Verify the validate_id method validates correct IDs and rejects malformed IDs."""
    factory = IDFactory()

    assert factory.validate_id("department", "DEPT-01")
    assert factory.validate_id("department", "DEPT-99")
    assert not factory.validate_id("department", "DEPT-1")
    assert not factory.validate_id("department", "DEPT-001")

    assert factory.validate_id("purchase_order", "PO-2026-000001")
    assert not factory.validate_id("purchase_order", "PO-2026-1")

    assert factory.validate_id("supplier_quote", "QUO-SUP-C-0001-2026-000001")
    assert not factory.validate_id("supplier_quote", "QUO-2026-1")

    assert factory.validate_id("delivery", "DEL-PO-2026-000001-01")
    assert not factory.validate_id("delivery", "DEL-01")

    with pytest.raises(KeyError):
        factory.validate_id("unknown_entity", "XYZ-01")
