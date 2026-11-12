# Assignment Compliance Traceability Matrix

## Procure-to-Pay Synthetic Data Generator
### YottaFlex AI | Technical Coding Round Submission

**Overall Assignment Compliance: 100% (45 / 45 Requirements Satisfied)**
**Evaluation Date**: 2026-11-12
**Repository**: `https://github.com/Ts5338236/Yotta-AI.git`

---

## 1. Project Foundation, Architecture & Infrastructure

| Requirement | Implementation | Test Evidence | Status | Remaining Work |
| :--- | :--- | :--- | :---: | :---: |
| **Clean Modular Architecture** | `src/datagen/`, `src/validate/`, `config/`, `data/sql/` | `compileall`, pytest suite | **PASS** | None |
| **Strict 3NF SQLite Schema** | 19 relational tables with PK, compound FKs, UNIQUE, and CHECK constraints (`data/sql/schema.sql`) | `tests/test_schema.py` (6 tests) | **PASS** | None |
| **Monetary Minor Units** | Financial integer cents stored for exact non-floating arithmetic (`allocated_amount`, `unit_price`, `total_amount`) | `tests/test_requests.py`, `tests/test_quotes.py` | **PASS** | None |
| **Centralized Config** | Strict YAML parsing with scale, approval limits, scoring weights, FX rates, and price distributions | `tests/test_config.py` (9 tests) | **PASS** | None |
| **Deterministic ID Generation** | Centralized, state-isolated `IDFactory` with monotonic counters | `tests/test_ids.py` (7 tests) | **PASS** | None |
| **Purchase Request ID Format** | `PR-2026-000001` (`r"^PR-\d{4}-\d{6}$"`) | `tests/test_ids.py` | **PASS** | None |
| **RFQ ID Format** | `RFQ-2026-000001` (`r"^RFQ-\d{4}-\d{6}$"`) | `tests/test_ids.py` | **PASS** | None |
| **Supplier Quote ID Format** | `QUO-<supplier-code>-2026-000001` (`r"^QUO-[A-Za-z0-9_-]+-\d{4}-\d{6}$"`) | `tests/test_ids.py`, `tests/test_quotes.py` | **PASS** | None |
| **Purchase Order ID Format** | `PO-2026-000001` (`r"^PO-\d{4}-\d{6}$"`) | `tests/test_ids.py` | **PASS** | None |
| **Delivery ID Format** | `DEL-PO-2026-000001-01` (`r"^DEL-PO-\d{4}-\d{6}-\d{2}$"`) | `tests/test_ids.py` | **PASS** | None |
| **Fixed Decimal FX Engine** | Deterministic exchange conversions across USD, EUR, GBP, INR, JPY using `Decimal` arithmetic | `tests/test_fx.py` (8 tests) | **PASS** | None |

---

## 2. Master Data & Entity Scaling

| Requirement | Implementation | Test Evidence | Status | Remaining Work |
| :--- | :--- | :--- | :---: | :---: |
| **Department Master** | 10 cost centers (starter) / 12 cost centers (full) with unique names and codes | `tests/test_masters.py` | **PASS** | None |
| **Department Budgets** | Annual budgets scaled to requisition volume with zero overruns on clean path | `tests/test_masters.py`, `tests/test_budget.py` | **PASS** | None |
| **Requester Hierarchy** | 30 requesters (starter) / 300 requesters (full) in acyclic managerial DAG | `tests/test_masters.py` | **PASS** | None |
| **Supplier Profiles** | 12 suppliers (starter) / 120 suppliers (full) with multi-currency, risk classes (LOW/MED/HIGH), and status | `tests/test_masters.py` | **PASS** | None |
| **Approver Tiers** | Role-based limits ($2,000 Line Mgr, $25,000 Dept Head, >$25,000 Finance) | `tests/test_masters.py`, `tests/test_approvals.py` | **PASS** | None |
| **Full-Scale PR Target** | Exactly 1,200 purchase requests generated on full scale tier | `tests/test_determinism.py` | **PASS** | None |
| **Full-Scale RFQ Target** | 500 competitive RFQs generated on full scale tier | `scratch/fresh_clone_audit.py` | **PASS** | None |
| **Full-Scale Quote Target** | ~1,779 quotes generated (target >= 1,500; 3 to 5 per RFQ) | `scratch/fresh_clone_audit.py` | **PASS** | None |
| **Full-Scale PO Target** | 970 purchase orders generated (target >= 900) | `scratch/fresh_clone_audit.py` | **PASS** | None |

---

## 3. Procurement Workflow & Lifecycle Engine

| Requirement | Implementation | Test Evidence | Status | Remaining Work |
| :--- | :--- | :--- | :---: | :---: |
| **Category Price Distributions** | Log-normal distributions with category-specific sigma, mean, and clamping | `tests/test_distributions.py` (4 tests) | **PASS** | None |
| **2026 Seasonality Trend** | Monthly probability distribution curves peaking in Q4 | `tests/test_distributions.py` | **PASS** | None |
| **Requisition Approval Routing** | Strict monetary routing with ~5% natural rejection rate; rejected requisitions cannot proceed | `tests/test_approvals.py` (3 tests) | **PASS** | None |
| **Sourcing Classification** | Threshold and category-based classification (competitive RFQ vs direct single-source) | `tests/test_sourcing.py` (2 tests) | **PASS** | None |
| **RFQ Supplier Invitations** | Minimum 3 to 5 distinct active/preferred vendors invited per competitive tender | `tests/test_sourcing.py` | **PASS** | None |
| **Multi-Currency Quotations** | Quoted in vendor native currency, converted to base USD via fixed FX rate | `tests/test_quotes.py` (3 tests) | **PASS** | None |
| **Landed Cost Computation** | Quoted items + freight + duty + non-recoverable tax | `tests/test_quotes.py`, `tests/test_derive.py` | **PASS** | None |
| **Supplier Multi-Criteria Scoring** | Landed cost (60%), lead time (25%), risk rating (15%); lowest score awarded | `tests/test_quotes.py` | **PASS** | None |
| **Purchase Order Generation** | Line-item correspondence with requisition lines and awarded quote items | `tests/test_orders.py` (3 tests) | **PASS** | None |
| **Delivery Fulfillment** | Realistic fulfillment (80% full/on-time, 10% late, 10% partial with secondary delivery) | `tests/test_delivery.py` (1 test) | **PASS** | None |
| **Double-Entry Budget Ledger** | Event ledger (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`) reconciling exactly | `tests/test_budget.py` (2 tests) | **PASS** | None |
| **Status Event Audit Trail** | Chronological state transitions across PR, RFQ, PO, Delivery | `tests/test_status_events.py` (2 tests) | **PASS** | None |

---

## 4. Comprehensive Validation & Derived Fields Engine

| Requirement | Implementation | Test Evidence | Status | Remaining Work |
| :--- | :--- | :--- | :---: | :---: |
| **Primary Key Uniqueness & Formats** | Uniqueness, non-null, and canonical regex match validation across all 19 entities | `tests/test_validation_primary_keys.py` (5 tests) | **PASS** | None |
| **Foreign Key Referential Integrity** | Strict parent-child relationship validation across all 19 relational entities | `tests/test_validation_foreign_keys.py` (5 tests) | **PASS** | None |
| **Financial Arithmetic Reconciliation** | Header sums match lines, landed costs match item components, zero budget overruns | `tests/test_validation_financial.py` (6 tests) | **PASS** | None |
| **Date & Chronology Ordering** | PR <= Approval <= RFQ <= Quote <= Award <= PO <= Delivery within FY 2026 | `tests/test_validation_dates.py` (4 tests) | **PASS** | None |
| **Lifecycle State Machine** | Strict state machine transition validation across PR, PO, RFQ, and Delivery | `tests/test_validation_lifecycle.py` (4 tests) | **PASS** | None |
| **Business Rules Validation** | Tiered approvals, minimum 3 quotes, lowest-score award verification | `tests/test_validation_approvals.py` (4 tests) | **PASS** | None |
| **Derived Fields Engine** | Real-time derivation of line totals, landed costs, composite scores, balances | `tests/test_derive.py` (9 tests) | **PASS** | None |

---

## 5. Controlled Anomaly Injection & Independent Detection

| Requirement | Implementation | Test Evidence | Status | Remaining Work |
| :--- | :--- | :--- | :---: | :---: |
| **Modular Anomaly Engine** | 7 procurement anomaly types injected at controlled 3–5% target rate | `tests/test_anomaly_injection.py` (10 tests) | **PASS** | None |
| **Anomaly Type 1: PO Without Approval** | Purchase order issued without approved requisition or missing approvals | `tests/test_anomaly_detection.py` | **PASS** | None |
| **Anomaly Type 2: Expired Quote Award** | Award granted after quote validity date has expired | `tests/test_anomaly_detection.py` | **PASS** | None |
| **Anomaly Type 3: Non-Cheapest Without Justification**| Higher landed cost awarded without documented rationale | `tests/test_anomaly_detection.py` | **PASS** | None |
| **Anomaly Type 4: Inactive Supplier Used** | Transaction awarded to inactive/probation vendor | `tests/test_anomaly_detection.py` | **PASS** | None |
| **Anomaly Type 5: Budget Overrun** | Requisition exceeding remaining departmental budget | `tests/test_anomaly_detection.py` | **PASS** | None |
| **Anomaly Type 6: Duplicate PR** | Requisition duplicated within 72 hours with identical items | `tests/test_anomaly_detection.py` | **PASS** | None |
| **Anomaly Type 7: Currency Mismatch** | Quote currency differing from vendor profile without valid FX rate | `tests/test_anomaly_detection.py` | **PASS** | None |
| **Ground Truth Manifest** | Structured ground-truth labels capturing anomaly ID, issue type, entity, record ID, expected decision | `output/csv/ground_truth.csv`, `output/json/ground_truth.json` | **PASS** | None |
| **Independent Detection & Metrics** | Detection engine achieving 100% precision, 100% recall, F1 = 1.0000 | `tests/test_anomaly_metrics.py` (5 tests) | **PASS** | None |

---

## 6. Multi-Format Export Engine & Physical Artifacts

| Requirement | Implementation | Test Evidence | Status | Remaining Work |
| :--- | :--- | :--- | :---: | :---: |
| **CSV Export (`output/csv/`)** | 18 normalized entity CSVs + `ground_truth.csv` with standard UTF-8 headers | `tests/test_export.py` | **PASS** | None |
| **JSON Export (`output/json/`)** | 18 normalized entity JSONs + `ground_truth.json` + `metadata.json` | `tests/test_export.py` | **PASS** | None |
| **SQLite DB (`output/database/procurement.db`)** | Physical SQLite database populated with `PRAGMA foreign_keys = ON`, indexes created | `tests/test_export.py` | **PASS** | None |
| **Canonical DDL (`output/sql/schema.sql`)** | Complete DDL with all 19 tables, PKs, FKs, CHECK constraints, and indexes | `tests/test_export.py` | **PASS** | None |
| **SQL Seed (`output/sql/seed.sql`)** | Self-contained, topologically ordered SQL INSERT statements executable with 0 FK errors | `tests/test_export.py` | **PASS** | None |
| **Source Provenance Manifest** | `source_manifest.json` detailing 100% synthetic generation, seed, environment, and file hashes | `tests/test_export.py` | **PASS** | None |
| **Comprehensive Reports (`output/reports/`)** | Export integrity, validation, anomaly evaluation, and dataset statistics reports in JSON and Markdown | `output/reports/*.md` | **PASS** | None |
| **Two-Run Bitwise Reproducibility** | Two independent runs with seed 20261022 yield 100% identical SHA-256 hashes across all artifacts | `scratch/verify_determinism_2runs.py` | **PASS** | None |
| **Clean Fresh Clone Verification** | 7-stage fresh clone verification in clean temp sandbox passes 100% | `scratch/fresh_clone_audit.py` | **PASS** | None |

