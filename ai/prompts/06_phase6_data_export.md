<USER_REQUEST>
# MASTER IMPLEMENTATION PROMPT
# PHASE 6: DATA EXPORT, DATABASE INTEGRATION & FINAL DELIVERABLES

## PROJECT

Project Name: YottaFlex Procure-to-Pay Synthetic Data Generator

GitHub Repository:
https://github.com/Ts5338236/Yotta-AI.git

You are working as a Senior Python Engineer, Data Engineer, Database Architect and QA Engineer.

Your responsibility is to complete Phase 6 of my existing project.

IMPORTANT:
- Work inside the existing repository.
- Do not create a new project.
- Do not rewrite completed Phases 1–5 unnecessarily.
- Do not delete working modules or tests.
- Do not change the business rules to make exports easier.
- Do not fabricate record counts or successful test results.
- Preserve all existing IDs, relationships and deterministic behavior.
- Follow the original assignment requirements exactly.

The goal is to build a reliable, reusable export and database persistence layer for the generated procurement dataset.

==================================================
1. INITIAL REPOSITORY INSPECTION
==================================================

Before implementing anything, inspect:

- README.md
- pyproject.toml
- config/
- src/datagen/
- src/validate/
- tests/
- docs/
- data/
- Existing database schema
- Existing CLI entry points
- Existing generation pipeline

Review Phases 1–5.

Run the existing test suite and record the actual result.

Inspect the existing output folders and determine whether they contain:
- Real generated files.
- Empty folders.
- Placeholder files.
- Incomplete exports.

Do not assume that an output folder means its export functionality is complete.

Create an initial report:

docs/phase6_initial_audit.md

Include:
- Existing export implementation.
- Missing export functionality.
- Existing database implementation.
- Missing SQL functionality.
- Existing tests.
- Required modifications.

==================================================
2. REQUIRED ENTITIES
==================================================

Export all 11 core entities:

1. Requester
2. Department
3. Budget
4. PurchaseRequest
5. RequestLine
6. Supplier
7. RFQ
8. SupplierQuote
9. Approval
10. PurchaseOrder
11. Delivery

Also export all additional entities implemented in earlier phases, including where present:

- PurchaseOrderLine
- QuoteLine
- Approver
- RFQSupplierInvite
- StatusEvent
- BudgetEvent
- ExceptionLog

Export ground truth separately.

Do not omit an entity simply because it is an additional technical entity.

Use the existing database schema and actual model definitions as the source of truth.

Do not invent columns.

==================================================
3. CSV EXPORT ENGINE
==================================================

Create or complete:

src/datagen/export.py

Implement a reusable CSV export engine.

Output directory:

data/csv/

Generate one CSV file per entity.

Expected filenames:

requesters.csv
departments.csv
budgets.csv
purchase_requests.csv
request_lines.csv
suppliers.csv
rfqs.csv
supplier_quotes.csv
approvals.csv
purchase_orders.csv
purchase_order_lines.csv
quote_lines.csv
approvers.csv
rfq_supplier_invites.csv
deliveries.csv
status_events.csv
budget_events.csv
exception_logs.csv

Export only files corresponding to actual implemented entities.

CSV requirements:

- UTF-8 encoding.
- Header row.
- Stable column ordering.
- Consistent date formatting.
- Consistent datetime formatting.
- Consistent decimal formatting.
- Correct null representation.
- No Python object representations.
- No NumPy-specific object serialization.
- No missing records.
- No duplicated records.
- Correct foreign-key references.
- Stable row ordering for deterministic exports.

Use a configurable output directory.

Support both starter and full dataset generation.

The exporter must not mutate source data.

==================================================
4. JSON EXPORT ENGINE
==================================================

Generate:

data/json/

Create one JSON file per entity.

Requirements:

- Valid JSON.
- UTF-8 encoding.
- Stable field ordering.
- Consistent date and datetime serialization.
- Correct Decimal serialization.
- Proper null handling.
- Numeric fields remain numeric where appropriate.
- No NaN or Infinity values.
- Stable ordering for reproducibility.

Use a reusable serialization utility.

Do not duplicate serialization logic across individual entity exporters.

After exporting, read every JSON file back using Python's JSON parser.

Compare exported record counts against source records.

==================================================
5. SQLITE DATABASE GENERATION
==================================================

Create or complete:

src/datagen/database.py

Generate:

data/database/procurement.db

Use the existing schema as the source of truth.

Requirements:

1. Create every required entity table.
2. Create additional technical entity tables.
3. Preserve primary keys.
4. Preserve foreign keys.
5. Apply unique constraints.
6. Apply appropriate NOT NULL constraints.
7. Add useful indexes.
8. Use appropriate SQLite data types.
9. Enable PRAGMA foreign_keys = ON.
10. Insert parent records before dependent records.
11. Preserve all source records.
12. Use transactions for bulk insertion.
13. Roll back safely on failure.
14. Support rebuilding the database from a clean state.

Do not use INSERT OR IGNORE to hide duplicate or invalid records.

Do not silently discard failed rows.

Add clear database error handling.

After database creation, execute:

PRAGMA integrity_check;

Expected result:

ok

Also execute:

PRAGMA foreign_key_check;

There must be no unexpected foreign-key violations.

Verify actual table counts against the source datasets.

==================================================
6. SQL SCHEMA EXPORT
==================================================

Generate:

data/sql/schema.sql

The schema must contain:

- CREATE TABLE statements.
- Primary keys.
- Foreign keys.
- Unique constraints.
- NOT NULL constraints.
- CHECK constraints where applicable.
- Useful indexes.
- Appropriate data types.

Requirements:

- Follow the existing entity relationships.
- Preserve the exact identifier formats.
- Preserve all foreign-key relationships.
- Do not create duplicate or contradictory schema definitions.

Test the generated schema against a completely fresh SQLite database.

==================================================
7. SQL SEED EXPORT
==================================================

Generate:

data/sql/seed.sql

IMPORTANT:

The previously reviewed repository contained a placeholder SQL seed.

Replace the placeholder with a real, populated SQL seed generated from the actual synthetic dataset.

The seed must include INSERT statements for all exported entities.

Requirements:

- Correct foreign-key insertion order.
- Correct SQL escaping.
- Correct null handling.
- Correct date representation.
- Correct numeric values.
- Correct IDs.
- No missing records.
- No duplicate records.

The seed must execute successfully against a fresh database after schema.sql.

Test:

1. Create a temporary SQLite database.
2. Execute schema.sql.
3. Execute seed.sql.
4. Run integrity checks.
5. Compare table counts against the generated source data.

The SQL seed must reproduce the same logical records as the source dataset.

==================================================
8. GROUND TRUTH EXPORT
==================================================

Ground truth must remain separate from operational procurement tables.

Generate:

data/ground_truth/ground_truth.csv

data/ground_truth/ground_truth.json

Include the fields implemented by the existing ground-truth schema, including:

- anomaly_id
- issue_type
- entity
- record_id
- expected_decision
- reason

Preserve additional fields where already implemented.

Requirements:

- Every injected anomaly must have a ground-truth record.
- Every ground-truth record must refer to a real affected record.
- No false ground-truth records.
- Unique anomaly IDs.
- Stable ordering.
- Deterministic output.

Never leak ground-truth labels into operational procurement entity files.

Also export an anomaly evaluation report containing:

- Total injected anomalies.
- Total detected anomalies.
- True positives.
- False positives.
- False negatives.
- Precision.
- Recall.
- Per-category results.

==================================================
9. EXPORT INTEGRITY VALIDATION
==================================================

Create or extend:

src/validate/export_checks.py

Validate:

A. CSV

- File existence.
- Header correctness.
- Record counts.
- Duplicate IDs.
- Foreign-key references.
- Data serialization.

B. JSON

- Valid JSON parsing.
- Expected schema fields.
- Record counts.
- Null handling.
- Numeric values.
- Date serialization.

C. SQLITE

- Expected tables.
- Primary-key uniqueness.
- Foreign-key integrity.
- Record counts.
- Database integrity.

D. SQL

- Schema executes successfully.
- Seed executes successfully.
- Record counts match source data.

E. CROSS-FORMAT

Compare CSV, JSON and SQLite logical records.

Ensure that:

- IDs match.
- Record counts match.
- Relationships match.
- Financial amounts match.
- Dates match.
- Null values are preserved.
- Ground truth remains separate.

Use canonical normalization before comparing data types across formats.

Do not rely only on file sizes or row counts to establish correctness.

==================================================
10. EXPORT REPORTS
==================================================

Generate:

docs/export_integrity_report.md

docs/export_integrity_report.json

Include:

- Export timestamp or fixed simulation metadata.
- Dataset scale.
- Random seed.
- Entity names.
- Source record counts.
- CSV exported record counts.
- JSON exported record counts.
- SQLite table counts.
- SQL seed record counts.
- File sizes.
- SHA-256 checksums.
- Integrity check results.
- Foreign-key check results.
- Cross-format comparison results.
- Errors and warnings.

Do not use current time as generated business data.

Execution metadata may record an actual execution timestamp, but document that it is operational metadata and not part of the deterministic business dataset.

==================================================
11. REPRODUCIBILITY
==================================================

Use the existing fixed seed:

20261022

Verify:

- Identical seed produces identical logical data.
- Identical seed produces identical normalized CSV exports.
- Identical seed produces identical normalized JSON exports.
- Identical seed produces identical database contents.
- Identical seed produces identical ground-truth records.

For SQLite, compare normalized logical table contents rather than relying exclusively on raw database binary checksums.

Ensure stable row ordering.

Ensure the exporter does not introduce nondeterministic output.

==================================================
12. CLI INTEGRATION
==================================================

Integrate export functionality into the existing CLI.

Do not create a competing CLI architecture.

Provide commands consistent with the current project.

The workflow must support:

1. Generate starter dataset.
2. Generate full dataset.
3. Run validation.
4. Inject anomalies.
5. Evaluate anomaly detection.
6. Export CSV.
7. Export JSON.
8. Build SQLite database.
9. Generate SQL schema.
10. Generate SQL seed.
11. Run export-integrity checks.

If the project uses a single pipeline command, extend it with appropriate options.

Use helpful error messages and nonzero exit codes on critical failures.

Update README commands to match the actual CLI.

==================================================
13. TESTING
==================================================

Create or extend:

tests/test_csv_export.py
tests/test_json_export.py
tests/test_database_export.py
tests/test_sql_schema.py
tests/test_sql_seed.py
tests/test_export_integrity.py
tests/test_export_determinism.py
tests/test_ground_truth_export.py

Test:

1. Every implemented entity is exported.
2. All required core entities are exported.
3. CSV headers are correct.
4. CSV counts match source records.
5. JSON files parse successfully.
6. JSON counts match source records.
7. SQLite tables contain all records.
8. SQLite primary keys are valid.
9. SQLite foreign keys are valid.
10. SQL schema executes on a fresh database.
11. SQL seed executes on a fresh database.
12. SQL seed reproduces source records.
13. Ground truth remains separate.
14. Decimal values are preserved.
15. Date values are preserved.
16. Null values are preserved.
17. Repeated exports are deterministic.
18. Failed exports do not leave misleading partial success reports.
19. Existing Phase 1–5 tests continue to pass.

Use temporary directories for test exports.

Do not overwrite production data during unit tests.

==================================================
14. DOCUMENTATION
==================================================

Update:

README.md
docs/data_dictionary.md
docs/architecture.md
docs/reproducibility.md
docs/validation_summary.md
docs/prompt_history.md
AI_USAGE.md

Document:

- CSV export commands.
- JSON export commands.
- SQLite generation.
- SQL schema generation.
- SQL seed execution.
- Ground-truth export.
- Export integrity validation.
- Output folder structure.
- Reproducibility instructions.

Create or update:

docs/export_specification.md

Explain the output format, file naming conventions, data serialization rules and database relationships.

Create or update:

source_manifest.json

Document whether external datasets were used.

If only synthetic data was used, explicitly state:

"No external datasets were used. All procurement records were generated synthetically using documented deterministic generation logic."

Do not claim an external source was used unless it was actually used and legally permitted.

==================================================
15. EXPECTED FINAL DIRECTORY STRUCTURE
==================================================

Adapt this structure to the actual project without duplicating existing directories.

Yotta-AI/
│
├── config/
│
├── src/
│   ├── datagen/
│   │   ├── export.py
│   │   └── database.py
│   │
│   └── validate/
│       └── export_checks.py
│
├── tests/
│   ├── test_csv_export.py
│   ├── test_json_export.py
│   ├── test_database_export.py
│   ├── test_sql_schema.py
│   ├── test_sql_seed.py
│   ├── test_export_integrity.py
│   ├── test_export_determinism.py
│   └── test_ground_truth_export.py
│
├── data/
│   ├── csv/
│   ├── json/
│   ├── database/
│   │   └── procurement.db
│   ├── sql/
│   │   ├── schema.sql
│   │   └── seed.sql
│   └── ground_truth/
│       ├── ground_truth.csv
│       └── ground_truth.json
│
├── docs/
│   ├── export_specification.md
│   ├── export_integrity_report.md
│   ├── export_integrity_report.json
│   └── existing documentation
│
├── source_manifest.json
├── README.md
├── AI_USAGE.md
└── pyproject.toml

Do not duplicate existing output files or modules.

==================================================
16. EXECUTION ORDER
==================================================

Implement in this exact order:

Step 1: Inspect current implementation.

Step 2: Fix incomplete export architecture.

Step 3: Implement CSV export.

Step 4: Implement JSON export.

Step 5: Implement SQLite database generation.

Step 6: Generate SQL schema.

Step 7: Generate populated SQL seed.

Step 8: Export ground truth separately.

Step 9: Implement export integrity validation.

Step 10: Integrate export CLI.

Step 11: Add automated tests.

Step 12: Generate starter outputs.

Step 13: Generate full-scale outputs.

Step 14: Verify actual record counts.

Step 15: Run all export-integrity checks.

Step 16: Run the complete existing test suite.

Step 17: Update documentation.

Step 18: Produce the Phase 6 completion report.

Do not skip execution steps.

==================================================
17. DEFINITION OF DONE
==================================================

Phase 6 is complete only when:

- All 11 core entities are exported.
- All implemented additional entities are exported.
- CSV export works.
- JSON export works.
- SQLite database is generated.
- SQL schema is executable.
- SQL seed contains actual records.
- Ground truth is exported separately.
- Exported values match source data.
- Foreign-key integrity passes.
- Database integrity passes.
- Determinism is verified.
- Starter and full-scale export work.
- Export tests pass.
- Existing Phase 1–5 tests pass.
- Documentation is updated.
- Source manifest is present.
- No placeholder implementation remains in required export deliverables.

==================================================
18. FINAL PHASE 6 REPORT
==================================================

Create:

docs/phase6_completion_report.md

Include:

1. Initial audit findings.
2. Files created.
3. Files modified.
4. Export architecture.
5. Actual entity record counts.
6. CSV export results.
7. JSON export results.
8. SQLite integrity results.
9. SQL schema execution results.
10. SQL seed execution results.
11. Ground-truth export results.
12. Cross-format comparison results.
13. Determinism results.
14. New tests and test results.
15. Full test-suite results.
16. Known limitations.
17. Remaining Phase 7 work.

Do not claim success unless the actual commands have executed successfully.

STOP AFTER PHASE 6.

Do not begin Phase 7.

Do not mark Phase 6 completed in README until all acceptance criteria have passed.

Wait for my next instruction after generating the Phase 6 completion report.

BEGIN BY INSPECTING THE EXISTING YOTTA-AI REPOSITORY.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-11-12T21:03:49+05:30.

The user's current state is as follows:
Active Document: c:\Users\sony\Desktop\Yotta\data\sql\schema.sql (LANGUAGE_UNSPECIFIED)
Cursor is on line: 1
Other open documents:
- c:\Users\sony\Desktop\Yotta\tests\test_validation_integration.py (LANGUAGE_UNSPECIFIED)
- c:\Users\sony\Desktop\Yotta\ai\prompts\04_phase4_derived_validation.md (LANGUAGE_UNSPECIFIED)
- c:\Users\sony\Desktop\Yotta\README.md (LANGUAGE_UNSPECIFIED)
- c:\Users\sony\Desktop\Yotta\tests\test_config.py (LANGUAGE_UNSPECIFIED)
- c:\Users\sony\Desktop\Yotta\src\datagen\ids.py (LANGUAGE_UNSPECIFIED)
</ADDITIONAL_METADATA>