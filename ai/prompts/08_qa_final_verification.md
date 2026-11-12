<USER_REQUEST>

You are now the Lead QA Engineer for the Yotta-AI project.

Perform a complete end-to-end verification of the Procure-to-Pay Synthetic Data Generator.

TEST 1: MASTER DATA
Verify departments, budgets, requesters and suppliers.

TEST 2: PROCUREMENT WORKFLOW
Verify:
Requester → Purchase Request → Approval → RFQ → Supplier Quotes → Comparison → Award → Purchase Order → Delivery.

TEST 3: APPROVAL RULES
Test purchases below, at and above each approval threshold.
Verify that unauthorized POs are rejected in the normal workflow.

TEST 4: QUOTE COMPARISON
Verify at least three quotes for competitive purchases.
Recalculate landed costs.
Verify supplier scores and award rationale.

TEST 5: BUDGET
Verify allocated, reserved, committed and spent amounts.
Check all budget ledger transactions.

TEST 6: ANOMALIES
Test all seven required edge cases individually.
Verify issue_type, record_id, expected_decision and reason.
Ensure ground truth is not leaked into model input data.

TEST 7: DATA INTEGRITY
Verify all primary keys, foreign keys, cardinalities, lifecycle transitions and date sequences.

TEST 8: OUTPUTS
Verify CSV, JSON, SQLite, SQL schema, SQL seed and ground-truth files.

TEST 9: FULL-SCALE DATA
Check the requested baseline:
300 requesters
120 suppliers
1,200 requests
500 RFQs
1,500 quotes
900 POs

Document any intentional additional records or differences.

TEST 10: REPRODUCIBILITY
Run the full generator twice using seed 20261022.
Compare all output row counts and SHA-256 checksums.

TEST 11: FRESH INSTALLATION
Clone the public repository into a clean directory.
Install dependencies using documented instructions.
Run the generator and validator.
Verify all outputs.

DELIVERABLES:
- docs/FINAL_TEST_REPORT.md
- docs/FINAL_VALIDATION_REPORT.md
- docs/REPRODUCIBILITY_REPORT.md
- Machine-readable validation JSON.

Report actual results, failed tests, warnings and unresolved issues.

Do not claim 100% completion if any mandatory requirement fails.

</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-11-12T22:11:29+05:30.

The user's current state is as follows:
Active Document: c:\Users\sony\Desktop\Yotta\data\sql\schema.sql (LANGUAGE_UNSPECIFIED)
Cursor is on line: 1
Other open documents:
- c:\Users\sony\Desktop\Yotta\src\datagen\export.py (LANGUAGE_UNSPECIFIED)
- c:\Users\sony\Desktop\Yotta\README.md (LANGUAGE_UNSPECIFIED)
- c:\Users\sony\Desktop\Yotta\tests\test_validation_integration.py (LANGUAGE_UNSPECIFIED)
- c:\Users\sony\Desktop\Yotta\ai\prompts\04_phase4_derived_validation.md (LANGUAGE_UNSPECIFIED)
- c:\Users\sony\Desktop\Yotta\tests\test_config.py (LANGUAGE_UNSPECIFIED)
</ADDITIONAL_METADATA>