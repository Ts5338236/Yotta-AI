# AI Usage & Governance Declaration

This document transparently records how Artificial Intelligence (AI) tools were employed in the architectural design, schema drafting, and code implementation of Phase 1 of the Procure-to-Pay Synthetic Data Generator.

---

## 1. AI Tools Utilized

- **AI Model**: Antigravity Assistant (Google DeepMind - Gemini 3.8 Flash).
- **Execution Environment**: Windows 11 PowerShell pair-programming environment.
- **Reference Implementation Prompt**: Stored verbatim at `ai/prompts/01_phase1_foundation.md`.

---

## 2. AI Assistance in Architecture & Design

AI assisted in the following architectural design aspects:
- **Relational Normalization**: Structuring the 18 core and auxiliary procurement entities into third normal form (3NF).
- **Relational Integrity Design**: Designing compound foreign keys in SQLite (e.g. `FOREIGN KEY (rfq_id, supplier_id) REFERENCES rfq_supplier_invites(rfq_id, supplier_id)`) to enforce at the relational engine level that uninvited vendors cannot submit quotations.
- **Monetary Storage Modeling**: Formulating the decision to represent monetary values in SQLite as `INTEGER` minor units (cents) rather than floating-point `REAL`, eliminating IEEE 754 rounding inaccuracies.
- **Package Modularity**: Structuring the repository under Python's `src`-layout (`src/datagen` and `src/validate`) with isolation of configuration, identifiers, and foreign exchange logic.

---

## 3. AI Assistance in Code Generation

AI generated the following code modules:
1. `src/datagen/config.py`: Strict schema validation for YAML configurations without default fallback substitutions.
2. `src/datagen/ids.py`: State-isolated, zero-padded, collision-free `IDFactory` with regex validation.
3. `src/datagen/fx.py`: High-precision `decimal.Decimal` FX engine adhering to `ROUND_HALF_UP` quantization.
4. `src/datagen/cli.py` & `__main__.py`: Modular CLI using `argparse`.
5. `src/validate/checks.py` & `__main__.py`: Foundational SQLite database and schema integrity validators.
6. `data/sql/schema.sql`: Complete DDL schema containing 18 tables with primary keys, foreign keys, CHECK constraints, and performance indexes.
7. `tests/`: 31 comprehensive unit and integration tests across 4 test modules (`test_config.py`, `test_fx.py`, `test_ids.py`, `test_schema.py`).

---

## 4. Verification & Testing of Generated Code

- **Automated Test Execution**: All 31 automated tests were executed using `pytest -v` and passed with 100% pass rate (31/31 passed in 0.70 seconds).
- **CLI Verification**: The CLI entry points (`python -m datagen --validate-config`, `python -m datagen --init-db data/test.db`, and `python -m validate data/test.db`) were executed and verified against real SQLite instances.
- **Foreign Key Violation Testing**: Automated tests explicitly attempted to insert orphaned records and uninvited supplier quotes to ensure SQLite `PRAGMA foreign_keys = ON` actively rejected illegal states.

---

## 5. Items Requiring Human Review (TODO)

The following items are designated for human developer evaluation and sign-off:

- [ ] **TODO: Human Assessment of Schema Coverage**: Verify whether 18 tables and relationships adequately cover future YottaFlex AI domain requirements.
- [ ] **TODO: Human Assessment of Scale Parameters**: Confirm whether Starter (30 requesters, 12 suppliers, 115 PRs) and Full (300 requesters, 120 suppliers, 1150 PRs) scale values meet performance test targets.
- [ ] **TODO: Human Assessment of Exchange Rates**: Review whether the static planning exchange rates (USD 1.0, INR 0.012, EUR 1.08, GBP 1.27, JPY 0.0067) align with enterprise assumptions.
- [ ] **TODO: Human Approval for Phase 2 Transition**: Explicit developer approval required prior to beginning master data generation in Phase 2.

---

## 6. Known Limitations (Phase 1)

1. **No Data Generation in Phase 1**: By design, Phase 1 only creates the architectural and schema foundation; no business records (PRs, POs, deliveries) are generated yet.
2. **Fixed Exchange Rates**: Exchange rates are static for the entire fiscal year; daily currency volatility curves are not modeled in Phase 1.
3. **No AP / Invoicing Engine**: The `SPEND` budget event models synthetic expenditure upon delivery; actual invoice ingestion and payment matching are outside project scope.
