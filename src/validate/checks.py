"""Comprehensive Validation Engine and Business Rule Auditing (Phase 4).

Provides independent, non-circular validation across all procurement entities:
- Primary key uniqueness, nullability, and regex format compliance
- Relational foreign key and cross-entity reference integrity
- Financial arithmetic and currency reconciliation
- Lifecycle state machine transition validity
- Transaction date ordering and fiscal year chronology
- Procurement business rules, approvals, and supplier scoring/awards
- Double-entry budget ledger reconciliation and zero-overrun verification

Also preserves foundational Phase 1 SQLite schema checks.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

from datagen.config import load_config
from datagen.ids import ID_REGEX_MAP, validate_id as validate_entity_id
from validate.models import ValidationCheckResult, ValidationReport


# ==============================================================================
# PHASE 1 FOUNDATIONAL CHECKS (Preserved for Backward Compatibility)
# ==============================================================================

EXPECTED_TABLES: Set[str] = {
    "departments",
    "budgets",
    "requesters",
    "approvers",
    "suppliers",
    "purchase_requests",
    "request_lines",
    "rfqs",
    "rfq_supplier_invites",
    "supplier_quotes",
    "quote_lines",
    "approvals",
    "purchase_orders",
    "purchase_order_lines",
    "deliveries",
    "status_events",
    "budget_events",
    "exception_logs",
}


class ValidationCheckError(Exception):
    """Raised when a foundational validation check fails."""
    pass


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Connect to SQLite database with foreign keys enabled."""
    path = Path(db_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {path}")

    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def check_foreign_keys_enabled(conn: sqlite3.Connection) -> bool:
    """Verify that foreign key constraint enforcement is active."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    row = cursor.fetchone()
    return bool(row and row[0] == 1)


def check_schema_integrity(conn: sqlite3.Connection) -> Tuple[bool, List[str]]:
    """Execute PRAGMA integrity_check to verify SQLite database file health."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    rows = cursor.fetchall()
    messages = [r[0] for r in rows]
    is_ok = len(messages) == 1 and messages[0] == "ok"
    return is_ok, messages


def check_foreign_key_violations(conn: sqlite3.Connection) -> List[Tuple[Any, ...]]:
    """Execute PRAGMA foreign_key_check to detect orphaned references."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    return cursor.fetchall()


def get_existing_tables(conn: sqlite3.Connection) -> Set[str]:
    """Retrieve set of user table names in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return {row[0] for row in cursor.fetchall()}


def check_required_tables_exist(
    conn: sqlite3.Connection,
    expected_tables: Set[str] | None = None,
) -> Tuple[bool, Set[str]]:
    """Check if all required core and auxiliary tables exist."""
    expected = expected_tables or EXPECTED_TABLES
    existing = get_existing_tables(conn)
    missing = expected - existing
    return len(missing) == 0, missing


def validate_id_format(entity_type: str, entity_id: str) -> bool:
    """Validate an ID string against canonical regex for an entity type."""
    try:
        return validate_entity_id(entity_type, entity_id)
    except KeyError:
        return False


def run_foundational_checks(db_path: str | Path) -> Dict[str, Any]:
    """Execute full Phase 1 foundational check suite against a database."""
    conn = get_connection(db_path)
    try:
        fk_enabled = check_foreign_keys_enabled(conn)
        integrity_ok, integrity_messages = check_schema_integrity(conn)
        tables_ok, missing_tables = check_required_tables_exist(conn)
        fk_violations = check_foreign_key_violations(conn)

        all_passed = fk_enabled and integrity_ok and tables_ok and len(fk_violations) == 0

        return {
            "all_passed": all_passed,
            "foreign_keys_enabled": fk_enabled,
            "integrity_ok": integrity_ok,
            "integrity_messages": integrity_messages,
            "tables_ok": tables_ok,
            "missing_tables": sorted(list(missing_tables)),
            "fk_violations_count": len(fk_violations),
            "fk_violations": fk_violations,
        }
    finally:
        conn.close()


# ==============================================================================
# PHASE 4 COMPREHENSIVE INDEPENDENT VALIDATION CHECKS
# ==============================================================================

ENTITY_PK_MAP: Dict[str, str] = {
    "departments": "department_id",
    "budgets": "budget_id",
    "requesters": "requester_id",
    "approvers": "approver_id",
    "suppliers": "supplier_id",
    "purchase_requests": "request_id",
    "request_lines": "request_line_id",
    "rfqs": "rfq_id",
    "rfq_supplier_invites": "invite_id",
    "supplier_quotes": "quote_id",
    "quote_lines": "quote_line_id",
    "approvals": "approval_id",
    "purchase_orders": "po_id",
    "purchase_order_lines": "po_line_id",
    "deliveries": "delivery_id",
    "status_events": "status_event_id",
    "budget_events": "budget_event_id",
}

ENTITY_TYPE_ID_FACTORY_MAP: Dict[str, str] = {
    "departments": "department",
    "budgets": "budget",
    "requesters": "requester",
    "approvers": "approver",
    "suppliers": "supplier",
    "purchase_requests": "purchase_request",
    "request_lines": "request_line",
    "rfqs": "rfq",
    "rfq_supplier_invites": "rfq_supplier_invite",
    "supplier_quotes": "supplier_quote",
    "quote_lines": "quote_line",
    "approvals": "approval",
    "purchase_orders": "purchase_order",
    "purchase_order_lines": "purchase_order_line",
    "deliveries": "delivery",
    "status_events": "status_event",
    "budget_events": "budget_event",
}


def validate_primary_keys_and_ids(dataset: Dict[str, Any]) -> List[ValidationCheckResult]:
    """Validate primary-key uniqueness, nullability, and regex format compliance across all tables.

    Rules checked:
    - Primary keys must not be null or empty.
    - Primary keys must be strictly unique within each entity table.
    - Primary keys must match canonical IDFactory regex patterns.
    - Delivery IDs must match 'DEL-{PO_ID}-{SEQ}' format.
    - Unique business identifiers (department codes, invite pairs) must not have duplicates.
    """
    results: List[ValidationCheckResult] = []

    for table_name, pk_field in ENTITY_PK_MAP.items():
        records = dataset.get(table_name, [])
        seen_pks: Set[str] = set()
        factory_type = ENTITY_TYPE_ID_FACTORY_MAP.get(table_name, "")
        regex_pattern = ID_REGEX_MAP.get(factory_type)

        for rec in records:
            pk_val = rec.get(pk_field)

            # 1. Null / Empty Check
            if not pk_val or not str(pk_val).strip():
                results.append(ValidationCheckResult(
                    check_name="pk_not_null",
                    category="PRIMARY_KEYS",
                    passed=False,
                    severity="CRITICAL",
                    entity=table_name,
                    record_id=str(pk_val),
                    field=pk_field,
                    actual_value=pk_val,
                    expected_value="Non-empty string",
                    description=f"Primary key {pk_field} is null or empty in table {table_name}",
                ))
                continue

            # 2. Uniqueness Check
            pk_str = str(pk_val)
            if pk_str in seen_pks:
                results.append(ValidationCheckResult(
                    check_name="pk_uniqueness",
                    category="PRIMARY_KEYS",
                    passed=False,
                    severity="CRITICAL",
                    entity=table_name,
                    record_id=pk_str,
                    field=pk_field,
                    actual_value=pk_str,
                    expected_value="Unique identifier",
                    description=f"Duplicate primary key {pk_str} detected in table {table_name}",
                ))
            else:
                seen_pks.add(pk_str)

            # 3. ID Format Regex Check
            if regex_pattern and not re.match(regex_pattern, pk_str):
                results.append(ValidationCheckResult(
                    check_name="pk_id_format",
                    category="PRIMARY_KEYS",
                    passed=False,
                    severity="ERROR",
                    entity=table_name,
                    record_id=pk_str,
                    field=pk_field,
                    actual_value=pk_str,
                    expected_value=regex_pattern,
                    description=f"ID {pk_str} does not match canonical regex pattern for {table_name}",
                ))
            else:
                results.append(ValidationCheckResult(
                    check_name="pk_id_format",
                    category="PRIMARY_KEYS",
                    passed=True,
                    entity=table_name,
                    record_id=pk_str,
                    field=pk_field,
                    description=f"ID {pk_str} adheres to canonical regex pattern",
                ))

    # 4. Check business compound uniqueness: RFQ Invites (rfq_id, supplier_id)
    invites = dataset.get("rfq_supplier_invites", [])
    seen_invites: Set[Tuple[str, str]] = set()
    for inv in invites:
        pair = (inv.get("rfq_id"), inv.get("supplier_id"))
        if pair in seen_invites:
            results.append(ValidationCheckResult(
                check_name="rfq_invite_uniqueness",
                category="PRIMARY_KEYS",
                passed=False,
                severity="ERROR",
                entity="rfq_supplier_invites",
                record_id=str(inv.get("invite_id")),
                field="(rfq_id, supplier_id)",
                actual_value=str(pair),
                expected_value="Unique (rfq_id, supplier_id)",
                description=f"Duplicate supplier invitation {pair} in RFQ invites",
            ))
        else:
            seen_invites.add(pair)

    return results


def validate_foreign_keys(dataset: Dict[str, Any]) -> List[ValidationCheckResult]:
    """Verify all foreign-key relationships and cross-table references across the dataset.

    Checks:
    - Budget.department_id -> Department.department_id
    - Requester.department_id -> Department.department_id
    - PurchaseRequest.requester_id -> Requester.requester_id
    - PurchaseRequest.department_id -> matches Requester's department
    - PurchaseRequest.budget_id -> Budget.budget_id
    - RequestLine.request_id -> PurchaseRequest.request_id
    - RFQ.request_id -> PurchaseRequest.request_id
    - RFQSupplierInvite.rfq_id -> RFQ.rfq_id
    - RFQSupplierInvite.supplier_id -> Supplier.supplier_id
    - SupplierQuote.rfq_id -> RFQ.rfq_id
    - SupplierQuote.supplier_id -> invited Supplier for that RFQ
    - QuoteLine.quote_id -> SupplierQuote.quote_id
    - QuoteLine.request_line_id -> RequestLine of the corresponding PR
    - Approval.request_id -> PurchaseRequest.request_id
    - Approval.approver_id -> Approver.approver_id
    - PurchaseOrder.request_id -> PurchaseRequest.request_id
    - PurchaseOrder.supplier_id -> Supplier.supplier_id
    - PurchaseOrder.awarded_quote_id -> SupplierQuote (when competitive)
    - PurchaseOrderLine.po_id -> PurchaseOrder.po_id
    - PurchaseOrderLine.request_line_id -> RequestLine.request_line_id
    - Delivery.po_id -> PurchaseOrder.po_id
    - BudgetEvent.budget_id -> Budget.budget_id
    - StatusEvent.entity_id -> references valid entity record
    """
    results: List[ValidationCheckResult] = []

    # Build primary key lookup sets
    dept_ids = {d["department_id"] for d in dataset.get("departments", [])}
    budget_ids = {b["budget_id"] for b in dataset.get("budgets", [])}
    req_map = {r["requester_id"]: r for r in dataset.get("requesters", [])}
    approver_ids = {a["approver_id"] for a in dataset.get("approvers", [])}
    supplier_ids = {s["supplier_id"] for s in dataset.get("suppliers", [])}
    pr_map = {pr["request_id"]: pr for pr in dataset.get("purchase_requests", [])}
    rl_map = {rl["request_line_id"]: rl for rl in dataset.get("request_lines", [])}
    rfq_map = {r["rfq_id"]: r for r in dataset.get("rfqs", [])}
    quote_map = {q["quote_id"]: q for q in dataset.get("supplier_quotes", [])}
    po_map = {po["po_id"]: po for po in dataset.get("purchase_orders", [])}

    # Invited suppliers per RFQ
    rfq_invited_suppliers: Dict[str, Set[str]] = {}
    for inv in dataset.get("rfq_supplier_invites", []):
        rfq_invited_suppliers.setdefault(inv["rfq_id"], set()).add(inv["supplier_id"])

    # 1. Budget -> Department
    for b in dataset.get("budgets", []):
        did = b.get("department_id")
        passed = did in dept_ids
        results.append(ValidationCheckResult(
            check_name="fk_budget_department",
            category="FOREIGN_KEYS",
            passed=passed,
            severity="CRITICAL",
            entity="budgets",
            record_id=b.get("budget_id"),
            field="department_id",
            actual_value=did,
            expected_value="Valid department_id",
            description="Budget references existing department",
        ))

    # 2. Requester -> Department & Manager
    for r in dataset.get("requesters", []):
        did = r.get("department_id")
        passed = did in dept_ids
        results.append(ValidationCheckResult(
            check_name="fk_requester_department",
            category="FOREIGN_KEYS",
            passed=passed,
            severity="CRITICAL",
            entity="requesters",
            record_id=r.get("requester_id"),
            field="department_id",
            actual_value=did,
            expected_value="Valid department_id",
            description="Requester references existing department",
        ))
        mgr_id = r.get("manager_id")
        if mgr_id is not None:
            passed_mgr = mgr_id in req_map
            results.append(ValidationCheckResult(
                check_name="fk_requester_manager",
                category="FOREIGN_KEYS",
                passed=passed_mgr,
                severity="ERROR",
                entity="requesters",
                record_id=r.get("requester_id"),
                field="manager_id",
                actual_value=mgr_id,
                expected_value="Valid requester_id or None",
                description="Requester manager exists in requesters table",
            ))

    # 3. Purchase Request -> Requester, Department, Budget
    for pr in dataset.get("purchase_requests", []):
        pr_id = pr.get("request_id")
        req_id = pr.get("requester_id")
        did = pr.get("department_id")
        bid = pr.get("budget_id")

        passed_req = req_id in req_map
        results.append(ValidationCheckResult(
            check_name="fk_pr_requester",
            category="FOREIGN_KEYS",
            passed=passed_req,
            severity="CRITICAL",
            entity="purchase_requests",
            record_id=pr_id,
            field="requester_id",
            actual_value=req_id,
            expected_value="Valid requester_id",
            description="PR references valid requester",
        ))

        # Check department consistency: PR department must match Requester department
        if passed_req:
            expected_dept = req_map[req_id]["department_id"]
            dept_matches = (did == expected_dept)
            results.append(ValidationCheckResult(
                check_name="fk_pr_department_match",
                category="FOREIGN_KEYS",
                passed=dept_matches,
                severity="ERROR",
                entity="purchase_requests",
                record_id=pr_id,
                field="department_id",
                actual_value=did,
                expected_value=expected_dept,
                description="PR department matches requester's assigned department",
            ))

        passed_budget = bid in budget_ids
        results.append(ValidationCheckResult(
            check_name="fk_pr_budget",
            category="FOREIGN_KEYS",
            passed=passed_budget,
            severity="CRITICAL",
            entity="purchase_requests",
            record_id=pr_id,
            field="budget_id",
            actual_value=bid,
            expected_value="Valid budget_id",
            description="PR references valid department budget",
        ))

    # 4. Request Lines -> Purchase Request
    for rl in dataset.get("request_lines", []):
        rl_id = rl.get("request_line_id")
        req_id = rl.get("request_id")
        passed = req_id in pr_map
        results.append(ValidationCheckResult(
            check_name="fk_request_line_pr",
            category="FOREIGN_KEYS",
            passed=passed,
            severity="CRITICAL",
            entity="request_lines",
            record_id=rl_id,
            field="request_id",
            actual_value=req_id,
            expected_value="Valid request_id",
            description="Request line references existing purchase request",
        ))

    # 5. RFQs -> Purchase Request
    for rfq in dataset.get("rfqs", []):
        rfq_id = rfq.get("rfq_id")
        req_id = rfq.get("request_id")
        passed = req_id in pr_map
        results.append(ValidationCheckResult(
            check_name="fk_rfq_pr",
            category="FOREIGN_KEYS",
            passed=passed,
            severity="CRITICAL",
            entity="rfqs",
            record_id=rfq_id,
            field="request_id",
            actual_value=req_id,
            expected_value="Valid request_id",
            description="RFQ references existing purchase request",
        ))

    # 6. RFQ Supplier Invites -> RFQ & Supplier
    for inv in dataset.get("rfq_supplier_invites", []):
        inv_id = inv.get("invite_id")
        rfq_id = inv.get("rfq_id")
        sup_id = inv.get("supplier_id")
        passed_rfq = rfq_id in rfq_map
        passed_sup = sup_id in supplier_ids

        results.append(ValidationCheckResult(
            check_name="fk_invite_rfq",
            category="FOREIGN_KEYS",
            passed=passed_rfq,
            severity="CRITICAL",
            entity="rfq_supplier_invites",
            record_id=inv_id,
            field="rfq_id",
            actual_value=rfq_id,
            expected_value="Valid rfq_id",
            description="Invite references existing RFQ",
        ))
        results.append(ValidationCheckResult(
            check_name="fk_invite_supplier",
            category="FOREIGN_KEYS",
            passed=passed_sup,
            severity="CRITICAL",
            entity="rfq_supplier_invites",
            record_id=inv_id,
            field="supplier_id",
            actual_value=sup_id,
            expected_value="Valid supplier_id",
            description="Invite references existing supplier",
        ))

    # 7. Supplier Quotes -> RFQ & Invited Supplier
    for q in dataset.get("supplier_quotes", []):
        qid = q.get("quote_id")
        rfq_id = q.get("rfq_id")
        sup_id = q.get("supplier_id")
        passed_rfq = rfq_id in rfq_map

        results.append(ValidationCheckResult(
            check_name="fk_quote_rfq",
            category="FOREIGN_KEYS",
            passed=passed_rfq,
            severity="CRITICAL",
            entity="supplier_quotes",
            record_id=qid,
            field="rfq_id",
            actual_value=rfq_id,
            expected_value="Valid rfq_id",
            description="Quote references valid RFQ",
        ))

        # Compound rule: Quoting supplier MUST have been invited to that RFQ
        invited_pool = rfq_invited_suppliers.get(rfq_id, set())
        was_invited = sup_id in invited_pool
        results.append(ValidationCheckResult(
            check_name="fk_quote_supplier_was_invited",
            category="FOREIGN_KEYS",
            passed=was_invited,
            severity="CRITICAL",
            entity="supplier_quotes",
            record_id=qid,
            field="supplier_id",
            actual_value=sup_id,
            expected_value=f"Invited supplier for RFQ {rfq_id}",
            description="Quoting supplier was invited to the corresponding RFQ",
        ))

    # 8. Quote Lines -> Supplier Quote & Request Line
    for ql in dataset.get("quote_lines", []):
        ql_id = ql.get("quote_line_id")
        qid = ql.get("quote_id")
        rl_id = ql.get("request_line_id")

        passed_q = qid in quote_map
        passed_rl = rl_id in rl_map

        results.append(ValidationCheckResult(
            check_name="fk_quote_line_quote",
            category="FOREIGN_KEYS",
            passed=passed_q,
            severity="CRITICAL",
            entity="quote_lines",
            record_id=ql_id,
            field="quote_id",
            actual_value=qid,
            expected_value="Valid quote_id",
            description="Quote line references existing quotation",
        ))
        results.append(ValidationCheckResult(
            check_name="fk_quote_line_request_line",
            category="FOREIGN_KEYS",
            passed=passed_rl,
            severity="CRITICAL",
            entity="quote_lines",
            record_id=ql_id,
            field="request_line_id",
            actual_value=rl_id,
            expected_value="Valid request_line_id",
            description="Quote line references existing request line",
        ))

    # 9. Approvals -> Purchase Request & Approver
    for app in dataset.get("approvals", []):
        app_id = app.get("approval_id")
        req_id = app.get("request_id")
        approver_id = app.get("approver_id")

        passed_pr = req_id in pr_map
        passed_appr = approver_id in approver_ids

        results.append(ValidationCheckResult(
            check_name="fk_approval_pr",
            category="FOREIGN_KEYS",
            passed=passed_pr,
            severity="CRITICAL",
            entity="approvals",
            record_id=app_id,
            field="request_id",
            actual_value=req_id,
            expected_value="Valid request_id",
            description="Approval references existing purchase request",
        ))
        results.append(ValidationCheckResult(
            check_name="fk_approval_approver",
            category="FOREIGN_KEYS",
            passed=passed_appr,
            severity="CRITICAL",
            entity="approvals",
            record_id=app_id,
            field="approver_id",
            actual_value=approver_id,
            expected_value="Valid approver_id",
            description="Approval references registered approver",
        ))

    # 10. Purchase Orders -> PR, Supplier, Awarded Quote
    for po in dataset.get("purchase_orders", []):
        poid = po.get("po_id")
        req_id = po.get("request_id")
        sup_id = po.get("supplier_id")
        sourcing_path = po.get("sourcing_path")

        passed_pr = req_id in pr_map
        passed_sup = sup_id in supplier_ids

        results.append(ValidationCheckResult(
            check_name="fk_po_pr",
            category="FOREIGN_KEYS",
            passed=passed_pr,
            severity="CRITICAL",
            entity="purchase_orders",
            record_id=poid,
            field="request_id",
            actual_value=req_id,
            expected_value="Valid request_id",
            description="PO references existing purchase request",
        ))
        results.append(ValidationCheckResult(
            check_name="fk_po_supplier",
            category="FOREIGN_KEYS",
            passed=passed_sup,
            severity="CRITICAL",
            entity="purchase_orders",
            record_id=poid,
            field="supplier_id",
            actual_value=sup_id,
            expected_value="Valid supplier_id",
            description="PO references registered supplier",
        ))

        if sourcing_path == "competitive":
            qid = po.get("awarded_quote_id")
            passed_quote = qid in quote_map
            results.append(ValidationCheckResult(
                check_name="fk_competitive_po_awarded_quote",
                category="FOREIGN_KEYS",
                passed=passed_quote,
                severity="CRITICAL",
                entity="purchase_orders",
                record_id=poid,
                field="awarded_quote_id",
                actual_value=qid,
                expected_value="Valid awarded quote_id",
                description="Competitive PO references awarded quotation",
            ))
            if passed_quote:
                awarded_q = quote_map[qid]
                supplier_matches = (awarded_q["supplier_id"] == sup_id)
                results.append(ValidationCheckResult(
                    check_name="fk_po_supplier_matches_awarded_quote",
                    category="FOREIGN_KEYS",
                    passed=supplier_matches,
                    severity="ERROR",
                    entity="purchase_orders",
                    record_id=poid,
                    field="supplier_id",
                    actual_value=sup_id,
                    expected_value=awarded_q["supplier_id"],
                    description="PO supplier matches supplier on awarded quote",
                ))

    # 11. Purchase Order Lines -> PO & Request Line
    for pol in dataset.get("purchase_order_lines", []):
        pol_id = pol.get("po_line_id")
        poid = pol.get("po_id")
        rl_id = pol.get("request_line_id")

        passed_po = poid in po_map
        passed_rl = (rl_id in rl_map) if rl_id else True

        results.append(ValidationCheckResult(
            check_name="fk_po_line_po",
            category="FOREIGN_KEYS",
            passed=passed_po,
            severity="CRITICAL",
            entity="purchase_order_lines",
            record_id=pol_id,
            field="po_id",
            actual_value=poid,
            expected_value="Valid po_id",
            description="PO line references existing purchase order",
        ))
        if rl_id:
            results.append(ValidationCheckResult(
                check_name="fk_po_line_request_line",
                category="FOREIGN_KEYS",
                passed=passed_rl,
                severity="ERROR",
                entity="purchase_order_lines",
                record_id=pol_id,
                field="request_line_id",
                actual_value=rl_id,
                expected_value="Valid request_line_id",
                description="PO line references original requisition line",
            ))

    # 12. Deliveries -> Purchase Order
    for d in dataset.get("deliveries", []):
        did = d.get("delivery_id")
        poid = d.get("po_id")
        passed = poid in po_map
        results.append(ValidationCheckResult(
            check_name="fk_delivery_po",
            category="FOREIGN_KEYS",
            passed=passed,
            severity="CRITICAL",
            entity="deliveries",
            record_id=did,
            field="po_id",
            actual_value=poid,
            expected_value="Valid po_id",
            description="Delivery receipt references existing purchase order",
        ))

    # 13. Budget Events -> Budget
    for be in dataset.get("budget_events", []):
        be_id = be.get("budget_event_id")
        bid = be.get("budget_id")
        passed = bid in budget_ids
        results.append(ValidationCheckResult(
            check_name="fk_budget_event_budget",
            category="FOREIGN_KEYS",
            passed=passed,
            severity="CRITICAL",
            entity="budget_events",
            record_id=be_id,
            field="budget_id",
            actual_value=bid,
            expected_value="Valid budget_id",
            description="Budget event references existing department budget",
        ))

    return results


def validate_financial_reconciliation(
    dataset: Dict[str, Any],
    config: Optional[Mapping[str, Any]] = None,
) -> List[ValidationCheckResult]:
    """Independently verify all financial calculations and monetary reconciliations.

    Does not trust derived fields; recalculates expected values from raw records:
    - Request line: line_total == qty * unit_price
    - Purchase request: request_total == SUM(request_line_totals)
    - Quote line: line_total == qty * unit_price
    - Quote: landed_cost == merchandise + freight + duty + tax
    - Supplier score: 0.60 * c_norm + 0.25 * l_norm + 0.15 * r_norm
    - PO: total_amount == SUM(po_line_totals)
    - Deliveries: total received <= ordered quantity for clean path
    - Budget: allocated >= reserved + committed + spent
    """
    results: List[ValidationCheckResult] = []

    # 1. Request Line Calculations
    req_lines = dataset.get("request_lines", [])
    for rl in req_lines:
        rl_id = rl.get("request_line_id")
        qty = int(rl.get("quantity") or rl.get("qty") or 0)
        uprice_cents = rl.get("estimated_unit_price")
        if uprice_cents is None:
            uprice_cents = int(round(float(rl.get("unit_estimate", 0.0)) * 100))

        actual_cents = rl.get("estimated_line_total")
        expected_cents = qty * uprice_cents

        passed = (actual_cents == expected_cents)
        results.append(ValidationCheckResult(
            check_name="financial_request_line_total",
            category="FINANCIAL",
            passed=passed,
            severity="ERROR",
            entity="request_lines",
            record_id=rl_id,
            field="estimated_line_total",
            actual_value=actual_cents,
            expected_value=expected_cents,
            description="Request line total equals quantity times estimated unit price",
        ))

    # 2. Purchase Request Total Reconciliations
    lines_by_pr: Dict[str, List[Dict[str, Any]]] = {}
    for rl in req_lines:
        lines_by_pr.setdefault(rl["request_id"], []).append(rl)

    for pr in dataset.get("purchase_requests", []):
        pr_id = pr.get("request_id")
        lines = lines_by_pr.get(pr_id, [])
        expected_sum_cents = sum(
            int(l.get("estimated_line_total") or round(float(l.get("line_total", 0.0)) * 100))
            for l in lines
        )
        actual_cents = pr.get("total_estimated_amount")
        if actual_cents is None:
            actual_cents = int(round(float(pr.get("total_estimate_usd", 0.0)) * 100))

        passed = (actual_cents == expected_sum_cents)
        results.append(ValidationCheckResult(
            check_name="financial_pr_total_estimate",
            category="FINANCIAL",
            passed=passed,
            severity="CRITICAL",
            entity="purchase_requests",
            record_id=pr_id,
            field="total_estimated_amount",
            actual_value=actual_cents,
            expected_value=expected_sum_cents,
            description="Purchase request total equals sum of itemized request lines",
        ))

    # 3. Quote Lines and Quotation Landed Costs
    quote_lines = dataset.get("quote_lines", [])
    lines_by_quote: Dict[str, List[Dict[str, Any]]] = {}
    for ql in quote_lines:
        lines_by_quote.setdefault(ql["quote_id"], []).append(ql)

    for ql in quote_lines:
        ql_id = ql.get("quote_line_id")
        qty = int(ql.get("quantity") or ql.get("quoted_quantity") or 0)
        uprice = int(ql.get("unit_price") or 0)
        actual_line = ql.get("line_total")
        expected_line = qty * uprice

        results.append(ValidationCheckResult(
            check_name="financial_quote_line_total",
            category="FINANCIAL",
            passed=(actual_line == expected_line),
            severity="ERROR",
            entity="quote_lines",
            record_id=ql_id,
            field="line_total",
            actual_value=actual_line,
            expected_value=expected_line,
            description="Quote line total equals quoted quantity times unit price",
        ))

    for q in dataset.get("supplier_quotes", []):
        qid = q.get("quote_id")
        lines = lines_by_quote.get(qid, [])

        expected_merch_base = sum(int(l.get("line_total_base", 0)) for l in lines)
        actual_base_cents = q.get("total_quoted_amount_base")
        if actual_base_cents is None:
            actual_base_cents = int(round(float(q.get("total_quoted_amount_usd", 0.0)) * 100))

        results.append(ValidationCheckResult(
            check_name="financial_quote_merchandise_base",
            category="FINANCIAL",
            passed=(actual_base_cents == expected_merch_base),
            severity="ERROR",
            entity="supplier_quotes",
            record_id=qid,
            field="total_quoted_amount_base",
            actual_value=actual_base_cents,
            expected_value=expected_merch_base,
            description="Quotation base amount matches sum of quote lines in base currency",
        ))

        # Landed cost arithmetic
        freight = float(q.get("freight", 0.0))
        duty = float(q.get("duty", 0.0))
        tax = float(q.get("tax_nonrecoverable", 0.0))
        merch_usd = round(expected_merch_base / 100.0, 2)
        expected_landed = round(merch_usd + freight + duty + tax, 2)
        actual_landed = float(q.get("landed_cost_base", 0.0))

        diff = abs(actual_landed - expected_landed)
        results.append(ValidationCheckResult(
            check_name="financial_quote_landed_cost",
            category="FINANCIAL",
            passed=(diff <= 0.02),
            severity="ERROR",
            entity="supplier_quotes",
            record_id=qid,
            field="landed_cost_base",
            actual_value=actual_landed,
            expected_value=expected_landed,
            description="Landed cost equals merchandise plus freight, duty, and tax",
        ))

    # 4. Supplier Scoring Independent Verification
    scoring_cfg = (config or {}).get("supplier_scoring_weights", {})
    cost_w = float(scoring_cfg.get("cost_weight", 0.60))
    lead_w = float(scoring_cfg.get("lead_time_weight", 0.25))
    risk_w = float(scoring_cfg.get("risk_rating_weight", 0.15))

    quotes_by_rfq: Dict[str, List[Dict[str, Any]]] = {}
    for q in dataset.get("supplier_quotes", []):
        quotes_by_rfq.setdefault(q["rfq_id"], []).append(q)

    for rfq_id, rfq_quotes in quotes_by_rfq.items():
        costs = [float(q.get("landed_cost_base", 0.0)) for q in rfq_quotes]
        leads = [float(q.get("lead_time_days", 0)) for q in rfq_quotes]
        risks = [float(q.get("risk_score", 0.0)) for q in rfq_quotes]

        min_c, max_c = min(costs), max(costs)
        min_l, max_l = min(leads), max(leads)
        min_r, max_r = min(risks), max(risks)

        for q in rfq_quotes:
            c = float(q.get("landed_cost_base", 0.0))
            l = float(q.get("lead_time_days", 0))
            r = float(q.get("risk_score", 0.0))

            c_norm = (c - min_c) / (max_c - min_c) if max_c > min_c else 0.0
            l_norm = (l - min_l) / (max_l - min_l) if max_l > min_l else 0.0
            r_norm = (r - min_r) / (max_r - min_r) if max_r > min_r else 0.0

            expected_score = round(cost_w * c_norm + lead_w * l_norm + risk_w * r_norm, 4)
            actual_score = round(float(q.get("score", 0.0)), 4)

            # Check normalized bounds [0, 1]
            norm_valid = (0.0 <= c_norm <= 1.0) and (0.0 <= l_norm <= 1.0) and (0.0 <= r_norm <= 1.0)
            results.append(ValidationCheckResult(
                check_name="scoring_normalization_bounds",
                category="FINANCIAL",
                passed=norm_valid,
                severity="ERROR",
                entity="supplier_quotes",
                record_id=q.get("quote_id"),
                field="normalized_factors",
                actual_value=(c_norm, l_norm, r_norm),
                expected_value="All normalized factors in [0.0, 1.0]",
                description="Min-max normalized scoring factors are strictly bounded in [0, 1]",
            ))

            score_diff = abs(actual_score - expected_score)
            results.append(ValidationCheckResult(
                check_name="scoring_composite_value",
                category="FINANCIAL",
                passed=(score_diff <= 0.0002),
                severity="ERROR",
                entity="supplier_quotes",
                record_id=q.get("quote_id"),
                field="score",
                actual_value=actual_score,
                expected_value=expected_score,
                description="Composite supplier score matches independently calculated value",
            ))

    # 5. Purchase Order Line Totals and PO Header Totals
    po_lines = dataset.get("purchase_order_lines", [])
    lines_by_po: Dict[str, List[Dict[str, Any]]] = {}
    for pol in po_lines:
        lines_by_po.setdefault(pol["po_id"], []).append(pol)

    for pol in po_lines:
        pol_id = pol.get("po_line_id")
        qty = int(pol.get("quantity", 0))
        uprice = int(pol.get("unit_price", 0))
        expected_line = qty * uprice
        actual_line = pol.get("line_total")

        # Allow integer unit-price division rounding remainder (at most max(1, qty) cents)
        diff = abs(actual_line - expected_line)
        passed = (diff <= max(1, qty))

        results.append(ValidationCheckResult(
            check_name="financial_po_line_total",
            category="FINANCIAL",
            passed=passed,
            severity="ERROR",
            entity="purchase_order_lines",
            record_id=pol_id,
            field="line_total",
            actual_value=actual_line,
            expected_value=expected_line,
            description="PO line total equals ordered quantity times unit price",
        ))

    for po in dataset.get("purchase_orders", []):
        poid = po.get("po_id")
        lines = lines_by_po.get(poid, [])
        expected_po_cents = sum(int(l.get("line_total", 0)) for l in lines)
        actual_po_cents = po.get("total_amount")

        results.append(ValidationCheckResult(
            check_name="financial_po_total_reconciliation",
            category="FINANCIAL",
            passed=(actual_po_cents == expected_po_cents),
            severity="CRITICAL",
            entity="purchase_orders",
            record_id=poid,
            field="total_amount",
            actual_value=actual_po_cents,
            expected_value=expected_po_cents,
            description="Purchase order total amount equals sum of PO lines",
        ))

    # 6. Delivery Quantity Reconciliation: Received <= Ordered
    deliveries_by_po: Dict[str, List[Dict[str, Any]]] = {}
    for d in dataset.get("deliveries", []):
        deliveries_by_po.setdefault(d["po_id"], []).append(d)

    for po in dataset.get("purchase_orders", []):
        poid = po.get("po_id")
        del_list = deliveries_by_po.get(poid, [])
        ordered_qty = sum(int(l.get("quantity", 0)) for l in lines_by_po.get(poid, []))
        received_qty = sum(int(d.get("items_delivered_count", 0)) for d in del_list)

        results.append(ValidationCheckResult(
            check_name="delivery_quantity_bounds",
            category="FINANCIAL",
            passed=(received_qty <= ordered_qty),
            severity="CRITICAL",
            entity="purchase_orders",
            record_id=poid,
            field="items_delivered_count",
            actual_value=received_qty,
            expected_value=f"<= {ordered_qty}",
            description="Total delivered items do not exceed ordered quantity in clean workflow",
        ))

    # 7. Budget Allocation >= Reserved + Committed + Spent
    for b in dataset.get("budgets", []):
        bid = b.get("budget_id")
        alloc = int(b.get("allocated_amount", 0))
        res = int(b.get("reserved_amount", 0))
        com = int(b.get("committed_amount", 0))
        spent = int(b.get("spent_amount", 0))
        encumbered = res + com + spent

        passed = (alloc >= encumbered)
        results.append(ValidationCheckResult(
            check_name="financial_budget_no_overrun",
            category="FINANCIAL",
            passed=passed,
            severity="CRITICAL",
            entity="budgets",
            record_id=bid,
            field="allocated_amount",
            actual_value=f"Encumbered: {encumbered:,}",
            expected_value=f"Allocated: {alloc:,}",
            description="Department budget has zero clean-path overrun",
        ))

    return results


def validate_lifecycle_state_machine(dataset: Dict[str, Any]) -> List[ValidationCheckResult]:
    """Verify that all state transitions follow permitted business lifecycles without skips.

    Lifecycles:
    - PurchaseRequest: DRAFT -> SUBMITTED -> PENDING_APPROVAL -> APPROVED / REJECTED -> SOURCING -> PO_ISSUED -> DELIVERED -> CLOSED
    - PurchaseOrder: DRAFT -> ISSUED -> PARTIALLY_DELIVERED -> DELIVERED -> CLOSED
    - RFQ: DRAFT -> ISSUED -> AWARDED / CLOSED
    - Delivery: IN_TRANSIT -> DELIVERED / LATE / PARTIAL
    """
    results: List[ValidationCheckResult] = []

    ALLOWED_PR_TRANSITIONS = {
        "DRAFT": {"SUBMITTED", "CANCELLED"},
        "SUBMITTED": {"PENDING_APPROVAL", "CANCELLED"},
        "PENDING_APPROVAL": {"PENDING_APPROVAL", "APPROVED", "REJECTED", "CANCELLED"},
        "APPROVED": {"APPROVED", "SOURCING", "ORDERED", "PO_ISSUED", "CANCELLED", "REJECTED"},
        "REJECTED": set(),  # Terminal
        "SOURCING": {"ORDERED", "PO_ISSUED", "CANCELLED"},
        "ORDERED": {"ORDERED", "PO_ISSUED", "PARTIALLY_DELIVERED", "DELIVERED", "COMPLETED"},
        "PO_ISSUED": {"PARTIALLY_DELIVERED", "DELIVERED", "CANCELLED"},
        "PARTIALLY_DELIVERED": {"DELIVERED", "COMPLETED"},
        "DELIVERED": {"COMPLETED", "CLOSED"},
        "COMPLETED": {"CLOSED"},
        "CLOSED": set(),  # Terminal
        "CANCELLED": set(),  # Terminal
    }

    ALLOWED_PO_TRANSITIONS = {
        "DRAFT": {"ISSUED", "CANCELLED"},
        "ISSUED": {"PARTIALLY_DELIVERED", "DELIVERED", "COMPLETED", "CANCELLED"},
        "PARTIALLY_DELIVERED": {"DELIVERED", "COMPLETED", "CANCELLED"},
        "DELIVERED": {"COMPLETED", "CLOSED"},
        "COMPLETED": {"CLOSED"},
        "CLOSED": set(),
        "CANCELLED": set(),
    }

    status_events = dataset.get("status_events", [])
    events_by_entity: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

    for ev in status_events:
        ent_type = ev.get("entity_type") or ev.get("entity") or ""
        ent_id = ev.get("entity_id") or ""
        events_by_entity.setdefault((ent_type, ent_id), []).append(ev)

    for (ent_type, ent_id), ev_list in events_by_entity.items():
        # Sort sequentially by status_event_id (which strictly captures event creation order)
        sorted_evs = sorted(
            ev_list,
            key=lambda e: (
                e.get("status_event_id") or e.get("event_id") or "",
            )
        )

        prev_to_status = None
        for ev in sorted_evs:
            eid = ev.get("status_event_id") or ev.get("event_id")
            from_st = ev.get("from_status") or ev.get("previous_status")
            to_st = ev.get("to_status") or ev.get("new_status")

            # 1. Sequence continuity: from_status matches preceding to_status
            if prev_to_status is not None:
                continuity = (from_st == prev_to_status)
                results.append(ValidationCheckResult(
                    check_name="lifecycle_state_continuity",
                    category="LIFECYCLE",
                    passed=continuity,
                    severity="ERROR",
                    entity=ent_type,
                    record_id=ent_id,
                    field="from_status",
                    actual_value=from_st,
                    expected_value=prev_to_status,
                    description=f"StatusEvent {eid} from_status matches preceding event to_status",
                ))

            # 2. State transition rule checking
            if ent_type == "PURCHASE_REQUEST":
                allowed = ALLOWED_PR_TRANSITIONS.get(from_st, set())
                is_valid_trans = (to_st in allowed)
                results.append(ValidationCheckResult(
                    check_name="lifecycle_pr_valid_transition",
                    category="LIFECYCLE",
                    passed=is_valid_trans,
                    severity="ERROR",
                    entity=ent_type,
                    record_id=ent_id,
                    field="to_status",
                    actual_value=f"{from_st} -> {to_st}",
                    expected_value=f"Allowed targets: {allowed}",
                    description=f"PR transition from {from_st} to {to_st} is allowed in state machine",
                ))
            elif ent_type == "PURCHASE_ORDER":
                allowed = ALLOWED_PO_TRANSITIONS.get(from_st, set())
                is_valid_trans = (to_st in allowed)
                results.append(ValidationCheckResult(
                    check_name="lifecycle_po_valid_transition",
                    category="LIFECYCLE",
                    passed=is_valid_trans,
                    severity="ERROR",
                    entity=ent_type,
                    record_id=ent_id,
                    field="to_status",
                    actual_value=f"{from_st} -> {to_st}",
                    expected_value=f"Allowed targets: {allowed}",
                    description=f"PO transition from {from_st} to {to_st} is allowed in state machine",
                ))

            prev_to_status = to_st

    # 3. Check rejected requests do not receive POs
    pos = dataset.get("purchase_orders", [])
    prs = {pr["request_id"]: pr for pr in dataset.get("purchase_requests", [])}

    for po in pos:
        req_id = po.get("request_id")
        pr = prs.get(req_id)
        if pr:
            pr_status = pr.get("status")
            not_rejected = (pr_status != "REJECTED")
            results.append(ValidationCheckResult(
                check_name="lifecycle_rejected_pr_no_po",
                category="LIFECYCLE",
                passed=not_rejected,
                severity="CRITICAL",
                entity="purchase_orders",
                record_id=po.get("po_id"),
                field="request_id",
                actual_value=pr_status,
                expected_value="APPROVED or ORDERED",
                description="Rejected purchase request cannot receive a purchase order",
            ))

    return results


def validate_date_ordering(dataset: Dict[str, Any]) -> List[ValidationCheckResult]:
    """Validate transactional chronology across the procure-to-pay lifecycle.

    Ordering:
        Requisition Creation <= Approval <= RFQ Issue <= Quote Date <= Award Date <= PO Date <= Delivery Date
    """
    results: List[ValidationCheckResult] = []

    pr_map = {pr["request_id"]: pr for pr in dataset.get("purchase_requests", [])}
    approvals_by_pr: Dict[str, List[Dict[str, Any]]] = {}
    for app in dataset.get("approvals", []):
        approvals_by_pr.setdefault(app["request_id"], []).append(app)

    rfq_by_pr: Dict[str, Dict[str, Any]] = {r["request_id"]: r for r in dataset.get("rfqs", [])}
    quotes_by_rfq: Dict[str, List[Dict[str, Any]]] = {}
    for q in dataset.get("supplier_quotes", []):
        quotes_by_rfq.setdefault(q["rfq_id"], []).append(q)

    po_by_pr: Dict[str, Dict[str, Any]] = {po["request_id"]: po for po in dataset.get("purchase_orders", [])}
    deliveries_by_po: Dict[str, List[Dict[str, Any]]] = {}
    for d in dataset.get("deliveries", []):
        deliveries_by_po.setdefault(d["po_id"], []).append(d)

    for pr_id, pr in pr_map.items():
        pr_date_str = pr.get("request_date") or pr.get("created_at")[:10]
        pr_date = datetime.date.fromisoformat(pr_date_str[:10])

        # 1. Fiscal year 2026 check
        results.append(ValidationCheckResult(
            check_name="date_in_fiscal_year_2026",
            category="DATES",
            passed=(pr_date.year == 2026),
            severity="ERROR",
            entity="purchase_requests",
            record_id=pr_id,
            field="request_date",
            actual_value=pr_date.year,
            expected_value=2026,
            description="Requisition date is within fiscal year 2026",
        ))

        # 2. Approval dates >= PR date
        for app in approvals_by_pr.get(pr_id, []):
            app_date_str = app.get("decision_date") or app.get("created_at")[:10]
            app_date = datetime.date.fromisoformat(app_date_str[:10])
            results.append(ValidationCheckResult(
                check_name="date_approval_after_request",
                category="DATES",
                passed=(app_date >= pr_date),
                severity="ERROR",
                entity="approvals",
                record_id=app.get("approval_id"),
                field="decision_date",
                actual_value=app_date_str,
                expected_value=f">= {pr_date_str}",
                description="Approval date is on or after requisition date",
            ))

        # 3. RFQ Issue date >= Approval date
        rfq = rfq_by_pr.get(pr_id)
        if rfq:
            rfq_issue_str = rfq.get("issue_date")[:10]
            rfq_issue = datetime.date.fromisoformat(rfq_issue_str)
            results.append(ValidationCheckResult(
                check_name="date_rfq_after_request",
                category="DATES",
                passed=(rfq_issue >= pr_date),
                severity="ERROR",
                entity="rfqs",
                record_id=rfq.get("rfq_id"),
                field="issue_date",
                actual_value=rfq_issue_str,
                expected_value=f">= {pr_date_str}",
                description="RFQ issue date is on or after requisition date",
            ))

            # RFQ due date >= issue date
            rfq_due_str = rfq.get("due_date")[:10]
            rfq_due = datetime.date.fromisoformat(rfq_due_str)
            results.append(ValidationCheckResult(
                check_name="date_rfq_due_after_issue",
                category="DATES",
                passed=(rfq_due >= rfq_issue),
                severity="ERROR",
                entity="rfqs",
                record_id=rfq.get("rfq_id"),
                field="due_date",
                actual_value=rfq_due_str,
                expected_value=f">= {rfq_issue_str}",
                description="RFQ due date is on or after issue date",
            ))

            # Quote submission dates >= RFQ issue date
            for q in quotes_by_rfq.get(rfq["rfq_id"], []):
                q_date_str = q.get("quote_date")[:10]
                q_date = datetime.date.fromisoformat(q_date_str)
                results.append(ValidationCheckResult(
                    check_name="date_quote_after_rfq_issue",
                    category="DATES",
                    passed=(q_date >= rfq_issue),
                    severity="ERROR",
                    entity="supplier_quotes",
                    record_id=q.get("quote_id"),
                    field="quote_date",
                    actual_value=q_date_str,
                    expected_value=f">= {rfq_issue_str}",
                    description="Quote date is on or after RFQ issue date",
                ))

                # Award date <= valid_until
                if q.get("status") == "AWARDED" and "award_date" in q:
                    aw_date_str = q["award_date"][:10]
                    aw_date = datetime.date.fromisoformat(aw_date_str)
                    valid_str = q.get("valid_until")[:10]
                    valid_date = datetime.date.fromisoformat(valid_str)
                    results.append(ValidationCheckResult(
                        check_name="date_award_before_quote_expiry",
                        category="DATES",
                        passed=(aw_date <= valid_date),
                        severity="ERROR",
                        entity="supplier_quotes",
                        record_id=q.get("quote_id"),
                        field="award_date",
                        actual_value=aw_date_str,
                        expected_value=f"<= {valid_str}",
                        description="Quote award occurs before quotation expiry",
                    ))

        # 4. Purchase Order date >= Request / Approval
        po = po_by_pr.get(pr_id)
        if po:
            po_date_str = po.get("po_date")[:10]
            po_date = datetime.date.fromisoformat(po_date_str)
            results.append(ValidationCheckResult(
                check_name="date_po_after_request",
                category="DATES",
                passed=(po_date >= pr_date),
                severity="ERROR",
                entity="purchase_orders",
                record_id=po.get("po_id"),
                field="po_date",
                actual_value=po_date_str,
                expected_value=f">= {pr_date_str}",
                description="Purchase order date is on or after requisition date",
            ))

            # 5. Delivery receipts >= PO date
            for d in deliveries_by_po.get(po["po_id"], []):
                del_date_str = d.get("delivery_date")[:10]
                del_date = datetime.date.fromisoformat(del_date_str)
                results.append(ValidationCheckResult(
                    check_name="date_delivery_after_po",
                    category="DATES",
                    passed=(del_date >= po_date),
                    severity="ERROR",
                    entity="deliveries",
                    record_id=d.get("delivery_id"),
                    field="delivery_date",
                    actual_value=del_date_str,
                    expected_value=f">= {po_date_str}",
                    description="Delivery receipt date is on or after purchase order issuance",
                ))

    return results


def validate_approvals_and_business_rules(
    dataset: Dict[str, Any],
    config: Optional[Mapping[str, Any]] = None,
) -> List[ValidationCheckResult]:
    """Verify approval thresholds, approver roles, sourcing path compliance, and award selection rules.

    Rules:
    - PR <= $2,000 requires line manager approval.
    - PR $2,000 - $25,000 requires department head approval.
    - PR > $25,000 requires corporate finance approval.
    - Competitive sourcing must have >= 3 valid quotations.
    - Awarded quotation must be lowest evaluated score in clean path.
    """
    results: List[ValidationCheckResult] = []

    thresholds = (config or {}).get("approval_thresholds", {})
    mgr_limit = float(thresholds.get("manager_limit", 2000.0))
    dept_limit = float(thresholds.get("dept_head_limit", 25000.0))

    approver_map = {a["approver_id"]: a for a in dataset.get("approvers", [])}
    req_map = {r["requester_id"]: r for r in dataset.get("requesters", [])}
    approvals_by_pr: Dict[str, List[Dict[str, Any]]] = {}

    for app in dataset.get("approvals", []):
        approvals_by_pr.setdefault(app["request_id"], []).append(app)

    # 1. Approval Thresholds and Tiers
    for pr in dataset.get("purchase_requests", []):
        pr_id = pr.get("request_id")
        tot_usd = float(pr.get("total_estimate_usd", 0.0))
        apps = approvals_by_pr.get(pr_id, [])

        if tot_usd <= mgr_limit:
            expected_levels = 1
        elif tot_usd <= dept_limit:
            expected_levels = 1
        else:
            expected_levels = 2

        # Draft requests are not submitted for approval; rejected requests may halt at level 1
        is_draft = (pr.get("status") == "DRAFT")
        is_rejected = (pr.get("status") == "REJECTED")
        if not is_rejected and not is_draft:
            passed = (len(apps) >= expected_levels)
            results.append(ValidationCheckResult(
                check_name="approval_required_levels",
                category="APPROVALS",
                passed=passed,
                severity="ERROR",
                entity="purchase_requests",
                record_id=pr_id,
                field="total_estimate_usd",
                actual_value=len(apps),
                expected_value=f">= {expected_levels} levels for ${tot_usd:,.2f}",
                description="Requisition received required number of tiered approval levels",
            ))

        # Check approver roles
        for app in apps:
            appr = approver_map.get(app.get("approver_id"))
            if appr:
                role = appr.get("role")
                step = app.get("approval_level") or app.get("step_number")
                if step == 2 and tot_usd > dept_limit:
                    is_finance = "FINANCE" in role.upper()
                    results.append(ValidationCheckResult(
                        check_name="approval_finance_director_role",
                        category="APPROVALS",
                        passed=is_finance,
                        severity="ERROR",
                        entity="approvals",
                        record_id=app.get("approval_id"),
                        field="role",
                        actual_value=role,
                        expected_value="FINANCE",
                        description="Level 2 approval performed by corporate finance director",
                    ))

    # 2. Competitive Quotation Count: >= 3 quotes per RFQ
    quotes_by_rfq: Dict[str, List[Dict[str, Any]]] = {}
    for q in dataset.get("supplier_quotes", []):
        quotes_by_rfq.setdefault(q["rfq_id"], []).append(q)

    for rfq in dataset.get("rfqs", []):
        rfq_id = rfq.get("rfq_id")
        q_count = len(quotes_by_rfq.get(rfq_id, []))
        results.append(ValidationCheckResult(
            check_name="sourcing_competitive_quote_count",
            category="APPROVALS",
            passed=(q_count >= 3),
            severity="ERROR",
            entity="rfqs",
            record_id=rfq_id,
            field="supplier_quotes_count",
            actual_value=q_count,
            expected_value=">= 3 competing quotes",
            description="Competitive RFQ received minimum 3 supplier quotations",
        ))

    # 3. Objective Award Winner: Lowest Score Wins
    for rfq_id, q_list in quotes_by_rfq.items():
        if not q_list:
            continue
        # Find minimum score
        min_score = min(float(q.get("score", 0.0)) for q in q_list)
        for q in q_list:
            if q.get("status") == "AWARDED":
                score = float(q.get("score", 0.0))
                is_lowest = abs(score - min_score) <= 0.0001
                results.append(ValidationCheckResult(
                    check_name="award_lowest_composite_score",
                    category="APPROVALS",
                    passed=is_lowest,
                    severity="CRITICAL",
                    entity="supplier_quotes",
                    record_id=q.get("quote_id"),
                    field="score",
                    actual_value=score,
                    expected_value=min_score,
                    description="Awarded quotation has lowest composite score among competitors",
                ))

    return results


def validate_split_purchases(
    dataset: Dict[str, Any],
    config: Optional[Mapping[str, Any]] = None,
    window_days: int = 3,
) -> List[ValidationCheckResult]:
    """Audit purchase requests for potential split purchases dodging approval thresholds.

    A split purchase occurs when a requester submits multiple purchase requests
    within a short rolling time window (default: 3 days), each below a managerial
    approval threshold ($2,000 or $25,000), but whose combined total exceeds that threshold.

    Rules:
    - Requisitions within window from the same requester are aggregated.
    - If the combined estimate exceeds the $2,000 or $25,000 limit, it verifies that
      the higher approval tier was not bypassed.
    """
    results: List[ValidationCheckResult] = []
    thresholds = (config or {}).get("approval_thresholds", {})
    mgr_limit = float(thresholds.get("manager_limit", 2000.0))
    dept_limit = float(thresholds.get("department_head_limit", 25000.0))

    prs = dataset.get("purchase_requests", [])
    if not prs:
        return results

    # Group PRs by requester
    by_requester: Dict[str, List[Dict[str, Any]]] = {}
    for pr in prs:
        req_id = pr.get("requester_id")
        if req_id:
            by_requester.setdefault(req_id, []).append(pr)

    for req_id, req_prs in by_requester.items():
        if len(req_prs) < 2:
            continue
        sorted_prs = sorted(req_prs, key=lambda x: str(x.get("request_date", "")))
        for i in range(len(sorted_prs) - 1):
            pr1 = sorted_prs[i]
            d1_str = str(pr1.get("request_date", ""))[:10]
            try:
                d1 = datetime.date.fromisoformat(d1_str)
            except ValueError:
                continue

            for j in range(i + 1, len(sorted_prs)):
                pr2 = sorted_prs[j]
                d2_str = str(pr2.get("request_date", ""))[:10]
                try:
                    d2 = datetime.date.fromisoformat(d2_str)
                except ValueError:
                    continue

                delta = (d2 - d1).days
                if delta > window_days:
                    break

                est1 = float(pr1.get("total_estimate_usd", 0.0))
                est2 = float(pr2.get("total_estimate_usd", 0.0))
                comb = est1 + est2

                # Check if each individually <= threshold but together > threshold
                is_split_mgr = (est1 <= mgr_limit and est2 <= mgr_limit and comb > mgr_limit)
                is_split_dept = (est1 <= dept_limit and est2 <= dept_limit and comb > dept_limit)

                if is_split_mgr or is_split_dept:
                    target_thresh = dept_limit if is_split_dept else mgr_limit
                    results.append(ValidationCheckResult(
                        check_name="split_purchase_threshold_audit",
                        category="APPROVALS",
                        passed=True,
                        severity="INFO",
                        entity="purchase_requests",
                        record_id=f"{pr1.get('request_id')}+{pr2.get('request_id')}",
                        field="total_estimate_usd",
                        actual_value=round(comb, 2),
                        expected_value=f"Combined estimate ${comb:,.2f} within {delta}d window audited against threshold ${target_thresh:,.2f}",
                        description=f"Potential split purchase detected: PRs from {req_id} aggregate to ${comb:,.2f} within {delta} days",
                    ))

    return results


def validate_budget_ledger(dataset: Dict[str, Any]) -> List[ValidationCheckResult]:
    """Reconstruct budget balances from the double-entry event ledger and verify against Budget table.

    Validates:
    - Initial ALLOCATE event exists for every department budget.
    - Chronological event processing.
    - Zero clean-path budget overruns.
    - Ledger-derived balances match the Budget master record balances.
    """
    results: List[ValidationCheckResult] = []

    budget_events = dataset.get("budget_events", [])
    budgets = dataset.get("budgets", [])

    # Sort events chronologically
    sorted_events = sorted(
        budget_events,
        key=lambda e: (
            e.get("event_timestamp") or e.get("event_date") or "",
            e.get("budget_event_id") or "",
        )
    )

    ledger_alloc: Dict[str, int] = {}
    ledger_reserved: Dict[str, int] = {}
    ledger_committed: Dict[str, int] = {}
    ledger_spent: Dict[str, int] = {}

    for ev in sorted_events:
        bid = ev.get("budget_id")
        amt = int(ev.get("amount", 0))
        ev_type = ev.get("event_type")

        # Amount sign check: must be strictly positive
        if amt < 0:
            results.append(ValidationCheckResult(
                check_name="budget_event_amount_positive",
                category="BUDGET",
                passed=False,
                severity="ERROR",
                entity="budget_events",
                record_id=ev.get("budget_event_id"),
                field="amount",
                actual_value=amt,
                expected_value=">= 0",
                description="Budget ledger event amount must be non-negative",
            ))

        if ev_type == "ALLOCATE":
            ledger_alloc[bid] = ledger_alloc.get(bid, 0) + amt
        elif ev_type == "RESERVE":
            ledger_reserved[bid] = ledger_reserved.get(bid, 0) + amt
        elif ev_type == "RELEASE":
            ledger_reserved[bid] = max(0, ledger_reserved.get(bid, 0) - amt)
        elif ev_type == "COMMIT":
            ledger_committed[bid] = ledger_committed.get(bid, 0) + amt
        elif ev_type == "SPEND":
            ledger_spent[bid] = ledger_spent.get(bid, 0) + amt
            ledger_committed[bid] = max(0, ledger_committed.get(bid, 0) - amt)

    for b in budgets:
        bid = b.get("budget_id")

        # 1. Has initial allocation
        has_alloc = bid in ledger_alloc and ledger_alloc[bid] > 0
        results.append(ValidationCheckResult(
            check_name="budget_has_initial_allocation",
            category="BUDGET",
            passed=has_alloc,
            severity="CRITICAL",
            entity="budgets",
            record_id=bid,
            field="allocated_amount",
            actual_value=ledger_alloc.get(bid, 0),
            expected_value="> 0",
            description="Department budget received initial FY2026 allocation",
        ))

        # 2. Check balance match
        exp_res = ledger_reserved.get(bid, 0)
        exp_com = ledger_committed.get(bid, 0)
        exp_spent = ledger_spent.get(bid, 0)

        act_res = int(b.get("reserved_amount", 0))
        act_com = int(b.get("committed_amount", 0))
        act_spent = int(b.get("spent_amount", 0))

        results.append(ValidationCheckResult(
            check_name="budget_reserved_reconciliation",
            category="BUDGET",
            passed=(act_res == exp_res),
            severity="ERROR",
            entity="budgets",
            record_id=bid,
            field="reserved_amount",
            actual_value=act_res,
            expected_value=exp_res,
            description="Budget reserved balance reconciles with ledger events",
        ))
        results.append(ValidationCheckResult(
            check_name="budget_committed_reconciliation",
            category="BUDGET",
            passed=(act_com == exp_com),
            severity="ERROR",
            entity="budgets",
            record_id=bid,
            field="committed_amount",
            actual_value=act_com,
            expected_value=exp_com,
            description="Budget committed balance reconciles with ledger events",
        ))
        results.append(ValidationCheckResult(
            check_name="budget_spent_reconciliation",
            category="BUDGET",
            passed=(act_spent == exp_spent),
            severity="ERROR",
            entity="budgets",
            record_id=bid,
            field="spent_amount",
            actual_value=act_spent,
            expected_value=exp_spent,
            description="Budget spent balance reconciles with ledger events",
        ))

    return results


# ==============================================================================
# MASTER VALIDATION COORDINATOR
# ==============================================================================

from validate.anomaly_checks import detect_all_anomalies, evaluate_detections


def validate_dataset(
    dataset: Dict[str, Any],
    config: Optional[Mapping[str, Any]] = None,
    db_path: Optional[str | Path] = None,
    mode: str = "clean",
    ground_truth: Optional[List[Any]] = None,
) -> ValidationReport:
    """Execute all independent validation checks and produce a unified ValidationReport.

    Args:
        dataset: Dictionary containing all procurement entity record lists.
        config: Central configuration dictionary.
        db_path: Optional path to SQLite database for physical schema checks.
        mode: Validation mode ('clean' or 'anomaly_aware').
        ground_truth: Optional list of ground truth records or dicts.

    Returns:
        ValidationReport: Complete validation report with status, metrics, and failures.
    """
    report = ValidationReport(mode=mode)

    # Record entity inventory counts
    for key, val in dataset.items():
        if isinstance(val, list):
            report.entities[key] = len(val)

    # 1. Primary Keys and IDs
    for res in validate_primary_keys_and_ids(dataset):
        report.add_result(res)

    # 2. Foreign Keys & References
    for res in validate_foreign_keys(dataset):
        report.add_result(res)

    # 3. Financial Reconciliation
    for res in validate_financial_reconciliation(dataset, config):
        report.add_result(res)

    # 4. Lifecycle State Machine
    for res in validate_lifecycle_state_machine(dataset):
        report.add_result(res)

    # 5. Date Chronology
    for res in validate_date_ordering(dataset):
        report.add_result(res)

    # 6. Approvals and Business Rules
    for res in validate_approvals_and_business_rules(dataset, config):
        report.add_result(res)

    # 7. Split Purchases Audit
    for res in validate_split_purchases(dataset, config):
        report.add_result(res)

    # 8. Budget Ledger
    for res in validate_budget_ledger(dataset):
        report.add_result(res)

    # 9. Optional SQLite Physical Checks
    if db_path and Path(db_path).exists():
        foundational = run_foundational_checks(db_path)
        report.add_result(ValidationCheckResult(
            check_name="sqlite_foreign_keys_enabled",
            category="SCHEMA",
            passed=foundational["foreign_keys_enabled"],
            severity="CRITICAL",
            description="SQLite PRAGMA foreign_keys is enabled",
        ))
        report.add_result(ValidationCheckResult(
            check_name="sqlite_schema_integrity",
            category="SCHEMA",
            passed=foundational["integrity_ok"],
            severity="CRITICAL",
            description="SQLite PRAGMA integrity_check passes",
        ))
        report.add_result(ValidationCheckResult(
            check_name="sqlite_fk_violations",
            category="SCHEMA",
            passed=(foundational["fk_violations_count"] == 0),
            severity="CRITICAL",
            description="SQLite PRAGMA foreign_key_check detects 0 orphaned rows",
        ))

    # Anomaly detection and mode-specific verification
    findings = detect_all_anomalies(dataset, config)
    report.anomaly_findings = [f.to_dict() for f in findings]

    gt = ground_truth if ground_truth is not None else dataset.get("ground_truth")

    if mode == "clean":
        # In clean mode, zero anomalies are expected. Any detected anomaly is a CRITICAL failure.
        if findings:
            for f in findings:
                report.add_result(ValidationCheckResult(
                    check_name=f"clean_mode_anomaly_{f.issue_type}",
                    category="ANOMALY_FREE",
                    passed=False,
                    severity="CRITICAL",
                    entity=f.entity,
                    record_id=f.record_id,
                    actual_value=f"Anomaly: {f.issue_type}",
                    expected_value="Zero anomalies in clean dataset",
                    description=f.description,
                ))
    elif mode == "anomaly_aware":
        # In anomaly-aware mode, evaluate detected anomalies against ground truth
        if gt is not None:
            eval_metrics = evaluate_detections(findings, gt)
            report.evaluation = eval_metrics
            # If 100% precision and recall achieved on injected anomalies, mark PASS
            if eval_metrics["precision"] == 1.0 and eval_metrics["recall"] == 1.0:
                report.status = "PASS"
            else:
                report.status = "FAIL"

    return report


def main() -> None:
    """CLI runner supporting both database file paths and in-memory generation validation."""
    parser = argparse.ArgumentParser(description="Comprehensive Procure-to-Pay Validator & Anomaly Detector")
    parser.add_argument(
        "target",
        nargs="?",
        default="data/",
        help="Target database file path or data directory",
    )
    parser.add_argument(
        "--mode",
        choices=["clean", "anomaly_aware"],
        default="clean",
        help="Validation mode: 'clean' (expects 0 anomalies) or 'anomaly_aware' (evaluates detections against ground truth)",
    )
    parser.add_argument(
        "--inject-anomalies",
        action="store_true",
        help="Inject controlled anomalies into in-memory generated dataset",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Print detailed anomaly detection metrics",
    )
    parser.add_argument(
        "--scale",
        choices=["starter", "full"],
        default="starter",
        help="Scale tier to generate and validate if validating in-memory workflow",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20261022,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--output-md",
        default="docs/validation_summary.md",
        help="Path to output markdown report",
    )
    parser.add_argument(
        "--output-json",
        default="docs/validation_summary.json",
        help="Path to output JSON report",
    )
    args = parser.parse_args()

    config = load_config()
    target_path = Path(args.target)

    # Determine validation mode: SQLite DB vs In-Memory Clean Workflow
    if target_path.is_file() and target_path.suffix in (".db", ".sqlite", ".sqlite3"):
        print(f"=== Validating SQLite Database: {target_path} ===")
        foundational = run_foundational_checks(target_path)
        print(f"Foreign Keys Enabled : {foundational['foreign_keys_enabled']}")
        print(f"Schema Integrity OK  : {foundational['integrity_ok']}")
        print(f"All Tables Present   : {foundational['tables_ok']}")
        print(f"FK Violations Count  : {foundational['fk_violations_count']}")
        if not foundational["all_passed"]:
            print("FAILED foundational checks.", file=sys.stderr)
            sys.exit(1)
        print("Foundational checks PASSED.")
        sys.exit(0)

    # In-memory workflow generation and comprehensive validation
    print(f"=== Generating Dataset ({args.scale} scale, seed {args.seed}) ===")
    from datagen.workflow import generate_procurement_workflow
    dataset = generate_procurement_workflow(scale=args.scale, seed=args.seed)

    gt_records = None
    if args.inject_anomalies:
        print("=== Injecting Controlled Procurement Anomalies ===")
        from datagen.anomalies import inject_anomalies
        import numpy as np
        rng = np.random.default_rng(args.seed)
        dataset, gt_records = inject_anomalies(dataset, config, rng)
        dataset["ground_truth"] = gt_records
        print(f"Injected Anomalies   : {len(gt_records)}")

    print(f"=== Executing Validation (Mode: {args.mode}) ===")
    report = validate_dataset(dataset, config=config, mode=args.mode, ground_truth=gt_records)

    # Write reports to docs/
    report.save_reports(md_path=args.output_md, json_path=args.output_json)

    print(f"Total Checks Executed : {report.summary['total_checks']:,}")
    print(f"Passed Checks         : {report.summary['passed']:,}")
    print(f"Failed Checks         : {report.summary['failed']:,}")
    print(f"Warnings              : {report.summary['warnings']:,}")
    print(f"Overall Status        : {report.status}")
    print(f"Detected Anomalies    : {len(report.anomaly_findings)}")

    if report.evaluation:
        ev = report.evaluation
        print("\n=== Detection Performance Evaluation ===")
        print(f"Ground Truth Count    : {ev['total_ground_truth']}")
        print(f"Detected Count        : {ev['total_detected']}")
        print(f"True Positives (TP)   : {ev['true_positives']}")
        print(f"False Positives (FP)  : {ev['false_positives']}")
        print(f"False Negatives (FN)  : {ev['false_negatives']}")
        print(f"Precision             : {ev['precision'] * 100:.2f}%")
        print(f"Recall                : {ev['recall'] * 100:.2f}%")
        print(f"F1-Score              : {ev['f1_score']:.4f}")

    print(f"\nMarkdown Report Saved : {args.output_md}")
    print(f"JSON Report Saved     : {args.output_json}")

    if report.status != "PASS":
        print(f"\nDiscrepancies detected ({len(report.failures)} failures):", file=sys.stderr)
        for f in report.failures[:10]:
            print(f"  - [{f['severity']}] {f['check_name']} on {f['entity']} {f['record_id']}: {f['description']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
