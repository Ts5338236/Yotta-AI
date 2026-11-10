# AI Usage & Governance Declaration

This document transparently records how Artificial Intelligence (AI) tools were employed in the architectural design, schema drafting, and code implementation of the Procure-to-Pay Synthetic Data Generator.

---

## 1. AI Tools Utilized

- **AI Model**: Antigravity Assistant (Google DeepMind - Gemini 3.8 Flash).
- **Execution Environment**: Windows 11 PowerShell pair-programming environment.
- **Reference Implementation Prompts**:
  - Phase 1: `ai/prompts/01_phase1_foundation.md`
  - Phase 2: `ai/prompts/02_phase2_generation.md`

---

## 2. AI Assistance in Phase 2 Implementation

AI assisted in the following Phase 2 modules:
- **Master Data Generation (`src/datagen/masters.py`)**:
  - Designing an acyclic hierarchical reporting tree (DAG) for requesters ensuring top-level leaders have `manager_id = None` and subordinates report to senior managers within the same department.
  - Formulating realistic synthetic name, cost center, and supplier profile generators.
  - Enforcing consistent budget allocations across departments.
- **Purchase Requisition Engine (`src/datagen/requests.py`)**:
  - Implementing category-specific log-normal price generation bounded by minimum and maximum thresholds.
  - Simulating 2026 calendar seasonality with monthly probability distributions.
  - Implementing exact financial reconciliation where `total_estimate_usd` is strictly derived from the sum of request lines.
- **Configuration & Validation Expansion**:
  - Updating `config/default.yaml` and `src/datagen/config.py` with schema validation for `category_distributions` and `seasonality`.
- **Test Suite Expansion (`tests/`)**:
  - Drafting 15 comprehensive unit tests across 4 new test modules: `test_masters.py`, `test_requests.py`, `test_determinism.py`, and `test_distributions.py`.

---

## 3. Verification & Testing of Generated Code

- **Automated Test Execution**: All 46 automated tests were executed using `pytest -v` and passed with 100% pass rate (46/46 passed in 4.22 seconds).
- **Determinism Verification**: Automated tests confirmed that identical seeds produce 100% identical record structures, dates, prices, and IDs.
- **CLI Verification**: The CLI data generator (`python -m datagen --generate --scale starter` and `python -m datagen --generate --scale full`) was executed and verified against scale targets.

---

## 4. Items Requiring Human Review (TODO)

The following items are designated for human developer evaluation and sign-off:

- [ ] **TODO: Human Assessment of Category Log-Normal Parameters**: Verify whether the log_mean, log_sigma, min_price, and max_price bounds for the 10 categories meet downstream testing expectations.
- [ ] **TODO: Human Assessment of Seasonal Weights**: Confirm whether the Q4 year-end budget exhaustion weighting matches desired domain realism.
- [ ] **TODO: Human Approval for Phase 3 Transition**: Explicit developer approval required prior to beginning Phase 3 (RFQ and Supplier Quotation generation).

---

## 5. Known Limitations (Phase 2)

1. **Pre-Approval Workflow Only**: Requisitions generated in Phase 2 are restricted to `DRAFT` and `SUBMITTED` states; approval events and state transitions occur in Phase 4.
2. **In-Memory Datasets**: Data is generated in-memory; database persistence and bulk ingestion occur in later pipeline phases.
3. **No Sourcing or PO Records in Phase 2**: RFQs, supplier quotes, purchase orders, and deliveries are intentionally deferred to Phase 3 through Phase 5.
