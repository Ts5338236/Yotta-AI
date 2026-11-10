# Project Assumptions & Design Decisions

This document provides a transparent and auditable record of all foundational assumptions, technical design choices, and business workflow constraints across Phases 1, 2, and 3 of the Procure-to-Pay Synthetic Data Generator.

Assumptions are classified into three distinct categories:
- **Category A**: Explicit Requirements from the Master Prompt / PRD.
- **Category B**: Technical Design Decisions made by the Engineering Lead.
- **Category C**: Working Assumptions where exact real-world or domain behavior was unspecified.

---

## Category A: Explicit Requirements from PRD / Prompt

1. **Fiscal Year & Temporal Base**:
   - Fiscal year is fixed to `2026`.
   - Base date is fixed to `2026-01-01`.
   - All generated transaction dates strictly fall within 2026 (non-leap year, 365 days).
2. **Base Currency**:
   - `USD` is the central base currency of the procurement system.
3. **Approval Thresholds & Governance**:
   - Line Manager approval threshold: Up to \$2,000 (direct purchase order, catalogue sourcing).
   - Department Head approval threshold: Up to \$25,000 (competitive RFQ with >= 3 supplier quotes).
   - Purchases exceeding \$25,000 require Department Head approval + Corporate Finance approval.
4. **Supplier Scoring Weights**:
   - Landed Cost Weight: `0.60` (60%)
   - Lead Time Weight: `0.25` (25%)
   - Risk Rating Weight: `0.15` (15%)
   - Normalized score formula: $\text{score} = 0.60 \times C_{\text{norm}} + 0.25 \times L_{\text{norm}} + 0.15 \times R_{\text{norm}}$ (lower score is better).
5. **Fixed FX Rates**:
   - `USD`: 1.0, `INR`: 0.012, `EUR`: 1.08, `GBP`: 1.27, `JPY`: 0.0067.
6. **Dataset Scale Tiers**:
   - **Starter Scale**: 10 Departments, 30 Requesters, 12 Suppliers, 115 Purchase Requests, 50 RFQs, ~150 Quotes, ~90 Purchase Orders.
   - **Full Scale**: 12 Departments, 300 Requesters, 120 Suppliers, 1,150 Purchase Requests, 500 RFQs, ~1,500 Quotes, ~900 Purchase Orders.
7. **Sourcing Constraints**:
   - Exactly one RFQ per eligible purchase request (1:1 relationship).
   - An invited vendor cannot be invited multiple times to the same RFQ (`UNIQUE(rfq_id, supplier_id)`).
   - Sourcing paths supported: `competitive`, `catalogue`, `single_source`, `contract`.
   - Single-source reason codes: `sole_supplier`, `urgent`, `contract`.
   - Every competitive RFQ must have at least 3 supplier invitations and 3 quotations.
8. **Anomalies Envelope**:
   - Target anomaly rate: 3% to 5% (strictly deferred to Phase 6; clean workflow in Phase 3).
9. **Landed Cost Formula**:
   $$\text{Landed Cost} = (\text{Quoted Price} \times \text{Quantity}) + \text{Freight} + \text{Duty} + \text{Non-recoverable Tax}$$

---

## Category B: Technical Design Decisions

1. **Monetary Representation (INTEGER Minor Units & Exact Reconciliation)**:
   - In SQLite and ledger operations, all monetary amounts are stored as `INTEGER` minor units (cents).
   - Line Total Reconciliation: `line_total = round(qty * unit_estimate, 2)`.
   - PO Value Reconciliation: `po.total_amount = sum(line.line_total)` and `po.value = sum(line.line_total_usd)`.
2. **Single Deterministic RNG Pass-Through**:
   - Exactly one `numpy.random.Generator` is instantiated at the entry point (`np.random.default_rng(seed)`).
   - Submodules never instantiate independent random instances.
3. **Multicriteria Supplier Scoring Normalization**:
   - Normalization within each RFQ across competing bids:
     $$\text{metric}_{\text{norm}} = \frac{v - \min(v)}{\max(v) - \min(v)}$$
     (If $\max == \min$, normalized value is `0.0`).
   - Clean-path award rule: The eligible quotation with the lowest score wins.
4. **Delivery Shipment Distribution**:
   - ~80% single on-time shipments (delivered on or 1–2 days before expected date).
   - ~10% single late shipments (delivered 1–5 days after expected date).
   - ~10% multi-shipment partial fulfillments (split into 2 deliveries: 50%–70% initial partial receipt, remainder final receipt).
5. **Double-Entry Style Budget Event Ledger**:
   - `ALLOCATE`: Initial department funding.
   - `RESERVE`: Pre-encumbrance when a Purchase Request is approved.
   - `COMMIT`: Binding contract commitment upon Purchase Order issuance (relieving PR reservation).
   - `RELEASE`: De-encumbrance if a request is cancelled or rejected.
   - `SPEND`: Synthetic accounting expenditure recognized upon physical goods delivery.
   - Clean-path guarantee: `allocated_amount >= reserved_amount + committed_amount + spent_amount` across all departments.

---

## Category C: Domain & Operational Assumptions

1. **Pre-PO Rejection Behavior**:
   - Natural business variation: ~5% of submitted requests are rejected during Level 1 or Level 2 approval.
   - Rejected requests are halted immediately: they never receive RFQs, quotations, purchase orders, or commitments.
2. **Synthetic Expenditure (No Accounts Payable / Invoicing Engine)**:
   - The `SPEND` budget event and `spent_amount` field model synthetic accounting disbursement triggered upon goods receipt.
   - Actual invoice OCR, 3-way invoice matching, and bank payment processing are explicitly out of scope.
3. **Approver Organization Hierarchy**:
   - Each department has 1 designated `LINE_MANAGER` and 1 `DEPARTMENT_HEAD`.
   - Corporate Finance maintains centralized oversight for requests > \$25,000.
