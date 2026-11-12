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
  - Phase 5: `ai/prompts/05_phase5_anomalies.md`

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
  - Authored 46 unit and integration tests across 9 focused validation test suites.
  - Created intentionally corrupted test fixtures to prove the validator detects duplicate PKs, broken FKs, arithmetic discrepancies, illegal state jumps, date inversions, and budget overruns.

### Phase 5 Anomaly Injection, Ground Truth Generation & Detection Engine
- **Modular Anomaly Injection Engine (`src/datagen/anomalies.py`)**:
  - Implemented 7 distinct procurement anomaly mutations post-generation without polluting core master data generation.
  - Built dynamic IDFactory sequence counter synchronization (`sync_factory_counters`) preventing primary key collisions when synthesizing new records.
  - Maintained disjoint mutation candidate tracking to guarantee that multiple injectors do not corrupt the same target records.
- **Ground Truth Isolation & Modeling**:
  - Formatted dedicated `GroundTruthRecord` objects with standardized `ANOM-######` primary keys.
  - Kept ground truth strictly isolated from operational tables (zero boolean injection flags or contamination).
- **Independent Anomaly Detection & Evaluation (`src/validate/anomaly_checks.py`)**:
  - Created 7 independent rule-based detectors inspecting operational tables without reading ground truth or injection metadata.
  - Implemented edge-case discrimination (e.g. non-cheapest award with valid justification is not flagged; quotes awarded before expiry pass).
  - Built comprehensive evaluation engine calculating TP, FP, FN, Precision, Recall, and F1 overall and per-category.
- **Dual Validation Modes**:
  - `clean` mode: validates baseline data health and expects 0 anomalies (clean datasets pass, anomaly-injected datasets fail).
  - `anomaly_aware` mode: validates baseline data health, runs detectors, and evaluates detections against ground truth.

---

## 3. Verification & Testing of Generated Code

- **Automated Test Execution**: All 142 automated pytest tests passed with a 100% pass rate:
  - Foundational and generation suites: 66 tests.
  - Derived fields and validation suites: 46 tests.
  - Anomaly injection, detection, ground truth, and metrics suites: 30 tests.
- **Comprehensive Validation Audit Execution**:
  - **Starter Scale Dataset (Clean Mode)**: 10,830 checks executed, 10,830 passed, 0 failed, 0 warnings (**PASS**).
  - **Starter Scale Dataset (Anomaly-Aware Mode)**: 7/7 anomalies detected, 0 FP, 0 FN, 100% precision, 100% recall (**PASS**).
  - **Full Scale Dataset (Anomaly-Aware Mode)**: 35/35 anomalies detected, 0 FP, 0 FN, 100% precision, 100% recall (**PASS**).
- **Clean Mode Rejection**: Anomaly-injected datasets reliably fail validation in `clean` mode, proving zero silent acceptance of non-compliant records.

---

## 4. Items Requiring Human Review (TODO)

The following items are designated for human developer evaluation and sign-off:

- [ ] **TODO: Review Anomaly Distribution Weights**: Confirm that 1 anomaly per category in starter scale and 5 per category in full scale matches expected machine learning training/eval ratios.
- [ ] **TODO: Review Operational Action Taxonomy**: Confirm that `expected_decision` values (`REJECT`, `DISQUALIFY`, `JUSTIFY_OR_REVERT`, `BLOCK`, `FLAG`, `REVISE`) conform to client ERP policy.
- [ ] **TODO: Human Approval for Phase 6 Transition**: Explicit developer approval required prior to beginning Phase 6 (Data Export Engine & Relational Storage).

---

## 5. Scope Boundaries Maintained

In strict accordance with Phase 5 instructions:
1. **No Final Export Engine**: CSV, JSON export formats and SQLite persistent disk storage engine are deferred strictly to Phase 6.
2. **Zero Contamination**: Detectors never read ground truth records or injection metadata; ground truth is never saved as operational table columns.
3. **Execution Boundary**: Stopped immediately upon completion of Phase 5. Awaiting explicit user instruction before Phase 6.
