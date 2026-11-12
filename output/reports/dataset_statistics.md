# Dataset Summary Statistics

- **Generated At**: `2026-11-12T15:10:01.834746+00:00`
- **Total Purchase Requests**: `1205`
- **Total Purchase Orders**: `970`
- **Total Committed PO Value**: `$0.00`
- **Total Injected Anomalies**: `35`

## Entity Record Counts

| Entity Name | Record Count |
| :--- | :--- |
| `departments` | 12 |
| `budgets` | 12 |
| `requesters` | 300 |
| `suppliers` | 125 |
| `approvers` | 26 |
| `purchase_requests` | 1,205 |
| `request_lines` | 2,529 |
| `rfqs` | 500 |
| `supplier_quotes` | 1,779 |
| `quote_lines` | 4,497 |
| `approvals` | 1,018 |
| `purchase_orders` | 970 |
| `purchase_order_lines` | 2,051 |
| `deliveries` | 1,048 |
| `status_events` | 9,664 |
| `budget_events` | 3,970 |
| `ground_truth_anomalies` | 35 |

## Financial Summary

- **Total PR Estimate**: `$5,836,299.32`
- **Total PO Committed**: `$0.00`
- **Competitive Orders**: 500 ($0.00)
- **Non-Competitive Orders**: 470 ($0.00)

## Injected Anomaly Distribution

| Anomaly Type | Count |
| :--- | :--- |
| `po_without_approval` | 5 |
| `expired_quote_before_award` | 5 |
| `non_cheapest_quote_without_rationale` | 5 |
| `inactive_supplier_used` | 5 |
| `budget_overrun` | 5 |
| `duplicate_purchase_request` | 5 |
| `quote_currency_mismatch` | 5 |
