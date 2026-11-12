# Data Validation & Integrity Report

**Validation Mode**: `anomaly_aware`  
**Overall Status**: `PASS`  
**Total Checks Executed**: 111,886  
**Passed Checks**: 111,853  
**Failed Checks**: 33  
**Warnings**: 0  

---

## 1. Summary by Validation Category

| Category | Total Checks | Passed | Failed | Warnings | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `APPROVALS` | 1,998 | 1,980 | 18 | 0 | **FAILED** |
| `BUDGET` | 48 | 48 | 0 | 0 | **PASSED** |
| `DATES` | 7,520 | 7,514 | 6 | 0 | **FAILED** |
| `FINANCIAL` | 19,351 | 19,345 | 6 | 0 | **FAILED** |
| `FOREIGN_KEYS` | 37,451 | 37,448 | 3 | 0 | **FAILED** |
| `LIFECYCLE` | 14,032 | 14,032 | 0 | 0 | **PASSED** |
| `PRIMARY_KEYS` | 31,486 | 31,486 | 0 | 0 | **PASSED** |

---

## 2. Validated Entity Inventory

| Entity Table | Record Count |
| :--- | :---: |
| `approvals` | 1,017 |
| `approvers` | 26 |
| `budget_events` | 3,970 |
| `budgets` | 12 |
| `deliveries` | 1,048 |
| `departments` | 12 |
| `exception_logs` | 591 |
| `ground_truth` | 42 |
| `purchase_order_lines` | 2,051 |
| `purchase_orders` | 970 |
| `purchase_requests` | 1,206 |
| `quote_lines` | 4,497 |
| `request_lines` | 2,529 |
| `requesters` | 300 |
| `rfq_supplier_invites` | 1,779 |
| `rfqs` | 500 |
| `status_events` | 9,664 |
| `supplier_quotes` | 1,779 |
| `suppliers` | 126 |

---

## 3. Discrepancies and Failures

### Critical & Error Failures

| Check Name | Entity | Record ID | Field | Expected | Actual | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `fk_po_supplier_matches_awarded_quote` | `purchase_orders` | `PO-2026-000067` | `supplier_id` | `SUP-0007` | `SUP-0123` | PO supplier matches supplier on awarded quote |
| `fk_po_supplier_matches_awarded_quote` | `purchase_orders` | `PO-2026-000069` | `supplier_id` | `SUP-0111` | `SUP-0122` | PO supplier matches supplier on awarded quote |
| `fk_po_supplier_matches_awarded_quote` | `purchase_orders` | `PO-2026-000270` | `supplier_id` | `SUP-0049` | `SUP-0125` | PO supplier matches supplier on awarded quote |
| `financial_budget_no_overrun` | `budgets` | `BUD-0001` | `allocated_amount` | `Allocated: 58,445,769` | `Encumbered: 97,409,616` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0003` | `allocated_amount` | `Allocated: 36,393,492` | `Encumbered: 60,655,820` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0005` | `allocated_amount` | `Allocated: 26,644,741` | `Encumbered: 44,407,902` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0006` | `allocated_amount` | `Allocated: 28,521,021` | `Encumbered: 47,535,035` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0007` | `allocated_amount` | `Allocated: 10,937,112` | `Encumbered: 18,228,521` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0011` | `allocated_amount` | `Allocated: 8,756,643` | `Encumbered: 14,594,405` | Department budget has zero clean-path overrun |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0009-2026-000014` | `award_date` | `<= 2026-01-18` | `2026-01-22` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0104-2026-000144` | `award_date` | `<= 2026-02-03` | `2026-02-09` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0011-2026-000488` | `award_date` | `<= 2026-04-10` | `2026-04-16` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0091-2026-000812` | `award_date` | `<= 2026-06-10` | `2026-06-13` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0109-2026-001186` | `award_date` | `<= 2026-08-12` | `2026-08-16` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0079-2026-001326` | `award_date` | `<= 2026-08-31` | `2026-09-07` | Quote award occurs before quotation expiry |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000870` | `total_estimate_usd` | `>= 1 levels for $1,503.26` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001139` | `total_estimate_usd` | `>= 1 levels for $107.02` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000221` | `total_estimate_usd` | `>= 1 levels for $708.24` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000042` | `total_estimate_usd` | `>= 1 levels for $1,081.38` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000032` | `total_estimate_usd` | `>= 1 levels for $1,787.20` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000402` | `total_estimate_usd` | `>= 1 levels for $13,788.02` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001201` | `total_estimate_usd` | `>= 1 levels for $3,510.09` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001202` | `total_estimate_usd` | `>= 1 levels for $1,098.36` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001203` | `total_estimate_usd` | `>= 1 levels for $5,734.55` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001204` | `total_estimate_usd` | `>= 1 levels for $417.48` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001205` | `total_estimate_usd` | `>= 1 levels for $616.85` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001206` | `total_estimate_usd` | `>= 1 levels for $4,670.84` | `0` | Requisition received required number of tiered approval levels |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0039-2026-000694` | `score` | `0.15` | `0.8588` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0044-2026-001103` | `score` | `0.25` | `0.8187` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0004-2026-001171` | `score` | `0.1285` | `0.8421` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0073-2026-001234` | `score` | `0.0091` | `0.8682` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0041-2026-001665` | `score` | `0.1316` | `0.7316` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0049-2026-001749` | `score` | `0.25` | `0.9521` | Awarded quotation has lowest composite score among competitors |

---

## 4. Anomaly Detection & Ground Truth Evaluation

**Total Ground Truth Anomalies**: 42  
**Total Inferred Detections**: 42  
**True Positives**: 42  
**False Positives**: 0  
**False Negatives**: 0  
**Overall Precision**: 100.00%  
**Overall Recall**: 100.00%  
**Overall F1-Score**: 1.0000  

### Performance by Anomaly Category

| Category | Ground Truth | Detected | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `budget_overrun` | 6 | 6 | 6 | 0 | 0 | 100.0% | 100.0% | 1.0000 |
| `duplicate_purchase_request` | 6 | 6 | 6 | 0 | 0 | 100.0% | 100.0% | 1.0000 |
| `expired_quote_before_award` | 6 | 6 | 6 | 0 | 0 | 100.0% | 100.0% | 1.0000 |
| `inactive_supplier_used` | 6 | 6 | 6 | 0 | 0 | 100.0% | 100.0% | 1.0000 |
| `non_cheapest_quote_without_rationale` | 6 | 6 | 6 | 0 | 0 | 100.0% | 100.0% | 1.0000 |
| `po_without_approval` | 6 | 6 | 6 | 0 | 0 | 100.0% | 100.0% | 1.0000 |
| `quote_currency_mismatch` | 6 | 6 | 6 | 0 | 0 | 100.0% | 100.0% | 1.0000 |
