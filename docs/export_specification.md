# Procure-to-Pay Export Engine Specification

**Document Version**: 1.0.0  
**Status**: APPROVED  
**Target Release**: Phase 6 Deliverables  

---

## 1. Scope and Objective

This document defines the formal technical specification for the multi-format data export engine of the YottaFlex Procure-to-Pay Synthetic Data Generator. The export subsystem transforms internal in-memory Python procurement graph structures into standardized, production-ready persistence layers:
- Relational SQLite 3 database (`procurement.db`)
- RFC 4180-compliant Delimited CSV files (`csv/*.csv`)
- Structured UTF-8 JSON documents (`json/*.json`)
- Canonical ANSI SQL Schema DDL (`sql/schema.sql`)
- Fully populated SQL Seed script (`sql/seed.sql`)
- Segregated Ground Truth Anomaly Datasets (`ground_truth/*`)

---

## 2. Directory Layout & Storage Hierarchy

All exported deliverables are written to a configurable destination directory (defaulting to `data/` for starter scale and `output/` for full scale):

```
<base_dir>/
├── csv/
│   ├── departments.csv
│   ├── budgets.csv
│   ├── requesters.csv
│   ├── approvers.csv
│   ├── suppliers.csv
│   ├── purchase_requests.csv
│   ├── request_lines.csv
│   ├── rfqs.csv
│   ├── rfq_supplier_invites.csv
│   ├── supplier_quotes.csv
│   ├── quote_lines.csv
│   ├── approvals.csv
│   ├── purchase_orders.csv
│   ├── purchase_order_lines.csv
│   ├── deliveries.csv
│   ├── status_events.csv
│   └── budget_events.csv
├── json/
│   ├── departments.json
│   ├── budgets.json
│   ├── requesters.json
│   ├── approvers.json
│   ├── suppliers.json
│   ├── purchase_requests.json
│   ├── request_lines.json
│   ├── rfqs.json
│   ├── rfq_supplier_invites.json
│   ├── supplier_quotes.json
│   ├── quote_lines.json
│   ├── approvals.json
│   ├── purchase_orders.json
│   ├── purchase_order_lines.json
│   ├── deliveries.json
│   ├── status_events.json
│   ├── budget_events.json
│   └── metadata.json
├── database/
│   └── procurement.db
├── sql/
│   ├── schema.sql
│   └── seed.sql
├── ground_truth/
│   ├── ground_truth.csv
│   └── ground_truth.json
└── reports/
    ├── export_integrity_report.md
    └── dataset_statistics.md
```

---

## 3. Operational Entities & Relational Schema Mapping

The system manages 17 operational tables mapped to SQLite tables, CSV files, and JSON collections:

| Entity Name | Primary Key | Foreign Key Dependencies | Description |
| :--- | :--- | :--- | :--- |
| `departments` | `department_id` | *None* | Organizational business units and cost centers |
| `budgets` | `budget_id` | `department_id -> departments` | Annual departmental spending allocations |
| `requesters` | `requester_id` | `department_id -> departments` | Employees authorized to raise purchase requests |
| `approvers` | `approver_id` | *None* | Management tiers authorized to approve spend |
| `suppliers` | `supplier_id` | *None* | Onboarded vendor catalog and payment terms |
| `purchase_requests` | `request_id` | `department_id -> departments`, `requester_id -> requesters` | Purchase requisitions raised by requesters |
| `request_lines` | `line_id` | `request_id -> purchase_requests` | Itemized goods/services on a purchase request |
| `rfqs` | `rfq_id` | `request_id -> purchase_requests` | Sourcing event for competitive requisitions |
| `rfq_supplier_invites` | `invite_id` | `rfq_id -> rfqs`, `supplier_id -> suppliers` | Invitation sent to a supplier to participate in RFQ |
| `supplier_quotes` | `quote_id` | `rfq_id -> rfqs`, `supplier_id -> suppliers` | Commercial quotation submitted by an invited supplier |
| `quote_lines` | `quote_line_id` | `quote_id -> supplier_quotes`, `line_id -> request_lines` | Line-item pricing, lead time, and tax breakdown |
| `approvals` | `approval_id` | `request_id -> purchase_requests`, `approver_id -> approvers` | Approval/rejection record according to financial delegation |
| `purchase_orders` | `po_id` | `request_id -> purchase_requests`, `supplier_id -> suppliers`, `quote_id -> supplier_quotes` | Legally binding purchase contract |
| `purchase_order_lines` | `po_line_id` | `po_id -> purchase_orders`, `request_line_id -> request_lines`, `quote_line_id -> quote_lines` | Individual committed line item on a purchase order |
| `deliveries` | `delivery_id` | `po_id -> purchase_orders`, `po_line_id -> purchase_order_lines` | Goods receipt note (GRN) and fulfillment log |
| `status_events` | `event_id` | Dynamic (`entity_id` polymorphic reference) | Audit trail of entity lifecycle transitions |
| `budget_events` | `event_id` | `budget_id -> budgets`, `request_id -> purchase_requests`, `po_id -> purchase_orders` | Double-entry budget reservation and commitment ledger |

---

## 4. Multi-Format Serialization Rules

### 4.1 CSV Export (`csv/*.csv`)
- **Format**: RFC 4180 standard.
- **Encoding**: UTF-8 without BOM.
- **Header Line**: Exact column names matching SQLite DDL columns.
- **Null Values**: Empty string `""`.
- **Numbers**: Decimal values formatted to 2 decimal places without thousand separators.
- **Booleans**: Formatted as integer `1` (True) or `0` (False).
- **Determinism**: Rows sorted deterministically by primary key or chronological timestamp.

### 4.2 JSON Export (`json/*.json`)
- **Format**: JSON array of homogeneous objects (or single object for `metadata.json`).
- **Encoding**: UTF-8.
- **Indentation**: 2 spaces for human inspectability.
- **Dates**: ISO 8601 strings (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`).
- **Nulls**: Native `null`.

### 4.3 SQLite Database (`database/procurement.db`)
- **Engine**: SQLite 3 with WAL mode support.
- **PRAGMA Settings**:
  - `PRAGMA foreign_keys = ON;` (Mandatory before all operations).
  - `PRAGMA synchronous = NORMAL;`
- **Transactions**: Populated using an atomic transaction wrapper. On any failure, full rollback is triggered.
- **Indices**: All foreign keys and high-frequency join columns indexed per `data/sql/schema.sql`.

### 4.4 SQL DDL & Seed (`sql/schema.sql` & `sql/seed.sql`)
- **Schema**: Canonical DDL statements defining tables, column types, constraints, and composite indices.
- **Seed**: Valid ANSI SQL `INSERT INTO <table> (...) VALUES (...);` statements.
- **Topological Ingestion Order**: Tables inserted strictly from parent to child to guarantee zero foreign key violations during sequential replay.

---

## 5. Ground Truth Storage Separation Policy

To support unbiased machine learning and rule-based anomaly detection benchmarking:
1. **Isolated Directory**: Ground truth anomaly labels are saved exclusively to `<base_dir>/ground_truth/ground_truth.csv` and `<base_dir>/ground_truth/ground_truth.json`.
2. **Operational Exclusion**: Operational directories (`csv/` and `json/`) MUST NEVER contain `ground_truth.csv` or `ground_truth.json`.
3. **Database Exclusion**: `procurement.db` and `seed.sql` must contain only operational procurement tables; ground truth labels are not persisted into operational business tables.
4. **Schema**:
   - `anomaly_id` (`ANOM-XXXX`)
   - `entity_type` (e.g., `purchase_orders`, `purchase_requests`, `supplier_quotes`)
   - `entity_id` (Primary key of the affected operational record)
   - `anomaly_category` (One of the 7 PRD anomaly types)
   - `severity` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
   - `description` (Human-readable explanation of injected defect)
   - `detected_by` (Detection engine identifier)
   - `timestamp` (Injection timestamp)

