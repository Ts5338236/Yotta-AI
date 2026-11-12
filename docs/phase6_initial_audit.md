# Phase 6 Initial Repository & Export Audit Report

**Project**: YottaFlex Procure-to-Pay Synthetic Data Generator  
**Audit Date**: 2026-11-12  
**Auditor**: Senior Python Data Engineer, Database Architect & QA Lead  
**Scope**: Pre-implementation inspection of data export, SQLite database generation, SQL schema/seed artifacts, and test coverage for Phase 6.

---

## 1. Executive Summary of Initial State

An exhaustive audit of the repository was conducted before writing Phase 6 implementations. The core procurement pipeline (Phases 1–5) is mathematically sound, deterministic, fully integrated, and verified with **148 passing automated tests**.

However, the existing export and persistence layer exhibits significant gaps relative to Phase 6 specifications:
1. `src/datagen/database.py` is **missing**; SQLite database generation is currently partially implemented inside `export.py` rather than as a dedicated, transactional database persistence layer.
2. `src/validate/export_checks.py` is **missing**; cross-format verification between CSV, JSON, and SQLite is not encapsulated in an autonomous validator module.
3. `data/sql/seed.sql` is a **4-line placeholder file** lacking actual SQL `INSERT` statements.
4. `data/database/procurement.db` does not exist (an older file `data/p2p_procurement.db` existed in the root of `data/`).
5. `data/ground_truth/` does not exist as an independent directory; ground truth was previously embedded alongside operational tables.
6. The 8 dedicated Phase 6 export test modules (`test_csv_export.py`, `test_json_export.py`, `test_database_export.py`, `test_sql_schema.py`, `test_sql_seed.py`, `test_export_integrity.py`, `test_export_determinism.py`, `test_ground_truth_export.py`) are **not yet created**.

---

## 2. Existing Export Implementation vs. Required Architecture

### A. Existing Export Code (`src/datagen/export.py`)
- Provides baseline functions `export_to_csv`, `export_to_json`, `export_to_sqlite`, and `export_to_sql_seed`.
- Handles data formatting for basic tabular output.
- **Shortcomings**:
  - Does not enforce strict separation between operational entities and ground truth in directory paths (`data/ground_truth/`).
  - Does not provide standalone database connection management, transaction rollback on failure, or dedicated schema migration helpers.
  - Mixes database build logic with file serialization logic.

### B. Missing Database Architecture (`src/datagen/database.py`)
A dedicated module `src/datagen/database.py` must be built to:
- Connect to SQLite with `PRAGMA foreign_keys = ON;`.
- Apply transactions for bulk row insertion without `INSERT OR IGNORE`.
- Guarantee topological insertion order (parent tables before dependent child tables).
- Implement explicit error handling with automatic rollback on integrity violation.
- Run `PRAGMA integrity_check` (asserting `ok`) and `PRAGMA foreign_key_check` (asserting zero violations).
- Output the database to the canonical path `data/database/procurement.db` and `output/database/procurement.db`.

### C. Missing SQL Seed Architecture (`data/sql/seed.sql`)
- The current `data/sql/seed.sql` contains placeholder comments from Phase 1.
- Must be replaced with a real, generated, self-contained SQL script containing formatted `INSERT` statements for all 18 procurement tables, preserving topological FK dependency order, string escaping, NULL handling, and integer minor units.

### D. Ground Truth Isolation (`data/ground_truth/`)
- Ground truth records must be completely isolated from operational tables.
- Must generate `data/ground_truth/ground_truth.csv` and `data/ground_truth/ground_truth.json` containing `anomaly_id`, `issue_type`, `entity`, `record_id`, `expected_decision`, `reason`, and `metadata`.

### E. Missing Validation Module (`src/validate/export_checks.py`)
- An independent export integrity validator must be created to verify:
  - CSV header and row count alignment with in-memory datasets.
  - JSON parseability and record count alignment.
  - SQLite table counts, primary key uniqueness, foreign key integrity, and PRAGMA status.
  - Cross-format consistency: verifying that CSV, JSON, and SQLite contain identical logical records without data corruption or type degradation.

---

## 3. Test Suite Status & Baseline Execution

- **Baseline Test Execution**: `pytest tests/ -v`
- **Result**: `148 passed in 35.03s`
- **Existing Coverage**:
  - Foundational config, ID generation, FX conversion (Phases 1–2).
  - Workflow, approvals, quotes, POs, deliveries, budget events, status events (Phase 3).
  - Derived fields, primary keys, foreign keys, financial reconciliation, lifecycle, dates (Phase 4).
  - Anomaly injection, independent detectors, metrics evaluation (Phase 5).
  - Baseline export smoke tests in `tests/test_export.py`.

---

## 4. Required Modifications & Implementation Plan

| Step | Action Item | Target File / Artifact |
| :---: | :--- | :--- |
| **Step 1** | Initial repository audit report | `docs/phase6_initial_audit.md` |
| **Step 2** | Refactor export architecture & separate database engine | `src/datagen/export.py` |
| **Step 3** | Implement standalone SQLite database manager | `src/datagen/database.py` |
| **Step 4** | Build independent export integrity validator | `src/validate/export_checks.py` |
| **Step 5** | Generate populated SQL seed script | `data/sql/seed.sql` & `output/sql/seed.sql` |
| **Step 6** | Generate isolated ground-truth exports | `data/ground_truth/ground_truth.csv/.json` |
| **Step 7** | Create 8 dedicated test suites | `tests/test_*_export*.py`, `tests/test_sql_*.py` |
| **Step 8** | Generate starter and full-scale datasets to disk | `data/` and `output/` directories |
| **Step 9** | Execute export integrity audit and generate reports | `docs/export_integrity_report.md/.json` |
| **Step 10** | Document export specifications & complete Phase 6 report | `docs/export_specification.md`, `docs/phase6_completion_report.md` |

