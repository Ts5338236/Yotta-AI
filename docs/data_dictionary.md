# Data Dictionary

This document details the relational schema, field definitions, integrity constraints, and data formats for all 18 tables defined in `data/sql/schema.sql`.

---

## 1. Department (`departments`)
Master entity defining organizational business units. Generated in Phase 2 by `src/datagen/masters.py`.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `department_id` | TEXT | PRIMARY KEY | Yes | Unique department code | `^DEPT-\d{2}$` (e.g. `DEPT-01`) | Dimension |
| `name` | TEXT | UNIQUE, NOT NULL | Yes | Department operational name | Non-empty string | - |
| `cost_center_code`| TEXT | UNIQUE, NOT NULL | Yes | ERP cost center identifier | Unique alphanumeric (e.g. `CC-ENG-100`) | - |
| `cost_centre` | TEXT | Alias | Yes | Alias for `cost_center_code` | Alphanumeric | - |
| `effective_from` | TEXT | Attribute | Yes | Department active start date | `YYYY-MM-DD` (`2026-01-01`) | Date |
| `effective_to` | TEXT | Attribute | Yes | Department active end date | `YYYY-MM-DD` (`2026-12-31`) | Date |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

---

## 2. Budget (`budgets`)
Financial allocations per department and fiscal year. Generated in Phase 2 by `src/datagen/masters.py`.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `budget_id` | TEXT | PRIMARY KEY | Yes | Unique budget identifier | `^BUD-\d{4}$` (e.g. `BUD-0001`) | Dimension |
| `department_id` | TEXT | FK (`departments`), NOT NULL | Yes | Owning department | Valid `department_id` | Dimension |
| `fiscal_year` | INTEGER | CHECK (>= 2000), NOT NULL | Yes | Operating fiscal year | e.g. 2026 | Year |
| `currency` | TEXT | NOT NULL | Yes | Base operating currency | `USD` | ISO 4217 |
| `allocated` | REAL | Attribute | Yes | Total budget allocated in USD | Non-negative float | USD |
| `allocated_amount`| INTEGER | CHECK (>= 0), NOT NULL | Yes | Total budget allocated in cents | Non-negative integer | Cents |
| `reserved` | REAL | Attribute | Yes | Pre-encumbered in USD (PR submitted) | `0.0` initially | USD |
| `reserved_amount` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Pre-encumbered (PR submitted) | Non-negative integer (0 initially) | Cents |
| `committed` | REAL | Attribute | Yes | Encumbered in USD (PO issued) | `0.0` initially | USD |
| `committed_amount`| INTEGER | CHECK (>= 0), NOT NULL | Yes | Encumbered (PO issued) | Non-negative integer (0 initially) | Cents |
| `spent` | REAL | Attribute | Yes | Disbursed in USD (Goods received) | `0.0` initially | USD |
| `spent_amount` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Disbursed (Goods received) | Non-negative integer (0 initially) | Cents |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

*Table Constraints:* `UNIQUE (department_id, fiscal_year)`.

---

## 3. Requester (`requesters`)
Corporate employees authorized to raise purchase requests. Generated in Phase 2 by `src/datagen/masters.py`.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `requester_id` | TEXT | PRIMARY KEY | Yes | Unique requester code | `^REQ-\d{4}$` (e.g. `REQ-0001`) | Dimension |
| `department_id` | TEXT | FK (`departments`), NOT NULL | Yes | Assigned department | Valid `department_id` | Dimension |
| `name` | TEXT | NOT NULL | Yes | Full employee name | Non-empty string | - |
| `email` | TEXT | UNIQUE, NOT NULL | Yes | Corporate email address | Valid corporate email | - |
| `grade` | TEXT | Attribute | Yes | Seniority grade tier | `'DIRECTOR'`, `'SENIOR_MANAGER'`, `'MANAGER'`, `'SENIOR_INDIVIDUAL'`, `'INDIVIDUAL'` | Enum |
| `job_title` | TEXT | NOT NULL | Yes | Job designation | Non-empty string | - |
| `manager_id` | TEXT | FK (`requesters`), Nullable | Yes | Reporting manager ID | Valid `requester_id` in same dept, or `NULL` for Director | Dimension |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

---

## 4. Approver (`approvers`)
Corporate actors authorized to approve purchase requests based on financial delegation of authority.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `approver_id` | TEXT | PRIMARY KEY | Yes | Unique approver code | `^APP-\d{4}$` (e.g. `APP-0001`) | Dimension |
| `name` | TEXT | NOT NULL | Yes | Full approver name | Non-empty string | - |
| `email` | TEXT | UNIQUE, NOT NULL | Yes | Corporate email address | Valid corporate email | - |
| `department_id` | TEXT | FK (`departments`) | Optional | Associated department (or NULL for central) | Valid `department_id` or NULL | Dimension |
| `role` | TEXT | CHECK enum, NOT NULL | Yes | Approval role | `'LINE_MANAGER'`, `'DEPARTMENT_HEAD'`, `'FINANCE'` | Enum |
| `approval_limit`| INTEGER | CHECK (>= 0), NOT NULL | Yes | Financial signing threshold | Minor units (cents) | Cents |
| `is_active` | INTEGER | CHECK (0, 1), NOT NULL | Yes | Active status flag | `1` (Active), `0` (Inactive) | Boolean |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

---

## 5. Supplier (`suppliers`)
External commercial vendors providing goods and services. Generated in Phase 2 by `src/datagen/masters.py`.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `supplier_id` | TEXT | PRIMARY KEY | Yes | Unique vendor identifier | `^SUP-\d{4}$` (e.g. `SUP-0001`) | Dimension |
| `supplier_code` | TEXT | Attribute | Yes | Vendor operational code | `^SUP-C-\d{4}$` (e.g. `SUP-C-0001`) | Dimension |
| `name` | TEXT | UNIQUE, NOT NULL | Yes | Legal company name | Non-empty string | - |
| `contact_email` | TEXT | NOT NULL | Yes | Sales contact email | Valid email | - |
| `country` | TEXT | NOT NULL | Yes | Operating country | e.g. `'USA'`, `'DEU'`, `'IND'`, `'GBR'`, `'JPN'` | ISO 3166 |
| `currency` | TEXT | NOT NULL | Yes | Native invoicing currency | `'USD'`, `'EUR'`, `'GBP'`, `'INR'`, `'JPY'` | ISO 4217 |
| `status` | TEXT | CHECK enum, NOT NULL | Yes | Vendor onboarding status | `'ACTIVE'`, `'PREFERRED'`, `'PROBATION'`, `'INACTIVE'` | Enum |
| `status_effective_dates`| TEXT | Attribute | Yes | Effective period | `'2026-01-01 to 2026-12-31'` | String |
| `effective_from` | TEXT | Attribute | Yes | Effective start date | `YYYY-MM-DD` | Date |
| `effective_to` | TEXT | Attribute | Yes | Effective end date | `YYYY-MM-DD` | Date |
| `risk_flag` | TEXT | CHECK enum, NOT NULL | Yes | Assessed vendor risk | `'LOW'`, `'MEDIUM'`, `'HIGH'` | Enum |
| `risk_classification` | TEXT | CHECK enum, NOT NULL | Yes | Alias for `risk_flag` | `'LOW'`, `'MEDIUM'`, `'HIGH'` | Enum |
| `risk_score` | REAL | Attribute | Yes | Quantitative vendor risk score | Low: 0.05-0.30, Med: 0.31-0.65, High: 0.66-0.95 | Score |
| `lead_time_mean` | INTEGER | Attribute | Yes | Expected delivery lead time | 3 to 30 days | Days |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

---

## 6. PurchaseRequest (`purchase_requests`)
Requisition raised by a requester for goods or services. Generated in Phase 2 by `src/datagen/requests.py`.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `request_id` | TEXT | PRIMARY KEY | Yes | Requisition ID | `^PR-\d{4}-\d{6}$` (e.g. `PR-2026-000001`) | Dimension |
| `requester_id` | TEXT | FK (`requesters`), NOT NULL | Yes | Requisition author | Valid `requester_id` | Dimension |
| `department_id` | TEXT | FK (`departments`), NOT NULL | Yes | Charged department | Valid `department_id` (matches requester's dept) | Dimension |
| `budget_id` | TEXT | FK (`budgets`), NOT NULL | Yes | Funded budget account | Valid `budget_id` (matches dept's budget) | Dimension |
| `currency` | TEXT | NOT NULL | Yes | Request currency | `'USD'` | ISO 4217 |
| `request_date` | TEXT | NOT NULL | Yes | Business requisition date | `YYYY-MM-DD` (strictly within 2026) | Date |
| `created_date` | TEXT | Alias | Yes | Alias for `request_date` | `YYYY-MM-DD` | Date |
| `status` | TEXT | CHECK enum, NOT NULL | Yes | Requisition lifecycle stage | `'DRAFT'`, `'SUBMITTED'` (pre-approval workflow in Phase 2) | Enum |
| `priority` | TEXT | Attribute | Yes | Requisition priority | `'LOW'`, `'MEDIUM'`, `'HIGH'`, `'CRITICAL'` | Enum |
| `justification` | TEXT | NOT NULL | Yes | Business purpose summary | Non-empty string | - |
| `total_estimate_usd` | REAL | Attribute | Yes | Exact derived sum from request lines | `SUM(request_line.line_total)` | USD |
| `total_estimated_amount` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Estimated requisition sum in cents | `SUM(request_line.estimated_line_total)` | Cents |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |
| `updated_at` | TEXT | NOT NULL | Yes | Last status update timestamp | ISO 8601 UTC timestamp | Time |

---

## 7. RequestLine (`request_lines`)
Individual line item breakdown for a purchase request. Generated in Phase 2 by `src/datagen/requests.py`.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `request_line_id` | TEXT | PRIMARY KEY | Yes | Line item identifier | `^RL-\d{6}$` (e.g. `RL-000001`) | Dimension |
| `request_id` | TEXT | FK (`purchase_requests`), NOT NULL | Yes | Parent purchase request | Valid `request_id` | Dimension |
| `line_number` | INTEGER | CHECK (> 0), NOT NULL | Yes | Sequential line index | Pos integer (1, 2, ...) | Index |
| `item` | TEXT | Attribute | Yes | Catalog item description | Non-empty string per category | - |
| `item_description` | TEXT | NOT NULL | Yes | Alias for `item` | Non-empty string | - |
| `category` | TEXT | NOT NULL | Yes | Procurement category | 10 approved categories | - |
| `qty` | INTEGER | CHECK (> 0), NOT NULL | Yes | Required units | Positive integer | Count |
| `quantity` | INTEGER | CHECK (> 0), NOT NULL | Yes | Alias for `qty` | Positive integer | Count |
| `unit_estimate` | REAL | Attribute | Yes | Unit estimate in USD | Log-normal sample bounded by `[min, max]` | USD |
| `estimated_unit_price` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Unit estimate in cents | Non-negative integer | Cents |
| `line_total` | REAL | Attribute | Yes | `round(qty * unit_estimate, 2)` | Exactly `qty * unit_estimate` | USD |
| `estimated_line_total` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Line total in cents | `int(round(line_total * 100))` | Cents |

*Table Constraints:* `UNIQUE (request_id, line_number)`.

---

## 8. RFQ (`rfqs`)
Request for Quotation issued for competitive sourcing.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rfq_id` | TEXT | PRIMARY KEY | Yes | RFQ identifier | `^RFQ-\d{4}-\d{6}$` (e.g. `RFQ-2026-000001`) | Dimension |
| `request_id` | TEXT | FK (`purchase_requests`), UNIQUE, NOT NULL | Yes | Parent purchase request | Valid `request_id` (1:1 relationship) | Dimension |
| `issue_date` | TEXT | NOT NULL | Yes | Sourcing issue date | `YYYY-MM-DD` | Date |
| `due_date` | TEXT | NOT NULL | Yes | Bid closing date | `YYYY-MM-DD` (>= issue_date) | Date |
| `status` | TEXT | CHECK enum, NOT NULL | Yes | RFQ lifecycle state | `'DRAFT'`, `'ISSUED'`, `'CLOSED'`, `'AWARDED'`, `'CANCELLED'` | Enum |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

---

## 9. RFQSupplierInvite (`rfq_supplier_invites`)
Vendors invited to bid on a specific RFQ.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invite_id` | TEXT | PRIMARY KEY | Yes | Invite record identifier | `^INV-\d{6}$` (e.g. `INV-000001`) | Dimension |
| `rfq_id` | TEXT | FK (`rfqs`), NOT NULL | Yes | Target RFQ | Valid `rfq_id` | Dimension |
| `supplier_id` | TEXT | FK (`suppliers`), NOT NULL | Yes | Invited vendor | Valid `supplier_id` | Dimension |
| `invited_at` | TEXT | NOT NULL | Yes | Invitation timestamp | ISO 8601 UTC timestamp | Time |
| `invitation_status` | TEXT | CHECK enum, NOT NULL | Yes | Vendor response to invite | `'SENT'`, `'ACCEPTED'`, `'DECLINED'`, `'NO_RESPONSE'` | Enum |

*Table Constraints:* `UNIQUE (rfq_id, supplier_id)`.

---

## 10. SupplierQuote (`supplier_quotes`)
Commercial bids submitted by invited suppliers.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `quote_id` | TEXT | PRIMARY KEY | Yes | Quote identifier | `^QUO-\d{4}-\d{6}$` (e.g. `QUO-2026-000001`) | Dimension |
| `rfq_id` | TEXT | FK (`rfqs`), NOT NULL | Yes | Quoted RFQ | Valid `rfq_id` | Dimension |
| `supplier_id` | TEXT | FK (`suppliers`), NOT NULL | Yes | Bidding supplier | Valid `supplier_id` | Dimension |
| `quote_date` | TEXT | NOT NULL | Yes | Quotation submission date | `YYYY-MM-DD` | Date |
| `currency` | TEXT | NOT NULL | Yes | Quotation billing currency | `'USD'`, `'EUR'`, `'GBP'`, `'INR'`, `'JPY'` | ISO 4217 |
| `fx_rate_to_base`| REAL | CHECK (> 0), NOT NULL | Yes | Configured exchange rate factor | Fixed rate (Base / Quote) | Factor |
| `total_quoted_amount` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Quoted total in native minor units | Non-negative integer | Minor units |
| `total_quoted_amount_base` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Total normalized to USD cents | Non-negative integer | Cents |
| `lead_time_days`| INTEGER | CHECK (>= 0), NOT NULL | Yes | Committed delivery lead time | Non-negative integer | Days |
| `status` | TEXT | CHECK enum, NOT NULL | Yes | Quote evaluation status | `'SUBMITTED'`, `'UNDER_REVIEW'`, `'AWARDED'`, `'REJECTED'`, `'EXPIRED'` | Enum |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

*Table Constraints:* `FOREIGN KEY (rfq_id, supplier_id) REFERENCES rfq_supplier_invites(rfq_id, supplier_id)`, `UNIQUE (rfq_id, supplier_id)`.

---

## 11. QuoteLine (`quote_lines`)
Itemized line pricing submitted in a supplier quote.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `quote_line_id` | TEXT | PRIMARY KEY | Yes | Quote line identifier | `^QL-\d{6}$` (e.g. `QL-000001`) | Dimension |
| `quote_id` | TEXT | FK (`supplier_quotes`), NOT NULL | Yes | Parent quotation | Valid `quote_id` | Dimension |
| `request_line_id` | TEXT | FK (`request_lines`), NOT NULL | Yes | Quoted request line | Valid `request_line_id` | Dimension |
| `quoted_quantity` | INTEGER | CHECK (> 0), NOT NULL | Yes | Offered quantity | Positive integer | Count |
| `unit_price` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Quoted unit price in quote currency | Non-negative integer | Minor units |
| `line_total` | INTEGER | CHECK (>= 0), NOT NULL | Yes | `quoted_quantity * unit_price` | Non-negative integer | Minor units |
| `line_total_base` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Line total converted to USD cents | Non-negative integer | Cents |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

*Table Constraints:* `UNIQUE (quote_id, request_line_id)`.

---

## 12. Approval (`approvals`)
Financial and operational sign-off steps on purchase requests.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `approval_id` | TEXT | PRIMARY KEY | Yes | Approval record ID | `^APR-\d{6}$` (e.g. `APR-000001`) | Dimension |
| `request_id` | TEXT | FK (`purchase_requests`), NOT NULL | Yes | Target purchase request | Valid `request_id` | Dimension |
| `approver_id` | TEXT | FK (`approvers`), NOT NULL | Yes | Assigned approver | Valid `approver_id` | Dimension |
| `approval_level`| INTEGER | CHECK (1, 2, 3), NOT NULL | Yes | Tier (1: Mgr, 2: Dept Head, 3: Finance) | `1`, `2`, `3` | Tier |
| `decision` | TEXT | CHECK enum, NOT NULL | Yes | Outcome | `'PENDING'`, `'APPROVED'`, `'REJECTED'` | Enum |
| `decision_date` | TEXT | Optional | Decision timestamp | ISO 8601 UTC timestamp or NULL | Time |
| `comments` | TEXT | Optional | Approver comments or remarks | Free text | - |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

*Table Constraints:* `UNIQUE (request_id, approval_level)`.

---

## 13. PurchaseOrder (`purchase_orders`)
Binding commercial commitment issued to a vendor.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `po_id` | TEXT | PRIMARY KEY | Yes | Purchase Order identifier | `^PO-\d{4}-\d{6}$` (e.g. `PO-2026-000001`) | Dimension |
| `request_id` | TEXT | FK (`purchase_requests`), NOT NULL | Yes | Backing purchase request | Valid `request_id` | Dimension |
| `supplier_id` | TEXT | FK (`suppliers`), NOT NULL | Yes | Awarded vendor | Valid `supplier_id` | Dimension |
| `awarded_quote_id` | TEXT | FK (`supplier_quotes`), Optional | Awarded quote (for competitive POs) | Valid `quote_id` or NULL | Dimension |
| `sourcing_type` | TEXT | CHECK enum, NOT NULL | Yes | Sourcing procedure | `'COMPETITIVE'`, `'SOLE_SOURCE'`, `'EMERGENCY'`, `'CONTRACT_RENEWAL'` | Enum |
| `sourcing_justification` | TEXT | Optional | Required rationale for non-competitive sourcing | Free text | - |
| `currency` | TEXT | NOT NULL | Yes | Contract currency | `'USD'` | ISO 4217 |
| `total_amount` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Committed total in USD cents | Non-negative integer | Cents |
| `status` | TEXT | CHECK enum, NOT NULL | Yes | PO lifecycle state | `'ISSUED'`, `'PARTIALLY_DELIVERED'`, `'COMPLETED'`, `'CANCELLED'` | Enum |
| `po_date` | TEXT | NOT NULL | Yes | PO issuance date | `YYYY-MM-DD` | Date |
| `expected_delivery_date` | TEXT | NOT NULL | Yes | Expected fulfillment date | `YYYY-MM-DD` | Date |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |
| `updated_at` | TEXT | NOT NULL | Yes | Audit modification timestamp | ISO 8601 UTC timestamp | Time |

---

## 14. PurchaseOrderLine (`purchase_order_lines`)
Itemized line items contracted on a Purchase Order.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `po_line_id` | TEXT | PRIMARY KEY | Yes | PO line identifier | `^POL-\d{6}$` (e.g. `POL-000001`) | Dimension |
| `po_id` | TEXT | FK (`purchase_orders`), NOT NULL | Yes | Parent PO | Valid `po_id` | Dimension |
| `line_number` | INTEGER | CHECK (> 0), NOT NULL | Yes | Sequential line index | Positive integer | Index |
| `request_line_id` | TEXT | FK (`request_lines`), NOT NULL | Yes | Fulfill request line | Valid `request_line_id` | Dimension |
| `awarded_quote_line_id` | TEXT | FK (`quote_lines`), Optional | Reference quoted price line | Valid `quote_line_id` or NULL | Dimension |
| `quantity` | INTEGER | CHECK (> 0), NOT NULL | Yes | Contracted quantity | Positive integer | Count |
| `unit_price` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Contracted unit price in USD cents | Non-negative integer | Cents |
| `line_total` | INTEGER | CHECK (>= 0), NOT NULL | Yes | `quantity * unit_price` in USD cents | Non-negative integer | Cents |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

*Table Constraints:* `UNIQUE (po_id, line_number)`.

---

## 15. Delivery (`deliveries`)
Goods receipts and shipment fulfillments recorded against Purchase Orders.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `delivery_id` | TEXT | PRIMARY KEY | Yes | Delivery ID | `^DEL-PO-\d{4}-\d{6}-\d{2}$` (e.g. `DEL-PO-2026-000001-01`) | Dimension |
| `po_id` | TEXT | FK (`purchase_orders`), NOT NULL | Yes | Contracted Purchase Order | Valid `po_id` | Dimension |
| `delivery_sequence` | INTEGER | CHECK (> 0), NOT NULL | Yes | Shipment sequence (1, 2, ...) | Positive integer | Sequence |
| `delivery_date` | TEXT | NOT NULL | Yes | Receipt date | `YYYY-MM-DD` | Date |
| `received_by` | TEXT | NOT NULL | Yes | Receiving employee name | Non-empty string | - |
| `delivery_status` | TEXT | CHECK enum, NOT NULL | Yes | Shipment condition | `'PARTIAL'`, `'FULL'`, `'DAMAGED'`, `'RETURNED'` | Enum |
| `items_delivered_count` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Units received in shipment | Non-negative integer | Count |
| `notes` | TEXT | Optional | Delivery receiving notes | Free text | - |
| `created_at` | TEXT | NOT NULL | Yes | Audit creation timestamp | ISO 8601 UTC timestamp | Time |

*Table Constraints:* `UNIQUE (po_id, delivery_sequence)`.

---

## 16. StatusEvent (`status_events`)
Comprehensive audit log of lifecycle state transitions across all entities.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `event_id` | TEXT | PRIMARY KEY | Yes | Status event identifier | `^SE-\d{6}$` (e.g. `SE-000001`) | Dimension |
| `entity_type` | TEXT | CHECK enum, NOT NULL | Yes | Entity being modified | `'PURCHASE_REQUEST'`, `'RFQ'`, `'QUOTE'`, `'PURCHASE_ORDER'`, `'DELIVERY'`, `'BUDGET'` | Enum |
| `entity_id` | TEXT | NOT NULL | Yes | ID of modified entity | Valid entity ID | Dimension |
| `previous_status` | TEXT | Optional | Prior state | Valid status string or NULL | Enum |
| `new_status` | TEXT | NOT NULL | Yes | Resulting state | Valid status string | Enum |
| `actor_id` | TEXT | NOT NULL | Yes | Acting user/system ID | e.g. `REQ-0001`, `APP-0001`, `SYSTEM` | Dimension |
| `actor_type` | TEXT | CHECK enum, NOT NULL | Yes | Classification of actor | `'REQUESTER'`, `'APPROVER'`, `'SUPPLIER'`, `'BUYER'`, `'SYSTEM'` | Enum |
| `event_timestamp` | TEXT | NOT NULL | Yes | Precise transition time | ISO 8601 UTC timestamp | Time |
| `reason` | TEXT | Optional | Transition justification | Free text | - |

---

## 17. BudgetEvent (`budget_events`)
Immutable double-entry style financial ledger tracking budget lifecycle balances.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `budget_event_id` | TEXT | PRIMARY KEY | Yes | Ledger entry identifier | `^BE-\d{6}$` (e.g. `BE-000001`) | Dimension |
| `budget_id` | TEXT | FK (`budgets`), NOT NULL | Yes | Targeted budget line | Valid `budget_id` | Dimension |
| `request_id` | TEXT | FK (`purchase_requests`), Optional | Associated requisition | Valid `request_id` or NULL | Dimension |
| `po_id` | TEXT | FK (`purchase_orders`), Optional | Associated Purchase Order | Valid `po_id` or NULL | Dimension |
| `event_type` | TEXT | CHECK enum, NOT NULL | Yes | Financial operation | `'ALLOCATE'`, `'RESERVE'`, `'COMMIT'`, `'RELEASE'`, `'SPEND'` | Enum |
| `amount` | INTEGER | CHECK (>= 0), NOT NULL | Yes | Transacted value in cents | Non-negative integer | Cents |
| `currency` | TEXT | NOT NULL | Yes | Transaction currency | `'USD'` | ISO 4217 |
| `event_timestamp` | TEXT | NOT NULL | Yes | Ledger event timestamp | ISO 8601 UTC timestamp | Time |
| `description` | TEXT | NOT NULL | Yes | Ledger entry explanation | Non-empty string | - |

---

## 18. ExceptionLog (`exception_logs`)
Detailed operational and anomaly event log for data auditing and pipeline exceptions.

| Field Name | Data Type | Constraint | Required | Description | Allowed Values / Format | Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `exception_id` | TEXT | PRIMARY KEY | Yes | Exception event ID | `^EXC-\d{6}$` (e.g. `EXC-000001`) | Dimension |
| `exception_type` | TEXT | NOT NULL | Yes | Categorical classification | e.g. `'SPLIT_PO'`, `'BUDGET_OVERRUN'`, `'LATE_DELIVERY'` | - |
| `severity` | TEXT | CHECK enum, NOT NULL | Yes | Criticality level | `'LOW'`, `'MEDIUM'`, `'HIGH'`, `'CRITICAL'` | Enum |
| `affected_entity_type` | TEXT | NOT NULL | Yes | Targeted entity category | Entity table name or type | - |
| `affected_entity_id` | TEXT | NOT NULL | Yes | Targeted entity ID | Valid entity identifier | Dimension |
| `reason` | TEXT | NOT NULL | Yes | Root cause or violation text | Non-empty string | - |
| `logged_at` | TEXT | NOT NULL | Yes | Exception detection timestamp | ISO 8601 UTC timestamp | Time |
| `resolved` | INTEGER | CHECK (0, 1), NOT NULL | Yes | Resolution flag | `0` (Unresolved), `1` (Resolved) | Boolean |
