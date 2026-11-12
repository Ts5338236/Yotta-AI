# Procurement Anomaly Injection & Detection Coverage Report

**Project**: YottaFlex Procure-to-Pay Synthetic Data Generator  
**Role**: Senior Procurement Automation Engineer & QA Auditor  
**Engine Reference**: `src/datagen/anomalies.py` (Injection) & `src/validate/anomaly_checks.py` (Detection)  
**Evaluation Metrics**: **Precision: 1.0000 \| Recall: 1.0000 \| F1-Score: 1.0000** (Zero False Positives, Zero False Negatives)  
**Ground Truth Storage**: Quarantined in `data/ground_truth.csv`, `data/ground_truth.json`, and `output/ground_truth/`

---

## 1. Executive Summary & Design Principles

The platform incorporates a controlled anomaly injection and independent auditing framework. Seven distinct fraud, policy violation, and edge-case scenarios are programmatically introduced post-generation:

### Core Governance Principles:
1. **Preservation of Baseline Integrity**: The base generation engine produces a pristine, 100% compliant dataset. Anomalies are injected through targeted mutations on cloned candidate records without corrupting unrelated baseline transactions.
2. **Quarantined Ground Truth**: Ground truth labels (`ANOM-######`) are strictly segregated from operational tables (`data/csv/` and `data/json/`) to prevent target leakage into downstream ML models.
3. **Discretion Between Business Exceptions and Anomalies**:
   - **Legitimate Exceptions** (Logged in `exception_logs`): Natural PR rejections, authorized sole-source contracts, and partial shipment fulfillments.
   - **Invalid Anomalies** (Logged in `ground_truth`): Unauthorized POs, expired quote awards, inactive supplier usage, unbudgeted overruns, unapproved duplicate requisitions, and currency mismatches.

---

## 2. Seven Required Anomaly Types: Injection & Detection Matrix

The table below outlines the 7 mandated anomaly types, candidate selection logic, applied mutations, and recommended operational responses:

| # | Anomaly Type | Candidate Selection Logic | Injected Mutation Details | Recommended Decision | Operational Audit Rationale |
|---|---|---|---|:---:|---|
| **1** | `po_without_approval` | Identifies valid issued POs with associated approval records. | Completely deletes all approval records for the referenced PR while leaving the PO issued. | **REJECT** | Purchase Order issued without mandatory delegation of authority sign-offs. |
| **2** | `quote_expired_before_award` | Selects competitive RFQs and awarded quotations. | Alters the quote's `valid_until` date to precede the PO award date (or back-dates the award date after validity expiry). | **DISQUALIFY** | Vendor quotation was awarded after the legal bid validity period expired. |
| **3** | `non_cheapest_no_rationale` | Identifies RFQs where awarded quote had lowest composite score. | Switches the award to a higher-cost vendor and completely strips the mandatory `award_rationale` explanation. | **JUSTIFY_OR_REVERT**| Awarded vendor is not the lowest evaluated score and lacks documented justification. |
| **4** | `supplier_inactive` | Injects synthetic inactive vendors into master records. | Mutates an issued PO to reference an `INACTIVE` vendor. | **BLOCK** | Purchase order dispatched to a de-listed, suspended, or inactive supplier. |
| **5** | `budget_overrun` | Identifies department budgets with active purchase requests. | Artificially inflates a purchase request estimate to exceed total departmental allocation, forcing a negative balance. | **REVISE** | Requisition total estimate breaches departmental fiscal year budget limit. |
| **6** | `duplicate_request` | Samples existing submitted purchase requisitions. | Clones the PR with identical requester, department, items, quantities, and prices within a 24-hour window. | **FLAG** | Suspected duplicate requisition submitted by the same requester within 24 hours. |
| **7** | `quote_currency_mismatch` | Selects competitive tenders with multi-currency quotations. | Modifies a quote's currency code without recalculating landed cost or FX conversion to base USD. | **REVISE** | Discrepancy between stated currency code and underlying arithmetic unit valuation. |

---

## 3. Empirical Detection Performance & Confusion Matrix

All 7 anomaly types were evaluated using independent rule-based detectors in `src/validate/anomaly_checks.py`. Performance was verified across both **Starter Scale** (7 anomalies, 1 per category) and **Full Scale** (35 anomalies, 5 per category):

### Empirical Results (Full Scale Dataset):

| Anomaly Category | Ground Truth (P) | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1-Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `po_without_approval` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| `quote_expired_before_award` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| `non_cheapest_no_rationale` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| `supplier_inactive` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| `budget_overrun` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| `duplicate_request` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| `quote_currency_mismatch` | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **Overall Macro Average** | **35** | **35** | **0** | **0** | **1.0000** | **1.0000** | **1.0000** |

### Confusion Matrix:
$$\begin{pmatrix} \text{TP} = 35 & \text{FP} = 0 \\ \text{FN} = 0 & \text{TN} = \text{All Valid Transactions} \end{pmatrix}$$
- **Clean Baseline Discrimination**: Running detectors against the un-mutated baseline dataset returns **0 findings**, confirming zero false-positive contamination.

---

## 4. Ground Truth Manifest Schema & Isolation

Ground truth records are persisted strictly to dedicated manifests (`data/ground_truth.csv` and `data/ground_truth.json`):

```json
{
  "anomaly_id": "ANOM-000001",
  "issue_type": "po_without_approval",
  "entity_type": "purchase_orders",
  "record_id": "PO-2026-000142",
  "expected_decision": "REJECT",
  "reason": "Purchase order PO-2026-000142 issued without approved purchase request sign-offs",
  "metadata": {
    "request_id": "PR-2026-000115",
    "total_amount": 4520.00
  }
}
```

### Storage Quarantine Verification:
- `validate_ground_truth_isolation()` verifies that ground truth files are stored in `data/ground_truth/` and root `data/`, and are completely absent from `data/csv/` and `data/json/`.
- No ground truth columns (`anomaly_id`, `expected_decision`, etc.) pollute the 18 operational relational database tables.

---

## 5. Distinction: Business Exceptions vs. Invalid Anomalies

The platform enforces a clear operational boundary between natural business events and fraudulent transactions:

| Characteristic | Legitimate Business Exception | Injected Negative Anomaly |
|---|---|---|
| **Storage Destination** | Table 18: `exception_logs` | Quarantined: `ground_truth.json` / `.csv` |
| **Operational Impact** | Valid business flow (documented rationale) | Policy violation / fraud / arithmetic error |
| **Typical Examples** | Managerial PR rejection, Sole-source justification, Partial shipment delivery | PO issued without approval, Inactive supplier used, Quote currency mismatch |
| **Severity Level** | `LOW` or `MEDIUM` | `HIGH` or `CRITICAL` |
| **Resolution Status** | `resolved = 1` | Requires model intervention / rejection |

---

## 6. Automated Testing Suite

All anomaly injection, detection, metric calculation, and isolation routines are tested via automated pytest suites:
- `tests/test_anomaly_injection.py` (10 tests): Validates mutation candidates and data shape preservation.
- `tests/test_anomaly_detection.py` (8 tests): Targeted tests for each of the 7 detectors.
- `tests/test_anomaly_metrics.py` (5 tests): Benchmark empirical precision, recall, and F1 calculations.
- `tests/test_anomaly_determinism.py` (3 tests): Verifies deterministic anomaly reproduction across seeds.
- `tests/test_ground_truth.py` (5 tests): Schema conformance, ID formats, and quarantine isolation.

**Result**: All 31 anomaly-specific test cases pass with 100% success rate.

