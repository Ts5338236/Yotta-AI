# MASTER IMPLEMENTATION PROMPT
## PHASE 7: FINAL AUDIT, FRESH CLONE VERIFICATION & GITHUB SUBMISSION

You are working on the **YottaFlex Procure-to-Pay Synthetic Data Generator**.

Your task is to perform a complete final audit of the project implemented across Phases 1–6.

This is a quality-assurance and submission-readiness phase. Do not introduce new features or redesign the architecture. Identify and fix genuine defects while preserving all working functionality.

---

## 1. REVIEW THE ORIGINAL REQUIREMENTS

Before auditing:

1. Read the original PRD.
2. Read the original master prompt.
3. Review the completed implementation from Phases 1–6.
4. Review the phase-wise prompt history.
5. Review `AI_USAGE.md`.
6. Review the README and all documentation.

Create a requirement traceability checklist mapping every PRD requirement to:

- Implementation file/module.
- Corresponding test.
- Generated output or documentation.
- Verification result.

Use these statuses:

- PASS
- FAIL
- PARTIAL
- NOT IMPLEMENTED

Do not mark a requirement as PASS without evidence.

---

## 2. COMPLETE PROJECT STRUCTURE AUDIT

Inspect the repository for:

- Missing files.
- Duplicate modules.
- Unused code.
- Temporary scripts.
- Debugging statements.
- Hardcoded paths.
- Hardcoded record IDs.
- Unnecessary dependencies.
- Inconsistent naming.
- Missing type hints where appropriate.
- Missing error handling.
- Incorrect import paths.
- Circular imports.
- Untracked output files.

Remove only unnecessary artifacts.

Do not delete required documentation, prompts, generated outputs, or test fixtures.

---

## 3. FRESH CLONE VERIFICATION

The most important requirement is that the project works from a clean environment.

Simulate a fresh clone using a separate temporary directory.

Follow these steps:

1. Clone the repository into a clean directory.
2. Create a new Python virtual environment.
3. Install dependencies using the documented installation command.
4. Verify package imports.
5. Load the configuration.
6. Generate the starter dataset.
7. Run all validations.
8. Inject anomalies.
9. Run independent anomaly detection.
10. Evaluate detection results against ground truth.
11. Confirm all tests pass.
12. Verify zero warnings, zero errors.
