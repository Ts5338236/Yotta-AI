# Business Rules & Exception Engine Architecture Report

**Project**: YottaFlex Procure-to-Pay Synthetic Data Generator  
**Role**: Senior Procurement Automation Engineer  
**Configuration Reference**: `config/default.yaml`  
**Core Modules**: `src/datagen/approvals.py`, `src/datagen/sourcing.py`, `src/datagen/orders.py`, `src/datagen/budget.py`, `src/validate/checks.py`  
**Test Suite**: 27 dedicated tests passing in `tests/test_approvals.py`, `tests/test_quotes.py`, `tests/test_validation_approvals.py`

---

## 1. Approval Workflows & Financial Authority Limits

The platform enforces a configurable, multi-tier financial delegation of authority based on requisition total estimated amount:

```yaml
approval_thresholds:
  manager_limit: 2000.00          # Tier 1 ceiling
  department_head_limit: 25000.00 # Tier 2 ceiling
```

### Delegation Matrix:
| Requisition Value Range | Tier Level | Designee Role | Required Approvers | Natural Rejection Handling |
|---|:---:|---|---|---|
| **$\le \$2,000.00$** | Level 1 | `LINE_MANAGER` | Requester's direct managerial supervisor | ~5% natural business rejection |
| **$\$2,000.01$ to $\$25,000.00$** | Level 1 | `DEPARTMENT_HEAD` | Department Director | ~5% natural business rejection |
| **$> \$25,000.00$** | Levels 1 & 2 | `DEPARTMENT_HEAD` + `FINANCE` | Sequential: Dept Head approval followed by Corporate Finance Director | Level 1 rejection halts workflow; Level 2 failure records Finance rejection |

### Boundary & Exception Verification:
- **Exact Thresholds**: A requisition of exactly \$2,000.00 requires only Level 1 Line Manager approval; \$2,000.01 promotes to Department Head. A requisition of exactly \$25,000.00 requires only Department Head approval; \$25,000.01 promotes to sequential Corporate Finance sign-off.
- **Rejection Enforcement**: Rejected requisitions immediately transition to `status = 'REJECTED'`, halting progression. Zero purchase orders or RFQs are ever issued for rejected requisitions on the clean path.

---

## 2. Purchasing Rules & Sourcing Pathways

The platform distinguishes between competitive bidding and authorized direct non-competitive purchasing:

### A. Direct & Catalogue Purchasing (Low-Value Path)
- **Eligibility**: Requisitions $\le \$2,000.00$ or recurring standard goods.
- **Workflow**: Bypasses RFQ tenders and issues direct purchase orders to pre-approved active vendors.
- **Sourcing Classification**: `sourcing_path = "catalogue"`, `sourcing_type = "SOLE_SOURCE"`.

### B. Competitive Sourcing & Quorum Rule
- **Eligibility**: Requisitions $>\$2,000.00$ lacking single-source exemptions.
- **Quorum Requirement**: **Strict minimum of 3 valid supplier quotes**.
  - RFQs invite 3 to 5 distinct active/preferred vendors.
  - Across 500 competitive RFQs in full scale: 307 received 3 quotes, 105 received 4 quotes, and 88 received 5 quotes. Zero competitive tenders have $<3$ quotes.

### C. Documented Single-Source Purchasing Exceptions
High-value purchases bypassing competitive tenders mandate documented business justification codes recorded in `sourcing_justification` and `single_source_reason_code`:
1. `contract`: Master Service Agreement (MSA) or corporate volume discount agreement renewal.
2. `sole_supplier`: OEM exclusive provider or proprietary intellectual property (e.g. Cisco hardware, specialized SaaS seats).
3. `urgent`: Emergency mission-critical operational repairs to avoid business disruption.

### D. Vendor Activity & Quote Expiry Invariants
- **Active Supplier Rule**: Only vendors with status `ACTIVE` or `PREFERRED` can receive clean purchase orders. Probationary vendors require special review; inactive vendors are completely barred.
- **Quote Expiry Invariant**: Every quotation defines a `valid_until` date. In normal workflows, purchase order award dates strictly precede quote expiry:
  $$\text{Award Date} \le \text{Quote Validity Expiry Date}$$

---

## 3. Supplier Evaluation & Multicriteria Scoring

### A. Landed Cost Calculation Formula
For every supplier quote line item, total delivered cost is computed in minor currency units:
$$\text{Landed Cost} = (\text{Unit Price} \times \text{Quantity}) + \text{Freight Charges} + \text{Customs Duty} + \text{Non-Recoverable Taxes}$$

### B. Foreign Exchange Determinism
Multi-currency quotations (EUR, GBP, INR, JPY) are converted to base currency (USD) using institutional fixed exchange rates:
$$\text{Landed Cost}_{\text{USD}} = \text{round}\left(\text{Landed Cost}_{\text{Currency}} \times \text{FX Rate}, 2\right)$$

| Currency | FX Rate to USD | Conversion Behavior |
|:---:|:---:|---|
| **USD** | 1.0000 | Native base currency |
| **EUR** | 1.0800 | European Union single currency |
| **GBP** | 1.2700 | British Pound Sterling |
| **INR** | 0.0120 | Indian Rupee |
| **JPY** | 0.0067 | Japanese Yen |

### C. 60 / 25 / 15 Multicriteria Evaluation Model
All quotes for an RFQ are normalized and scored according to configurable strategic weights:
$$\text{Composite Score} = 0.60 \times \text{Cost Score} + 0.25 \times \text{Lead Time Score} + 0.15 \times \text{Risk Score}$$

Where:
- $\text{Cost Score} = \frac{\text{Landed Cost}_{\text{USD}}}{\min(\text{Landed Cost across RFQ})}$
- $\text{Lead Time Score} = \frac{\text{Lead Time Days}}{\min(\text{Lead Time across RFQ})}$
- $\text{Risk Score} = \frac{\text{Supplier Risk Score}}{100.0}$

### D. Award Rationale Governance
- **Default Award**: The quote with the lowest evaluated composite score is awarded the purchase order.
- **Exception Governance**: When a non-cheapest supplier is selected (e.g., due to superior delivery speed or lower operational risk), an explicit audit trail is recorded in `award_rationale` justifying the business decision.

---

## 4. Double-Entry Budget Event Lifecycle

Budgetary accountability follows strict state-based double-entry ledger transactions:

```
[PR Submitted] ────────▶ RESERVE event logged ───▶ Remaining balance pre-allocated
       │
       ├─▶ [PR Rejected] ────────▶ RELEASE event logged ──▶ Funds returned to remaining balance
       │
       └─▶ [PO Issued] ──────────▶ COMMIT event logged  ──▶ Funds locked in committed vendor spend
              │
              └─▶ [Delivery/Receipt] ──▶ SPEND event logged ──▶ Realized cash expenditure
```

### Invariant Equation:
$$\text{Allocated Amount} = \text{Remaining Balance} + \text{Reserved Amount} + \text{Committed Amount} + \text{Spent Amount}$$
- Clean generation path overrun count: **0 violations across all 12 department budgets**.

---

## 5. Split Purchase Evasion Detection

The audit module `validate_split_purchases` in `src/validate/checks.py` protects against threshold structuring:
- **Algorithm**: Examines all requisitions originating from the same `requester_id` within a sliding 3-calendar-day window (`window_days = 3`).
- **Trigger**: Flags requisition clusters where individual purchases remain sub-threshold (e.g., \$1,900 each) but cumulatively breach approval tier boundaries ($\sum > \$2,000$ or $\sum > \$25,000$).
- **Status**: Implemented and verified by unit test `test_validate_split_purchases_auditing`.

---

## 6. Automated Verification Matrix

All business rules are backed by dedicated pytest test suites:

| Domain | Test File | Test Case | Scenario Verified | Status |
|---|---|---|---|:---:|
| **Approvals** | `tests/test_approvals.py` | `test_approval_thresholds_and_tiers` | Normal & boundary limits (\$2k, \$25k) | **PASS** |
| **Approvals** | `tests/test_approvals.py` | `test_rejected_requests_cannot_proceed` | Rejection halts downstream PO issuance | **PASS** |
| **Quotes** | `tests/test_quotes.py` | `test_quote_lines_and_landed_cost_reconciliation` | Landed cost formula & line reconciliation | **PASS** |
| **Scoring** | `tests/test_quotes.py` | `test_multicriteria_scoring_and_lowest_score_award`| 60/25/15 scoring & lowest score award | **PASS** |
| **Quorum** | `tests/test_validation_approvals.py` | `test_detects_insufficient_competitive_quotes`| Detects tenders with $<3$ quotes | **PASS** |
| **Award Rationale**| `tests/test_validation_approvals.py` | `test_detects_non_lowest_score_awarded` | Enforces rationale when non-lowest is awarded | **PASS** |
| **Split Purchase** | `tests/test_validation_approvals.py` | `test_validate_split_purchases_auditing` | Sliding window structuring audit | **PASS** |
| **Budget Ledger** | `tests/test_budget.py` | `test_budget_balances_reconciled_without_overrun`| Double-entry reconciliation equation | **PASS** |

