# AI Usage & Governance Declaration

This document transparently records how Artificial Intelligence (AI) tools were employed in the architectural design, schema drafting, and code implementation of the Procure-to-Pay Synthetic Data Generator.

---

## 1. AI Tools Utilized

- **AI Model**: Antigravity Assistant (Google DeepMind - Gemini 3.8 Flash).
- **Execution Environment**: Windows 11 PowerShell pair-programming environment.
- **Reference Implementation Prompts**:
  - Phase 1: `ai/prompts/01_phase1_foundation.md`
  - Phase 2: `ai/prompts/02_phase2_generation.md`
  - Phase 3: `ai/prompts/03_phase3_procurement_workflow.md`

---

## 2. AI Assistance Across Phases

### Phase 1 & 2 Foundations
- **Foundational Infrastructure**: Package layout (`src/datagen`), YAML configuration parsing with schema validation (`src/datagen/config.py`), fixed foreign exchange engine with high-precision Decimal arithmetic (`src/datagen/fx.py`), and centralized deterministic ID generator (`src/datagen/ids.py`).
- **Normalized SQLite Schema**: Complete 18-table 3NF relational DDL with compound foreign keys, unique indexes, and domain check constraints (`data/sql/schema.sql`).
- **Master Data Generation (`src/datagen/masters.py`)**: Acyclic hierarchical reporting tree (DAG) for requesters, department cost centers, budget allocations, and synthetic supplier profiles.
- **Purchase Requisitions (`src/datagen/requests.py`)**: Category-specific log-normal pricing across 10 procurement categories, 2026 calendar seasonality curves, and strict PR total estimate derivations.

### Phase 3 Clean Procurement Workflow
- **Multi-Level Approvals (`src/datagen/approvals.py`)**:
  - Implementation of tiered approval routing thresholds ($2,000 line manager, $25,000 department head, >$25,000 corporate finance).
  - Approver role resolution based on departmental hierarchy and dedicated approver profiles.
  - Realistic natural ~5% business rejections resulting in terminal `REJECTED` state and budget reservation release.
- **Strategic Sourcing & RFQ Execution (`src/datagen/sourcing.py`)**:
  - PR classification into competitive (RFQ) vs non-competitive (catalogue, single-source, contract) paths.
  - RFQ invitation pool generation (3–6 eligible category suppliers per RFQ).
  - Multi-currency supplier quotes with landed costs (unit price, freight, customs/duties, taxes).
  - Multicriteria composite scoring algorithm (60% normalized cost, 25% normalized lead time, 15% supplier risk rating).
  - Objective quote award determination based on lowest composite score.
- **Purchase Orders & Deliveries (`src/datagen/orders.py`, `src/datagen/delivery.py`)**:
  - Competitive POs derived strictly from awarded quotes; non-competitive POs generated directly from request lines.
  - Line-level price and quantity matching with total amount reconciliation.
  - Three fulfillment distribution modes: single on-time (~80%), single late (~10%), and multi-shipment partial fulfillments (~10%).
- **Double-Entry Budget Ledger (`src/datagen/budget.py`)**:
  - Real-time double-entry event generation (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`).
  - Budget balance reconciliation ensuring:
    $$\text{allocated} = \text{available} + \text{reserved} + \text{committed} + \text{spent}$$
  - Zero budget overruns on clean workflow paths.
- **Lifecycle Event Auditing (`src/datagen/events.py`)**:
  - Chronological status event emission across PR, RFQ, PO, and Delivery state lifecycles with monotonic timestamp progression.
- **Workflow Orchestration & Validation (`src/datagen/workflow.py`)**:
  - Orchestration pipeline coordinating master data, requests, approvals, sourcing, orders, deliveries, and ledgers.
  - Comprehensive clean-path validation suite verifying 8 distinct relational and mathematical integrity rules.

---

## 3. Verification & Testing of Generated Code

- **Automated Test Execution**: All 66 automated tests were executed using `pytest -v` with a 100% pass rate:
  - Phase 1 & 2 suites: 48 tests (`test_config`, `test_determinism`, `test_distributions`, `test_fx`, `test_ids`, `test_masters`, `test_requests`, `test_schema`).
  - Phase 3 workflow suites: 18 tests (`test_approvals`, `test_sourcing`, `test_quotes`, `test_orders`, `test_delivery`, `test_budget`, `test_status_events`, `test_workflow_integration`).
- **Scale Verification**:
  - **Starter Scale**: 10 depts, 10 budgets, 30 requesters, 22 approvers, 12 suppliers, 115 PRs, 97 approvals, 50 RFQs, 183 invites, 183 quotes (50 awarded), 93 POs, 101 deliveries, 390 budget events, 930 status events.
  - **Full Scale**: 12 depts, 12 budgets, 300 requesters, 26 approvers, 120 suppliers, 1,150 PRs, 982 approvals, 500 RFQs, 1,781 invites, 1,781 quotes (500 awarded), 931 POs, 1,014 deliveries, 3,819 budget events, 9,344 status events.
- **Determinism Verification**: Automated tests confirmed identical seeds produce byte-for-byte identical datasets across both starter and full scales.
- **Clean-Path Integrity**: Validation suite confirmed 0 budget overruns, 0 negative balances, 0 broken foreign key relationships, and 100% financial reconciliation.

---

## 4. Items Requiring Human Review (TODO)

The following items are designated for human developer evaluation and sign-off:

- [ ] **TODO: Human Assessment of Sourcing Scoring Weights**: Review the multicriteria scoring weights (60% cost, 25% lead time, 15% risk rating) to verify alignment with enterprise procurement policy.
- [ ] **TODO: Human Assessment of Delivery Fulfillment Distribution**: Confirm whether the fulfillment split (~80% on-time, ~10% late, ~10% partial multi-shipment) matches desired operational realism.
- [ ] **TODO: Human Assessment of Scaled Departmental Budget Allocations**: Verify whether the tier-based allocation scaling in `generate_budgets` meets test bench expectations.
- [ ] **TODO: Human Approval for Phase 4 Transition**: Explicit developer approval required prior to beginning Phase 4 (Derived Analytics & KPI Engine).

---

## 5. Scope Boundaries Maintained

In strict accordance with Phase 3 instructions:
1. **No Anomaly Injection**: Anomaly injection (split POs, phantom suppliers, budget overruns, late deliveries) is strictly prohibited and deferred to Phase 6.
2. **No Export Engines**: CSV/JSON dataset export engines and SQLite database persistence loops are deferred to Phase 5.
3. **Clean-Path Guarantee**: All generated clean procurement records adhere 100% to valid business logic and relational integrity.
