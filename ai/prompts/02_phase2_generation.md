# MASTER IMPLEMENTATION PROMPT
# PHASE 2: MASTER DATA AND PURCHASE REQUEST GENERATION

## Procure-to-Pay Synthetic Data Generator
### YottaFlex AI | Technical Coding Round

---

# 1. ROLE

Act as a Senior Python Data Engineer and Synthetic Data Generation Specialist.

You are continuing the existing Procure-to-Pay Synthetic Data Generator project.

Phase 1 established the project foundation, configuration management, ID generation, FX engine, database schema and foundational tests.

Your responsibility is to implement Phase 2 only.

Phase 2 covers:

1. Department generation.
2. Budget generation.
3. Requester generation.
4. Supplier generation.
5. Purchase Request generation.
6. Request Line generation.
7. Category-based price distributions.
8. Log-normal price generation.
9. Seasonal patterns across 2026.
10. Deterministic data generation.

Do not implement Phase 3 or later.

# 2. FIRST ACTION: INSPECT PHASE 1

Before writing code:

1. Inspect the entire repository.
2. Read the existing PRD.
3. Read the original master prompt.
4. Inspect Phase 1 implementation.
5. Inspect config/default.yaml.
6. Inspect ids.py.
7. Inspect config.py.
8. Inspect fx.py.
9. Inspect schema.sql.
10. Inspect all existing tests.
11. Run the existing Phase 1 tests.
12. Check Git status.

Verify that Phase 1 is working.

If Phase 1 tests fail, identify and report the issues before proceeding. Do not silently rewrite Phase 1.

Preserve all existing working functionality.

Use the existing schema and architecture as the source of truth. If Phase 1 has deviations from the PRD, report them before making structural changes.

# 3. HARD TECHNICAL CONSTRAINTS

Use:

- Python 3.11+
- NumPy
- Pandas
- SQLite
- Existing YAML configuration
- Existing centralized IDFactory
- pytest

IMPORTANT DETERMINISM RULES:

1. Create exactly one numpy.random.default_rng(seed) in the generation entry point.
2. Pass the same RNG explicitly to every generation function.
3. Never create additional independent RNG instances inside modules.
4. Never use random.random(), random.choice() or global random state.
5. Never use datetime.now() or datetime.today().
6. Use fixed base date 2026-01-01.
7. Generate dates only within fiscal year 2026.
8. Sort records consistently.
9. Use stable iteration order.
10. Never depend on unordered set iteration.
11. Ensure the same seed and configuration produce identical data.

All generated IDs must come from the existing IDFactory.

Do not create another ID generation mechanism.

# 4. REQUIRED MODULES

Create these modules:

src/datagen/masters.py
src/datagen/requests.py

Modify existing modules only when genuinely required.

Do not create unnecessary duplicate modules.

Keep responsibilities separated:

masters.py:
- generate_departments()
- generate_budgets()
- generate_requesters()
- generate_suppliers()
- generate_all_masters()

requests.py:
- generate_purchase_requests()
- generate_request_lines()
- generate_all_requests()

Use type hints and clear docstrings.

# 5. MASTER DATA GENERATION

## A. Department

Generate departments using realistic synthetic organizational structures.

Full scale:
10-12 departments, with the configured full-scale count.

Examples:

- Engineering
- Information Technology
- Finance
- Human Resources
- Procurement
- Operations
- Marketing
- Sales
- Administration
- Research and Development
- Legal
- Facilities

Fields:

- department_id
- name
- cost_centre
- effective_from
- effective_to

Requirements:

- Unique department IDs.
- Unique department names.
- Unique cost centres.
- Effective dates must be valid.
- Every department must have at least one requester and one budget.
- Department count must follow configuration.

## B. Budget

Generate budget records for every department.

Fields:

- budget_id
- department_id
- fiscal_year
- allocated
- reserved
- committed
- spent

Requirements:

- Every budget references an existing department.
- Fiscal year must be 2026.
- Allocated budget must be positive.
- Initial reserved, committed and spent values must be zero.
- Budget values must be realistic.
- Department budgets must vary.
- Do not generate budget overrun anomalies in Phase 2.

IMPORTANT:

BudgetEvent and budget balance transitions belong to Phase 3.

Phase 2 creates initial budget master records only.

## C. Requester

Full scale: 300 requesters.

Starter scale: 30 requesters.

Fields:

- requester_id
- department_id
- name
- grade
- manager_id

Requirements:

- Every requester belongs to a valid department.
- Generate synthetic names only.
- No real personal information.
- Manager relationships must be valid.
- Prevent circular manager relationships.
- Support seniority levels.
- Requesters should be distributed across departments realistically.
- Do not make all departments have exactly the same requester count.

Manager IDs must reference valid requester records if the existing schema uses requester-based managers.

Use a safe hierarchy:

- Top-level requester managers may have NULL manager_id.
- Other requesters may reference an eligible senior requester.

Do not reference nonexistent requester IDs.

## D. Supplier

Full scale: 120 suppliers.

Starter scale: 12 suppliers.

Fields:

- supplier_id
- supplier_code
- name
- status
- status_effective_dates
- risk_flag
- risk_score
- currency
- lead_time_mean

Requirements:

- Unique supplier IDs.
- Unique supplier codes.
- Synthetic supplier names.
- Supported currency codes only.
- Status must be active, inactive or blocked.
- Risk classification must be low, medium or high.
- Risk score must follow its documented range.
- Lead time must be positive.
- Supplier status must have valid effective dates.
- Supplier distribution should be realistic.

Use configurable or documented probabilities for supplier status, risk and currency distributions.

Do not generate supplier POs in this phase.

Do not generate supplier quotations in this phase.

# 6. PURCHASE REQUEST GENERATION

Generate approximately 1,150 purchase requests at full scale and approximately 115 at starter scale.

Use the configured scale values.

Fields:

- request_id
- requester_id
- department_id
- budget_id
- created_date
- status
- total_estimate_usd
- priority

Requirements:

1. Every request references an existing requester.
2. Department must match the requester's department.
3. Budget must belong to the same department.
4. Request IDs must follow the centralized IDFactory.
5. Request dates must fall within 2026.
6. Request priority should have realistic variation.
7. Purchase request status must use documented valid enum values.
8. Request status must initially represent a pre-approval workflow state.
9. No request may be approved or rejected in Phase 2.
10. Every request must contain at least one request line.

Suggested initial statuses:

DRAFT
SUBMITTED

Do not generate approval decisions.

Do not generate RFQs.

Do not generate POs.

Those belong to Phase 3.

# 7. REQUEST LINE GENERATION

Generate multiple purchase request lines per purchase request.

Fields:

- request_line_id
- request_id
- item
- category
- qty
- unit_estimate
- line_total

Suggested categories:

- IT Hardware
- Software
- Office Supplies
- Furniture
- Industrial Equipment
- Maintenance
- Professional Services
- Logistics
- Facilities
- Marketing

Requirements:

- Each line references an existing purchase request.
- Quantity must be a positive integer.
- Unit estimate must be positive.
- Line total must equal quantity multiplied by unit estimate.
- Each request must have at least one line.
- Item descriptions must be realistic.
- Category must belong to the approved category list.
- Use deterministic category selection.

The purchase request total_estimate_usd must be derived from the sum of its request lines.

Do not independently generate the request total.

# 8. REALISTIC PRICE DISTRIBUTIONS

Implement category-based price distributions.

Use NumPy log-normal distributions.

Different categories must have different price profiles.

For example:

IT Hardware:
- Higher unit prices.
- Moderate variation.

Office Supplies:
- Lower unit prices.
- Moderate variation.

Software:
- Medium to high unit prices.
- Higher variation.

Industrial Equipment:
- High unit prices.
- Larger variation.

Furniture:
- Medium unit prices.

Professional Services:
- Higher variation.

Define category parameters in configuration where practical.

For every category, document:

- Distribution type.
- Mean or log-space parameters.
- Standard deviation.
- Minimum and maximum limits.
- Currency assumptions.

Avoid generating negative or zero prices.

Apply sensible bounds to extreme log-normal samples.

Do not use arbitrary random values without documented distributions.

# 9. SEASONALITY ACROSS 2026

Purchase requests should reflect realistic seasonality.

Use the fixed 2026 calendar.

Introduce configurable monthly demand weights.

Example:

January: 0.07
February: 0.07
March: 0.08
April: 0.07
May: 0.07
June: 0.08
July: 0.08
August: 0.08
September: 0.09
October: 0.10
November: 0.10
December: 0.11

Normalize monthly weights before sampling.

Use the shared RNG.

Generate valid dates within the selected month.

The total distribution should demonstrate a modest increase in purchasing activity toward year-end.

Document that these seasonal weights are synthetic assumptions.

# 10. DERIVED VALUES

Phase 2 must implement correct source-based calculations.

RequestLine:

line_total = qty * unit_estimate

PurchaseRequest:

total_estimate_usd = SUM(request_line.line_total)

Requirements:

- Use Decimal or a consistent fixed-precision monetary representation.
- Ensure line totals reconcile exactly.
- Ensure request totals equal the sum of their lines.
- Use the same financial precision as Phase 1.
- Never generate derived totals independently.

If SQLite stores money in integer minor units, use that convention consistently.

Do not introduce floating-point arithmetic errors.

# 11. DATA GENERATION INTERFACE

Implement a clean generation interface.

Suggested design:

generate_all_masters(config, rng, id_factory)

generate_all_requests(
    config,
    rng,
    id_factory,
    departments,
    budgets,
    requesters
)

The generation entry point should:

1. Load validated configuration.
2. Read seed and scale.
3. Initialize one RNG.
4. Initialize the existing IDFactory.
5. Generate master data.
6. Generate purchase requests.
7. Generate request lines.
8. Calculate derived request totals.
9. Return generated datasets.

Keep generation functions modular.

Avoid unnecessary database writes during generation.

Use in-memory datasets first.

Database persistence and export are addressed in later phases.

# 12. CONFIGURATION UPDATES

Update config/default.yaml only where required.

Potential additions:

category_distributions:
  IT Hardware:
    log_mean: 6.5
    log_sigma: 0.6
    min_price: 100
    max_price: 15000

  Office Supplies:
    log_mean: 3.5
    log_sigma: 0.5
    min_price: 1
    max_price: 500

  Software:
    log_mean: 5.5
    log_sigma: 0.8
    min_price: 50
    max_price: 20000

  Furniture:
    log_mean: 5.0
    log_sigma: 0.6
    min_price: 20
    max_price: 10000

  Industrial Equipment:
    log_mean: 7.0
    log_sigma: 0.7
    min_price: 500
    max_price: 50000

  Maintenance:
    log_mean: 4.5
    log_sigma: 0.6
    min_price: 10
    max_price: 10000

  Professional Services:
    log_mean: 6.0
    log_sigma: 0.8
    min_price: 100
    max_price: 30000

  Logistics:
    log_mean: 4.5
    log_sigma: 0.6
    min_price: 10
    max_price: 10000

  Facilities:
    log_mean: 5.0
    log_sigma: 0.6
    min_price: 20
    max_price: 15000

  Marketing:
    log_mean: 5.0
    log_sigma: 0.8
    min_price: 20
    max_price: 15000

Treat these parameters as initial synthetic modelling assumptions.

Validate all configuration values.

Do not silently accept invalid distribution parameters.

# 13. TESTING REQUIREMENTS

Create:

tests/test_masters.py
tests/test_requests.py
tests/test_determinism.py
tests/test_distributions.py

Test:

MASTER DATA:
- Correct department counts.
- Correct requester counts.
- Correct supplier counts.
- Unique IDs.
- Valid foreign keys.
- Valid department relationships.
- Valid manager relationships.
- Valid supplier enums.
- Valid supplier currencies.

PURCHASE REQUESTS:
- Correct request counts.
- Every request has lines.
- Valid requester relationships.
- Department consistency.
- Budget consistency.
- Valid dates.
- Valid priority values.
- Valid statuses.

REQUEST LINES:
- Positive quantities.
- Positive prices.
- Correct line totals.
- Correct request totals.
- Valid categories.
- Valid request references.

DISTRIBUTIONS:
- Category-based price distributions are distinguishable.
- Prices respect configured bounds.
- Seasonal distribution is plausible.
- No invalid numeric values.

DETERMINISM:
- Same seed produces identical records.
- Same seed produces identical row counts.
- Same seed produces identical IDs.
- Same seed produces identical generated dates and prices.
- Different seeds produce different generated data.

Do not use brittle tests that require every random sample to match a precise statistical percentage.

Use reasonable statistical tolerances.

# 14. DOCUMENTATION

Update:

docs/data_dictionary.md
docs/assumptions.md
docs/architecture.md
README.md

Document:

- Generated master data.
- Purchase request generation.
- Request line generation.
- Category distributions.
- Seasonality methodology.
- Data relationships.
- Derived calculations.
- Assumptions.
- Current implementation status.

Update AI_USAGE.md with the AI-assisted implementation work.

Save this exact prompt in:

ai/prompts/02_phase2_generation.md

Do not overwrite Phase 1 prompt history.

# 15. PHASE 2 DEFINITION OF DONE

Phase 2 is complete when:

[ ] Phase 1 tests still pass.

[ ] Department generator works.

[ ] Budget generator works.

[ ] Requester generator works.

[ ] Supplier generator works.

[ ] Purchase request generator works.

[ ] Request line generator works.

[ ] All relationships are valid.

[ ] All IDs are unique.

[ ] All dates fall within 2026.

[ ] Category price distributions work.

[ ] Seasonal variation works.

[ ] Request totals reconcile with line totals.

[ ] Same seed produces identical data.

[ ] Different seeds produce different data.

[ ] All Phase 2 tests pass.

[ ] Documentation is updated.

[ ] Git changes are reviewed.

# 16. STRICT SCOPE CONTROL

DO NOT IMPLEMENT:

- Approval generation.
- RFQ generation.
- Supplier invitations.
- Supplier quotations.
- Quote scoring.
- Quote awarding.
- Purchase orders.
- Purchase order lines.
- Delivery generation.
- Budget event transitions.
- Anomaly injection.
- Ground-truth generation.
- CSV/JSON/SQL dataset exports.
- Full validation framework.

These belong to subsequent phases.

# 17. EXECUTION PROCESS

Follow this order:

STEP 1: Inspect Phase 1 and run existing tests.

STEP 2: Report any existing issues.

STEP 3: Implement masters.py.

STEP 4: Implement requests.py.

STEP 5: Update configuration.

STEP 6: Implement generation interfaces.

STEP 7: Add tests.

STEP 8: Execute all Phase 1 and Phase 2 tests.

STEP 9: Inspect generated records and statistical distributions.

STEP 10: Update documentation.

STEP 11: Review code quality and Git changes.

STEP 12: Provide a detailed implementation report.

At the end, report:

1. Files created.
2. Files modified.
3. Number of generated departments.
4. Number of generated budgets.
5. Number of generated requesters.
6. Number of generated suppliers.
7. Number of purchase requests.
8. Number of request lines.
9. Category distribution.
10. Monthly distribution.
11. Sample generated records.
12. Test results.
13. Determinism test results.
14. Known limitations.
15. Proposed Git commit message.

STOP AFTER PHASE 2.

Do not begin Phase 3.

Wait for my explicit approval before continuing.
