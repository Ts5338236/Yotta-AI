# AI Usage & Governance Declaration

This document transparently records how Artificial Intelligence (AI) tools were employed in the architectural design, schema drafting, and code implementation of the Procure-to-Pay Synthetic Data Generator.

---

## 1. AI Tools Utilized

- **AI Model**: Antigravity Assistant (Google DeepMind / Anthropic Claude Sonnet 4.6).
- **Execution Environment**: Windows 11 PowerShell pair-programming environment.
- **Reference Implementation Prompts**:
  - Phase 1: `ai/prompts/01_phase1_foundation.md`
  - Phase 2: `ai/prompts/02_phase2_generation.md`
  - Phase 3: `ai/prompts/03_phase3_procurement_workflow.md`
  - Phase 4: `ai/prompts/04_phase4_derived_validation.md`

---

## 2. AI Assistance Across Phases

### Phase 1 & 2 Foundations
- **Foundational Infrastructure**: Package layout (`src/datagen`), YAML configuration parsing with schema validation (`src/datagen/config.py`), fixed foreign exchange engine with high-precision Decimal arithmetic (`src/datagen/fx.py`), and centralized deterministic ID generator (`src/datagen/ids.py`).
- **Normalized SQLite Schema**: Complete 18-table 3NF relational DDL with compound foreign keys, unique indexes, and domain check constraints (`data/sql/schema.sql`).
- **Master Data Generation (`src/datagen/masters.py`)**: Acyclic hierarchical reporting tree (DAG) for requesters, department cost centers, budget allocations, and synthetic supplier profiles.
- **Purchase Requisitions (`src/datagen/requests.py`)**: Category-specific log-normal pricing across 10 procurement categories, 2026 calendar seasonality curves, and strict PR total estimate derivations.

### Phase 3 Clean Procurement Workflow
- **Multi-Level Approvals (`src/datagen/approvals.py`)**: Tiered routing thresholds ($2,000 line manager, $25,000 department head, >$25,000 corporate finance), role resolution, and ~5% natural business rejections.
- **Strategic Sourcing & RFQ Execution (`src/datagen/sourcing.py`)**: Sourcing path classification, RFQ invitation pools (3–6 suppliers), multi-currency landed cost calculations, and multicriteria scoring.
- **Purchase Orders & Deliveries (`src/datagen/orders.py`, `src/datagen/delivery.py`)**: Competitive and non-competitive POs, line-level matching, single on-time/late receipts, and multi-shipment partial fulfillments.
- **Double-Entry Budget Ledger (`src/datagen/budget.py`)**: Real-time event ledger (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`) with zero clean-path overruns.
- **Lifecycle Event Auditing (`src/datagen/events.py`)**: Chronological status event emission across PR, RFQ, PO, and Delivery state lifecycles.

### Phase 4 Derived Fields Engine & Comprehensive Validation
- **Centralized Derived Fields Engine (`src/datagen/derive.py`)**:
  - Recalculates all derived fields directly from source records: request line totals, PR estimate sums, quote landed costs, multicriteria scores, PO totals, delivery fulfillments, current statuses, and budget balances.
- **Independent Validation Framework (`src/validate/checks.py`, `src/validate/models.py`)**:
  - Built 7 autonomous check domains operating independently of `derive.py` to prevent circular verification.
  - Implemented structured validation results with severity ratings (`CRITICAL`, `ERROR`, `WARNING`, `INFO`).
  - Added automated report generation for GitHub-flavored Markdown (`docs/validation_summary.md`) and deterministic JSON (`docs/validation_summary.json`).
- **Testing & Corrupted Fixture Design (`tests/`)**:
  - Authored 46 new unit and integration tests across 9 focused validation test suites.
  - Created intentionally corrupted test fixtures to prove the validator detects duplicate PKs, broken FKs, arithmetic discrepancies, illegal state jumps, date inversions, and budget overruns.

---

## 3. Verification & Testing of Generated Code

- **Automated Test Execution**: All 112 automated tests passed with a 100% pass rate:
  - Foundational and generation suites: 66 tests.
  - Derived fields and validation suites: 46 tests.
- **Comprehensive Validation Audit Execution**:
  - **Starter Scale Dataset**: 10,830 checks executed, 10,830 passed, 0 failed, 0 warnings (**PASS**).
  - **Full Scale Dataset**: 108,960 checks executed, 108,960 passed, 0 failed, 0 warnings (**PASS**).
- **Corrupted Fixture Detection**: Automated tests confirmed 100% detection rate for duplicate IDs, missing foreign keys, line-total arithmetic mismatches, illegal state jumps, date inversions, and budget overruns.

---

## 4. Items Requiring Human Review (TODO)

The following items are designated for human developer evaluation and sign-off:

- [ ] **TODO: Review Integer Cent Quantization Tolerance**: Confirm that allowing a tolerance of $\le \max(1, \text{quantity})$ cents between `line_total` and `quantity * unit_price` is acceptable for integer cent storage.
- [ ] **TODO: Review State Machine Target Set**: Verify whether `COMPLETED` and `ORDERED` terminal states match company ERP lifecycle conventions.
- [ ] **TODO: Human Approval for Phase 5 Transition**: Explicit developer approval required prior to beginning Phase 5 (Data Export & Storage Engine).

---

## 5. Scope Boundaries Maintained

In strict accordance with Phase 4 instructions:
1. **No Anomaly Injection**: Anomaly injection (split POs, phantom suppliers, budget overruns, off-contract spend) is deferred strictly to Phase 6.
2. **No Final Export Engine**: CSV, JSON, and bulk SQL relational export engines are deferred to Phase 5.
3. **Non-Circular Guarantee**: Validation routines do not call `derive.py` to verify output; all expectations are independently recalculated.
