# Source Code & Artifact Manifest

This manifest documents all files, modules, schemas, and configurations created in Phase 1 of the Procure-to-Pay Synthetic Data Generator.

---

## 1. Core Source Packages (`src/`)

### `src/datagen/`
- **`__init__.py`**: Declares `datagen` package namespace and exports package version (`1.0.0`).
- **`__main__.py`**: Module-level entry point forwarding execution to `datagen.cli:main`.
- **`cli.py`**: Command-line interface built with `argparse`, supporting `--init-db`, `--validate-config`, and `--version`.
- **`config.py`**: Robust YAML configuration loader implementing strict type checks, business threshold validations, and custom exceptions (`ConfigValidationError`).
- **`ids.py`**: Centralized `IDFactory` class maintaining deterministic entity counters, zero-padded formatting, delivery sequencing per PO, and canonical regex patterns (`ID_REGEX_MAP`).
- **`fx.py`**: Fixed Foreign Exchange engine calculating deterministic conversions with `decimal.Decimal`, `ROUND_HALF_UP` rounding, and integer minor-unit conversion helpers (`to_minor_units`, `from_minor_units`).

### `src/validate/`
- **`__init__.py`**: Declares `validate` package namespace and exports package version (`1.0.0`).
- **`__main__.py`**: Module-level entry point forwarding execution to `validate.checks:main`.
- **`checks.py`**: Foundational database and schema integrity validators (`check_foreign_keys_enabled`, `check_schema_integrity`, `check_required_tables_exist`, `run_foundational_checks`).

---

## 2. Configuration & Data Schemas

### `config/`
- **`default.yaml`**: Centralized configuration specifying project metadata, starter/full scale parameters, approval tiers, supplier scoring weights, anomaly rate envelopes, procurement constraints, and fixed FX rates.

### `data/`
- **`sql/schema.sql`**: Canonical SQLite DDL script defining 18 normalized tables with primary keys, foreign keys (`ON DELETE RESTRICT`), unique constraints, and check constraints for all enums and non-negative monetary fields.
- **`sql/seed.sql`**: SQL seed script placeholder for future master data generation.
- **`csv/.gitkeep`**: Placeholder preserving CSV export directory structure.
- **`json/.gitkeep`**: Placeholder preserving JSON export directory structure.

---

## 3. Test Suite (`tests/`)

- **`__init__.py`**: Test package marker.
- **`test_config.py`**: Unit tests validating successful config loading and rejection of invalid sections, inverted thresholds, non-summing weights, negative FX rates, and invalid scale numbers (7 tests).
- **`test_fx.py`**: Unit tests validating all currency pairs (USD, EUR, GBP, INR, JPY), unsupported currencies, zero amounts, negative numbers, decimal rounding, and determinism (11 tests).
- **`test_ids.py`**: Unit tests validating all 18 ID patterns, counter independence, multi-delivery sequencing per PO, reset functionality, and collision resistance (7 tests).
- **`test_schema.py`**: Database integration tests validating schema creation, foreign-key enforcement, unique constraints, CHECK constraints, 1:1 RFQ constraints, and RFQ quote invitation requirements (6 tests).

---

## 4. Documentation (`docs/`)

- **`architecture.md`**: Complete system architecture, package boundaries, data flows, and Mermaid ER diagram.
- **`data_dictionary.md`**: Field-level data dictionary for all 18 tables including types, constraints, allowed values, and units.
- **`assumptions.md`**: Explicit categorization of requirements (Category A), technical design choices (Category B), and operational assumptions (Category C).
- **`validation_summary.md`**: Test execution report, coverage matrix, and roadmap for future validation phases.
- **`reproducibility.md`**: Determinism guidelines, random seeding strategy, and environment setup.
- **`source_manifest.md`**: Comprehensive inventory of files, modules, and roles.
- **`AI_USAGE.md`**: Transparent accounting of AI assistance, code generation, human review items, and testing.

---

## 5. Repository Root Configuration

- **`pyproject.toml`**: Standard packaging metadata, build system configuration (`setuptools`), dependencies, and console script entry points (`p2p-datagen`, `p2p-validate`).
- **`requirements.txt`**: Pinned core and dev dependencies (`numpy==2.2.3`, `pandas==2.2.3`, `PyYAML==6.0.3`, `pytest==9.2.0`).
- **`.gitignore`**: Git exclusion rules for Python caches, virtual environments, SQLite database files, and local IDE configs.
- **`README.md`**: Comprehensive project guide, setup instructions, architecture overview, and phase roadmap.
