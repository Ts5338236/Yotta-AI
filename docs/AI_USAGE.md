# AI Usage & Governance Declaration

This document transparently records how Artificial Intelligence (AI) tools were employed in the architectural design, schema drafting, and code implementation of the Procure-to-Pay Synthetic Data Generator.

---

## 1. AI Tools Utilized

The following AI tools and interfaces were used during development:
- **Primary AI Assistant**: Antigravity Assistant (Google DeepMind / Anthropic Claude Sonnet 4.6), utilized for architectural design, code generation, refactoring, test drafting, and compliance documentation.
- **Code Autocompletion**: GitHub Copilot / Cursor IDE AI assistance, used for repetitive boilerplate, DDL typing, and test fixture expansion.
- **Execution Environment**: Windows 11 PowerShell pair-programming environment.

---

## 2. AI Assistance Across Phases

### Phase 1 & 2 Foundations
- **Foundational Infrastructure**: Package layout (`src/datagen`), YAML configuration parsing with schema validation (`src/datagen/config.py`), fixed foreign exchange engine with high-precision Decimal arithmetic (`src/datagen/fx.py`), and centralized deterministic ID generator (`src/datagen/ids.py`).
- **Normalized SQLite Schema**: Complete 19-table 3NF relational DDL with compound foreign keys, unique indexes, and domain check constraints (`output/sql/schema.sql`).
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
  - Built autonomous check domains operating independently of `derive.py` to prevent circular verification.
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
- Complete execution of fresh clone verification in an isolated directory.
- Full requirement traceability matrix and technical audit report authored at `docs/assignment_compliance_matrix.md` and `docs/final_audit_report.md`.

---

## 3. Human Oversight, Modifications & Engineering Governance

Every architectural decision, data model choice, mathematical equation, and code artifact was directly reviewed, challenged, and validated by the candidate engineer.

### Where AI Assistance was Significant
1. **Boilerplate & Schema Definitions**: Emitting repetitive DDL and dataclass boilerplate across 19 relational entities (`schema.sql`, `models.py`).
2. **Corrupted Test Fixture Permutations**: Synthesizing diverse, intentionally malformed test inputs across 39 pytest test modules (167 test cases) to stress-test validation boundaries.
3. **Draft Documentation Layouts**: Scaffold initial markdown templates for compliance matrices, gap analysis, and data dictionaries.

### Known AI-Generated Errors, Challenges & Remediation
1. **Field Name Hallucinations & Key Mismatches**: Initial AI-suggested helper scripts assumed standard ORM names like `purchase_request_id` or `purchase_order_id` instead of the canonical schema names `request_id` and `po_id`. Similarly, quote status was assumed to be a boolean `q["awarded"]` instead of enum `q["status"] == "AWARDED"`. Caught through unit test assertions and refactored.
2. **Topological Order in SQL Seeds**: Initial AI-generated SQL seed dumps attempted to insert `exception_logs` and `budget_events` before child relationships were established. Resolved by manually computing the topological DAG dependency rank across all 18 tables.
3. **Approval Tier Role vs Numeric Matching**: Initial test verification script compared `approver_role` against numeric integers (1, 2) rather than string roles (`LINE_MANAGER`, `DEPARTMENT_HEAD`, `FINANCE`). Corrected to role-based resolution.
4. **Currency Field Discrepancies**: Landed cost in base currency was named `landed_cost_base` rather than `landed_cost_usd`. Realigned across derivation and reporting modules.
5. **Clean Baseline Preserved**: Guarded against AI tendency to inline anomaly injection flags into operational tables, ensuring strict ground truth quarantine.

---

## 4. Disclosed Gaps & Prompt Provenance

In the spirit of complete disclosure and academic/professional honesty:

1. **Prompt Completeness**:
   - `ai/prompts/01_phase1_foundation.md` through `ai/prompts/06_phase6_data_export.md` are the verbatim foundational engineering prompts executed during Phases 1–6.
   - `ai/prompts/07_phase7_final_audit.md`, `08_qa_final_verification.md`, and `09_final_submission_prep.md` are concise milestone summaries and acceptance checklists rather than verbose conversational transcripts.
2. **Interactive Chat Logs**:
   - Spontaneous interactive debugging dialogues, terminal troubleshooting queries, and exploratory conversations conducted during the coding sessions were not exported into markdown or preserved in version control.
3. **AI Tools Disclosed**:
   - All AI models and tools utilized (Antigravity Claude Sonnet 4.6 and IDE autocompletion) are fully disclosed above. No undisclosed proprietary LLMs, private codebases, or black-box data generation services were used.
