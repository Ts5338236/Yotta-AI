# Project Assumptions & Design Decisions

This document provides a transparent and auditable record of all foundational assumptions, technical design choices, and business model constraints adopted in Phase 1 and Phase 2 of the Procure-to-Pay Synthetic Data Generator.

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
   - Minimum quotes per RFQ: 3; Maximum quotes: 6; Default invites: 3.
8. **Anomalies Envelope**:
   - Minimum target anomaly rate: 3% (`0.03`).
   - Maximum target anomaly rate: 5% (`0.05`).
9. **Pre-Approval Workflow Scope for Phase 2**:
   - Purchase requests generated in Phase 2 are restricted to pre-approval workflow states (`DRAFT` and `SUBMITTED`).
   - No approval decisions, rejections, RFQs, quotations, POs, or deliveries are generated in Phase 2.
10. **Log-Normal Price Distributions**:
    - Item unit prices are sampled from category-specific log-normal distributions bounded by explicit minimum and maximum limits.

---

## Category B: Technical Design Decisions

1. **Monetary Representation (INTEGER Minor Units & Exact Reconciliation)**:
   - *Decision*: In SQLite and ledger operations, all monetary amounts are stored as `INTEGER` minor units (cents).
   - *Line Total Reconciliation*: `line_total = round(qty * unit_estimate, 2)`.
   - *Request Total Reconciliation*: `total_estimate_usd = sum(request_line.line_total)` and `total_estimated_amount = sum(request_line.estimated_line_total)`.
   - *Rationale*: Guarantees zero floating-point accumulation discrepancies across tables.
2. **Single Deterministic RNG Pass-Through**:
   - *Decision*: Exactly one `numpy.random.Generator` is instantiated at the entry point (`np.random.default_rng(seed)`).
   - *Rule*: Submodules never instantiate new random instances or rely on Python global `random`.
3. **Acyclic Requester Manager Hierarchy (DAG Tree)**:
   - *Decision*: Within each department, the first requester created is assigned the top executive grade (`DIRECTOR`) with `manager_id = None`. Subsequent requesters are assigned an eligible senior manager from the same department who was created earlier in the sequence.
   - *Rationale*: Mathematically guarantees a directed acyclic tree with zero circular reporting loops.
4. **Category Log-Normal Distribution Parameters**:

| Category | Log Mean ($\mu$) | Log Sigma ($\sigma$) | Min Price ($) | Max Price ($) | Rationale |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **IT Hardware** | 6.5 | 0.6 | 100.00 | 15,000.00 | Higher unit costs (laptops, servers, displays) |
| **Software** | 5.5 | 0.8 | 50.00 | 20,000.00 | SaaS & enterprise licenses with high variance |
| **Office Supplies** | 3.5 | 0.5 | 1.00 | 500.00 | Low unit consumables (pens, paper, folders) |
| **Furniture** | 5.0 | 0.6 | 20.00 | 10,000.00 | Medium unit costs (ergonomic chairs, desks) |
| **Industrial Equipment** | 7.0 | 0.7 | 500.00 | 50,000.00 | Heavy capital equipment (pallet jacks, compressors) |
| **Maintenance** | 4.5 | 0.6 | 10.00 | 10,000.00 | Replacement parts, lubricants, filters |
| **Professional Services** | 6.0 | 0.8 | 100.00 | 30,000.00 | Hourly consulting & security audit retainers |
| **Logistics** | 4.5 | 0.6 | 10.00 | 10,000.00 | Packaging materials, pallet sets, scanners |
| **Facilities** | 5.0 | 0.6 | 20.00 | 15,000.00 | Air purifiers, sanitization stands, fire gear |
| **Marketing** | 5.0 | 0.8 | 20.00 | 15,000.00 | Exhibition displays, print runs, agency assets |

5. **2026 Calendar Demand Seasonality**:

| Month | Name | Days | Demand Weight | Synthetic Behavior |
| :---: | :--- | :---: | :---: | :--- |
| 1 | January | 31 | 0.07 | Post-holiday ramp-up, annual budget opening |
| 2 | February | 28 | 0.07 | Steady operational procurement |
| 3 | March | 31 | 0.08 | Q1 close purchasing push |
| 4 | April | 30 | 0.07 | Q2 initial planning |
| 5 | May | 31 | 0.07 | Mid-year project replenishment |
| 6 | June | 30 | 0.08 | Q2 half-year procurement close |
| 7 | July | 31 | 0.08 | Summer operational maintenance |
| 8 | August | 31 | 0.08 | Q3 preparations |
| 9 | September | 30 | 0.09 | Q3 close and Q4 budget acceleration |
| 10 | October | 31 | 0.10 | Fiscal year-end procurement increase |
| 11 | November | 30 | 0.10 | Pre-holiday capital equipment commitments |
| 12 | December | 31 | 0.11 | "Use-it-or-lose-it" year-end budget exhaustion |

---

## Category C: Domain & Operational Assumptions

1. **Initial Budget Encumbrance State**:
   - Initial department budgets generated in Phase 2 have `allocated > 0`, and `reserved = 0`, `committed = 0`, `spent = 0`.
   - Real-time balance deductions and ledger events (`RESERVE`, `COMMIT`, `SPEND`) are executed in Phase 3.
2. **Departmental Requisition Weighting**:
   - Operational and tech departments (Engineering, IT, Operations, R&D) generate higher volumes of purchase requisitions than administrative departments (Legal, HR, Facilities).
3. **Supplier Lead Time & Risk Score Model**:
   - Supplier mean lead time ranges from 3 to 30 days.
   - Risk score is calibrated by category: LOW (0.05 - 0.30), MEDIUM (0.31 - 0.65), HIGH (0.66 - 0.95).
