# MASTER IMPLEMENTATION PROMPT

# PHASE 1: PROJECT FOUNDATION & ARCHITECTURE

## Procure-to-Pay Synthetic Data Generator

### YottaFlex AI | Technical Coding Round

---

# 1. ROLE AND RESPONSIBILITY

Act as a Senior Python Data Engineer, Database Architect, and Software Engineering Lead.

You are pair-programming with me to build a production-quality Procure-to-Pay Synthetic Data Generator for the YottaFlex AI technical coding round.

Your responsibility is to implement Phase 1 only.

Think like an experienced data engineer. Prioritize:

- Clean architecture
- Database normalization
- Referential integrity
- Deterministic behavior
- Maintainable Python code
- Clear documentation
- Testability
- Reproducibilityjo 
- Explainable technical decisions

This is a data engineering project, NOT a web application.

Do not create:

- Frontend applications
- Dashboards
- REST APIs
- Authentication systems
- ML models
- Unnecessary infrastructure
- Docker or Kubernetes unless explicitly required later

The objective is to establish a technically sound foundation for the remaining six implementation phases.

# 2. FIRST ACTION: INSPECT THE EXISTING PROJECT

Before creating or modifying anything:

1. Inspect the complete current repository.
2. Identify existing files and folders.
3. Read the existing PRD and master prompt if available.
4. Identify existing implementations.
5. Check Python version.
6. Check installed dependencies.
7. Identify any existing tests.
8. Check Git status.
9. Identify inconsistencies between existing code and the intended architecture.

Do not overwrite existing working files blindly.

If the repository is already initialized, preserve its Git history.

If the project is empty, initialize the repository structure.

Before implementation, provide a short architecture assessment and list the files you intend to create or modify.

Then proceed with Phase 1.

# 3. TECHNICAL STACK

Use the following stack:

- Python 3.11+
- NumPy
- Pandas
- PyYAML
- SQLite
- pytest
- Python standard library
- hashlib for SHA-256 utilities
- pathlib for file management
- argparse for future CLI support

Use pinned dependency versions in requirements.txt.

Create pyproject.toml to support proper installation of the src-layout Python packages.

Do not introduce unnecessary dependencies.

# 4. REQUIRED REPOSITORY STRUCTURE

Create the following structure:

procure-to-pay-datagen/

```
README.md
requirements.txt
pyproject.toml
.gitignore

config/
    default.yaml

src/
    datagen/
        __init__.py
        __main__.py
        cli.py
        ids.py
        config.py
        fx.py

    validate/
        __init__.py
        __main__.py
        checks.py

data/
    csv/
    json/
    sql/
        schema.sql
        seed.sql

docs/
    architecture.md
    data_dictionary.md
    assumptions.md
    validation_summary.md
    reproducibility.md
    source_manifest.md
    AI_USAGE.md

tests/
    test_ids.py
    test_config.py
    test_fx.py
    test_schema.py

ai/
    prompts/
        01_phase1_foundation.md
```

IMPORTANT:

This is the Phase 1 repository foundation.

Do not implement future generation modules such as:

- masters.py
- requests.py
- approvals.py
- sourcing.py
- orders.py
- delivery.py
- budget.py
- anomalies.py
- derive.py
- export.py

Those modules belong to later phases.

Do not create fake implementations of future modules just to fill the folder structure.

# 5. CONFIGURATION MANAGEMENT

Implement config/default.yaml.

Configuration must be centralized.

Use the following initial configuration:

project:
name: procure-to-pay-datagen
version: 1.0.0
base_currency: USD
fiscal_year: 2026
base_date: "2026-01-01"

generation:
default_seed: 20261022
default_scale: starter

scale:
starter:
requesters: 30
suppliers: 12
departments: 10
purchase_requests: 115
rfqs: 50
quotes: 150
purchase_orders: 90

full:
requesters: 300
suppliers: 120
departments: 12
purchase_requests: 1150
rfqs: 500
quotes: 1500
purchase_orders: 900

approval_thresholds:
manager_limit: 2000
department_head_limit: 25000

supplier_scoring:
landed_cost_weight: 0.60
lead_time_weight: 0.25
risk_weight: 0.15

anomalies:
target_rate_min: 0.03
target_rate_max: 0.05

procurement:
minimum_quotes: 3
maximum_quotes: 6
default_invites: 3

fx_rates:
USD: 1.0
INR: 0.012
EUR: 1.08
GBP: 1.27
JPY: 0.0067

These are initial project assumptions, not externally verified exchange rates.

Requirements:

1. Implement config.py.
2. Load configuration from YAML.
3. Validate required configuration keys.
4. Validate data types.
5. Validate approval thresholds.
6. Validate supplier scoring weights sum to 1.0.
7. Validate FX rates are positive.
8. Validate scale parameters.
9. Raise meaningful exceptions for invalid configuration.
10. Never silently replace invalid values with defaults.

Use a clean configuration-loading function.

Example future interface:

load_config(config_path)

Return a validated configuration object or dictionary.

Do not use global mutable configuration.

# 6. CENTRALIZED ID GENERATION

Implement src/datagen/ids.py.

All entity identifiers must be generated centrally.

Use the following formats:

Department:
DEPT-01

Budget:
BUD-0001

Requester:
REQ-0001

Supplier:
SUP-0001

Purchase Request:
PR-2026-000001

RFQ:
RFQ-2026-000001

Supplier Quote:
QUO-2026-000001

Purchase Order:
PO-2026-000001

Delivery:
DEL-PO-2026-000001-01

Additional entity IDs:

Request Line:
RL-000001

Quote Line:
QL-000001

Approval:
APR-000001

Purchase Order Line:
POL-000001

Budget Event:
BE-000001

Status Event:
SE-000001

RFQ Supplier Invite:
INV-000001

Exception Log:
EXC-000001

Approver:
APP-0001

Requirements:

- Create a centralized IDFactory class.
- Maintain independent counters per entity.
- Generate zero-padded IDs.
- Support configurable fiscal year where appropriate.
- Support multiple delivery IDs per PO.
- Ensure deterministic ID generation.
- Prevent duplicate IDs.
- Export ID format regex patterns for future validation.
- Provide reset functionality for testing.
- Do not use UUIDs.
- Do not use uncontrolled randomness.
- Do not use global counters.

Write unit tests for every ID pattern.

Document all ID conventions in docs/data_dictionary.md.

# 7. FIXED FOREIGN EXCHANGE ENGINE

Implement src/datagen/fx.py.

Purpose:

Provide deterministic currency conversion for procurement quotations.

Base currency: USD.

Use FX rates from config/default.yaml.

Required functions:

1. get_exchange_rate(source_currency, target_currency, config)
2. convert_to_base_currency(amount, source_currency, config)
3. convert_currency(amount, source_currency, target_currency, config)

Requirements:

- Support USD, INR, EUR, GBP and JPY.
- Use fixed configured FX rates.
- Reject unsupported currencies.
- Reject negative monetary values where not allowed.
- Use Decimal for financial calculations.
- Define rounding to two decimal places.
- Never fetch live exchange rates.
- Never use external APIs.
- Ensure identical inputs produce identical results.

Add tests covering:

- USD to USD
- INR to USD
- EUR to USD
- GBP to USD
- JPY to USD
- USD to INR
- Unsupported currencies
- Zero values
- Negative values
- Decimal precision

Document the conversion methodology.

# 8. DATABASE SCHEMA DESIGN

Create data/sql/schema.sql.

Use SQLite.

Enable:

PRAGMA foreign_keys = ON;

Create normalized tables with:

- Primary keys
- Foreign keys
- NOT NULL constraints
- UNIQUE constraints
- CHECK constraints
- Appropriate indexes

Design the following entities.

## Core entities

1. Department
2. Budget
3. Requester
4. PurchaseRequest
5. RequestLine
6. Supplier
7. RFQ
8. SupplierQuote
9. Approval
10. PurchaseOrder
11. Delivery

## Additional entities

12. PurchaseOrderLine
13. QuoteLine
14. Approver
15. StatusEvent
16. RFQSupplierInvite
17. BudgetEvent
18. ExceptionLog

Ground truth must remain a separate export artifact. Do not mix it into ordinary operational input tables.

## Required relationships

Department:

- One department has multiple requesters.
- One department has multiple budgets.

Budget:

- Belongs to one department.
- Contains allocated, reserved, committed and spent balances.

Requester:

- Belongs to one department.
- Can create multiple purchase requests.

PurchaseRequest:

- Belongs to one requester.
- Belongs to one department.
- References one budget.
- Can contain multiple request lines.
- Can have zero or one RFQ.

RequestLine:

- Belongs to one purchase request.

Supplier:

- Can participate in multiple RFQs.
- Can submit multiple quotations.
- Has a supplier status and risk classification.

RFQ:

- Belongs to one purchase request.
- Has multiple supplier invitations.
- Can have multiple supplier quotations.

RFQSupplierInvite:

- Connects suppliers with RFQs.
- Enforces uniqueness of RFQ and supplier combinations.

SupplierQuote:

- Belongs to one RFQ.
- Belongs to one supplier.
- Can contain multiple QuoteLine records.

QuoteLine:

- References a supplier quote.
- References the original request line.
- Stores quoted quantity, unit price and line total.

Approval:

- Stores approval events.
- Supports multiple approval levels.
- Records decisions and timestamps.

Approver:

- Identifies authorized approval actors.
- Supports line manager, department head and finance roles.

PurchaseOrder:

- References a purchase request.
- References an awarded quotation where applicable.
- References a supplier.
- Supports competitive and non-competitive sourcing.

PurchaseOrderLine:

- Belongs to one purchase order.
- References the corresponding request line.
- References the awarded quote line where applicable.

Delivery:

- Belongs to one purchase order.
- Supports partial and multiple deliveries.

StatusEvent:

- Records every lifecycle state transition.
- Stores previous status, new status, timestamp and actor.

BudgetEvent:

- Records budget allocation, reservation, commitment, release and expenditure events.
- Supports reconciliation of all budget balances.

ExceptionLog:

- Records exception types, reasons, affected entities and timestamps.

## Important business-model constraints

1. Only one RFQ per purchase request.
2. A supplier cannot be invited twice to the same RFQ.
3. A quote must belong to an invited supplier.
4. Quote lines must reference valid request lines belonging to the RFQ's purchase request.
5. A PO must reference a valid request and supplier.
6. Competitive POs must reference an awarded quotation.
7. Non-competitive POs must have a documented sourcing path and reason where required.
8. Multiple deliveries must be supported.
9. Budget events must be traceable.
10. Foreign-key integrity must be enforceable.

Do not rely only on Python validation for relational integrity. Implement appropriate SQL constraints and indexes.

Where a cross-table business rule cannot be expressed safely using a simple SQL constraint, document it for implementation in the Python validator.

## Budget modelling assumption

BudgetEvent is the source ledger for budget balances.

Support these event types:

ALLOCATE
RESERVE
COMMIT
RELEASE
SPEND

The SPEND event represents synthetic expenditure for this dataset. Do not claim that an invoice or payment workflow is implemented because those entities are outside the current scope.

Document this assumption.

# 9. SCHEMA QUALITY REQUIREMENTS

The database schema must:

- Be normalized.
- Avoid unnecessary duplicate data.
- Use consistent naming conventions.
- Use appropriate monetary data representation.
- Include currency codes.
- Include date and timestamp fields.
- Include CHECK constraints for enums.
- Include appropriate indexes on foreign keys.
- Avoid unnecessary cascading deletes.
- Support lifecycle history.
- Support anomaly injection in later phases without redesigning the whole schema.

Use INTEGER minor units or another clearly documented fixed-precision representation for financial amounts in SQLite.

Explain your chosen representation and ensure it is consistent with the Decimal-based FX engine.

# 10. DATA DICTIONARY

Create docs/data_dictionary.md.

For every table and field, document:

1. Entity name.
2. Field name.
3. Data type.
4. Description.
5. Required or optional.
6. Allowed values.
7. Primary key or foreign key.
8. Uniqueness requirements.
9. Units where applicable.
10. Validation rule.

Document every core and additional entity.

Include the entity relationships and cardinalities.

Do not invent unspecified business fields without documenting the assumption.

# 11. ASSUMPTIONS DOCUMENTATION

Create docs/assumptions.md.

Document all initial assumptions, including:

- Fiscal year 2026.
- Base date 2026-01-01.
- Base currency USD.
- Approval thresholds.
- Supplier scoring weights.
- Fixed FX rates.
- ID conventions.
- QuoteLine addition.
- Approver modelling.
- BudgetEvent ledger.
- Synthetic expenditure representation.
- SQLite monetary precision.
- Starter and full dataset volumes.

Clearly separate:

A. Requirements explicitly stated in the PRD.

B. Technical design decisions.

C. Assumptions introduced because the PRD does not specify exact behavior.

Never present an assumption as an official YottaFlex AI requirement.

# 12. ARCHITECTURE DOCUMENTATION

Create docs/architecture.md.

Explain:

- Project purpose.
- System boundaries.
- Python package structure.
- Configuration flow.
- ID generation architecture.
- FX conversion architecture.
- Database design.
- Entity relationships.
- Future generation pipeline.
- Future validation architecture.
- Future export architecture.

Include a Mermaid ER diagram showing the core entities and their relationships.

Keep the architecture documentation consistent with schema.sql.

# 13. VALIDATION FRAMEWORK FOUNDATION

Create the initial validation package.

Files:

src/validate/__init__.py
src/validate/__main__.py
src/validate/checks.py

For Phase 1, implement only foundational checks:

- SQLite connection.
- Foreign-key enforcement.
- Database schema existence.
- Required tables existence.
- Primary-key uniqueness where applicable.
- Basic schema integrity.
- ID format validation utilities where practical.

Do not implement the complete procurement validator yet.

Do not implement anomaly detectors yet.

Do not generate procurement data yet.

The complete validator belongs to Phase 4 and Phase 5.

# 14. TESTING REQUIREMENTS

Create pytest tests.

Required test files:

tests/test_ids.py
tests/test_config.py
tests/test_fx.py
tests/test_schema.py

Test the following:

ID generation:

- All IDs follow their expected format.
- Independent entity counters.
- No duplicate IDs.
- Reset functionality.
- Multiple delivery IDs for one PO.

Configuration:

- Valid configuration loads.
- Missing required keys fail.
- Invalid thresholds fail.
- Invalid weights fail.
- Invalid FX rates fail.
- Invalid scale values fail.

FX:

- All supported conversions.
- Unsupported currency errors.
- Negative amount handling.
- Decimal precision.
- Deterministic results.

Database:

- Schema initializes successfully.
- All required tables exist.
- Foreign keys are enabled.
- Unique constraints work.
- CHECK constraints work.
- Invalid foreign-key relationships are rejected.

Tests must be meaningful and independent.

Do not write tests that simply repeat the implementation's own assumptions without checking actual behavior.

# 15. README DOCUMENTATION

Create README.md with:

1. Project introduction.
2. Project objectives.
3. Technical stack.
4. Repository structure.
5. Installation instructions.
6. Virtual environment setup.
7. Dependency installation.
8. Configuration explanation.
9. Database schema initialization.
10. Running tests.
11. Current implementation status.
12. Future development phases.

Use Windows PowerShell commands as the primary examples because the development environment is Windows.

Also provide Linux/macOS equivalents where practical.

Do not claim that full dataset generation is available in Phase 1.

Clearly state that Phase 1 establishes the foundation.

# 16. AI USAGE DOCUMENTATION

Create docs/AI_USAGE.md.

Include:

- AI tools used.
- How AI assisted in architecture.
- How AI assisted in code generation.
- What needs human review.
- How generated code was tested.
- Known limitations.

Leave sections requiring my personal assessment as TODO.

Do not falsely claim manual review or successful validation before it happens.

Save the current implementation prompt verbatim at:

ai/prompts/01_phase1_foundation.md

# 17. GIT AND VERSION CONTROL

If Git is already initialized:

- Preserve existing history.
- Check the working tree.
- Do not overwrite unrelated changes.
- Stage only Phase 1 files.

If Git is not initialized:

- Initialize Git.
- Configure the project appropriately.
- Create the first meaningful commit after successful tests.

Suggested commit:

feat(phase-1): establish project foundation and database schema

Do not push to a remote repository without my approval.

# 18. IMPLEMENTATION QUALITY RULES

Follow these rules throughout development:

1. Use type hints.
2. Write modular Python functions.
3. Use descriptive variable names.
4. Follow PEP 8.
5. Add docstrings to public functions and classes.
6. Handle errors explicitly.
7. Avoid unnecessary abstraction.
8. Avoid global mutable state.
9. Do not use uncontrolled randomness.
10. Do not use datetime.now() or datetime.today() for generated business dates.
11. Use pathlib instead of hardcoded filesystem paths.
12. Keep financial calculations deterministic.
13. Never hardcode configuration values in business logic when they belong in YAML.
14. Never fabricate test results.
15. Never skip failing tests to report success.

# 19. PHASE 1 DEFINITION OF DONE

Phase 1 is complete only when all the following conditions are satisfied:

[ ] Repository structure created.

[ ] Python package configuration works.

[ ] requirements.txt contains pinned dependencies.

[ ] YAML configuration loads and validates.

[ ] Centralized IDFactory implemented.

[ ] All documented ID patterns work.

[ ] FX engine works with Decimal precision.

[ ] SQLite schema initializes successfully.

[ ] All core entities are represented.

[ ] All additional entities are represented.

[ ] QuoteLine relationship is implemented.

[ ] BudgetEvent ledger is implemented.

[ ] Approver relationship is implemented.

[ ] Foreign-key constraints work.

[ ] Unique and CHECK constraints work.

[ ] Architecture documentation is complete.

[ ] Data dictionary is complete.

[ ] Assumptions are documented.

[ ] README is complete.

[ ] AI usage documentation exists.

[ ] Phase 1 tests pass.

[ ] Git commit is created if safe and appropriate.

# 20. FINAL EXECUTION INSTRUCTIONS

Work incrementally.

Do not generate the entire project in one uncontrolled operation.

Use the following execution order:

STEP 1: Inspect repository and existing files.

STEP 2: Report architecture findings.

STEP 3: Create repository structure.

STEP 4: Implement pyproject.toml and requirements.txt.

STEP 5: Implement configuration management.

STEP 6: Implement centralized ID generation.

STEP 7: Implement FX conversion.

STEP 8: Design and implement SQLite schema.

STEP 9: Create architecture and documentation files.

STEP 10: Implement foundational validation.

STEP 11: Write and execute tests.

STEP 12: Update README and AI_USAGE.md.

STEP 13: Review every created file.

STEP 14: Report results and propose Git commit.

After implementation, provide:

1. Files created.
2. Files modified.
3. Architecture decisions.
4. Assumptions made.
5. Database tables created.
6. Test execution results.
7. Any failing tests.
8. Known limitations.
9. Git status.
10. Proposed commit message.

IMPORTANT:

STOP AFTER PHASE 1.

Do not begin Phase 2.

Do not generate master data.

Do not generate purchase requests.

Do not generate supplier quotations.

Do not generate purchase orders.

Do not generate deliveries.

Do not inject anomalies.

Do not create production datasets.

Wait for my explicit approval before proceeding to Phase 2.

The objective is a clean, reliable, testable foundation that can support the complete Procure-to-Pay Synthetic Data Generator without requiring major architectural changes later.
