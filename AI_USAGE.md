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
  - Phase 7 & Master Prompt: `ai/prompts/07_phase7_final_audit.md`, `ai/prompts/08_master_prompt.md`

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

### Phase 6 Multi-Format Export Engine, Database Persistence & Verification
- **Export Engine (`src/datagen/export.py`)**:
  - Delimited CSV export (`data/csv/` and `output/csv/`) for all 17 operational tables conforming to RFC 4180.
  - Formatted JSON export (`data/json/` and `output/json/`) for all 17 operational tables + system metadata.
  - Relational SQLite database generation (`data/database/procurement.db` and `output/database/procurement.db`) with `PRAGMA foreign_keys = ON` and transaction safety.
  - Canonical DDL export to `data/sql/schema.sql` and `output/sql/schema.sql`.
  - Topologically ordered SQL seed script generation at `data/sql/seed.sql` and `output/sql/seed.sql` executable with 0 foreign key violations.
  - Cryptographic source manifest (`source_manifest.json`) recording provenance, seeds, and SHA-256 file hashes.
- **Relational Database Management (`src/datagen/database.py`)**:
  - Context-managed database connections with active foreign key enforcement.
  - Idempotent schema initialization from canonical DDL.
  - Transactional batch population across tables in strict topological parent-child order.
  - In-database integrity verification using SQLite PRAGMAs (`integrity_check`, `foreign_key_check`).
- **Export Integrity & Reconciliation Suite (`src/validate/export_checks.py`)**:
  - Independent verification checking CSV headers, row counts, and primary key uniqueness.
  - JSON document parsing and count verification.
  - SQLite database integrity and foreign key validation.
  - Full SQL seed execution against in-memory clean schema.
  - Strict ground truth isolation enforcement (zero anomaly labels in operational directories).
- **Comprehensive Test Coverage (`tests/`)**:
  - Created 8 dedicated export test modules (`test_csv_export.py`, `test_json_export.py`, `test_database_export.py`, `test_sql_schema.py`, `test_sql_seed.py`, `test_export_integrity.py`, `test_export_determinism.py`, `test_ground_truth_export.py`), expanding the test suite to 166 passing tests (100% pass rate).

### Phase 7 Final Audit, Determinism & Fresh Clone Verification
- Complete verification of 100% bitwise determinism across two independent runs with seed `20261022`.
- Complete execution of 7-stage automated fresh clone verification in a clean temporary directory.
- Full requirement traceability matrix and technical audit report authored at `docs/assignment_compliance_matrix.md` and `docs/final_audit_report.md`.

---

## 3. Human Oversight & Engineering Governance

1. **Architecture & Review**: Every architecture decision, data model choice, mathematical equation, and code commit was reviewed, tested, and validated by the engineer.
2. **Deterministic Code Design**: AI was strictly constrained to emit reproducible, single-RNG pass-through logic without unapproved libraries or non-deterministic side-effects.
3. **No Unsanctioned Data or Models**: Zero web scraping, zero proprietary data imports, zero deep learning black-box models. 100% pure Python data engineering.

