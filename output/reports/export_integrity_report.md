# Export Integrity Verification Report

- **Status**: `PASS`
- **Verified At**: `2026-11-12T15:10:01.816360+00:00`
- **Passed Checks**: `39 / 39`

| Artifact | Check | Passed | Details |
| :--- | :--- | :--- | :--- |
| `csv/departments.csv` | `record_count_match` | **PASS** | expected=12, actual=12 |
| `csv/budgets.csv` | `record_count_match` | **PASS** | expected=12, actual=12 |
| `csv/requesters.csv` | `record_count_match` | **PASS** | expected=300, actual=300 |
| `csv/approvers.csv` | `record_count_match` | **PASS** | expected=26, actual=26 |
| `csv/suppliers.csv` | `record_count_match` | **PASS** | expected=125, actual=125 |
| `csv/purchase_requests.csv` | `record_count_match` | **PASS** | expected=1205, actual=1205 |
| `csv/request_lines.csv` | `record_count_match` | **PASS** | expected=2529, actual=2529 |
| `csv/rfqs.csv` | `record_count_match` | **PASS** | expected=500, actual=500 |
| `csv/rfq_supplier_invites.csv` | `record_count_match` | **PASS** | expected=1779, actual=1779 |
| `csv/supplier_quotes.csv` | `record_count_match` | **PASS** | expected=1779, actual=1779 |
| `csv/quote_lines.csv` | `record_count_match` | **PASS** | expected=4497, actual=4497 |
| `csv/approvals.csv` | `record_count_match` | **PASS** | expected=1018, actual=1018 |
| `csv/purchase_orders.csv` | `record_count_match` | **PASS** | expected=970, actual=970 |
| `csv/purchase_order_lines.csv` | `record_count_match` | **PASS** | expected=2051, actual=2051 |
| `csv/deliveries.csv` | `record_count_match` | **PASS** | expected=1048, actual=1048 |
| `csv/status_events.csv` | `record_count_match` | **PASS** | expected=9664, actual=9664 |
| `csv/budget_events.csv` | `record_count_match` | **PASS** | expected=3970, actual=3970 |
| `csv/ground_truth.csv` | `record_count_match` | **PASS** | expected=35, actual=35 |
| `json/departments.json` | `record_count_match` | **PASS** | expected=12, actual=12 |
| `json/budgets.json` | `record_count_match` | **PASS** | expected=12, actual=12 |
| `json/requesters.json` | `record_count_match` | **PASS** | expected=300, actual=300 |
| `json/approvers.json` | `record_count_match` | **PASS** | expected=26, actual=26 |
| `json/suppliers.json` | `record_count_match` | **PASS** | expected=125, actual=125 |
| `json/purchase_requests.json` | `record_count_match` | **PASS** | expected=1205, actual=1205 |
| `json/request_lines.json` | `record_count_match` | **PASS** | expected=2529, actual=2529 |
| `json/rfqs.json` | `record_count_match` | **PASS** | expected=500, actual=500 |
| `json/rfq_supplier_invites.json` | `record_count_match` | **PASS** | expected=1779, actual=1779 |
| `json/supplier_quotes.json` | `record_count_match` | **PASS** | expected=1779, actual=1779 |
| `json/quote_lines.json` | `record_count_match` | **PASS** | expected=4497, actual=4497 |
| `json/approvals.json` | `record_count_match` | **PASS** | expected=1018, actual=1018 |
| `json/purchase_orders.json` | `record_count_match` | **PASS** | expected=970, actual=970 |
| `json/purchase_order_lines.json` | `record_count_match` | **PASS** | expected=2051, actual=2051 |
| `json/deliveries.json` | `record_count_match` | **PASS** | expected=1048, actual=1048 |
| `json/status_events.json` | `record_count_match` | **PASS** | expected=9664, actual=9664 |
| `json/budget_events.json` | `record_count_match` | **PASS** | expected=3970, actual=3970 |
| `json/ground_truth.json` | `record_count_match` | **PASS** | expected=35, actual=35 |
| `procurement.db` | `integrity_check` | **PASS** | OK |
| `procurement.db` | `foreign_key_check` | **PASS** | OK |
| `seed.sql` | `execution_against_clean_schema` | **PASS** | OK |
