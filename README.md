# Procure-to-Pay Synthetic Data Generator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Phase 2 Complete](https://img.shields.io/badge/Status-Phase%202%20Complete-green.svg)]()

Production-quality Procure-to-Pay (P2P) Synthetic Data Generator built for the **YottaFlex AI** technical coding round.

---

## 1. Project Introduction & Objectives

The **Procure-to-Pay Synthetic Data Generator** is an enterprise data engineering framework designed to simulate an authentic corporate procurement lifecycle. The platform generates realistic, normalized, relational procurement datasets with controlled anomalies for testing downstream data warehouses, fraud detection systems, and machine learning models.

### Key Capabilities (Phase 1 & Phase 2 Complete):
- **Master Data Generation**: Organizational hierarchy (Departments, Budgets, Requesters with DAG reporting trees, and Suppliers).
- **Purchase Requisitions**: Itemized Purchase Requests and Request Lines with category-based log-normal pricing and 2026 calendar seasonality.
- **Relational Integrity**: 100% normalized 3NF relational schema in SQLite enforcing strict foreign keys, unique constraints, and check constraints.
- **Deterministic & Reproducible**: Fully reproducible sequence identifiers and zero uncontrolled randomness (single shared RNG pass-through).
- **Financial Precision**: Absolute precision in monetary amounts and currency conversions using Python `decimal.Decimal` and SQLite integer minor units.

> **Status Notice**: Phase 1 (Foundation & Schema) and **Phase 2 (Master Data & Purchase Requests)** are **COMPLETE**. Downstream sourcing (RFQs, Quotes), approvals, purchase orders, deliveries, and anomaly injection will be implemented in Phases 3 through 7.

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
│   └── default.yaml            # Centralized system, scale, distribution & seasonality config
├── src/
│   ├── datagen/                # Core generator package
│   │   ├── __init__.py         # Package marker & generate_phase2_dataset entry point
│   │   ├── __main__.py         # datagen execution entry point
│   │   ├── cli.py              # CLI argument parser (argparse)
│   │   ├── config.py           # Strict YAML config parser & validator
│   │   ├── ids.py              # Centralized deterministic IDFactory
│   │   ├── fx.py               # Deterministic Decimal FX engine
│   │   ├── masters.py          # Master data generator (Depts, Budgets, Reqs, Sups)
│   │   └── requests.py         # Purchase requests & lines with log-normal pricing
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
│   ├── architecture.md         # System architecture & Mermaid data flow
│   ├── data_dictionary.md      # Comprehensive field-level data dictionary
│   ├── assumptions.md          # Classified assumptions & technical decisions
│   ├── validation_summary.md   # Test results & validation roadmap
│   ├── reproducibility.md      # Determinism & environment guide
│   ├── source_manifest.md      # Source inventory of all components
│   └── AI_USAGE.md             # Transparent AI governance log
├── tests/                      # Automated pytest suite (46 unit tests)
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_determinism.py     # Determinism & seed verification
│   ├── test_distributions.py   # Price & seasonality distribution verification
│   ├── test_fx.py
│   ├── test_ids.py
│   ├── test_masters.py         # Master data generator unit tests
│   ├── test_requests.py        # Purchase requests & lines unit tests
│   └── test_schema.py
└── ai/
    └── prompts/
        ├── 01_phase1_foundation.md
        └── 02_phase2_generation.md
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

4. Set the Python path:
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

## 5. Generating Synthetic Data (Phase 2)

Execute data generation directly through the CLI:

```powershell
# Generate starter scale dataset (default)
python -m datagen --generate

# Generate full scale dataset with specific seed
python -m datagen --generate --scale full --seed 20261022
```

Sample CLI Output:
```text
=== Phase 2 Data Generation Successful ===
Scale Tier        : starter
Random Seed       : 20261022
Departments       : 10
Budgets           : 10
Requesters        : 30
Suppliers         : 12
Purchase Requests : 115
Request Lines     : 217
Total Est. Spend  : $602,837.12 USD
```

### Programmatic Python Usage:
```python
from datagen import generate_phase2_dataset

dataset = generate_phase2_dataset(scale="starter", seed=20261022)
print(f"Generated {len(dataset['purchase_requests'])} requests.")
```

---

## 6. Database Schema Initialization & Validation

To initialize an empty SQLite database schema:

```powershell
python -m datagen --init-db data/p2p_procurement.db
```

To run foundational schema integrity and foreign-key checks:

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

All 46 unit tests cover:
- Master data counts, unique keys, manager DAG hierarchy, and currency compliance.
- Requisition departmental consistency, budget references, and derived spend reconciliation.
- Category log-normal price bounds and 2026 monthly seasonality trends.
- Deterministic byte-for-byte reproducibility across runs with identical seeds.
- Centralized `IDFactory` formatting, sequence independence, and regex validations.
- High-precision Decimal foreign exchange conversions.
- SQLite foreign key enforcement, unique constraints, and check constraints.

---

## 8. Development Roadmap

| Phase | Milestone | Scope | Status |
| :---: | :--- | :--- | :---: |
| **Phase 1** | **Project Foundation & Architecture** | Package structure, SQLite schema, IDFactory, FX engine, config management, docs, foundational tests | **COMPLETED** |
| **Phase 2** | **Master Data & Purchase Requests** | Departments, Budgets, Requesters (DAG), Suppliers, PRs, Request Lines, Log-normal Pricing, Seasonality | **COMPLETED** |
| Phase 3 | Requisition & Sourcing | Sourcing procedure, RFQs, Supplier Invitations, Multi-Currency Quotations | Upcoming |
| Phase 4 | Approval & Purchasing | Multi-level approvals, supplier scoring, PO creation, Budget commitments | Upcoming |
| Phase 5 | Delivery & Lifecycle | Deliveries, partial receipts, budget spend events, status transitions | Upcoming |
| Phase 6 | Anomaly Injection | Split POs, budget overruns, phantom vendors, late shipments | Upcoming |
| Phase 7 | Export & Verification | CSV/JSON exports, cross-entity reconciliation, audit ground truth | Upcoming |
