# Project Assumptions & Design Decisions

This document provides a transparent and auditable record of all foundational assumptions, technical design choices, and business model constraints adopted in Phase 1 of the Procure-to-Pay Synthetic Data Generator.

To maintain strict engineering rigor, assumptions are classified into three distinct categories:
- **Category A**: Explicit Requirements from the Master Prompt / PRD.
- **Category B**: Technical Design Decisions made by the Engineering Lead.
- **Category C**: Working Assumptions where exact real-world or domain behavior was unspecified.

---

## Category A: Explicit Requirements from PRD / Prompt

1. **Fiscal Year & Temporal Base**:
   - Fiscal year is fixed to `2026`.
   - Base date is fixed to `2026-01-01`.
2. **Base Currency**:
   - `USD` is the central base currency of the procurement system.
3. **Approval Thresholds**:
   - Line Manager approval threshold: Up to \$2,000.
   - Department Head approval threshold: Up to \$25,000.
   - Purchases exceeding \$25,000 require Finance / Executive review.
4. **Supplier Scoring Weights**:
   - Landed Cost Weight: `0.60` (60%)
   - Lead Time Weight: `0.25` (25%)
   - Risk Rating Weight: `0.15` (15%)
   - Weights must strictly sum to `1.0`.
5. **Fixed FX Rates**:
   - `USD`: 1.0
   - `INR`: 0.012 (1 INR = 0.012 USD)
   - `EUR`: 1.08 (1 EUR = 1.08 USD)
   - `GBP`: 1.27 (1 GBP = 1.27 USD)
   - `JPY`: 0.0067 (1 JPY = 0.0067 USD)
6. **Dataset Scale Tiers**:
   - **Starter Scale**: 10 Departments, 30 Requesters, 12 Suppliers, 115 Purchase Requests, 50 RFQs, 150 Quotes, 90 Purchase Orders.
   - **Full Scale**: 12 Departments, 300 Requesters, 120 Suppliers, 1,150 Purchase Requests, 500 RFQs, 1,500 Quotes, 900 Purchase Orders.
7. **Sourcing Constraints**:
   - Each Purchase Request can originate at most one RFQ (1:1 or 1:0 relationship).
   - An invited vendor cannot be invited multiple times to the same RFQ.
   - Quotations may only be accepted from suppliers actively invited to that specific RFQ.
   - Minimum quotes per RFQ: 3; Maximum quotes: 6; Default invites: 3.
8. **Anomalies Envelope**:
   - Minimum target anomaly rate: 3% (`0.03`).
   - Maximum target anomaly rate: 5% (`0.05`).

---

## Category B: Technical Design Decisions

1. **Monetary Representation (INTEGER Minor Units)**:
   - *Decision*: In SQLite, all financial amounts are stored as `INTEGER` representing the minor currency unit (e.g. cents for USD/EUR, paise for INR, pence for GBP, and whole yen for JPY).
   - *Rationale*: SQLite lacks a native IEEE-compliant fixed-point `DECIMAL` datatype. Using `REAL` introduces IEEE 754 floating-point inaccuracies, where sums such as $0.10 + $0.20 produce $0.30000000000000004. Minor integer units guarantee 100% exact arithmetic and eliminate rounding drift across ledgers.
   - *Python Bridge*: Python interactions utilize `decimal.Decimal` with explicit quantization to `Decimal("0.01")` using `ROUND_HALF_UP`, converted via `to_minor_units()` and `from_minor_units()`.
2. **Deterministic Sequence Counter Factory**:
   - *Decision*: Avoid UUIDv4 or system random IDs. Implement a centralized `IDFactory` maintaining independent state counters per entity.
   - *Rationale*: Predictable, sequential, zero-padded IDs (`PR-2026-000001`, `DEL-PO-2026-000001-01`) enable human-readable debugging, reliable automated test assertions, and seamless cross-table correlation.
3. **Double-Entry Style Budget Event Ledger**:
   - *Decision*: The `budget_events` table serves as the single source of truth for budget movements across the procurement lifecycle.
   - *Event Types*:
     - `ALLOCATE`: Initial department fiscal year funding.
     - `RESERVE`: Pre-encumbrance when a Purchase Request is submitted.
     - `COMMIT`: Encumbrance when a Purchase Order is issued.
     - `RELEASE`: De-encumbrance if a PR/PO is cancelled or rejected.
     - `SPEND`: Synthetic expenditure recognition upon delivery receipt.
   - *Rationale*: Directly updating balances on the `budgets` table without an immutable event log causes loss of audit trail and hinders reconciliation.
4. **Relational Enforcement of Quote Authorization**:
   - *Decision*: In `supplier_quotes`, a compound foreign key `FOREIGN KEY (rfq_id, supplier_id) REFERENCES rfq_supplier_invites(rfq_id, supplier_id)` is enforced at the database level.
   - *Rationale*: This guarantees by construction that no quotation can enter the system unless a preceding invitation record exists, preventing phantom quotation anomalies from violating relational integrity before Phase 6.

---

## Category C: Domain & Operational Assumptions

1. **Synthetic Expenditure Representation (Out of Scope Payment Processing)**:
   - *Assumption*: The `SPEND` budget event and `spent_amount` field represent synthetic accounting disbursements triggered upon successful physical delivery.
   - *Clarification*: Accounts Payable (AP) workflows, invoice ingestion, 3-way invoice matching, and payment gateway settlement are outside the scope of this generator.
2. **Approver Role Hierarchy**:
   - *Assumption*: Approver roles are stratified into three sequential tiers:
     - Level 1: `LINE_MANAGER` (approval limit <= \$2,000).
     - Level 2: `DEPARTMENT_HEAD` (approval limit <= \$25,000).
     - Level 3: `FINANCE` (approval limit > \$25,000 or company-wide).
   - *Department Scoping*: Line managers and department heads are assigned to specific departments, whereas finance approvers may hold global authority (`department_id` is nullable).
3. **QuoteLine Granularity**:
   - *Assumption*: Quotations are priced at the line-item level via `quote_lines`, each referencing a valid `request_line_id` from the parent Purchase Request.
   - *Rationale*: Real-world enterprise sourcing evaluates bids line-by-line rather than as an opaque aggregate sum.
4. **Fixed Exchange Rate Timing**:
   - *Assumption*: The configured exchange rates remain constant throughout fiscal year 2026.
   - *Clarification*: Daily or fluctuating FX curves are not simulated in Phase 1; historical procurement benchmarking assumes fixed planning rates.
5. **Single RFQ per Purchase Request**:
   - *Assumption*: In this procurement model, if competitive bidding is required, exactly one RFQ is issued for a given Purchase Request. Re-tendering would require raising a new PR or closing the prior cycle.
