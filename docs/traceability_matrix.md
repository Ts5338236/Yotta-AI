# PRD Requirement Traceability Matrix & Audit Checklist

## Procure-to-Pay Synthetic Data Generator | Final Quality Assurance Audit

This traceability matrix maps every technical requirement from the original Product Requirement Document (PRD) and architecture specifications to its implementing module, automated test coverage, generated artifacts, and verification status.

---

## 1. Master Data & Foundations

| PRD Requirement | Specification Details | Implementation Module | Automated Test File | Output / Artifact | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Strict 3NF Schema** | 18 normalized relational tables with check & unique constraints | `data/sql/schema.sql` | `tests/test_schema.py` | `data/p2p_procurement.db` | **PASS** |
| **Centralized Config** | Strict YAML parsing with scale, approval, and FX parameters | `src/datagen/config.py` | `tests/test_config.py` | `config/default.yaml` | **PASS** |
| **Deterministic IDs** | Zero-padded canonical regexes across all 18 entities | `src/datagen/ids.py` | `tests/test_ids.py` | Entity Primary Keys | **PASS** |
| **Fixed Decimal FX** | Deterministic exchange conversions using Python `Decimal` | `src/datagen/fx.py` | `tests/test_fx.py` | Landed costs & base totals | **PASS** |
| **Department Hierarchy** | 10 cost centers with unique names and department IDs | `src/datagen/masters.py` | `tests/test_masters.py` | `departments.csv/.json` | **PASS** |
| **Department Budgets** | Annual budgets with double-entry style ledger balances | `src/datagen/masters.py` | `tests/test_masters.py` | `budgets.csv/.json` | **PASS** |
| **Requester Hierarchy** | Acyclic reporting DAG with line managers and departments | `src/datagen/masters.py` | `tests/test_masters.py` | `requesters.csv/.json` | **PASS** |
| **Supplier Profiles** | Multi-currency vendors with risk classifications & status | `src/datagen/masters.py` | `tests/test_masters.py` | `suppliers.csv/.json` | **PASS** |
| **Tiered Approvers** | Monetary approval limits ($2k, $25k, >$25k) and roles | `src/datagen/masters.py` | `tests/test_masters.py` | `approvers.csv/.json` | **PASS** |

---

## 2. Requisitions & Sourcing Lifecycle

| PRD Requirement | Specification Details | Implementation Module | Automated Test File | Output / Artifact | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Purchase Requests** | Requisitions with justifications, statuses, and dates in 2026 | `src/datagen/requests.py` | `tests/test_requests.py` | `purchase_requests.csv` | **PASS** |
| **Request Lines** | Multi-item lines with category-based log-normal pricing | `src/datagen/requests.py` | `tests/test_distributions.py` | `request_lines.csv` | **PASS** |
| **Seasonality Trends** | 2026 monthly weighting curves with Q4 peak | `src/datagen/requests.py` | `tests/test_distributions.py` | Date distributions | **PASS** |
| **Tiered Approvals** | Routing to manager, dept head, finance with ~5% rejections | `src/datagen/approvals.py` | `tests/test_approvals.py` | `approvals.csv` | **PASS** |
| **Sourcing Routing** | Classification into competitive RFQ vs direct single-source | `src/datagen/sourcing.py` | `tests/test_sourcing.py` | `rfqs.csv` | **PASS** |
| **Supplier RFQs** | Pool of 3–6 invited vendors per competitive tender | `src/datagen/sourcing.py` | `tests/test_sourcing.py` | `rfq_supplier_invites.csv` | **PASS** |
| **Vendor Quotations** | Multi-currency bids, landed costs, and composite scoring | `src/datagen/sourcing.py` | `tests/test_quotes.py` | `supplier_quotes.csv` | **PASS** |
| **Quote Awards** | Lowest composite score awarded with documented rationale | `src/datagen/sourcing.py` | `tests/test_quotes.py` | Quote statuses & awards | **PASS** |

---

## 3. Orders, Fulfillment & Accounting

| PRD Requirement | Specification Details | Implementation Module | Automated Test File | Output / Artifact | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Purchase Orders** | Competitive & non-competitive POs matching requisitions | `src/datagen/orders.py` | `tests/test_orders.py` | `purchase_orders.csv` | **PASS** |
| **PO Line Items** | Itemized quantities and landed prices matching quotes/PRs | `src/datagen/orders.py` | `tests/test_orders.py` | `purchase_order_lines.csv` | **PASS** |
| **Delivery Receipts** | Fulfillment receipts (80% on-time, 10% late, 10% partial) | `src/datagen/delivery.py` | `tests/test_delivery.py` | `deliveries.csv` | **PASS** |
| **Budget Ledger** | Event ledger (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`) | `src/datagen/budget.py` | `tests/test_budget.py` | `budget_events.csv` | **PASS** |
| **Lifecycle Events** | State transition audit tracking across PR, RFQ, PO, Delivery | `src/datagen/events.py` | `tests/test_status_events.py` | `status_events.csv` | **PASS** |

---

## 4. Derived Fields & Independent Validation

| PRD Requirement | Specification Details | Implementation Module | Automated Test File | Output / Artifact | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Centralized Derivation** | Pure deterministic recalculation from source records | `src/datagen/derive.py` | `tests/test_derive.py` | 11 derivation functions | **PASS** |
| **Primary Key Auditing** | PK uniqueness, non-nullability, and canonical regex checks | `src/validate/checks.py` | `tests/test_validation_primary_keys.py` | `validation_summary.md` | **PASS** |
| **Foreign Key Auditing** | Referential integrity across all 18 tables with 0 orphans | `src/validate/checks.py` | `tests/test_validation_foreign_keys.py` | `validation_summary.md` | **PASS** |
| **Financial Reconciliation** | Request line math, header sums, quote landed costs, PO spend | `src/validate/checks.py` | `tests/test_validation_financial.py` | `validation_summary.md` | **PASS** |
| **Lifecycle Validation** | State machine continuity and disallowed transition checks | `src/validate/checks.py` | `tests/test_validation_lifecycle.py` | `validation_summary.md` | **PASS** |
| **Date Chronology** | PR <= Approval <= RFQ <= Quote <= Award <= PO <= Delivery in 2026 | `src/validate/checks.py` | `tests/test_validation_dates.py` | `validation_summary.md` | **PASS** |
| **Approvals & Rules** | Monetary threshold coverage, quote counts, lowest score awards | `src/validate/checks.py` | `tests/test_validation_approvals.py` | `validation_summary.md` | **PASS** |
| **Budget Balances** | Non-negative running balances and ledger balance reconciliation | `src/validate/checks.py` | `tests/test_validation_budget.py` | `validation_summary.md` | **PASS** |
| **Physical SQLite Checks** | PRAGMA integrity_check, foreign_key_check, table existence | `src/validate/checks.py` | `tests/test_schema.py` | Database PRAGMA results | **PASS** |

---

## 5. Anomaly Injection & Detection (Phase 5)

| PRD Requirement | Specification Details | Implementation Module | Automated Test File | Output / Artifact | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **PO Without Approval** | Issue PO lacking approved authorization in approvals ledger | `src/datagen/anomalies.py` | `tests/test_anomaly_injection.py` | `ground_truth.json` | **PASS** |
| **Expired Quote Award** | Award quote after validity expiration (`valid_until < award`) | `src/datagen/anomalies.py` | `tests/test_anomaly_injection.py` | `ground_truth.json` | **PASS** |
| **Non-Cheapest Award** | Award non-lowest price bid with null/empty rationale | `src/datagen/anomalies.py` | `tests/test_anomaly_injection.py` | `ground_truth.json` | **PASS** |
| **Inactive Supplier Used** | Issue PO to inactive/debarred vendor profile | `src/datagen/anomalies.py` | `tests/test_anomaly_injection.py` | `ground_truth.json` | **PASS** |
| **Budget Overrun** | Encumbrances exceed allocation with negative available funds | `src/datagen/anomalies.py` | `tests/test_anomaly_injection.py` | `ground_truth.json` | **PASS** |
| **Duplicate Requisition** | Identical items, requester, and quantities within 7 days | `src/datagen/anomalies.py` | `tests/test_anomaly_injection.py` | `ground_truth.json` | **PASS** |
| **Quote Currency Mismatch**| Unsupported currency code lacking valid FX rate | `src/datagen/anomalies.py` | `tests/test_anomaly_injection.py` | `ground_truth.json` | **PASS** |
| **Ground Truth Isolation** | Dedicated `ANOM-######` schema segregated from operational tables | `src/datagen/anomalies.py` | `tests/test_ground_truth.py` | `ground_truth.json` | **PASS** |
| **Independent Detectors** | 7 autonomous rule checkers operating without ground truth | `src/validate/anomaly_checks.py` | `tests/test_anomaly_detection.py` | `AnomalyFinding` list | **PASS** |
| **Evaluation Metrics** | TP, FP, FN, Precision, Recall, and F1 calculations | `src/validate/anomaly_checks.py` | `tests/test_anomaly_metrics.py` | Evaluation reports | **PASS** |
| **100% Precision & Recall** | Empirical benchmark achieving 100% precision & 100% recall | `src/validate/anomaly_checks.py` | `tests/test_anomaly_metrics.py` | 7/7 and 35/35 detected | **PASS** |

---

## 6. Persistence & Fresh Clone Execution (Phases 6 & 7)

| PRD Requirement | Specification Details | Implementation Module | Automated Test File | Output / Artifact | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **CSV Export Engine** | Export all 17 operational tables and ground truth to CSV | `src/datagen/export.py` | `tests/test_export.py` | `data/csv/*.csv` | **PASS** |
| **JSON Export Engine** | Export all tables and metadata to JSON format | `src/datagen/export.py` | `tests/test_export.py` | `data/json/*.json` | **PASS** |
| **SQLite Ingestion** | Bulk insert with foreign-key compliance into SQLite DB | `src/datagen/export.py` | `tests/test_export.py` | `data/p2p_procurement.db` | **PASS** |
| **Clean Environment Execution**| Verified fresh clone simulation in clean temporary directory | `scripts/fresh_clone_verify.py` | Integration CLI tests | End-to-end execution | **PASS** |

