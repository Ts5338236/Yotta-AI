# MASTER IMPLEMENTATION PROMPT
# PHASE 3: COMPLETE PROCUREMENT WORKFLOW

## Procure-to-Pay Synthetic Data Generator
### YottaFlex AI | Technical Coding Round

---

# 1. ROLE AND RESPONSIBILITY

Act as a Senior Python Data Engineer, Procurement Systems Architect, and Business Workflow Engineer.

You are continuing the existing Procure-to-Pay Synthetic Data Generator project.

Phases 1 and 2 established:

- Python project architecture.
- Configuration management.
- Centralized ID generation.
- Fixed FX conversion engine.
- SQLite database schema.
- Department generation.
- Budget generation.
- Requester generation.
- Supplier generation.
- Purchase Request generation.
- Request Line generation.
- Category-based pricing.
- Seasonal generation.
- Deterministic RNG.

Your responsibility is to implement Phase 3 only.

Phase 3 implements the complete CLEAN procurement workflow.

The goal is to transform generated purchase requests into realistic procurement transactions with approvals, sourcing, quotations, awards, purchase orders, deliveries and budget events.

IMPORTANT:

Do not implement anomaly injection in this phase.

Clean procurement records must follow all defined business rules.

---

# 2. FIRST ACTION: INSPECT THE EXISTING PROJECT

Before writing code:

1. Inspect the entire repository.
2. Read the original PRD.
3. Read the original master prompt.
4. Inspect Phase 1 implementation.
5. Inspect Phase 2 implementation.
6. Run all existing tests.
7. Inspect the existing database schema.
8. Inspect the IDFactory.
9. Inspect configuration management.
10. Inspect FX conversion.
11. Inspect generated master datasets.
12. Inspect purchase request and request line relationships.
13. Check Git status.

Do not blindly rewrite existing code.

If Phase 1 or Phase 2 tests fail, identify the issues and report them before continuing.

Preserve existing working functionality.

If the existing schema is insufficient for the required workflow, propose the smallest justified migration and document it before changing the schema.

---

# 3. HARD TECHNICAL CONSTRAINTS

Use:

- Python 3.11+
- NumPy
- Pandas
- SQLite
- Decimal for financial calculations
- Existing YAML configuration
- Existing IDFactory
- Existing FX engine
- pytest

DETERMINISM:

1. Create one numpy.random.default_rng(seed) in the generation entry point.
2. Pass the same RNG explicitly to every generation function.
3. Never create independent RNG instances inside modules.
4. Never use global random state.
5. Never use datetime.now() or datetime.today().
6. Use fixed base date 2026-01-01.
7. Generate dates within the 2026 dataset period.
8. Sort records consistently.
9. Keep IDs deterministic.
10. Same seed and configuration must produce identical workflow records.

Do not introduce live APIs, external data or real supplier information.

All supplier, approver and procurement records must remain synthetic.

---

# 4. REQUIRED MODULES

Implement or extend the following modules:

src/datagen/approvals.py
src/datagen/sourcing.py
src/datagen/orders.py
src/datagen/delivery.py
src/datagen/budget.py

Preserve existing:

masters.py
requests.py
ids.py
config.py
fx.py

Add supporting utilities only when required.

Responsibilities:

approvals.py:
- Generate approval events.
- Apply approval thresholds.
- Resolve approver roles.
- Handle approved and rejected requests.

sourcing.py:
- Classify sourcing paths.
- Generate RFQs.
- Generate supplier invitations.
- Generate supplier quotes.
- Generate QuoteLines.
- Calculate landed costs.
- Evaluate quotations.
- Award suppliers.

orders.py:
- Generate purchase orders.
- Generate purchase order lines.
- Connect awarded quotes to POs.
- Handle non-competitive POs.

delivery.py:
- Generate shipment records.
- Support partial deliveries.
- Calculate delivery status.

budget.py:
- Generate budget ledger events.
- Reserve budgets.
- Commit budgets.
- Release budgets.
- Record synthetic expenditure.
- Reconcile budget balances.

Keep all modules modular and testable.

---

# 5. APPROVAL ENGINE

Implement approval generation.

Use these configurable thresholds:

Estimated purchase request total in USD:

A. Up to and including $2,000:
- Line manager approval.
- Direct purchase order.
- No RFQ required.

B. Above $2,000 and up to $25,000:
- Department head approval.
- Competitive RFQ with at least 3 supplier quotes.

C. Above $25,000:
- Department head approval.
- Finance approval.
- Competitive RFQ with at least 3 supplier quotes.

These are project assumptions from the PRD, not official externally verified procurement policies.

Fields:

- approval_id
- request_id
- approver_id
- level
- decision
- decided_at

Requirements:

1. Generate approval events for each eligible request.
2. Use valid approvers.
3. Ensure the approver has the appropriate role.
4. Preserve approval history.
5. Do not overwrite previous approval events.
6. Ensure timestamps are in valid chronological order.
7. A rejected request must not proceed to PO creation.
8. A request requiring two approvals must receive both before sourcing.
9. An approved request must have all required approval events.
10. Every approval must reference a valid request and approver.

Allowed decisions:

APPROVED
REJECTED

Only fully approved requests may proceed to purchase order creation.

Generate some correctly rejected requests as natural business variation.

Do not create intentionally invalid approval records.

---

# 6. SOURCING PATH CLASSIFICATION

Implement sourcing classification.

Supported sourcing paths:

1. competitive
2. catalogue
3. single_source
4. contract

Business rules:

- Low-value approved purchases may follow catalogue/direct sourcing.
- Competitive sourcing requires RFQ and quotations.
- Single-source sourcing requires a valid reason code.
- Contract sourcing requires a valid contract-based justification.
- Every non-competitive purchase must have a documented sourcing reason where required.

Allowed single-source reason codes:

- sole_supplier
- urgent
- contract

Document the sourcing assumptions.

Full-scale targets from the PRD:

- Approximately 900 purchase orders.
- Approximately 500 competitive RFQs.
- Approximately 1,500 supplier quotations.
- Approximately 400 non-competitive purchase orders.

Starter scale should follow the corresponding configured proportions.

Treat these as target volumes rather than silently forcing inconsistent transactions.

If exact volumes conflict with eligibility or approval rules, report the discrepancy rather than fabricating relationships.

---

# 7. RFQ GENERATION

Implement RFQ generation.

Fields:

- rfq_id
- request_id
- currency
- issue_date
- close_date
- status

Requirements:

1. One RFQ per eligible purchase request.
2. RFQ must reference a valid approved purchase request.
3. Only requests eligible for competitive sourcing receive RFQs.
4. RFQ dates must follow request and approval dates.
5. Close date must be after issue date.
6. Use valid currency codes.
7. RFQ IDs must come from IDFactory.
8. Only valid supplier invitations may be associated with RFQs.

Generate approximately 500 RFQs at full scale, subject to valid transaction eligibility.

---

# 8. SUPPLIER INVITATIONS

Implement RFQSupplierInvite generation.

Fields:

- invite_id
- rfq_id
- supplier_id
- invited_at
- response_status

Requirements:

- Invite 3 to 6 suppliers per competitive RFQ.
- Suppliers must be eligible and active at invitation time.
- No duplicate RFQ and supplier combinations.
- All invited suppliers must exist.
- Use deterministic supplier selection.
- Invitation timestamps must follow RFQ issue dates.

Every generated competitive RFQ should have at least three valid supplier invitations and three valid quotations.

Do not invite blocked or inactive suppliers.

---

# 9. SUPPLIER QUOTATIONS

Implement SupplierQuote generation.

Fields:

- quote_id
- rfq_id
- supplier_id
- freight
- duty
- tax_nonrecoverable
- lead_time_days
- valid_until
- currency
- landed_cost_base
- score

Quote-level fields must be stored consistently with the existing schema.

Implement QuoteLine records.

Fields:

- quote_line_id
- quote_id
- request_line_id
- quantity
- unit_price
- line_total

Requirements:

1. Every quotation references a valid RFQ.
2. Supplier must have an invitation for that RFQ.
3. Supplier must be eligible on quotation submission date.
4. Every quotation must contain all required request lines.
5. Quoted quantities must match requested quantities in the clean path.
6. Unit prices must be positive.
7. Quote currency must be supported.
8. Quote validity must be after quote submission.
9. All IDs must come from IDFactory.
10. All monetary values must use consistent precision.

Generate approximately 1,500 quotations at full scale.

Most RFQs should receive three quotations, while some receive four to six.

---

# 10. LANDED COST CALCULATION

Implement deterministic landed-cost calculation.

Formula:

Landed Cost =
(Quoted Unit Price × Quantity)
+ Freight
+ Duty
+ Non-recoverable Tax

Convert the total into USD using the existing fixed FX engine.

Important:

- Calculate at quotation level.
- Aggregate QuoteLine totals correctly.
- Apply freight, duty and tax consistently.
- Avoid double-counting charges.
- Use Decimal.
- Round according to the established financial precision.
- Never use live FX rates.

For comparison across quotations, calculate landed cost using the same requested quantities and a consistent allocation methodology.

Document how quotation-level charges are allocated or aggregated.

---

# 11. SUPPLIER SCORING AND QUOTE AWARD

Implement the scoring model.

Weights:

- Landed cost: 60%
- Lead time: 25%
- Supplier risk: 15%

Formula:

supplier_score =
0.60 * landed_cost_normalized
+ 0.25 * lead_time_normalized
+ 0.15 * risk_normalized

Lower score is better.

Normalization:

- Normalize values within each RFQ's competing quotations.
- Handle identical minimum and maximum values safely.
- Ensure all normalized values fall within [0, 1].
- Ensure all components use consistent direction.
- Lower landed cost, shorter lead time and lower risk must receive better scores.

Award rules:

1. Lowest valid score wins by default.
2. Award must occur on or before quotation expiry.
3. Supplier must be active on award date.
4. Record award rationale.
5. Save the selected quote reference.
6. Ensure the selected quotation belongs to the RFQ.
7. Ensure the winning supplier has a valid invitation.

For clean-path records, the selected quotation must be the lowest-scoring eligible quotation.

Do not introduce non-cheapest awards without rationale in Phase 3.

That anomaly belongs to Phase 5.

---

# 12. PURCHASE ORDER GENERATION

Implement PurchaseOrder generation.

Fields:

- po_id
- request_id
- quote_id
- supplier_id
- po_date
- value
- sourcing_path
- single_source_reason_code
- award_rationale
- status

Requirements:

1. Only fully approved requests can receive POs.
2. Competitive POs must reference the awarded quote.
3. Non-competitive POs may have a NULL quote_id.
4. Supplier must be eligible and active on PO date.
5. PO date must follow required approval and award events.
6. PO value must be derived from PO lines.
7. Every PO must have at least one PO line.
8. Every competitive PO must reference the correct awarded supplier.
9. Non-competitive sourcing must have appropriate documented reasons.
10. No duplicate PO for a purchase request unless the business model explicitly supports it.

Generate approximately 900 POs at full scale, with approximately 500 competitive and 400 non-competitive paths.

Use configuration to control target volumes.

---

# 13. PURCHASE ORDER LINE GENERATION

Implement PurchaseOrderLine.

Fields should include:

- po_line_id
- po_id
- request_line_id
- quote_line_id
- quantity
- unit_price
- line_total

Requirements:

- Competitive PO lines must derive from the awarded QuoteLines.
- Non-competitive PO lines must derive from the original request lines and documented synthetic sourcing prices.
- Quantities must reconcile with the corresponding request lines.
- All monetary values must be consistent.
- PO value must equal the sum of PO line totals.
- Prevent duplicate request lines within the same PO unless explicitly justified.

Use the same financial precision as Phase 1 and Phase 2.

---

# 14. DELIVERY GENERATION

Implement Delivery generation.

Fields:

- delivery_id
- po_id
- ship_date
- received_date
- qty_received
- status

Requirements:

1. Every delivery references an existing PO.
2. Delivery dates must follow PO dates.
3. Support multiple shipments per PO.
4. Support partial deliveries.
5. Received quantities must be positive.
6. Cumulative delivered quantity must not exceed PO quantity in the clean path.
7. All fully delivered orders must reconcile with ordered quantities.
8. Delivery IDs must use the existing IDFactory.

Use configurable delivery patterns.

Suggested clean-path distribution:

- Approximately 80% on-time deliveries.
- Remaining deliveries may be late, partial or multiple-shipment cases.

These are synthetic assumptions.

Define clear delivery status values, for example:

IN_TRANSIT
PARTIALLY_RECEIVED
RECEIVED
LATE

Ensure final PO delivery status reflects the complete delivery history.

Do not generate intentionally incorrect delivery quantities or invalid dates.

---

# 15. BUDGET EVENT LEDGER

Implement BudgetEvent generation.

Fields:

- budget_event_id
- budget_id
- request_id
- po_id
- event_type
- amount
- event_date
- reference_id

Allowed event types:

ALLOCATE
RESERVE
COMMIT
RELEASE
SPEND

Business rules:

1. Initial budget allocation must be recorded consistently.
2. Approved requests reserve their estimated amount.
3. Rejected requests must not retain reserved budget.
4. Cancellations release reservations where applicable.
5. When a PO is created, the corresponding reservation converts to committed.
6. Committed amounts must reconcile with PO values.
7. SPEND represents synthetic expenditure, not an actual payment record.
8. Every event must reference valid records.
9. No clean-path budget overrun is permitted.
10. Event ordering must be valid.

Important:

Do not independently generate budget balances.

Derive budget reserved, committed and spent balances from the event ledger.

Ensure:

allocated >= reserved + committed

for all clean-path budgets.

Document the exact accounting convention and event amount signs.

If expenditure is recorded based on received goods, document that assumption explicitly. Do not imply that invoice or payment processing exists.

---

# 16. STATUS EVENT HISTORY

Implement StatusEvent generation.

Fields:

- status_event_id
- entity
- entity_id
- from_status
- to_status
- event_ts
- actor

Track lifecycle history for:

- PurchaseRequest
- RFQ
- PurchaseOrder
- Delivery

Requirements:

1. Every state transition creates a new event.
2. Never overwrite previous events.
3. Transitions must follow the allowed state machine.
4. Timestamps must be chronological.
5. Current entity status must equal the final event's to_status.
6. Initial transitions must correctly represent the first state.
7. All event actors must be valid synthetic actors.

PurchaseRequest lifecycle:

DRAFT
SUBMITTED
PENDING_APPROVAL
APPROVED or REJECTED
SOURCING
PO_ISSUED
PARTIALLY_DELIVERED
DELIVERED
CLOSED

Pre-PO requests may transition to CANCELLED.

RFQ, PO and Delivery transitions must also have documented allowed states.

---

# 17. GENERATION ORCHESTRATION

Create or extend a clean workflow orchestration interface.

Suggested interface:

generate_approvals(...)
generate_sourcing(...)
generate_orders(...)
generate_deliveries(...)
generate_budget_events(...)
generate_status_events(...)

The complete workflow must execute in this order:

1. Load existing Phase 2 datasets.
2. Generate approvals.
3. Classify sourcing paths.
4. Generate RFQs.
5. Generate supplier invitations.
6. Generate supplier quotations.
7. Generate QuoteLines.
8. Calculate landed costs.
9. Calculate supplier scores.
10. Award quotations.
11. Generate purchase orders.
12. Generate purchase order lines.
13. Generate deliveries.
14. Generate budget events.
15. Generate status history.
16. Recalculate current statuses and budget balances.
17. Run clean-path validation.

All generated datasets should be available in memory and structured for later export.

Do not implement CSV, JSON or SQL exports in this phase.

---

# 18. CLEAN-PATH VALIDATION

Implement Phase 3 integration checks.

Verify:

- Approval completeness.
- Valid approver roles.
- Request and RFQ relationships.
- Supplier invitation relationships.
- Quote and QuoteLine relationships.
- Quote expiry.
- Supplier eligibility.
- Award selection.
- PO and PO line arithmetic.
- Delivery quantities.
- Date ordering.
- Budget reconciliation.
- Status transition history.

The Phase 3 clean dataset must contain zero intentionally injected anomalies.

Do not implement anomaly injection or ground-truth detectors yet.

---

# 19. TESTING REQUIREMENTS

Create:

tests/test_approvals.py
tests/test_sourcing.py
tests/test_quotes.py
tests/test_orders.py
tests/test_delivery.py
tests/test_budget.py
tests/test_status_events.py
tests/test_workflow_integration.py

Test:

APPROVALS:
- Correct approval levels.
- Multi-level approvals.
- Rejected requests cannot proceed.
- Valid approver references.
- Correct timestamps.

SOURCING:
- Valid sourcing paths.
- Required reason codes.
- RFQ eligibility.
- Minimum supplier invitations.
- No duplicate invitations.

QUOTATIONS:
- Valid quote references.
- Complete QuoteLines.
- Correct landed cost.
- Correct FX conversion.
- Correct score normalization.
- Valid quote expiry.

AWARDS:
- Lowest-scoring eligible supplier wins.
- Award date respects quote validity.
- Awarded supplier is active.

PURCHASE ORDERS:
- Correct PO counts within configured targets.
- Only approved requests receive POs.
- Competitive POs reference awarded quotes.
- PO lines reconcile with quote lines.
- PO value equals line totals.

DELIVERIES:
- Multiple shipments supported.
- Partial delivery supported.
- Cumulative quantities reconcile.
- Delivery dates follow PO dates.

BUDGET:
- Reservation works.
- Commitment works.
- Release works.
- Expenditure works.
- No clean-path overrun.
- Ledger balances reconcile.

STATUS EVENTS:
- Valid transitions.
- Chronological event history.
- Current status equals last event.

DETERMINISM:
- Same seed produces identical workflow datasets.
- Different seeds produce different data.

Run all Phase 1, Phase 2 and Phase 3 tests.

---

# 20. DOCUMENTATION

Update:

README.md
docs/architecture.md
docs/data_dictionary.md
docs/assumptions.md
docs/AI_USAGE.md

Document:

- Approval workflow.
- Sourcing classification.
- RFQ workflow.
- Supplier invitations.
- Quotation structure.
- Landed-cost formula.
- Scoring methodology.
- Award selection.
- PO generation.
- Delivery patterns.
- Budget ledger.
- Status event state machines.

Record every new assumption.

Save this exact prompt in:

ai/prompts/03_phase3_procurement_workflow.md

Preserve previous prompt history.

---

# 21. PHASE 3 DEFINITION OF DONE

[ ] Phase 1 tests pass.

[ ] Phase 2 tests pass.

[ ] Approval engine works.

[ ] RFQ generation works.

[ ] Supplier invitations work.

[ ] Supplier quotations work.

[ ] QuoteLine generation works.

[ ] Landed cost calculations reconcile.

[ ] Supplier scoring works.

[ ] Supplier award selection works.

[ ] Purchase order generation works.

[ ] PurchaseOrderLine generation works.

[ ] Delivery generation works.

[ ] BudgetEvent ledger works.

[ ] StatusEvent history works.

[ ] All foreign-key relationships are valid.

[ ] All financial totals reconcile.

[ ] All event timestamps are valid.

[ ] Clean-path validation passes.

[ ] Determinism tests pass.

[ ] Documentation is updated.

[ ] All tests pass.

---

# 22. STRICT SCOPE CONTROL

DO NOT IMPLEMENT:

- Anomaly injection.
- Ground-truth generation.
- Seven anomaly detectors.
- Non-cheapest award anomalies.
- Expired quote award anomalies.
- Inactive supplier PO anomalies.
- Budget overrun anomalies.
- Duplicate request anomalies.
- Missing approval anomalies.
- Currency mismatch anomalies.
- CSV/JSON/SQL final export engine.
- Final reproducibility report.

These belong to later phases.

All Phase 3 data must represent valid procurement transactions.

---

# 23. FINAL EXECUTION INSTRUCTIONS

Follow this sequence:

STEP 1: Inspect and test previous phases.

STEP 2: Report existing problems.

STEP 3: Implement approvals.py.

STEP 4: Implement sourcing.py.

STEP 5: Implement orders.py.

STEP 6: Implement delivery.py.

STEP 7: Implement budget.py.

STEP 8: Implement StatusEvent generation.

STEP 9: Implement workflow orchestration.

STEP 10: Write unit and integration tests.

STEP 11: Execute all previous and current tests.

STEP 12: Inspect sample procurement transactions.

STEP 13: Verify financial reconciliation.

STEP 14: Verify seeded reproducibility.

STEP 15: Update documentation.

STEP 16: Review Git changes.

STEP 17: Provide the final implementation report.

The report must contain:

1. Files created.
2. Files modified.
3. Approval statistics.
4. RFQ count.
5. Supplier invitation count.
6. Supplier quotation count.
7. Award statistics.
8. Purchase order count.
9. Competitive versus non-competitive PO count.
10. Delivery statistics.
11. Budget reconciliation results.
12. Status event statistics.
13. Test results.
14. Determinism results.
15. Known limitations.
16. Proposed conventional Git commit.

Create a commit only after all tests pass and after checking the working tree. Do not push to GitHub without my approval.

STOP AFTER PHASE 3.

Do not begin Phase 4.

Wait for my explicit approval before proceeding.
