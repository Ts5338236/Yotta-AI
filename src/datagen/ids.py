"""Centralized ID generation module for Procure-to-Pay Synthetic Data Generator.

Provides deterministic, zero-padded, collision-free identifiers for all procurement
entities without global mutable state, uncontrolled randomness, or UUIDs.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, Pattern, Set


# Exported regular expression patterns for validating entity identifiers across phases
ID_REGEX_MAP: Dict[str, str] = {
    "department": r"^DEPT-\d{2}$",
    "budget": r"^BUD-\d{4}$",
    "requester": r"^REQ-\d{4}$",
    "supplier": r"^SUP-\d{4}$",
    "approver": r"^APP-\d{4}$",
    "purchase_request": r"^PR-\d{4}-\d{6}$",
    "rfq": r"^RFQ-\d{4}-\d{6}$",
    "supplier_quote": r"^QUO-\d{4}-\d{6}$",
    "purchase_order": r"^PO-\d{4}-\d{6}$",
    "delivery": r"^DEL-PO-\d{4}-\d{6}-\d{2}$",
    "request_line": r"^RL-\d{6}$",
    "quote_line": r"^QL-\d{6}$",
    "approval": r"^APR-\d{6}$",
    "purchase_order_line": r"^POL-\d{6}$",
    "budget_event": r"^BE-\d{6}$",
    "status_event": r"^SE-\d{6}$",
    "rfq_supplier_invite": r"^INV-\d{6}$",
    "exception_log": r"^EXC-\d{6}$",
    "anomaly": r"^ANOM-\d{6}$",
}

# Pre-compiled patterns for high-performance validation
COMPILED_ID_PATTERNS: Dict[str, Pattern[str]] = {
    entity: re.compile(pattern) for entity, pattern in ID_REGEX_MAP.items()
}


class IDFactory:
    """Centralized, state-isolated factory for generating deterministic entity IDs.

    Maintains independent monotonic sequence counters for each entity type.
    """

    def __init__(self, fiscal_year: int = 2026) -> None:
        """Initialize the IDFactory.

        Args:
            fiscal_year: Four-digit fiscal year used for fiscal-scoped entity IDs.
        """
        self.fiscal_year = fiscal_year
        self._counters: Dict[str, int] = defaultdict(int)
        self._po_delivery_counters: Dict[str, int] = defaultdict(int)
        self._generated_ids: Set[str] = set()

    def reset(self, fiscal_year: int | None = None) -> None:
        """Reset all counters and tracked IDs, optionally updating the fiscal year.

        Args:
            fiscal_year: Optional new fiscal year. If None, current fiscal year is preserved.
        """
        if fiscal_year is not None:
            self.fiscal_year = fiscal_year
        self._counters.clear()
        self._po_delivery_counters.clear()
        self._generated_ids.clear()

    def _generate(self, entity_key: str, formatted_id: str) -> str:
        """Register and verify uniqueness of a generated ID."""
        if formatted_id in self._generated_ids:
            raise ValueError(f"Duplicate ID detected during generation: {formatted_id}")
        self._generated_ids.add(formatted_id)
        return formatted_id

    # Core master & actor entities
    def next_department_id(self) -> str:
        """Generate next Department ID (e.g. DEPT-01)."""
        self._counters["department"] += 1
        seq = self._counters["department"]
        return self._generate("department", f"DEPT-{seq:02d}")

    def next_budget_id(self) -> str:
        """Generate next Budget ID (e.g. BUD-0001)."""
        self._counters["budget"] += 1
        seq = self._counters["budget"]
        return self._generate("budget", f"BUD-{seq:04d}")

    def next_requester_id(self) -> str:
        """Generate next Requester ID (e.g. REQ-0001)."""
        self._counters["requester"] += 1
        seq = self._counters["requester"]
        return self._generate("requester", f"REQ-{seq:04d}")

    def next_supplier_id(self) -> str:
        """Generate next Supplier ID (e.g. SUP-0001)."""
        self._counters["supplier"] += 1
        seq = self._counters["supplier"]
        return self._generate("supplier", f"SUP-{seq:04d}")

    def next_approver_id(self) -> str:
        """Generate next Approver ID (e.g. APP-0001)."""
        self._counters["approver"] += 1
        seq = self._counters["approver"]
        return self._generate("approver", f"APP-{seq:04d}")

    # Core procurement transaction entities (fiscal year scoped)
    def next_purchase_request_id(self) -> str:
        """Generate next Purchase Request ID (e.g. PR-2026-000001)."""
        self._counters["purchase_request"] += 1
        seq = self._counters["purchase_request"]
        return self._generate("purchase_request", f"PR-{self.fiscal_year}-{seq:06d}")

    def next_rfq_id(self) -> str:
        """Generate next RFQ ID (e.g. RFQ-2026-000001)."""
        self._counters["rfq"] += 1
        seq = self._counters["rfq"]
        return self._generate("rfq", f"RFQ-{self.fiscal_year}-{seq:06d}")

    def next_supplier_quote_id(self) -> str:
        """Generate next Supplier Quote ID (e.g. QUO-2026-000001)."""
        self._counters["supplier_quote"] += 1
        seq = self._counters["supplier_quote"]
        return self._generate("supplier_quote", f"QUO-{self.fiscal_year}-{seq:06d}")

    def next_purchase_order_id(self) -> str:
        """Generate next Purchase Order ID (e.g. PO-2026-000001)."""
        self._counters["purchase_order"] += 1
        seq = self._counters["purchase_order"]
        return self._generate("purchase_order", f"PO-{self.fiscal_year}-{seq:06d}")

    def next_delivery_id(self, po_id: str) -> str:
        """Generate next Delivery ID for a specific Purchase Order.

        Args:
            po_id: Purchase Order ID (e.g. PO-2026-000001).

        Returns:
            Delivery identifier formatted as DEL-{po_id}-{seq:02d}.
        """
        if not COMPILED_ID_PATTERNS["purchase_order"].match(po_id):
            raise ValueError(f"Invalid purchase order ID format for delivery: {po_id}")

        self._po_delivery_counters[po_id] += 1
        seq = self._po_delivery_counters[po_id]
        return self._generate("delivery", f"DEL-{po_id}-{seq:02d}")

    # Additional line items, events and logs
    def next_request_line_id(self) -> str:
        """Generate next Request Line ID (e.g. RL-000001)."""
        self._counters["request_line"] += 1
        seq = self._counters["request_line"]
        return self._generate("request_line", f"RL-{seq:06d}")

    def next_quote_line_id(self) -> str:
        """Generate next Quote Line ID (e.g. QL-000001)."""
        self._counters["quote_line"] += 1
        seq = self._counters["quote_line"]
        return self._generate("quote_line", f"QL-{seq:06d}")

    def next_approval_id(self) -> str:
        """Generate next Approval ID (e.g. APR-000001)."""
        self._counters["approval"] += 1
        seq = self._counters["approval"]
        return self._generate("approval", f"APR-{seq:06d}")

    def next_purchase_order_line_id(self) -> str:
        """Generate next Purchase Order Line ID (e.g. POL-000001)."""
        self._counters["purchase_order_line"] += 1
        seq = self._counters["purchase_order_line"]
        return self._generate("purchase_order_line", f"POL-{seq:06d}")

    def next_budget_event_id(self) -> str:
        """Generate next Budget Event ID (e.g. BE-000001)."""
        self._counters["budget_event"] += 1
        seq = self._counters["budget_event"]
        return self._generate("budget_event", f"BE-{seq:06d}")

    def next_status_event_id(self) -> str:
        """Generate next Status Event ID (e.g. SE-000001)."""
        self._counters["status_event"] += 1
        seq = self._counters["status_event"]
        return self._generate("status_event", f"SE-{seq:06d}")

    def next_rfq_supplier_invite_id(self) -> str:
        """Generate next RFQ Supplier Invite ID (e.g. INV-000001)."""
        self._counters["rfq_supplier_invite"] += 1
        seq = self._counters["rfq_supplier_invite"]
        return self._generate("rfq_supplier_invite", f"INV-{seq:06d}")

    def next_exception_log_id(self) -> str:
        """Generate next Exception Log ID (e.g. EXC-000001)."""
        self._counters["exception_log"] += 1
        seq = self._counters["exception_log"]
        return self._generate("exception_log", f"EXC-{seq:06d}")

    def next_anomaly_id(self) -> str:
        """Generate next Anomaly Ground Truth ID (e.g. ANOM-000001)."""
        self._counters["anomaly"] += 1
        seq = self._counters["anomaly"]
        return self._generate("anomaly", f"ANOM-{seq:06d}")

    def validate_id(self, entity_type: str, entity_id: str) -> bool:
        """Validate if an entity ID matches the canonical pattern for that entity type.

        Args:
            entity_type: Entity key (e.g. 'purchase_order', 'delivery', 'requester').
            entity_id: The ID string to check.

        Returns:
            bool: True if valid, False otherwise.
        """
        return validate_id(entity_type, entity_id)


def validate_id(entity_type: str, entity_id: str) -> bool:
    """Validate if an entity ID matches the canonical pattern for that entity type.

    Args:
        entity_type: Entity key (e.g. 'purchase_order', 'delivery', 'requester').
        entity_id: The ID string to check.

    Returns:
        bool: True if valid, False otherwise.
    """
    pattern = COMPILED_ID_PATTERNS.get(entity_type)
    if pattern is None:
        raise KeyError(f"Unknown entity type for ID validation: {entity_type}")
    return bool(pattern.match(entity_id))

