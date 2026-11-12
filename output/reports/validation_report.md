# Data Validation & Integrity Report

**Validation Mode**: `clean`  
**Overall Status**: `FAIL`  
**Total Checks Executed**: 111,905  
**Passed Checks**: 111,842  
**Failed Checks**: 63  
**Warnings**: 0  

---

## 1. Summary by Validation Category

| Category | Total Checks | Passed | Failed | Warnings | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ANOMALY_FREE` | 35 | 0 | 35 | 0 | **FAILED** |
| `APPROVALS` | 1,985 | 1,970 | 15 | 0 | **FAILED** |
| `BUDGET` | 48 | 48 | 0 | 0 | **PASSED** |
| `DATES` | 7,520 | 7,515 | 5 | 0 | **FAILED** |
| `FINANCIAL` | 19,350 | 19,345 | 5 | 0 | **FAILED** |
| `FOREIGN_KEYS` | 37,450 | 37,447 | 3 | 0 | **FAILED** |
| `LIFECYCLE` | 14,032 | 14,032 | 0 | 0 | **PASSED** |
| `PRIMARY_KEYS` | 31,485 | 31,485 | 0 | 0 | **PASSED** |

---

## 2. Validated Entity Inventory

| Entity Table | Record Count |
| :--- | :---: |
| `approvals` | 1,018 |
| `approvers` | 26 |
| `budget_events` | 3,970 |
| `budgets` | 12 |
| `deliveries` | 1,048 |
| `departments` | 12 |
| `ground_truth` | 35 |
| `purchase_order_lines` | 2,051 |
| `purchase_orders` | 970 |
| `purchase_requests` | 1,205 |
| `quote_lines` | 4,497 |
| `request_lines` | 2,529 |
| `requesters` | 300 |
| `rfq_supplier_invites` | 1,779 |
| `rfqs` | 500 |
| `status_events` | 9,664 |
| `supplier_quotes` | 1,779 |
| `suppliers` | 125 |

---

## 3. Discrepancies and Failures

### Critical & Error Failures

| Check Name | Entity | Record ID | Field | Expected | Actual | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `fk_po_supplier_matches_awarded_quote` | `purchase_orders` | `PO-2026-000067` | `supplier_id` | `SUP-0007` | `SUP-0123` | PO supplier matches supplier on awarded quote |
| `fk_po_supplier_matches_awarded_quote` | `purchase_orders` | `PO-2026-000174` | `supplier_id` | `SUP-0014` | `SUP-0121` | PO supplier matches supplier on awarded quote |
| `fk_po_supplier_matches_awarded_quote` | `purchase_orders` | `PO-2026-000235` | `supplier_id` | `SUP-0025` | `SUP-0122` | PO supplier matches supplier on awarded quote |
| `financial_budget_no_overrun` | `budgets` | `BUD-0004` | `allocated_amount` | `Allocated: 26,873,562` | `Encumbered: 44,789,271` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0005` | `allocated_amount` | `Allocated: 26,644,741` | `Encumbered: 44,407,902` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0006` | `allocated_amount` | `Allocated: 28,521,021` | `Encumbered: 47,535,035` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0009` | `allocated_amount` | `Allocated: 15,531,637` | `Encumbered: 25,886,063` | Department budget has zero clean-path overrun |
| `financial_budget_no_overrun` | `budgets` | `BUD-0010` | `allocated_amount` | `Allocated: 4,010,406` | `Encumbered: 6,684,011` | Department budget has zero clean-path overrun |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0009-2026-000014` | `award_date` | `<= 2026-01-16` | `2026-01-22` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0044-2026-000252` | `award_date` | `<= 2026-03-01` | `2026-03-07` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0116-2026-000492` | `award_date` | `<= 2026-04-10` | `2026-04-14` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0091-2026-000547` | `award_date` | `<= 2026-04-21` | `2026-04-27` | Quote award occurs before quotation expiry |
| `date_award_before_quote_expiry` | `supplier_quotes` | `QUO-SUP-C-0002-2026-001330` | `award_date` | `<= 2026-09-06` | `2026-09-11` | Quote award occurs before quotation expiry |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000870` | `total_estimate_usd` | `>= 1 levels for $1,503.26` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001139` | `total_estimate_usd` | `>= 1 levels for $107.02` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-000221` | `total_estimate_usd` | `>= 1 levels for $708.24` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001151` | `total_estimate_usd` | `>= 1 levels for $3,262.98` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001112` | `total_estimate_usd` | `>= 1 levels for $767.70` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001201` | `total_estimate_usd` | `>= 1 levels for $1,135.82` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001202` | `total_estimate_usd` | `>= 1 levels for $709.60` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001203` | `total_estimate_usd` | `>= 1 levels for $4,006.10` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001204` | `total_estimate_usd` | `>= 1 levels for $1,787.20` | `0` | Requisition received required number of tiered approval levels |
| `approval_required_levels` | `purchase_requests` | `PR-2026-001205` | `total_estimate_usd` | `>= 1 levels for $14,350.42` | `0` | Requisition received required number of tiered approval levels |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0069-2026-000119` | `score` | `0.1811` | `0.75` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0003-2026-000487` | `score` | `0.15` | `0.775` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0059-2026-000560` | `score` | `0.3306` | `0.75` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0071-2026-001325` | `score` | `0.25` | `0.75` | Awarded quotation has lowest composite score among competitors |
| `award_lowest_composite_score` | `supplier_quotes` | `QUO-SUP-C-0020-2026-001747` | `score` | `0.031` | `0.9318` | Awarded quotation has lowest composite score among competitors |
| `clean_mode_anomaly_po_without_approval` | `purchase_orders` | `PO-2026-000503` | `None` | `Zero anomalies in clean dataset` | `Anomaly: po_without_approval` | Purchase order PO-2026-000503 issued for requisition PR-2026-000870 lacking approved authorization |
| `clean_mode_anomaly_po_without_approval` | `purchase_orders` | `PO-2026-000560` | `None` | `Zero anomalies in clean dataset` | `Anomaly: po_without_approval` | Purchase order PO-2026-000560 issued for requisition PR-2026-001139 lacking approved authorization |
| `clean_mode_anomaly_po_without_approval` | `purchase_orders` | `PO-2026-000562` | `None` | `Zero anomalies in clean dataset` | `Anomaly: po_without_approval` | Purchase order PO-2026-000562 issued for requisition PR-2026-000221 lacking approved authorization |
| `clean_mode_anomaly_po_without_approval` | `purchase_orders` | `PO-2026-000267` | `None` | `Zero anomalies in clean dataset` | `Anomaly: po_without_approval` | Purchase order PO-2026-000267 issued for requisition PR-2026-001151 lacking approved authorization |
| `clean_mode_anomaly_po_without_approval` | `purchase_orders` | `PO-2026-000745` | `None` | `Zero anomalies in clean dataset` | `Anomaly: po_without_approval` | Purchase order PO-2026-000745 issued for requisition PR-2026-001112 lacking approved authorization |
| `clean_mode_anomaly_expired_quote_before_award` | `supplier_quotes` | `QUO-SUP-C-0009-2026-000014` | `None` | `Zero anomalies in clean dataset` | `Anomaly: expired_quote_before_award` | Quote QUO-SUP-C-0009-2026-000014 validity expired on 2026-01-16 before award date 2026-01-22 |
| `clean_mode_anomaly_expired_quote_before_award` | `supplier_quotes` | `QUO-SUP-C-0044-2026-000252` | `None` | `Zero anomalies in clean dataset` | `Anomaly: expired_quote_before_award` | Quote QUO-SUP-C-0044-2026-000252 validity expired on 2026-03-01 before award date 2026-03-07 |
| `clean_mode_anomaly_expired_quote_before_award` | `supplier_quotes` | `QUO-SUP-C-0116-2026-000492` | `None` | `Zero anomalies in clean dataset` | `Anomaly: expired_quote_before_award` | Quote QUO-SUP-C-0116-2026-000492 validity expired on 2026-04-10 before award date 2026-04-14 |
| `clean_mode_anomaly_expired_quote_before_award` | `supplier_quotes` | `QUO-SUP-C-0091-2026-000547` | `None` | `Zero anomalies in clean dataset` | `Anomaly: expired_quote_before_award` | Quote QUO-SUP-C-0091-2026-000547 validity expired on 2026-04-21 before award date 2026-04-27 |
| `clean_mode_anomaly_expired_quote_before_award` | `supplier_quotes` | `QUO-SUP-C-0002-2026-001330` | `None` | `Zero anomalies in clean dataset` | `Anomaly: expired_quote_before_award` | Quote QUO-SUP-C-0002-2026-001330 validity expired on 2026-09-06 before award date 2026-09-11 |
| `clean_mode_anomaly_non_cheapest_quote_without_rationale` | `supplier_quotes` | `QUO-SUP-C-0069-2026-000119` | `None` | `Zero anomalies in clean dataset` | `Anomaly: non_cheapest_quote_without_rationale` | Quote QUO-SUP-C-0069-2026-000119 awarded at $25,417.09 exceeding minimum available cost ($22,732.03) without documented justification |
| `clean_mode_anomaly_non_cheapest_quote_without_rationale` | `supplier_quotes` | `QUO-SUP-C-0003-2026-000487` | `None` | `Zero anomalies in clean dataset` | `Anomaly: non_cheapest_quote_without_rationale` | Quote QUO-SUP-C-0003-2026-000487 awarded at $5,190.87 exceeding minimum available cost ($4,717.36) without documented justification |
| `clean_mode_anomaly_non_cheapest_quote_without_rationale` | `supplier_quotes` | `QUO-SUP-C-0059-2026-000560` | `None` | `Zero anomalies in clean dataset` | `Anomaly: non_cheapest_quote_without_rationale` | Quote QUO-SUP-C-0059-2026-000560 awarded at $14,139.78 exceeding minimum available cost ($12,640.12) without documented justification |
| `clean_mode_anomaly_non_cheapest_quote_without_rationale` | `supplier_quotes` | `QUO-SUP-C-0071-2026-001325` | `None` | `Zero anomalies in clean dataset` | `Anomaly: non_cheapest_quote_without_rationale` | Quote QUO-SUP-C-0071-2026-001325 awarded at $5,373.38 exceeding minimum available cost ($5,127.75) without documented justification |
| `clean_mode_anomaly_non_cheapest_quote_without_rationale` | `supplier_quotes` | `QUO-SUP-C-0020-2026-001747` | `None` | `Zero anomalies in clean dataset` | `Anomaly: non_cheapest_quote_without_rationale` | Quote QUO-SUP-C-0020-2026-001747 awarded at $19,479.82 exceeding minimum available cost ($18,435.34) without documented justification |
| `clean_mode_anomaly_inactive_supplier_used` | `purchase_orders` | `PO-2026-000067` | `None` | `Zero anomalies in clean dataset` | `Anomaly: inactive_supplier_used` | Purchase order PO-2026-000067 issued to inactive/suspended vendor SUP-0123 |
| `clean_mode_anomaly_inactive_supplier_used` | `purchase_orders` | `PO-2026-000174` | `None` | `Zero anomalies in clean dataset` | `Anomaly: inactive_supplier_used` | Purchase order PO-2026-000174 issued to inactive/suspended vendor SUP-0121 |
| `clean_mode_anomaly_inactive_supplier_used` | `purchase_orders` | `PO-2026-000235` | `None` | `Zero anomalies in clean dataset` | `Anomaly: inactive_supplier_used` | Purchase order PO-2026-000235 issued to inactive/suspended vendor SUP-0122 |
| `clean_mode_anomaly_inactive_supplier_used` | `purchase_orders` | `PO-2026-000919` | `None` | `Zero anomalies in clean dataset` | `Anomaly: inactive_supplier_used` | Purchase order PO-2026-000919 issued to inactive/suspended vendor SUP-0124 |
| `clean_mode_anomaly_inactive_supplier_used` | `purchase_orders` | `PO-2026-000921` | `None` | `Zero anomalies in clean dataset` | `Anomaly: inactive_supplier_used` | Purchase order PO-2026-000921 issued to inactive/suspended vendor SUP-0125 |
| `clean_mode_anomaly_budget_overrun` | `budgets` | `BUD-0004` | `None` | `Zero anomalies in clean dataset` | `Anomaly: budget_overrun` | Department budget BUD-0004 total commitments ($447,892.71) exceed allocated budget ($268,735.62) by $179,157.09 |
| `clean_mode_anomaly_budget_overrun` | `budgets` | `BUD-0005` | `None` | `Zero anomalies in clean dataset` | `Anomaly: budget_overrun` | Department budget BUD-0005 total commitments ($444,079.02) exceed allocated budget ($266,447.41) by $177,631.61 |
*(and 13 more failures truncated)*
