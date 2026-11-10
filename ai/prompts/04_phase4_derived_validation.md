# MASTER IMPLEMENTATION PROMPT
# PHASE 4: DERIVED FIELDS ENGINE AND COMPREHENSIVE VALIDATION

## Procure-to-Pay Synthetic Data Generator
### YottaFlex AI | Technical Coding Round

---

# 1. ROLE AND RESPONSIBILITY

Act as a Senior Python Data Engineer, Data Quality Architect, Database Validation Specialist, and Financial Reconciliation Engineer.

You are continuing the existing Procure-to-Pay Synthetic Data Generator project.

Previous phases established:

Phase 1:
- Project architecture.
- Configuration management.
- IDFactory.
- FX conversion.
- SQLite schema.
- Foundational validation.

Phase 2:
- Department generation.
- Budget generation.
- Requester generation.
- Supplier generation.
- Purchase Request generation.
- Request Line generation.
- Category-based pricing.
- Seasonal generation.

Phase 3:
- Approval generation.
- RFQ generation.
- Supplier invitations.
- Supplier quotations.
- QuoteLine generation.
- Landed-cost calculation.
- Supplier scoring.
- Quote awards.
- Purchase Orders.
- PurchaseOrderLines.
- Deliveries.
- BudgetEvent ledger.
- StatusEvent history.

Your responsibility is to implement Phase 4 only.

The primary objectives are:

1. Centralize all derived field calculations.
2. Recalculate derived values from original source records.
3. Implement comprehensive independent validation.
4. Verify financial reconciliation.
5. Verify foreign-key integrity.
6. Verify lifecycle consistency.
7. Verify business-rule compliance.
8. Prove that the clean procurement dataset contains zero unintended anomalies.

Do not implement anomaly injection in this phase.

---

# 2. FIRST ACTION: INSPECT THE EXISTING PROJECT

Before modifying anything:

1. Inspect the complete repository.
2. Read the original PRD.
3. Read all previous implementation prompts.
4. Inspect Phase 1 implementation.
5. Inspect Phase 2 implementation.
6. Inspect Phase 3 implementation.
7. Run all existing tests.
8. Inspect the existing data structures.
9. Inspect the database schema.
10. Inspect all derived calculations currently implemented.
11. Inspect the budget ledger.
12. Inspect StatusEvent records.
13. Check Git status.

Identify duplicated calculations and inconsistencies.

If previous phases contain failing tests, report them before proceeding.

Do not silently rewrite working modules.

Preserve existing architecture and functionality.

If any business rule is ambiguous, document the assumption rather than inventing an official requirement.

---

# 3. REQUIRED MODULES

Create or extend:

src/datagen/derive.py

src/validate/checks.py

src/validate/__main__.py

src/validate/__init__.py

Create supporting validation modules only when necessary.

The derive.py module must be responsible for centralized derived-field calculations.

The validate package must independently verify the generated results.

Do not combine derivation and validation into one function.

The validator must independently recalculate expected values rather than trusting already-derived fields.

---

# 4. DERIVED FIELDS ENGINE

Implement derive.py.

Required responsibilities:

- RequestLine calculations.
- PurchaseRequest totals.
- Supplier quotation landed costs.
- Supplier scores.
- PurchaseOrderLine totals.
- PurchaseOrder values.
- Delivery summaries.
- Current lifecycle statuses.
- Budget balances.
- Derived delivery metrics.

Create modular functions.

Suggested interfaces:

derive_request_line_totals(...)
derive_purchase_request_totals(...)
derive_quote_landed_costs(...)
derive_supplier_scores(...)
derive_purchase_order_line_totals(...)
derive_purchase_order_totals(...)
derive_delivery_summaries(...)
derive_current_statuses(...)
derive_budget_balances(...)
derive_all(...)

Use the existing project data structures and interfaces.

Do not introduce duplicate entity models unnecessarily.

## Important rule

Every derived field must be recalculated from its source records.

Examples:

PurchaseRequest.total_estimate_usd =
SUM(RequestLine.line_total)

PurchaseOrder.value =
SUM(PurchaseOrderLine.line_total)

SupplierQuote.landed_cost_base =
Converted total of quoted line values plus applicable freight, duty and non-recoverable tax.

Budget balances =
Calculated from the BudgetEvent ledger.

Current entity status =
Latest valid StatusEvent.

Delivery completion =
Calculated from cumulative received quantities compared with ordered quantities.

Do not independently generate any of these values.

Use Decimal or the existing fixed-precision financial representation.

Avoid floating-point financial calculations.

---

# 5. FINANCIAL RECONCILIATION

Implement complete arithmetic validation.

## A. Request lines

Verify:

line_total = quantity * unit_price

## B. Purchase requests

Verify:

request_total = SUM(request_line_totals)

## C. Supplier quotations

Verify:

quote line totals match quoted quantities and unit prices.

Verify:

landed_cost =
quoted merchandise total + freight + duty + non-recoverable tax

Verify FX conversion using the existing fixed FX engine.

Ensure that freight, duty and tax are not counted twice.

## D. Supplier scoring

Verify:

score =
0.60 * landed_cost_normalized
+ 0.25 * lead_time_normalized
+ 0.15 * risk_normalized

Use the actual configured scoring weights.

Ensure normalized values are within [0, 1].

## E. Purchase orders

Verify:

PO value = SUM(PO line totals)

For competitive sourcing:

PO lines must reconcile with the awarded quotation lines.

For non-competitive sourcing:

PO lines must reconcile with their original request lines and documented sourcing prices.

## F. Delivery

Verify:

Total received quantity <= ordered quantity

for clean-path transactions.

Fully delivered orders must have received quantities equal to ordered quantities.

## G. Budget

Recalculate:

Reserved balance from reservation and release events.

Committed balance from commitment and release/adjustment events according to the documented accounting convention.

Spent balance from expenditure events.

Verify:

allocated >= reserved + committed

for all clean-path budgets.

Do not silently repair financial inconsistencies.

Report discrepancies.

---

# 6. PRIMARY KEY AND ID VALIDATION

Implement validation for every entity.

Check:

- Primary-key uniqueness.
- Null primary keys.
- Empty identifiers.
- Expected ID format.
- Correct fiscal year where applicable.
- Delivery ID format.
- Duplicate business identifiers.
- Duplicate supplier codes.
- Duplicate RFQ and supplier invitation combinations.

Use the existing IDFactory regex patterns.

Do not create a separate conflicting ID format definition.

Every invalid record must be reported with:

- Entity.
- Record ID.
- Field.
- Actual value.
- Expected rule.
- Severity.

---

# 7. FOREIGN KEY VALIDATION

Verify every relationship.

Required checks:

- Budget.department_id references Department.
- Requester.department_id references Department.
- PurchaseRequest.requester_id references Requester.
- PurchaseRequest.department_id matches Requester's department.
- PurchaseRequest.budget_id references Budget.
- RequestLine.request_id references PurchaseRequest.
- RFQ.request_id references PurchaseRequest.
- RFQSupplierInvite.rfq_id references RFQ.
- RFQSupplierInvite.supplier_id references Supplier.
- SupplierQuote.rfq_id references RFQ.
- SupplierQuote.supplier_id references invited Supplier.
- QuoteLine.quote_id references SupplierQuote.
- QuoteLine.request_line_id references the correct request.
- Approval.request_id references PurchaseRequest.
- Approval.approver_id references Approver.
- PurchaseOrder.request_id references PurchaseRequest.
- PurchaseOrder.quote_id references the awarded quote when competitive.
- PurchaseOrder.supplier_id references Supplier.
- PurchaseOrderLine.po_id references PurchaseOrder.
- PurchaseOrderLine.request_line_id references RequestLine.
- Delivery.po_id references PurchaseOrder.
- BudgetEvent.budget_id references Budget.
- StatusEvent references valid entities and records.

Check cross-table relationships, not just the existence of foreign keys.

Where SQLite can enforce the rule, also use PRAGMA foreign_key_check.

Report every invalid relationship separately.

---

# 8. LIFECYCLE STATE MACHINE VALIDATION

Implement independent state-machine validation.

## PurchaseRequest

Allowed lifecycle:

DRAFT
SUBMITTED
PENDING_APPROVAL
APPROVED or REJECTED
SOURCING
PO_ISSUED
PARTIALLY_DELIVERED
DELIVERED
CLOSED

Pre-PO states may transition to CANCELLED where permitted.

Validate:

- Every transition is allowed.
- No skipped mandatory approval state.
- Rejected requests cannot receive POs.
- Cancelled requests cannot receive new POs.
- Current status equals the latest StatusEvent.

## RFQ

Define and validate allowed RFQ transitions based on the existing implementation.

## PurchaseOrder

Define and validate:

DRAFT
ISSUED
PARTIALLY_DELIVERED
DELIVERED
CLOSED
CANCELLED

Use only transitions supported by the implemented workflow.

## Delivery

Validate its documented shipment lifecycle.

For all entities:

- Event timestamps must be chronological.
- Every event must reference an existing entity.
- The final event must match the current status.
- Previous status must match the preceding event's new status.

Do not modify source events to make validation pass.

---

# 9. DATE ORDERING VALIDATION

Validate transaction chronology.

Expected order:

Purchase Request Creation
< Approval
< RFQ Issue
< Supplier Quote Submission
< Award
< Purchase Order
< Shipment
< Delivery Receipt

Apply only relevant events to each sourcing path.

Additional checks:

- Request date must fall within 2026.
- Approval date must not precede request submission.
- RFQ close date must follow issue date.
- Quote submission must follow RFQ issue.
- Award must not occur after quote expiry.
- PO date must follow required approvals.
- Shipment date must not precede PO date.
- Received date must not precede shipment date.
- Delivery must not precede PO issuance.

Use fixed date boundaries.

Do not use the current system date.

---

# 10. APPROVAL AND PROCUREMENT BUSINESS RULE VALIDATION

Verify approval thresholds.

Up to and including $2,000:
- Line manager approval.

Above $2,000 and up to $25,000:
- Department head approval.

Above $25,000:
- Department head and Finance approvals.

Verify:

- Required approver roles.
- Correct approval decisions.
- Approval completion before PO creation.
- Rejected requests do not proceed to PO.
- Only eligible sourcing paths receive RFQs.
- Competitive sourcing has at least three valid quotations.
- Single-source POs have valid reason codes.
- Contract sourcing has documented justification.
- Only eligible suppliers receive quotations and POs.
- Competitive POs reference awarded quotations.
- Awarded quotations belong to the corresponding RFQ.

Treat thresholds and weights as documented project assumptions.

---

# 11. SUPPLIER QUOTE AND AWARD VALIDATION

Independently verify:

- Quote belongs to RFQ.
- Supplier was invited.
- Quote contains required request lines.
- Quote quantity is correct.
- Quote currency is supported.
- FX conversion is correct.
- Quote has not expired before award.
- Supplier is eligible on award date.
- Lowest-scoring eligible quote wins in the clean path.
- Award rationale is consistent with the selection.

Do not use existing award decisions as proof that the award is correct.

Recalculate the expected winner independently.

---

# 12. BUDGET LEDGER VALIDATION

Treat BudgetEvent as the source of truth for budget balances.

Reconstruct balances by processing events chronologically.

Validate:

- Initial allocations.
- Reservations.
- Commitments.
- Releases.
- Synthetic expenditure.
- Event references.
- Event dates.
- Event amount signs.
- No invalid balance transitions.
- No clean-path overrun.

Compare independently calculated balances with Budget table balances.

Report differences.

Do not update balances silently during validation.

---

# 13. VALIDATION REPORTING

Generate:

docs/validation_summary.md

docs/validation_summary.json

The report should contain:

- Overall validation status.
- Total checks.
- Passed checks.
- Failed checks.
- Warning count.
- Entity counts.
- Primary-key results.
- Foreign-key results.
- Arithmetic results.
- Date-ordering results.
- State-machine results.
- Approval results.
- Supplier eligibility results.
- Quote and award results.
- Budget reconciliation results.
- Delivery reconciliation results.

For every failure, include:

- Check name.
- Entity.
- Record ID.
- Description.
- Expected value.
- Actual value.
- Severity.

Suggested JSON structure:

{
  "status": "PASS",
  "summary": {
    "total_checks": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0
  },
  "entities": {},
  "checks": [],
  "failures": [],
  "warnings": []
}

This is a structural example. Implement a proper deterministic JSON report.

The validator must return a non-zero exit code if critical checks fail.

Warnings must not be silently treated as successful validation.

---

# 14. INDEPENDENT VALIDATION REQUIREMENT

The validator must not simply trust the derived fields engine.

For example:

The derivation engine calculates:

PurchaseOrder.value = SUM(PO lines)

The validator must independently calculate the same expected value from the source records and compare it with the stored value.

Use separate validation logic.

Do not simply call derive.py from every validation function and compare the output to itself.

Avoid circular validation.

---

# 15. TESTING REQUIREMENTS

Create:

tests/test_derive.py
tests/test_validation_primary_keys.py
tests/test_validation_foreign_keys.py
tests/test_validation_financial.py
tests/test_validation_dates.py
tests/test_validation_lifecycle.py
tests/test_validation_approvals.py
tests/test_validation_budget.py
tests/test_validation_integration.py

Test:

1. Correct calculations.
2. Incorrect calculations.
3. Duplicate IDs.
4. Missing foreign keys.
5. Invalid enum values.
6. Invalid date sequences.
7. Invalid lifecycle transitions.
8. Incorrect approval levels.
9. Incorrect quote scoring.
10. Invalid PO totals.
11. Budget balance discrepancies.
12. Delivery quantity discrepancies.

Use intentionally corrupted test fixtures to prove the validator detects errors.

IMPORTANT:

These corrupted fixtures are test-only.

Do not inject anomalies into the production clean dataset.

Run all tests from previous phases.

---

# 16. CLI INTEGRATION

Integrate the validation command:

python -m validate data/

Use the existing CLI architecture.

If the generated data is currently in memory rather than exported files, provide a compatible validation interface for the existing workflow.

Do not implement the final CSV, JSON and SQL export engine yet.

Do not break future Phase 6 export compatibility.

---

# 17. DOCUMENTATION

Update:

README.md
docs/architecture.md
docs/data_dictionary.md
docs/assumptions.md
docs/validation_summary.md
docs/AI_USAGE.md

Document:

- Derived-field calculation methodology.
- Financial reconciliation.
- Validation architecture.
- Validation severity levels.
- State machine rules.
- Budget reconciliation methodology.
- Date validation.
- Known limitations.

Save this prompt verbatim at:

ai/prompts/04_phase4_derived_validation.md

Preserve previous prompt history.

---

# 18. PHASE 4 DEFINITION OF DONE

[ ] Phase 1 tests pass.

[ ] Phase 2 tests pass.

[ ] Phase 3 tests pass.

[ ] derive.py implemented.

[ ] All derived values centralized.

[ ] Request totals reconcile.

[ ] Quote landed costs reconcile.

[ ] Supplier scores reconcile.

[ ] PO totals reconcile.

[ ] Delivery quantities reconcile.

[ ] Budget balances reconcile.

[ ] Primary-key validation works.

[ ] Foreign-key validation works.

[ ] Date validation works.

[ ] State-machine validation works.

[ ] Approval validation works.

[ ] Supplier eligibility validation works.

[ ] Award selection validation works.

[ ] Machine-readable validation report generated.

[ ] Corrupted test fixtures are detected.

[ ] Clean procurement dataset passes all critical checks.

[ ] No intentionally injected anomalies exist.

[ ] All tests pass.

[ ] Documentation updated.

---

# 19. STRICT SCOPE CONTROL

DO NOT IMPLEMENT:

- Anomaly injection.
- Ground-truth generation.
- The seven required anomaly injectors.
- Independent anomaly detectors for the seven required cases.
- Precision and recall calculations against ground truth.
- CSV/JSON/SQL final export engine.
- Final reproducibility report.

These belong to Phase 5 and Phase 6.

---

# 20. EXECUTION PROCESS

Follow this exact sequence:

STEP 1: Inspect all previous phases.

STEP 2: Run all existing tests.

STEP 3: Identify duplicate calculations.

STEP 4: Implement derive.py.

STEP 5: Centralize derived-field calculations.

STEP 6: Implement independent validation checks.

STEP 7: Implement financial reconciliation.

STEP 8: Implement relationship validation.

STEP 9: Implement lifecycle and date validation.

STEP 10: Implement budget validation.

STEP 11: Implement validation reports.

STEP 12: Create corrupted test fixtures.

STEP 13: Run all project tests.

STEP 14: Generate and validate clean starter-scale data.

STEP 15: Run full-scale validation if practical.

STEP 16: Update documentation.

STEP 17: Review Git changes.

STEP 18: Provide the final implementation report.

The final report must contain:

1. Files created.
2. Files modified.
3. Derived fields implemented.
4. Number of validation checks.
5. Passed checks.
6. Failed checks.
7. Warnings.
8. Financial reconciliation results.
9. Foreign-key validation results.
10. Lifecycle validation results.
11. Budget validation results.
12. Corrupted fixture detection results.
13. Test results.
14. Known limitations.
15. Proposed conventional Git commit.

Never fabricate validation results.

If the clean dataset fails validation, report the actual failures.

Do not silently repair invalid data.

Create a Git commit only after reviewing the working tree and confirming tests pass. Do not push to GitHub without my approval.

STOP AFTER PHASE 4.

Wait for my explicit approval before beginning Phase 5.
