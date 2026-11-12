# MASTER IMPLEMENTATION PROMPT
## PHASE 5: ANOMALY INJECTION & GROUND TRUTH GENERATION

You are working on the **YottaFlex Procure-to-Pay Synthetic Data Generator**.

Your task is to implement Phase 5 of the project: introduce controlled procurement anomalies into the clean synthetic dataset, generate ground-truth labels, and independently detect those anomalies.

Do not rebuild the project. Extend the existing implementation while preserving all completed work from Phases 1–4.

---

## 1. FIRST: INSPECT THE EXISTING PROJECT

Before writing code:

1. Inspect the complete repository structure.
2. Read the PRD and original master prompt.
3. Review all implementations from Phases 1–4.
4. Run the existing test suite.
5. Confirm that clean synthetic data passes Phase 4 validation.
6. Identify existing entity schemas, ID conventions, data relationships, and validation interfaces.

If any previous phase is incomplete or failing, report the issue before proceeding. Do not silently rewrite working modules.

---

## 2. IMPLEMENT ANOMALY INJECTION

Create:

`src/datagen/anomalies.py`

Implement a modular anomaly-injection engine.

The engine must:
- Accept clean generated datasets as input.
- Use the existing configuration and shared seeded random generator.
- Inject anomalies deterministically.
- Record every injected anomaly in a separate ground-truth structure.
- Preserve all unaffected records.
- Avoid introducing unrelated data-integrity or arithmetic errors.
- Never silently repair an intentionally injected anomaly.

Use post-generation mutations. Do not contaminate the master-data generation logic with anomaly-specific behavior.

### Required anomaly types

Implement all seven anomaly categories defined in the PRD.

**1. PO Without Approval**
- Create a purchase order without the required approval record.
- Preserve the PO and its other valid relationships.
- Ground truth must identify the PO.

**2. Expired Quote Before Award**
- Select a supplier quote whose validity period ends before the award date.
- Preserve the original quote and award relationship.
- Ground truth must identify the affected quote or award record consistently.

**3. Non-Cheapest Quote Without Rationale**
- Award a quote that is not the cheapest eligible quote.
- Leave the justification or award rationale missing.
- Ensure the selected quote was otherwise eligible for comparison.

**4. Inactive Supplier Used**
- Create a purchase order linked to a supplier whose status is inactive.
- Preserve the supplier relationship.
- Ground truth must identify the affected PO.

**5. Budget Overrun**
- Create a transaction that exceeds the available budget.
- Keep the budget ledger arithmetically consistent.
- Do not create artificial calculation errors to simulate an overrun.
- The violation must be the actual business-rule condition that spending commitments exceed the available budget.

**6. Duplicate Purchase Request**
- Create a genuine duplicate purchase request.
- Use the same requester and substantially identical item and quantity within a short time window.
- Keep both records individually valid.
- Ground truth must identify the duplicate record and, where useful, its original counterpart.

**7. Quote Currency Mismatch**
- Create a quote whose currency does not match the RFQ currency.
- Do not provide a valid conversion record for the mismatched quote.
- Preserve valid FX conversions for normal quotes.

---

## 3. ANOMALY RATE AND CONFIGURATION

Use configuration-driven anomaly rates.

Target approximately 3–5% anomalies, consistent with the PRD.

Before implementation:
- Inspect the original PRD's definition of anomaly rate.
- Define the denominator clearly.
- Document whether the rate is calculated using affected transaction records or anomaly cases.
- Avoid double-counting a record affected by multiple anomaly types.
- Ensure each anomaly category is represented at the configured scale.

Support a smaller starter dataset and the full dataset without hardcoding record IDs.

If the dataset does not contain enough eligible records for a particular anomaly, report the shortfall rather than creating invalid references.

---

## 4. GROUND TRUTH GENERATION

Maintain ground truth separately from the operational procurement tables.

Required fields:

| Field | Description |
|---|---|
| anomaly_id | Unique anomaly identifier |
| issue_type | One of the seven anomaly categories |
| entity | Affected entity/table |
| record_id | Affected record identifier |
| expected_decision | Expected detector outcome |
| reason | Explanation of the injected violation |

Additional fields may be added only when they improve traceability and are documented.

Ground truth must:
- Be generated at injection time.
- Have a unique anomaly ID.
- Reference existing records.
- Include every injected anomaly.
- Never contain anomalies that were not actually injected.
- Remain separate from the operational dataset.

Do not let anomaly detectors read ground truth.

---

## 5. INDEPENDENT ANOMALY DETECTION

Implement independent anomaly detection in:

`src/validate/anomaly_checks.py`

You may extend the existing validation framework if its architecture requires it.

Create a detector for each of the seven anomaly types.

Critical rule:

**Detectors must inspect procurement data and business rules independently. They must never read ground_truth, anomaly-injector metadata, or injection flags to decide whether a violation exists.**

The detector should return structured findings containing:

- issue_type
- entity
- record_id
- detected
- reason

The detection logic must distinguish genuine violations from legitimate procurement scenarios.

Examples:
- A valid single-source purchase with a documented reason must not be flagged.
- A rejected request due to insufficient budget must not be flagged as a budget overrun.
- A non-cheapest award with a valid documented rationale must not be flagged.
- A valid foreign-currency quote with a valid conversion must not be flagged.
- An inactive supplier that is not used for a new PO must not be flagged.

---

## 6. DETECTION EVALUATION

Create an evaluation function that compares detector output against ground truth.

Calculate:

- True Positives (TP)
- False Positives (FP)
- False Negatives (FN)
- Precision
- Recall
- Detection rate

Calculate metrics:
1. Overall
2. Separately for each anomaly category

Target 100% precision and 100% recall on the controlled anomalies injected by this generator.

Do not manipulate detector output to achieve these metrics. Fix the underlying detection logic if results do not match.

The evaluation process may read ground truth. The anomaly detectors themselves may not.

---

## 7. VALIDATION MODES

Preserve the clean-data validation behavior implemented in Phase 4.

Provide two clearly separated validation modes:

**Clean mode**
- Expects zero injected anomalies.
- Must pass on the original clean dataset.
- Must fail when intentional anomaly violations are present.

**Anomaly-aware mode**
- Runs independent anomaly detectors.
- Reports detected anomalies.
- Compares findings against ground truth only in the evaluation step.
- Reports any unlabelled violations or missed injected anomalies.

Do not weaken Phase 4 integrity, foreign-key, financial, date, or lifecycle checks simply to make anomaly-injected data pass.

Intentional anomalies should be reported as business-rule violations, not silently ignored.

---

## 8. TESTING

Create or extend:

- `tests/test_anomaly_injection.py`
- `tests/test_anomaly_detection.py`
- `tests/test_ground_truth.py`
- `tests/test_anomaly_metrics.py`
- `tests/test_anomaly_determinism.py`

Test the following:

1. Each of the seven anomalies can be injected.
2. Every injected anomaly receives a ground-truth record.
3. Ground-truth IDs are unique.
4. Ground-truth references resolve to existing records.
5. Detectors identify all seven anomaly types.
6. Detectors do not use ground truth.
7. Clean datasets produce zero anomaly findings.
8. Legitimate procurement exceptions are not falsely flagged.
9. Repeated execution with the same seed produces identical anomalies and ground truth.
10. Different seeds can produce different anomaly selections.
11. Precision and recall are calculated correctly.
12. Multiple anomaly types affecting one record do not cause incorrect rate calculations.

Use small deterministic fixtures for individual tests and a realistic integration dataset for end-to-end testing.

Never inject anomalies into the permanent clean fixture used by Phase 4 tests.

---

## 9. DOCUMENTATION

Update:

- `docs/anomaly_catalog.md`
- `docs/validation_summary.md`
- `docs/architecture.md`
- `docs/prompt_history.md`
- `AI_USAGE.md`
- `README.md`

Document:
- All seven anomaly definitions.
- Injection methodology.
- Anomaly-rate denominator.
- Ground-truth schema.
- Independent detection methodology.
- Precision and recall calculations.
- Known limitations and assumptions.
- How to run anomaly injection and evaluation.

Keep the implementation transparent and reproducible.

---

## 10. CLI AND EXECUTION

Integrate Phase 5 with the existing CLI.

Provide commands consistent with the existing project architecture to:

1. Generate clean data.
2. Inject configured anomalies.
3. Run independent anomaly detection.
4. Evaluate detector output against ground truth.
5. Print a readable summary.

Do not invent a second competing CLI architecture.

Do not implement final CSV/JSON export in this phase unless the existing architecture requires an intermediate format. Final deliverables and exports belong to Phase 6.

---

## 11. DEFINITION OF DONE

Phase 5 is complete only when:

- All seven anomaly types are implemented.
- Injection is deterministic.
- Ground truth is complete and separate.
- Detectors operate independently of ground truth.
- Clean and anomaly-aware validation modes work.
- Precision and recall are calculated correctly.
- Controlled anomalies achieve 100% precision and recall.
- Existing Phase 1–4 tests continue to pass.
- Documentation is updated.
- No external data, scraping, ML models, or unrelated features are introduced.

---

## 12. FINAL REPORT

After implementation, provide:

1. Files created and modified.
2. Architecture and implementation summary.
3. Number of anomalies injected by category.
4. Ground-truth record count.
5. Overall precision and recall.
6. Per-category precision and recall.
7. Existing and new test results.
8. Any known limitations.
9. Exact commands to reproduce Phase 5.

Run the full test suite before declaring completion.

**STOP AFTER PHASE 5. Do not start Phase 6 until I explicitly approve it.**
