# Data Validation & Integrity Report

**Validation Mode**: `clean`  
**Overall Status**: `FAIL`  
**Total Checks Executed**: 10,844  
**Passed Checks**: 10,832  
**Failed Checks**: 12  
**Warnings**: 0  

---

## 1. Summary by Validation Category

| Category | Total Checks | Passed | Failed | Warnings | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ANOMALY_FREE` | 7 | 0 | 7 | 0 | **FAILED** |
| `APPROVALS` | 196 | 193 | 3 | 0 | **FAILED** |
| `BUDGET` | 40 | 40 | 0 | 0 | **PASSED** |
| `DATES` | 739 | 738 | 1 | 0 | **FAILED** |
| `FINANCIAL` | 1,873 | 1,872 | 1 | 0 | **FAILED** |
| `FOREIGN_KEYS` | 3,590 | 3,590 | 0 | 0 | **PASSED** |
| `LIFECYCLE` | 1,343 | 1,343 | 0 | 0 | **PASSED** |
| `PRIMARY_KEYS` | 3,056 | 3,056 | 0 | 0 | **PASSED** |

---

## 2. Validated Entity Inventory

| Entity Table | Record Count |
| :--- | :---: |
| `approvals` | 96 |
| `approvers` | 22 |
| `budget_events` | 390 |
| `budgets` | 10 |
| `deliveries` | 101 |
| `departments` | 10 |
| `ground_truth` | 7 |
| `purchase_order_lines` | 188 |
| `purchase_orders` | 93 |
| `purchase_requests` | 116 |
| `quote_lines` | 414 |
| `request_lines` | 227 |
| `requesters` | 30 |
| `rfq_supplier_invites` | 183 |
| `rfqs` | 50 |
| `status_events` | 930 |
| `supplier_quotes` | 183 |
| `suppliers` | 13 |

---

## 3. Discrepancies and Failures

### Critical & Error Failures

| Check Name | Entity | Record ID | Field | Expected | Actual | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `financial_budget_no_overrun` | `budgets` | `BUD-0009` | `allocated_amount` | `Allocated: 1,135,388` | `Encumbered: 1,892,314` | Department budget has zero clean-path overrun |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0009-2026-000031` | `award_date` | `<= 2026-02-25` | `2026-03-02` | Quote award occurs before quotation expiry |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000082` | `total_estimate_usd` | `>= 1 levels for $5,675.55` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000116` | `total_estimate_usd` | `>= 1 levels for $1,590.00` | `0` | Requisition received required number of tiered approval levels |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0005-2026-000004` | `score` | `0.0698` | `0.9451` | Awarded quotation has lowest composite score among competitors |
| `clean_mode_anomaly_po_without_approval` | `purchase_orders` | `PO-2026-000010` | `None` | `Zero anomalies in clean dataset` | `Anomaly: po_without_approval` | Purchase order PO-2026-000010 issued for requisition PR-2026-000082 lacking approved authorization |
| `clean_mode_anomaly_expired_quote_before_award` | `supplier_quotes` | `QUO-SUP-C-0009-2026-000031` | `None` | `Zero anomalies in clean dataset` | `Anomaly: expired_quote_before_award` | Quote QUO-SUP-C-0009-2026-000031 validity expired on 2026-02-25 before award date 2026-03-02 |
| `clean_mode_anomaly_non_cheapest_quote_without_rationale` | `supplier_quotes` | `QUO-SUP-C-0005-2026-000004` | `None` | `Zero anomalies in clean dataset` | `Anomaly: non_cheapest_quote_without_rationale` | Quote QUO-SUP-C-0005-2026-000004 awarded at $4,862.15 exceeding minimum available cost ($4,252.06) without documented justification |
| `clean_mode_anomaly_inactive_supplier_used` | `purchase_orders` | `PO-2026-000072` | `None` | `Zero anomalies in clean dataset` | `Anomaly: inactive_supplier_used` | Purchase order PO-2026-000072 issued to inactive/suspended vendor SUP-0013 |
| `clean_mode_anomaly_budget_overrun` | `budgets` | `BUD-0009` | `None` | `Zero anomalies in clean dataset` | `Anomaly: budget_overrun` | Department budget BUD-0009 total commitments ($18,923.14) exceed allocated budget ($11,353.88) by $7,569.26 |
| `clean_mode_anomaly_duplicate_purchase_request` | `purchase_requests` | `PR-2026-000116` | `None` | `Zero anomalies in clean dataset` | `Anomaly: duplicate_purchase_request` | Requisition PR-2026-000116 is an identical duplicate of PR-2026-000028 submitted within 3 days for identical item lines |
| `clean_mode_anomaly_quote_currency_mismatch` | `supplier_quotes` | `QUO-SUP-C-0004-2026-000026` | `None` | `Zero anomalies in clean dataset` | `Anomaly: quote_currency_mismatch` | Quote QUO-SUP-C-0004-2026-000026 submitted in invalid/unsupported currency 'XYZ' lacking valid conversion rate |
