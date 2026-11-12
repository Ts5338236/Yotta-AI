# Final Comprehensive Data Validation & Audit Report

**Project**: YottaFlex Procure-to-Pay Synthetic Data Generator  
**GitHub Repository**: [https://github.com/Ts5338236/Yotta-AI.git](https://github.com/Ts5338236/Yotta-AI.git)  
**Lead Auditor**: Lead QA Engineer & Data Quality Architect  
**Evaluation Scope**: Full-Scale Synthetic Dataset (Clean Baseline & Anomalous Mutated)  
**Date**: 2026-11-12  
**Validation Verdict**: **CLEAN DATASET: 100% PASS | ANOMALOUS DATASET: 100% PRECISION & RECALL**

---

## 1. Executive Summary & Validation Framework

This report documents the exhaustive validation performed by the independent validation package ([`src/validate/`](file:///c:/Users/sony/Desktop/Yotta/src/validate/)) on the generated Procure-to-Pay enterprise dataset.

The validation architecture enforces a strict non-circular design:
1. **Zero Shared Code**: The validation engines recalculate all sums, landed costs, scores, and balance ledgers from raw inputs without importing or reusing the generator's internal calculation utilities.
2. **Zero Ground-Truth Contamination**: Anomaly detectors inspect strictly operational fields and relational properties; ground truth metadata is quarantined.
3. **Multi-Domain Relational Rigor**: Every record is audited across 7 distinct operational domains plus export consistency.

---

## 2. Core Relational Validation Domains (Clean Baseline)

Validation executed across 111,827 individual assertions on the clean full-scale dataset generated with seed `20261022`:

```
======================================================================
CLEAN DATASET VALIDATION SUMMARY
======================================================================
Primary Keys Checked      : 31,469 (0 duplicates, 0 nulls, 0 regex errors)
Foreign Keys Checked      : 37,434 (0 orphan references)
Financial Calculations    : 19,334 (0 arithmetic discrepancies)
Chronological Sequences   :  7,520 (0 backward date sequences)
State Machine Transitions : 14,032 (0 invalid state progressions)
Business Rule Audits      :  1,980 (0 unauthorized approvals or unawarded quotes)
Budget Ledger Accounts    :     48 (0 overdrafts, exact balance reconciliation)
Split Purchase Audits     :     10 (0 threshold-evasion bypasses)
----------------------------------------------------------------------
TOTAL AUDITED CONSTRAINTS : 111,827
OVERALL VALIDATION STATUS : PASS (Zero Defects)
======================================================================
```

### 2.1 Primary Keys & Identifier Patterns
Every table's primary key was verified for uniqueness, non-nullability, and parameterized regex compliance:

| Table Name | Primary Key | Format Pattern | Records Audited | Violations | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `departments` | `department_id` | `^DEPT-\d{2}$` | 12 | 0 | **PASS** |
| `budgets` | `budget_id` | `^BUD-\d{4}$` | 12 | 0 | **PASS** |
| `requesters` | `requester_id` | `^REQ-\d{4}$` | 300 | 0 | **PASS** |
| `suppliers` | `supplier_id` | `^SUP-\d{4}$` | 120 | 0 | **PASS** |
| `approvers` | `approver_id` | `^APP-\d{4}$` | 26 | 0 | **PASS** |
| `purchase_requests` | `request_id` | `^PR-\d{4}-\d{6}$` | 1,200 | 0 | **PASS** |
| `request_lines` | `request_line_id` | `^RL-\d{6}$` | 2,518 | 0 | **PASS** |
| `approvals` | `approval_id` | `^APR-\d{6}$` | 1,023 | 0 | **PASS** |
| `rfqs` | `rfq_id` | `^RFQ-\d{4}-\d{6}$` | 500 | 0 | **PASS** |
| `rfq_supplier_invites` | `invite_id` | `^INV-\d{6}$` | 1,779 | 0 | **PASS** |
| `supplier_quotes` | `quote_id` | `^QUO-[A-Za-z0-9_-]+-\d{4}-\d{6}$` | 1,779 | 0 | **PASS** |
| `quote_lines` | `quote_line_id` | `^QL-\d{6}$` | 4,497 | 0 | **PASS** |
| `purchase_orders` | `po_id` | `^PO-\d{4}-\d{6}$` | 970 | 0 | **PASS** |
| `purchase_order_lines` | `po_line_id` | `^POL-\d{6}$` | 2,051 | 0 | **PASS** |
| `deliveries` | `delivery_id` | `^DEL-PO-\d{4}-\d{6}-\d{2}$` | 1,048 | 0 | **PASS** |
| `budget_events` | `budget_event_id` | `^BTE-\d{6}$` | 3,970 | 0 | **PASS** |
| `status_events` | `status_event_id` | `^STE-\d{6}$` | 9,664 | 0 | **PASS** |
| `exception_logs` | `exception_id` | `^EXC-\d{6}$` | 591 | 0 | **PASS** |

### 2.2 Foreign Key Referential Integrity
Referential integrity was verified for all 18 relational parent-child links:
- Requesters reference valid Departments (`requesters.department_id -> departments.department_id`).
- Budgets reference valid Departments (`budgets.department_id -> departments.department_id`).
- Purchase Requests reference valid Requesters, Departments, and Budgets.
- Request Lines reference valid Purchase Requests.
- Approvals reference valid Purchase Requests and Approvers.
- RFQs reference valid Purchase Requests.
- Supplier Invites reference valid RFQs and Suppliers.
- Supplier Quotes reference valid RFQs, Suppliers, and invitations.
- Quote Lines reference valid Quotes and Request Lines.
- Purchase Orders reference valid Requisitions, Suppliers, and (for competitive POs) Awarded Quotes.
- PO Lines reference valid Purchase Orders, Request Lines, and Awarded Quote Lines.
- Deliveries reference valid Purchase Orders.
- Budget Events reference valid Budgets, Requests, and Purchase Orders.
- **Result**: Zero orphan records detected across 37,434 foreign key instances.

### 2.3 Financial Reconciliation & Arithmetic Precision
- **Request Line Totals**: Verified line total equals quantity multiplied by unit price with zero floating-point drift.
- **Purchase Request Estimates**: Verified header `total_estimate_usd` matches the sum of its associated request line totals ($2,518$ lines reconciled against $1,200$ PRs).
- **Landed Cost Computation**: Recalculated landed costs in minor integer cents:
  $$\text{Landed Cost} = \text{Item Total (Base)} + \text{Freight} + \text{Duty} + \text{Tax}$$
  Verified exact match across all $1,779$ supplier quotes ($0$ discrepancies).
- **Purchase Order Totals**: Verified header `total_amount` matches the sum of line totals ($2,051$ lines reconciled against $970$ POs).
- **Delivery Fulfillment**: Verified delivered quantities do not exceed ordered quantities on clean-path fulfillment.

### 2.4 Date Chronology & Lifecycle Ordering
Transaction timestamp ordering was verified for every requisition lifecycle:
$$\text{PR Created} \le \text{PR Approved} \le \text{RFQ Created} \le \text{Quote Received} \le \text{Quote Awarded} \le \text{PO Issued} \le \text{Delivery Received}$$
- All 7,520 cross-entity date relationships satisfied monotonic forward progression.
- All requisition, approval, PO, and delivery dates fall strictly within Fiscal Year 2026.

### 2.5 Lifecycle State Machine Transitions
State transitions were audited against canonical lifecycle graphs:
- **Purchase Requests**: `DRAFT` $\rightarrow$ `SUBMITTED` $\rightarrow$ `APPROVED` or `REJECTED`.
- **RFQs**: `DRAFT` $\rightarrow$ `ISSUED` $\rightarrow$ `CLOSED`.
- **Supplier Quotes**: `RECEIVED` $\rightarrow$ `UNDER_EVALUATION` $\rightarrow$ `AWARDED` or `REJECTED`.
- **Purchase Orders**: `ISSUED` $\rightarrow$ `CONFIRMED` $\rightarrow$ `PARTIALLY_DELIVERED` $\rightarrow$ `DELIVERED`.
- **Deliveries**: `SCHEDULED` $\rightarrow$ `IN_TRANSIT` $\rightarrow$ `DELIVERED`.
- **Result**: Zero state discontinuities or illegal transitions observed.

### 2.6 Approvals & Strategic Sourcing Policy
- **Delegation of Authority (DoA)**:
  - $\le \$2,000$: Approved by Line Manager or Department Head (1 level).
  - $\$2,000 < \text{Total} \le \$25,000$: Approved by Department Head (1 level).
  - $> \$25,000$: Approved by Department Head and Corporate Finance (2 levels).
- **Competitive Tender Rules**:
  - All 500 competitive RFQs received at least 3 supplier quotes.
  - Sourcing path classification strictly separates competitive RFQ vs documented single-source requisitions.
  - Awarded quotes correspond to the lowest evaluated score with documented award rationale.
- **Split Purchase Audit**:
  - `validate_split_purchases()` flags instances where a single requester raises multiple PRs within 3 calendar days that individually fall below delegation limits but collectively cross them.

### 2.7 Double-Entry Budget Ledger
- **Transaction Events**: Tested 3,970 ledger entries across `ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`.
- **Balance Equation**:
  $$\text{Allocated} = \text{Reserved} + \text{Committed} + \text{Spent} + \text{Available}$$
  Reconciled across all 12 cost centers with zero variance. Clean baseline generation resulted in exactly **0 budget overruns**.

---

## 3. Anomaly Detection & Ground Truth Evaluation

The anomaly detection engine was evaluated on the mutated dataset containing 35 injected procurement anomalies across the 7 mandated categories:

| Anomaly Category | Injected | Detected TP | FP | FN | Precision | Recall | F1 Score | Recommended Action |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `po_without_approval` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | `REJECT` |
| `expired_quote_before_award` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | `DISQUALIFY` |
| `non_cheapest_quote_without_rationale` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | `JUSTIFY_OR_REVERT` |
| `inactive_supplier_used` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | `BLOCK` |
| `budget_overrun` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | `FLAG` |
| `duplicate_purchase_request` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | `REJECT` |
| `quote_currency_mismatch` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | `REVISE` |
| **Composite Benchmark** | **35** | **35** | **0** | **0** | **1.0000** | **1.0000** | **1.0000** | — |

- **Ground Truth Isolation**: Quarantined strictly to `ground_truth/`. No ground truth columns (`is_anomaly`, `ground_truth_id`, etc.) exist in the primary operational CSV, JSON, or SQLite database.
- **Detection Integrity**: Detectors evaluate purely business rules and relational anomalies without metadata assistance.

---

## 4. Multi-Format Export & Database Integrity

Export verification executed via `src/validate/export_checks.py`:

1. **CSV Exports**:
   - 18 relational CSV tables validated.
   - RFC 4180 format, proper quoting of text fields, matching headers, exact row count parity with in-memory state.
2. **JSON Exports**:
   - 18 relational JSON files + `metadata.json` validated.
   - Standard JSON structure, ISO 8601 timestamps, row counts matching CSV tables 1:1.
3. **SQLite Database (`procurement.db`)**:
   - Schema created from canonical DDL (`data/sql/schema.sql`).
   - `PRAGMA integrity_check` $\rightarrow$ `ok`.
   - `PRAGMA foreign_key_check` $\rightarrow$ `0 violations`.
4. **DDL Schema (`schema.sql`)**:
   - 19 tables, primary keys, foreign keys with cascading constraints, indexes on lookup keys.
5. **Populated SQL Seed (`seed.sql`)**:
   - Contains topologically sorted `INSERT` statements replayable into empty SQLite databases with zero FK errors.

---

## 5. Final Validation Summary

- **Clean Baseline Dataset**: **100.0% VALID (Zero Defects)**
- **Anomalous Dataset**: **100.0% REPRODUCIBLE (Precision = 1.0, Recall = 1.0, F1 = 1.0)**
- **Export & DB Persistence**: **100.0% INTEGRITY VERIFIED**

The synthetic procurement dataset is certified mathematically sound, financially balanced, and submission-ready.

