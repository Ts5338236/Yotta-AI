# Procure-to-Pay Synthetic Data Generator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Phase 3 Complete](https://img.shields.io/badge/Status-Phase%203%20Complete-green.svg)]()

Production-quality Procure-to-Pay (P2P) Synthetic Data Generator built for the **YottaFlex AI** technical coding round.

---

## 1. Project Introduction & Objectives

The **Procure-to-Pay Synthetic Data Generator** is an enterprise data engineering framework designed to simulate an authentic corporate procurement lifecycle. The platform generates realistic, normalized, relational procurement datasets with controlled anomalies for testing downstream data warehouses, fraud detection systems, and machine learning models.

### Key Capabilities (Phases 1, 2, and 3 Complete):
- **Master Data Generation**: Organizational hierarchy (Departments, Budgets, Requesters with DAG reporting trees, Approvers, and Suppliers).
- **Purchase Requisitions**: Itemized Purchase Requests and Request Lines with category-based log-normal pricing and 2026 calendar seasonality.
- **Multi-Level Approvals**: Tiered approval routing by total estimate ($2,000 line manager, $25,000 department head, >$25,000 corporate finance) with natural ~5% business rejections.
- **Sourcing & RFQ Execution**: Strategic classification (competitive vs non-competitive), RFQ creation, supplier invitations (3–6 per RFQ), multi-currency supplier quotes with landed costs, multicriteria scoring (60% cost, 25% lead time, 15% risk), and quote awards.
- **Purchase Orders & Deliveries**: Competitive (quote-backed) and non-competitive (direct-requisition) POs, single on-time/late deliveries, and multi-shipment partial fulfillments.
- **Double-Entry Budget Ledger**: Double-entry financial event tracking (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`) with zero clean-path overruns and exact balance reconciliation.
- **Lifecycle Event Auditing**: Comprehensive status event tracking across PR, RFQ, PO, and Delivery state lifecycles.
- **Relational Integrity**: 100% normalized 3NF relational schema in SQLite enforcing strict foreign keys, unique constraints, and check constraints across all 18 tables.
- **Deterministic & Reproducible**: Fully reproducible sequence identifiers and zero uncontrolled randomness (single shared RNG pass-through).
- **Financial Precision**: Absolute precision in monetary amounts and currency conversions using Python `decimal.Decimal` and SQLite integer minor units.

> **Status Notice**: Phase 1 (Foundation & Schema), Phase 2 (Master Data & Requests), and **Phase 3 (Complete Procurement Workflow)** are **COMPLETE**. Downstream derived analytics, reporting, and anomaly injection will be implemented in subsequent phases.

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
│   │   ├── __init__.py         # Package marker & generation entry points
│   │   ├── __main__.py         # datagen execution entry point
│   │   ├── cli.py              # CLI argument parser (argparse)
│   │   ├── config.py           # Strict YAML config parser & validator
│   │   ├── ids.py              # Centralized deterministic IDFactory
│   │   ├── fx.py               # Deterministic Decimal FX engine
│   │   ├── masters.py          # Master data generator (Depts, Budgets, Reqs, Approvers, Sups)
│   │   ├── requests.py         # Purchase requests & lines with log-normal pricing
│   │   ├── approvals.py        # Multi-tiered approval workflow generator
│   │   ├── sourcing.py         # Sourcing classifier, RFQs, quotes & scoring
│   │   ├── orders.py           # Competitive & non-competitive PO generator
│   │   ├── delivery.py         # Delivery receipts & partial fulfillment generator
│   │   ├── budget.py           # Double-entry ledger events & balance reconciliation
│   │   ├── events.py           # Status event lifecycle audit tracker
│   │   └── workflow.py         # End-to-end workflow orchestrator & validation
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
│   ├── architecture.md         # System architecture & pipeline data flows
│   ├── data_dictionary.md      # Comprehensive field-level data dictionary (all 18 tables)
│   ├── assumptions.md          # Classified assumptions & technical decisions
│   ├── validation_summary.md   # Test results & validation roadmap
│   ├── reproducibility.md      # Determinism & environment guide
│   ├── source_manifest.md      # Source inventory of all components
│   └── AI_USAGE.md             # Transparent AI governance log
├── tests/                      # Automated pytest suite (66 unit tests)
│   ├── __init__.py
│   ├── test_approvals.py       # Multi-level approval tests
│   ├── test_budget.py          # Double-entry budget ledger tests
│   ├── test_config.py          # Configuration parser tests
│   ├── test_delivery.py        # Delivery & partial shipment tests
│   ├── test_determinism.py     # Determinism & seed verification
│   ├── test_distributions.py   # Price & seasonality distribution verification
│   ├── test_fx.py              # Foreign exchange conversion tests
│   ├── test_ids.py             # Centralized IDFactory tests
│   ├── test_masters.py         # Master data generator unit tests
│   ├── test_orders.py          # Purchase order unit tests
│   ├── test_quotes.py          # Multi-currency quotation & scoring tests
│   ├── test_requests.py        # Purchase requests & lines unit tests
│   ├── test_schema.py          # SQLite schema & foreign key constraint tests
│   ├── test_sourcing.py        # Sourcing classification & RFQ tests
│   ├── test_status_events.py   # Status event audit lifecycle tests
│   └── test_workflow_integration.py # Full workflow integration & balance tests
└── ai/
    └── prompts/
        ├── 01_phase1_foundation.md
        ├── 02_phase2_generation.md
        └── 03_phase3_procurement_workflow.md
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

## 5. Generating Synthetic Data (Phase 3 Complete Workflow)

Execute the end-to-end clean procurement data generation workflow through the CLI:

```powershell
# Generate starter scale dataset (default)
python -m datagen --generate

# Generate full scale dataset with specific seed
python -m datagen --generate --scale full --seed 20261022
```

Sample CLI Output (Starter Scale):
```text
=== Phase 3 Clean Procurement Workflow Successful ===
Scale Tier            : starter
Random Seed           : 20261022
Departments           : 10
Budgets               : 10
Requesters            : 30
Approvers             : 22
Suppliers             : 12
Purchase Requests     : 115
Request Lines         : 217
Total PR Estimate     : $602,837.12 USD
Approval Events       : 97 (92 Approved, 5 Rejected)
RFQs Issued           : 50
RFQ Supplier Invites  : 183
Supplier Quotations   : 183 (50 Awarded)
Purchase Orders       : 93 (50 Competitive, 43 Non-Competitive)
PO Lines              : 173
Deliveries            : 101 (Fulfillments: on-time, late, partial)
Budget Events         : 390 (Allocated, Reserved, Committed, Released, Spent)
Status Events         : 930 (Full Lifecycle Audit Trail)
Clean-Path Validation : PASSED (0 Overruns, 0 Discrepancies)
```

### Programmatic Python Usage:
```python
from datagen.workflow import generate_procurement_workflow, run_clean_path_validation

dataset = generate_procurement_workflow(scale="starter", seed=20261022)
val_results = run_clean_path_validation(dataset)
assert val_results["is_valid"] is True
print(f"Generated {len(dataset['purchase_orders'])} purchase orders with zero budget overruns.")
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

All 66 automated tests cover:
- Master data counts, unique keys, manager DAG hierarchy, and currency compliance.
- Requisition departmental consistency, budget references, and derived spend reconciliation.
- Multi-tier approval thresholds ($2K, $25K, >$25K), approver role resolution, and rejection terminal states.
- Strategic sourcing classification, RFQ invitation pools, multi-currency quote landed costs, and multicriteria scoring.
- Competitive (quote-derived) and non-competitive (direct-line) purchase orders and item lines.
- Delivery lifecycle states, on-time delivery (~80%), late delivery (~10%), and multi-shipment partial fulfillments (~10%).
- Double-entry budget ledger integrity (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`) with zero clean-path overruns.
- Complete state transition audit events for PR, RFQ, PO, and Delivery lifecycles.
- Category log-normal price bounds and 2026 monthly seasonality trends.
- Deterministic byte-for-byte reproducibility across runs with identical seeds.
- Centralized `IDFactory` formatting, sequence independence, and regex validations.
- High-precision Decimal foreign exchange conversions.
- SQLite foreign key enforcement, compound references, unique constraints, and check constraints across all 18 tables.

---

## 8. Development Roadmap

| Phase | Milestone | Scope | Status |
| :---: | :--- | :--- | :---: |
| **Phase 1** | **Project Foundation & Architecture** | Package structure, SQLite schema, IDFactory, FX engine, config management, docs, foundational tests | **COMPLETED** |
| **Phase 2** | **Master Data & Purchase Requests** | Departments, Budgets, Requesters (DAG), Suppliers, PRs, Request Lines, Log-normal Pricing, Seasonality | **COMPLETED** |
| **Phase 3** | **Complete Procurement Workflow** | Multi-level Approvals, RFQs, Supplier Quotes & Scoring, POs, Deliveries, Budget Ledger, Lifecycle Events | **COMPLETED** |
| Phase 4 | Derived Analytics & KPI Engine | Cycle times, supplier performance metrics, spend analytics, materialization views | Upcoming |
| Phase 5 | Data Export & Storage Engine | CSV / JSON export engine, relational SQLite ingestion, bulk insert optimization | Upcoming |
| Phase 6 | Anomaly Injection Engine | Split POs, budget overruns, phantom vendors, off-contract spend, late deliveries | Upcoming |
| Phase 7 | End-to-End Validation & Audit | Cross-entity reconciliation, audit ground truth manifest, production test bench | Upcoming |
