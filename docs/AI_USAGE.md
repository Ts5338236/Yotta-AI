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
  - Phase 6: `ai/prompts/06_phase6_data_export.md`
  - Phase 7: `ai/prompts/07_phase7_final_audit.md`
  - QA Final Verification: `ai/prompts/08_qa_final_verification.md`
  - Final Submission Preparation: `ai/prompts/09_final_submission_prep.md`

---

## 2. AI Assistance Across Phases

### Phase 1 & 2 Foundations
- **Foundational Infrastructure**: Package layout (`src/datagen`), YAML configuration parsing with schema validation (`src/datagen/config.py`), fixed foreign exchange engine with high-precision Decimal arithmetic (`src/datagen/fx.py`), and centralized deterministic ID generator (`src/datagen/ids.py`).
- **Normalized SQLite Schema**: Complete 19-table 3NF relational DDL with compound foreign keys, unique indexes, and domain check constraints (`data/sql/schema.sql`).
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
- **Independent Validation Framework (`src/validate/checks.py`)**:
  - Built 6 autonomous check domains operating independently of `derive.py` to prevent circular verification.
  - Implemented structured validation results with severity ratings (`CRITICAL`, `ERROR`, `WARNING`, `INFO`).
  - Added automated report generation for GitHub-flavored Markdown (`docs/validation_summary.md`) and deterministic JSON (`docs/validation_summary.json`).
- **Testing & Corrupted Fixture Design (`tests/`)**:
  - Authored comprehensive validation test suites.
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
  - Built comprehensive evaluation engine calculating TP, FP, FN, Precision, Recall, and F1 overall and per-category (achieved 1.0000 F1 score).

### Phase 6 Multi-Format Export Engine & Persistence
- **Export Engine (`src/datagen/export.py`)**:
  - Direct export to `output/csv/` (18 tables + `ground_truth.csv`).
  - Direct export to `output/json/` (18 tables + `ground_truth.json` + `metadata.json`).
  - Relational SQLite database generation at `output/database/procurement.db` with foreign keys enforced.
  - Canonical DDL export to `output/sql/schema.sql`.
  - Topologically ordered SQL seed script generation at `output/sql/seed.sql` executable with 0 FK violations.
  - Cryptographic source manifest (`source_manifest.json`) recording provenance, seeds, and file hashes.
  - Automated generation of Markdown and JSON integrity, validation, anomaly evaluation, and statistics reports in `output/reports/`.

### Phase 7 Final Audit, Determinism & Fresh Clone Verification
- Complete verification of 100% bitwise determinism across two independent runs with seed `20261022`.
- Complete execution of 7-stage automated fresh clone verification in a clean temporary directory.
- Full requirement traceability matrix and technical audit report authored at `docs/assignment_compliance_matrix.md` and `docs/final_audit_report.md`.

---

## 3. Human Oversight, Modifications & Engineering Governance

Every architectural decision, data model choice, mathematical equation, and code artifact was directly reviewed, challenged, and validated by the candidate engineer.

### Where AI Assistance was Significant
1. **Boilerplate & Schema Definitions**: Emitting repetitive DDL and dataclass boilerplate across 19 relational entities (`schema.sql`, `models.py`).
2. **Corrupted Test Fixture Permutations**: Synthesizing diverse, intentionally malformed test inputs across 28 pytest test modules (167 test cases) to stress-test validation boundaries.
3. **Draft Documentation Layouts**: Scaffold initial markdown templates for compliance matrices, gap analysis, and data dictionaries.

### What Was Personally Reviewed, Changed, and Validated
1. **Mathematical Invariant Verification**: Personally verified all integer minor units (cents) arithmetic, currency conversions, and landed cost recalculations to guarantee zero IEEE 754 floating-point rounding drift.
2. **Topological Order & Database Foreign Keys**: Manually restructured `DB_TABLES_ORDER` in `src/datagen/database.py` and `src/datagen/export.py` to ensure `exception_logs` and `budget_events` insert strictly after their parent entities (`purchase_orders`, `purchase_requests`), eliminating SQLite foreign key check violations during database initialization and SQL seed replays.
3. **Split Purchase Audit Logic**: Designed and implemented `validate_split_purchases()` in `src/validate/checks.py` to audit clusters of sub-threshold purchase requests from the same requester within 3 calendar days that aggregate beyond approval tier boundaries.
4. **Operational Exception Logging**: Implemented `generate_operational_exception_logs()` in `src/datagen/workflow.py` ensuring natural managerial PR rejections, sole-source authorizations, and partial deliveries populate Table 18 `exception_logs` rather than leaving it empty.
5. **Strict Ground Truth Isolation**: Verified and enforced that ground truth files are exported strictly to isolated directories (`ground_truth/ground_truth.csv` and `ground_truth.json`), guaranteeing zero operational leakage or model contamination.
6. **Bitwise Determinism Verification**: Validated single-RNG pass-through logic across two independent full-scale runs with seed `20261022`, confirming 100% cryptographic SHA-256 match across all 21 exported artifacts.
7. **Zero Unsanctioned Data or Deep Learning Models**: Enforced 100% pure Python data engineering; zero unapproved third-party APIs, web scraping, or black-box dependencies.
