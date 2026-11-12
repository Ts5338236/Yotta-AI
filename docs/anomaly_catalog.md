# Procure-to-Pay Synthetic Data Generator — Anomaly Catalog

## Phase 5: Anomaly Injection, Ground Truth Generation & Detection Engine

This document provides a comprehensive technical catalog of the seven controlled procurement anomaly categories implemented in the YottaFlex Procure-to-Pay Synthetic Data Generator, including injection logic, ground truth schemas, detection criteria, and empirical verification benchmarks.

---

## 1. Architectural Philosophy & Separation of Concerns

1. **Post-Generation Mutation**: Anomaly injection operates exclusively on completed, clean synthetic datasets (`generate_procurement_workflow(...)`). Master data and procurement business generation logic remains 100% clean and unpolluted.
2. **Ground Truth Strict Isolation**: Ground truth records are stored in a dedicated metadata structure (`ground_truth`) with unique `ANOM-######` primary keys. Operational tables never store injection flags, boolean indicators, or ground truth references.
3. **Independent Detection**: Detection algorithms inspect only operational tables (`purchase_orders`, `supplier_quotes`, `budgets`, etc.) and business rules. Detectors **never** read ground truth records or injection metadata.
4. **Zero Collateral Damage**: Injectors mutate only the precise records selected for corruption. Referential foreign keys, arithmetic consistency of unaffected records, and unrelated entity relationships remain fully intact.

---

## 2. Injected Anomaly Specifications

### 2.1. Purchase Order Without Approval (`po_without_approval`)
- **Business Description**: A legally binding Purchase Order was issued without the required tiered management or financial approvals recorded for its originating requisition.
- **Entity**: `purchase_orders`
- **Injection Logic**: Identifies candidate purchase orders whose requisitions received approvals. Completely removes all approval ledger entries for that requisition in `dataset["approvals"]`, simulating a rogue or bypassed authorization workflow.
- **Expected Decision**: `REJECT`
- **Detection Rule**:
  ```python
  approved_pr_ids = {a["request_id"] for a in approvals if a.get("decision") == "APPROVED"}
  if po["request_id"] not in approved_pr_ids:
      flag_anomaly(po["po_id"])
  ```
- **Discrimination**: POs linked to requisitions with at least one recorded `APPROVED` event are verified as legitimate.

---

### 2.2. Expired Quote Before Award (`expired_quote_before_award`)
- **Business Description**: A vendor quotation was awarded after the expiration date specified by the supplier (`valid_until < award_date`).
- **Entity**: `supplier_quotes`
- **Injection Logic**: Selects an awarded competitive quote (`status == "AWARDED"`). Modifies `valid_until` to a calendar date 3 to 7 days prior to `award_date`.
- **Expected Decision**: `DISQUALIFY`
- **Detection Rule**:
  ```python
  if quote.get("status") == "AWARDED":
      if parse_date(quote["award_date"]) > parse_date(quote["valid_until"]):
          flag_anomaly(quote["quote_id"])
  ```
- **Discrimination**: Quotes awarded on or before `valid_until` pass without flags. Rejected or submitted unawarded quotes that expired naturally are not flagged.

---

### 2.3. Non-Cheapest Quote Awarded Without Rationale (`non_cheapest_quote_without_rationale`)
- **Business Description**: In a competitive tender with multiple compliant bids, an award was granted to a higher-cost vendor without documented justification or rationale.
- **Entity**: `supplier_quotes`
- **Injection Logic**: Selects a competitive RFQ with multiple quotes. Changes the awarded status from the lowest-cost quote to a more expensive quote, and explicitly sets `award_rationale` to empty/null.
- **Expected Decision**: `JUSTIFY_OR_REVERT`
- **Detection Rule**:
  ```python
  if quote["status"] == "AWARDED" and rfq_quotes_count > 1:
      if quote["landed_cost_base"] > min_available_landed_cost:
          if not quote.get("award_rationale") or not quote["award_rationale"].strip():
              flag_anomaly(quote["quote_id"])
  ```
- **Discrimination**: If the buyer awarded a non-cheapest quote but recorded a valid business justification (e.g., "Superior delivery lead time and comprehensive SLA"), the detector recognizes this as compliant and does not flag it.

---

### 2.4. Inactive Supplier Used (`inactive_supplier_used`)
- **Business Description**: A Purchase Order was issued to a de-registered, suspended, bankrupt, or inactive supplier.
- **Entity**: `purchase_orders`
- **Injection Logic**: Generates an inactive supplier record (`status="INACTIVE"`, `active=False`) and updates the targeted PO's `supplier_id` to reference this vendor. Avoids mutating existing active suppliers shared across multiple POs.
- **Expected Decision**: `BLOCK`
- **Detection Rule**:
  ```python
  supplier = supplier_lookup[po["supplier_id"]]
  if supplier.get("status") in ("INACTIVE", "SUSPENDED", "DEBARRED") or not supplier.get("active", True):
      flag_anomaly(po["po_id"])
  ```
- **Discrimination**: POs referencing vendors with `status == "ACTIVE"` and `active is True` pass cleanly.

---

### 2.5. Budget Overrun (`budget_overrun`)
- **Business Description**: The total committed encumbrances (reserved + committed + spent) across a department's procurement activities exceed the fiscal year allocated budget.
- **Entity**: `budgets`
- **Injection Logic**: Selects an active department budget. Reduces its `allocated_amount` below its currently encumbered spend and synchronizes the initial `ALLOCATE` ledger event, causing `available_amount < 0` while keeping ledger math 100% consistent.
- **Expected Decision**: `REJECT`
- **Detection Rule**:
  ```python
  total_encumbered = budget["reserved_amount"] + budget["committed_amount"] + budget["spent_amount"]
  if total_encumbered > budget["allocated_amount"] or budget["available_amount"] < 0:
      flag_anomaly(budget["budget_id"])
  ```
- **Discrimination**: Budgets where `allocated_amount >= total_encumbered` (i.e. `available_amount >= 0`) pass without flags.

---

### 2.6. Duplicate Purchase Request (`duplicate_purchase_request`)
- **Business Description**: The same employee submits identical requisitions (same department, cost center, line items, and quantities) within a narrow calendar window (<= 7 days).
- **Entity**: `purchase_requests`
- **Injection Logic**: Clones an existing purchase request and its request lines under a newly synchronized PR ID, shifts the `request_date` forward by 1 to 3 days, and inserts it into the dataset.
- **Expected Decision**: `FLAG`
- **Detection Rule**:
  ```python
  # Group requests by requester_id
  # Compare line items (description, category, quantity, estimate)
  # Flag if date difference <= 7 days and items match 100%
  ```
- **Discrimination**: Requisitions submitted by different requesters, requisitions with different line items, or identical requisitions submitted > 7 days apart are recognized as distinct business needs and not flagged.

---

### 2.7. Quote Currency Mismatch (`quote_currency_mismatch`)
- **Business Description**: A vendor quotation was submitted in an unmapped or invalid currency code lacking an authorized FX exchange rate.
- **Entity**: `supplier_quotes`
- **Injection Logic**: Mutates the quote currency to an unsupported code (`XYZ`) and sets `fx_rate_to_base = None`.
- **Expected Decision**: `REVISE`
- **Detection Rule**:
  ```python
  valid_currencies = {"USD", "EUR", "GBP", "INR", "JPY"}
  if quote["currency"] not in valid_currencies or quote["fx_rate_to_base"] is None:
      flag_anomaly(quote["quote_id"])
  ```
- **Discrimination**: All compliant multi-currency bids in EUR, GBP, INR, JPY, and USD with valid FX rates pass without flags.

---

## 3. Ground Truth Schema Specification

Every injected anomaly produces an immutable ground truth entry serialized into `ground_truth.json`:

```json
{
  "anomaly_id": "ANOM-000001",
  "issue_type": "po_without_approval",
  "entity": "purchase_orders",
  "record_id": "PO-2026-000010",
  "expected_decision": "REJECT",
  "reason": "Purchase order PO-2026-000010 issued for requisition PR-2026-000082 lacking required approval records",
  "metadata": {
    "request_id": "PR-2026-000082"
  }
}
```

### Field Definitions
| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `anomaly_id` | string | Yes | Unique identifier matching regex `^ANOM-\d{6}$`. |
| `issue_type` | string | Yes | Canonical issue category name. |
| `entity` | string | Yes | Target database table name where anomaly resides. |
| `record_id` | string | Yes | Primary key value of the anomalous record. |
| `expected_decision` | string | Yes | Recommended operational action (`REJECT`, `DISQUALIFY`, `JUSTIFY_OR_REVERT`, `BLOCK`, `FLAG`, `REVISE`). |
| `reason` | string | Yes | Human-readable explanation of why this record is non-compliant. |
| `metadata` | object | Yes | Key context attributes aiding validation and auditing. |

---

## 4. Empirical Detection Performance Benchmarks

Detection performance was evaluated across both standard scale tiers using the independent anomaly detectors:

### Starter Scale Benchmark (Seed 20261022)
- **Total Injected Anomalies**: 7 (1 per category)
- **True Positives (TP)**: 7
- **False Positives (FP)**: 0
- **False Negatives (FN)**: 0
- **Precision**: **100.00%**
- **Recall**: **100.00%**
- **F1-Score**: **1.0000**

### Full Scale Benchmark (Seed 20261022)
- **Total Injected Anomalies**: 35 (5 per category)
- **True Positives (TP)**: 35
- **False Positives (FP)**: 0
- **False Negatives (FN)**: 0
- **Precision**: **100.00%**
- **Recall**: **100.00%**
- **F1-Score**: **1.0000**

### Performance Breakdown by Category
| Anomaly Category | Ground Truth | Detected | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `po_without_approval` | 5 | 5 | 5 | 0 | 0 | 100% | 100% | 1.0000 |
| `expired_quote_before_award` | 5 | 5 | 5 | 0 | 0 | 100% | 100% | 1.0000 |
| `non_cheapest_quote_without_rationale` | 5 | 5 | 5 | 0 | 0 | 100% | 100% | 1.0000 |
| `inactive_supplier_used` | 5 | 5 | 5 | 0 | 0 | 100% | 100% | 1.0000 |
| `budget_overrun` | 5 | 5 | 5 | 0 | 0 | 100% | 100% | 1.0000 |
| `duplicate_purchase_request` | 5 | 5 | 5 | 0 | 0 | 100% | 100% | 1.0000 |
| `quote_currency_mismatch` | 5 | 5 | 5 | 0 | 0 | 100% | 100% | 1.0000 |
