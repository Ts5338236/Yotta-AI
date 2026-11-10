# Procure-to-Pay Synthetic Data Generator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Phase 1 Foundation](https://img.shields.io/badge/Status-Phase%201%20Foundation-orange.svg)]()

Production-quality Procure-to-Pay (P2P) Synthetic Data Generator built for the **YottaFlex AI** technical coding round.

---

## 1. Project Introduction & Objectives

The **Procure-to-Pay Synthetic Data Generator** is an enterprise data engineering framework designed to simulate an authentic corporate procurement lifecycle. The platform generates realistic, normalized, relational procurement datasets with controlled anomalies for testing downstream data warehouses, fraud detection systems, and machine learning models.

### Primary Objectives:
- **Relational Integrity**: 100% normalized 3NF relational schema in SQLite enforcing strict foreign keys, unique constraints, and check constraints.
- **Deterministic & Reproducible**: Fully reproducible sequence identifiers and zero uncontrolled randomness.
- **Financial Precision**: Absolute precision in monetary amounts and currency conversions using Python `decimal.Decimal` and SQLite integer minor units.
- **Traceable Ledger**: Complete auditability of budget movements (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`) and entity status transitions.

> **Status Notice**: This repository currently implements **Phase 1: Project Foundation & Architecture**. Data generation modules (master data, PRs, RFQs, POs, deliveries) will be implemented in Phases 2 through 7.

---

## 2. Technical Stack

- **Runtime**: Python 3.11+ (tested on Python 3.12.3)
- **Data Engineering**: NumPy (2.2.3), Pandas (2.2.3), PyYAML (6.0.3)
- **Database Engine**: SQLite 3 with `PRAGMA foreign_keys = ON`
- **Testing & Verification**: pytest (9.2.0)
- **Standard Library Modules**: `decimal`, `hashlib`, `pathlib`, `argparse`, `sqlite3`

---

## 3. Repository Structure

```
procure-to-pay-datagen/
├── .gitignore                  # Git ignore rules
├── pyproject.toml              # Build & packaging configuration
├── requirements.txt            # Pinned production dependencies
├── README.md                   # Project documentation & user guide
├── config/
│   └── default.yaml            # Centralized system & scale configuration
├── src/
│   ├── datagen/                # Core generator package
│   │   ├── __init__.py         # Package marker & version
│   │   ├── __main__.py         # datagen execution entry point
│   │   ├── cli.py              # CLI argument parser (argparse)
│   │   ├── config.py           # Strict YAML config parser & validator
│   │   ├── ids.py              # Centralized deterministic IDFactory
│   │   └── fx.py               # Deterministic Decimal FX engine
│   └── validate/               # Quality assurance package
│       ├── __init__.py
│       ├── __main__.py         # validate execution entry point
│       └── checks.py           # Foundational database integrity checks
├── data/
│   ├── csv/                    # Destination for CSV exports (.gitkeep)
│   ├── json/                   # Destination for JSON exports (.gitkeep)
│   └── sql/
│       ├── schema.sql          # Canonical DDL defining 18 normalized tables
│       └── seed.sql            # Seed SQL script placeholder
├── docs/                       # Architectural & design specifications
│   ├── architecture.md         # System architecture & Mermaid ER diagram
│   ├── data_dictionary.md      # Comprehensive field-level data dictionary
│   ├── assumptions.md          # Classified assumptions & technical decisions
│   ├── validation_summary.md   # Test results & validation roadmap
│   ├── reproducibility.md      # Determinism & environment guide
│   ├── source_manifest.md      # Source inventory of all components
│   └── AI_USAGE.md             # Transparent AI governance log
├── tests/                      # Automated pytest suite (31 unit tests)
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_fx.py
│   ├── test_ids.py
│   └── test_schema.py
└── ai/
    └── prompts/
        └── 01_phase1_foundation.md
```

---

## 4. Installation & Environment Setup

### Windows (PowerShell)

1. Clone or navigate to the repository directory:
   ```powershell
   cd C:\Users\sony\Desktop\Yotta
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install pinned dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Install the package in editable mode or configure the Python path:
   ```powershell
   $env:PYTHONPATH = "src"
   ```

### Linux / macOS (Bash)

```bash
cd procure-to-pay-datagen
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

---

## 5. Configuration Management

Configuration is centralized in `config/default.yaml` and strictly validated by `src/datagen/config.py`.

To validate the configuration via CLI:

```powershell
python -m datagen --validate-config
```

### Configuration Sections:
- **`project`**: Metadata, fiscal year (`2026`), base currency (`USD`), base date (`2026-01-01`).
- **`scale`**: Dataset volume definitions for `starter` and `full` tiers.
- **`approval_thresholds`**: Financial signing limits (`manager_limit: 2000`, `department_head_limit: 25000`).
- **`supplier_scoring`**: Multicriteria evaluation weights summing to 1.0 (cost: 0.60, lead time: 0.25, risk: 0.15).
- **`anomalies`**: Target anomaly rate envelope (`0.03` to `0.05`).
- **`procurement`**: Quotation constraints (`minimum_quotes: 3`, `maximum_quotes: 6`).
- **`fx_rates`**: Fixed conversion factors for USD, EUR, GBP, INR, and JPY.

---

## 6. Database Schema Initialization

The database schema is defined in `data/sql/schema.sql` and includes 18 normalized tables with foreign keys, check constraints, and performance indexes.

To initialize an empty SQLite database schema:

```powershell
# Create an initialized SQLite database
python -m datagen --init-db data/p2p_procurement.db
```

To run foundational schema integrity and foreign-key checks on the database:

```powershell
python -m validate data/p2p_procurement.db
```

Expected output:
```text
=== Foundational Validation Results ===
Foreign Keys Enabled : True
Schema Integrity OK  : True
All Tables Present   : True
FK Violations Count  : 0
Overall Status       : PASSED
```

---

## 7. Running the Test Suite

Execute the full automated test suite using `pytest`:

```powershell
python -m pytest -v
```

All 31 unit tests cover:
- Centralized `IDFactory` formatting, sequence independence, multi-delivery numbering, and regex patterns.
- YAML configuration loading, required key enforcement, threshold validations, and type checking.
- Deterministic FX currency conversions, decimal rounding, and negative value rejection.
- SQLite foreign key enforcement, uniqueness constraints, check constraints, and RFQ invite requirements.

---

## 8. Current Implementation Status & Roadmap

| Phase | Milestone | Scope | Status |
| :---: | :--- | :--- | :---: |
| **Phase 1** | **Project Foundation & Architecture** | Package structure, SQLite schema, IDFactory, FX engine, config management, docs, foundational tests | **COMPLETED** |
| Phase 2 | Master Data Generation | Departments, Budgets, Requesters, Approvers, Suppliers | Upcoming |
| Phase 3 | Requisition & Sourcing | Purchase Requests, Request Lines, RFQs, Supplier Quotes, Quote Lines | Upcoming |
| Phase 4 | Approval & Purchasing | Multi-level approvals, supplier scoring, PO creation, Budget commitments | Upcoming |
| Phase 5 | Delivery & Lifecycle | Deliveries, partial receipts, budget spend events, status transitions | Upcoming |
| Phase 6 | Anomaly Injection | Split POs, budget overruns, phantom vendors, late shipments | Upcoming |
| Phase 7 | Export & Verification | CSV/JSON exports, cross-entity reconciliation, audit ground truth | Upcoming |
