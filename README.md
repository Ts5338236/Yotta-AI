# Procure-to-Pay Synthetic Data Generator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Complete & Submission Ready](https://img.shields.io/badge/Status-Complete%20%26%20Submission%20Ready-green.svg)]()

Production-quality Procure-to-Pay (P2P) Synthetic Data Generator built for the **YottaFlex AI** technical coding round.

---

## 1. Project Introduction & Objectives

The **Procure-to-Pay Synthetic Data Generator** is an enterprise data engineering framework designed to simulate an authentic corporate procurement lifecycle. The platform generates realistic, normalized, relational procurement datasets with controlled anomalies for testing downstream data warehouses, fraud detection systems, and machine learning models.

### Key Capabilities (Phases 1 through 7 Complete):
- **Master Data Generation**: Organizational hierarchy (Departments, Budgets, Requesters with DAG reporting trees, Approvers, and Suppliers).
- **Purchase Requisitions**: Itemized Purchase Requests and Request Lines with category-based log-normal pricing and 2026 calendar seasonality.
- **Multi-Level Approvals**: Tiered approval routing by total estimate ($2,000 line manager, $25,000 department head, >$25,000 corporate finance) with natural ~5% business rejections.
- **Sourcing & RFQ Execution**: Strategic classification (competitive vs non-competitive), RFQ creation, supplier invitations (3–6 per RFQ), multi-currency supplier quotes with landed costs, multicriteria scoring (60% cost, 25% lead time, 15% risk), and quote awards.
- **Purchase Orders & Deliveries**: Competitive (quote-backed) and non-competitive (direct-requisition) POs, single on-time/late deliveries, and multi-shipment partial fulfillments.
- **Double-Entry Budget Ledger**: Double-entry financial event tracking (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`) with zero clean-path overruns and exact balance reconciliation.
- **Lifecycle Event Auditing**: Comprehensive status event tracking across PR, RFQ, PO, and Delivery state lifecycles.
- **Centralized Derived Fields Engine (`derive.py`)**: Pure deterministic recalculation of request line totals, PR estimates, quote landed costs, supplier scores, PO values, delivery fulfillments, current statuses, and budget balances.
- **Independent Validation Suite (`validate/`)**: Strict non-circular auditing across 7 critical domains: primary keys, foreign keys, financial reconciliation, lifecycle state machines, date chronology, approvals & awards, and budget ledgers.
- **Modular Anomaly Injection Engine (`anomalies.py`)**: Post-generation mutations introducing 7 procurement anomaly types (`po_without_approval`, `expired_quote_before_award`, `non_cheapest_quote_without_rationale`, `inactive_supplier_used`, `budget_overrun`, `duplicate_purchase_request`, `quote_currency_mismatch`).
- **Ground Truth Isolation**: Segregated ground truth records with `ANOM-######` IDs and recommended operational decisions (`REJECT`, `DISQUALIFY`, `JUSTIFY_OR_REVERT`, `BLOCK`, `FLAG`, `REVISE`).
- **Independent Anomaly Detectors & Evaluator (`anomaly_checks.py`)**: 7 independent rule-based detectors and an evaluation engine calculating True Positives, False Positives, False Negatives, Precision, Recall, and F1-score (100% precision and 100% recall achieved).
- **Multi-Format Export Engine (`export.py`)**: Seamless disk persistence to CSV (`output/csv/`), JSON (`output/json/`), SQLite database (`output/database/procurement.db`), canonical DDL (`output/sql/schema.sql`), and self-contained SQL seed (`output/sql/seed.sql`).
- **Relational Integrity**: 100% normalized 3NF relational schema in SQLite enforcing strict foreign keys, unique constraints, and check constraints across all 19 tables.
- **Deterministic & Reproducible**: Fully reproducible sequence identifiers and zero uncontrolled randomness (single shared RNG pass-through).
- **Financial Precision**: Absolute precision in monetary amounts and currency conversions using Python `decimal.Decimal` and SQLite integer minor units.

> **Status Notice**: All phases from Phase 1 (Foundation & Architecture) through Phase 7 (Final Audit, Fresh Clone Verification & Submission Readiness) are **100% COMPLETE**. The codebase is verified to run cleanly in fresh environments with 166 passing tests and 100% bitwise determinism.

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
│   │   ├── derive.py           # Centralized derived fields recalculation engine
│   │   ├── anomalies.py        # Modular anomaly injection engine & ground truth generator
│   │   ├── database.py         # Relational SQLite database management & integrity checks
│   │   ├── export.py           # Multi-format exporter, SQL seed & source manifest
│   │   └── workflow.py         # End-to-end workflow orchestrator & validation
│   └── validate/               # Comprehensive quality assurance package
│       ├── __init__.py         # Public exports for validators and models
│       ├── __main__.py         # validate CLI execution entry point
│       ├── models.py           # ValidationCheckResult & ValidationReport classes
│       ├── checks.py           # 7-domain independent auditing engine & SQLite checks
│       ├── anomaly_checks.py   # Independent anomaly detectors & evaluation engine
│       └── export_checks.py    # Multi-format export integrity & cross-format validation
├── data/
│   ├── csv/                    # 17 operational CSV tables
│   ├── json/                   # 18 operational & metadata JSON files
│   ├── database/               # Relational SQLite procurement.db
│   ├── sql/
│   │   ├── schema.sql          # Canonical 19-table DDL schema
│   │   └── seed.sql            # Populated sequential SQL seed script
│   └── ground_truth/           # Segregated anomaly ground truth (CSV/JSON)
├── docs/                       # Architectural & design specifications
│   ├── architecture.md         # System architecture & pipeline data flows
│   ├── anomaly_catalog.md      # Detailed anomaly specifications, injection logic & detection criteria
│   ├── data_dictionary.md      # Comprehensive field-level data dictionary (all 19 tables)
│   ├── export_specification.md # Multi-format export engine technical specification
│   ├── export_integrity_report.md # Verification audit of exported deliverables
│   ├── phase6_completion_report.md # Phase 6 completion and sign-off report
│   ├── assumptions.md          # Classified assumptions & technical decisions
│   ├── prompt_history.md       # Master prompt index & phase milestones trajectory
│   ├── validation_summary.md   # Machine-generated markdown validation report
│   ├── validation_summary.json # Machine-readable JSON validation report
│   ├── reproducibility.md      # Determinism & environment guide
│   ├── source_manifest.md      # Source inventory of all components
│   └── AI_USAGE.md             # Transparent AI governance log
├── tests/                      # Automated pytest suite (166 unit & integration tests)
│   ├── __init__.py
│   ├── test_anomaly_injection.py      # Anomaly injection engine & candidate tests
│   ├── test_anomaly_detection.py      # Independent detector & discrimination tests
│   ├── test_ground_truth.py           # Ground truth schema, resolution & isolation tests
│   ├── test_anomaly_metrics.py        # Precision, recall, F1-score & empirical tests
│   ├── test_anomaly_determinism.py    # Anomaly seed reproducibility & scale tests
│   ├── test_approvals.py       # Multi-level approval tests
│   ├── test_budget.py          # Double-entry budget ledger tests
│   ├── test_config.py          # Configuration parser tests
│   ├── test_csv_export.py      # Multi-table CSV export tests
│   ├── test_database_export.py # Relational SQLite database export & integrity tests
│   ├── test_delivery.py        # Delivery & partial shipment tests
│   ├── test_derive.py          # Centralized derived fields unit tests (11 functions)
│   ├── test_determinism.py     # Determinism & seed verification
│   ├── test_distributions.py   # Price & seasonality distribution verification
│   ├── test_export.py          # Master export orchestration tests
│   ├── test_export_determinism.py     # Export bit-for-bit determinism tests
│   ├── test_export_integrity.py       # Multi-format export reconciliation tests
│   ├── test_fx.py              # Foreign exchange conversion tests
│   ├── test_ground_truth_export.py    # Ground truth isolated export tests
│   ├── test_ids.py             # Centralized IDFactory tests
│   ├── test_json_export.py     # Multi-table JSON export tests
│   ├── test_masters.py         # Master data generator unit tests
│   ├── test_orders.py          # Purchase order unit tests
│   ├── test_quotes.py          # Multi-currency quotation & scoring tests
│   ├── test_requests.py        # Purchase requests & lines unit tests
│   ├── test_schema.py          # SQLite schema & foreign key constraint tests
│   ├── test_sourcing.py        # Sourcing classification & RFQ tests
│   ├── test_sql_schema.py      # Canonical SQL schema DDL tests
│   ├── test_sql_seed.py        # Populated SQL seed replay & foreign key tests
│   ├── test_status_events.py   # Status event audit lifecycle tests
│   ├── test_validation_approvals.py   # Approval & business rule validator tests
│   ├── test_validation_budget.py      # Budget ledger validator tests
│   ├── test_validation_dates.py       # Date chronology validator tests
│   ├── test_validation_financial.py   # Financial reconciliation validator tests
│   ├── test_validation_foreign_keys.py# Foreign key & relationship validator tests
│   ├── test_validation_integration.py # End-to-end validator & reporting tests
│   ├── test_validation_lifecycle.py   # Lifecycle state machine validator tests
│   ├── test_validation_primary_keys.py# Primary key & ID format validator tests
│   └── test_workflow_integration.py   # Full workflow integration & balance tests
└── ai/
    └── prompts/
        ├── 01_phase1_foundation.md
        ├── 02_phase2_generation.md
        ├── 03_phase3_procurement_workflow.md
        ├── 04_phase4_derived_validation.md
        └── 05_phase5_anomalies.md
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

## 5. Generating Synthetic Data (Clean & Anomaly-Injected)

Execute the end-to-end procurement data generation workflow through the CLI:

```powershell
# Generate clean starter scale dataset (default)
python -m datagen --generate

# Generate dataset with controlled anomalies injected
python -m datagen --generate --scale starter --inject-anomalies

# Generate full scale dataset with specific seed
python -m datagen --generate --scale full --seed 20261022 --inject-anomalies
```

Sample CLI Output with Anomalies Injected:
```text
=== Procurement Workflow Generation Successful ===
Scale Tier        : starter
Random Seed       : 20261022
Departments       : 10
Budgets           : 10
Requesters        : 30
Suppliers         : 13
Approvers         : 22
Purchase Requests : 116
Approvals         : 96
RFQs              : 50
Supplier Invites  : 183
Supplier Quotes   : 183
Quote Lines       : 414
Purchase Orders   : 93 (Competitive: 50, Non-Competitive: 43)
PO Lines          : 188
Deliveries        : 101
Budget Events     : 390
Status Events     : 930
Total PO Spend    : $483,184.73 USD

Injected Anomalies: 7
  - budget_overrun: 1
  - duplicate_purchase_request: 1
  - expired_quote_before_award: 1
  - inactive_supplier_used: 1
  - non_cheapest_quote_without_rationale: 1
  - po_without_approval: 1
  - quote_currency_mismatch: 1
```

---

## 6. Comprehensive Validation & Anomaly Detection (Phase 5)

Execute the independent validator in either `clean` mode (expects 0 anomalies) or `anomaly_aware` mode:

```powershell
# 1. Clean Validation Mode (Clean dataset PASSES)
python -m validate data/ --scale starter --mode clean

# 2. Clean Validation Mode on Mutated Data (Anomalies cause FAIL)
python -m validate data/ --scale starter --mode clean --inject-anomalies

# 3. Anomaly-Aware Mode with Evaluation Benchmark (Evaluates against Ground Truth)
python -m validate data/ --scale starter --mode anomaly_aware --inject-anomalies --evaluate
```

Sample CLI Output (Anomaly-Aware Mode with Evaluation):
```text
=== Generating Dataset (starter scale, seed 20261022) ===
=== Injecting Controlled Procurement Anomalies ===
Injected Anomalies   : 7
=== Executing Validation (Mode: anomaly_aware) ===
Total Checks Executed : 10,837
Passed Checks         : 10,832
Failed Checks         : 5
Warnings              : 0
Overall Status        : PASS
Detected Anomalies    : 7

=== Detection Performance Evaluation ===
Ground Truth Count    : 7
Detected Count        : 7
True Positives (TP)   : 7
False Positives (FP)  : 0
False Negatives (FN)  : 0
Precision             : 100.00%
Recall                : 100.00%
F1-Score              : 1.0000

Markdown Report Saved : docs/validation_summary.md
JSON Report Saved     : docs/validation_summary.json
```

---

## 7. Full-Scale Generation & Export (Assignment Deliverables)

Generate the full-scale procurement dataset (1,200 requisitions, 500 RFQs, ~1,779 quotes, 970 POs) with controlled anomaly injection and complete disk persistence:

```powershell
python -m datagen --generate --scale full --inject-anomalies --export --output-dir output
```

This populates all required submission artifacts into `output/`:
- **`output/csv/`**: 17 operational entity CSV tables conforming to RFC 4180
- **`output/json/`**: 17 operational entity JSON files + `metadata.json`
- **`output/database/procurement.db`**: Fully populated SQLite database with `PRAGMA foreign_keys = ON`
- **`output/sql/schema.sql`**: Canonical 19-table DDL schema with check constraints and indexes
- **`output/sql/seed.sql`**: Self-contained, topologically ordered SQL `INSERT` statements
- **`output/ground_truth/`**: Strictly isolated `ground_truth.csv` and `ground_truth.json`
- **`source_manifest.json`**: Cryptographic provenance manifest with SHA-256 hashes
- **`output/reports/`**: Comprehensive markdown and JSON reports for validation, anomaly detection, export integrity, and dataset statistics.

---

## 8. Running the Automated Test Suite & Fresh Clone Verification

### Pytest Test Suite
Execute the entire 166-test automated verification suite:

```powershell
python -m pytest tests/ -v
```

### Two-Run Bitwise Determinism Verification
Verify 100% bitwise reproducibility across independent runs with seed `20261022`:

```powershell
python scratch/verify_determinism_2runs.py
```

### Complete 7-Stage Fresh Clone Audit
Execute automated clean-room verification in an isolated temporary sandbox:

```powershell
python scratch/fresh_clone_audit.py
```

---

## 9. Assignment Compliance Matrix & Documentation Index

- **Assignment Compliance Matrix (100% Complete)**: [`docs/assignment_compliance_matrix.md`](docs/assignment_compliance_matrix.md)
- **Final Technical Audit Report (20 Points)**: [`docs/final_audit_report.md`](docs/final_audit_report.md)
- **System Architecture & Lifecycle DAG**: [`docs/architecture.md`](docs/architecture.md)
- **Data Dictionary (All 19 Tables)**: [`docs/data_dictionary.md`](docs/data_dictionary.md)
- **Anomaly Catalog & Detection Criteria**: [`docs/anomaly_catalog.md`](docs/anomaly_catalog.md)
- **Reproducibility & Determinism Guide**: [`docs/reproducibility.md`](docs/reproducibility.md)
- **AI Governance & Prompt History**: [`AI_USAGE.md`](AI_USAGE.md) and [`docs/prompt_history.md`](docs/prompt_history.md)
