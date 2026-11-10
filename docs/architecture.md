# System Architecture

## 1. Project Purpose & System Boundaries

The **Procure-to-Pay Synthetic Data Generator** (`procure-to-pay-datagen`) is an enterprise-grade synthetic data engineering platform designed to simulate a realistic, end-to-end corporate procurement lifecycle. The platform generates structurally sound, relational, anomaly-injected datasets for testing, machine learning evaluation, and data warehouse benchmarking.

### In Scope (Phases 1, 2, 3, and 4 Complete)
- **Master Data**: Departments, Budgets, Requesters (DAG tree), Suppliers, and Approvers (`src/datagen/masters.py`).
- **Requisitions**: Purchase Requests and Request Lines with log-normal pricing and 2026 calendar seasonality (`src/datagen/requests.py`).
- **Approval Engine**: Multi-level financial thresholds, line manager, department head, and corporate finance approvals (`src/datagen/approvals.py`).
- **Sourcing & Quotations**: Competitive RFQs, supplier invitations, multi-currency quotations, landed costs, and multicriteria scoring (`src/datagen/sourcing.py`).
- **Purchase Orders**: Binding POs and PO lines for competitive and non-competitive sourcing (`src/datagen/orders.py`).
- **Fulfillment & Deliveries**: Physical goods receipts supporting partial and multi-shipment scenarios (`src/datagen/delivery.py`).
- **Budget Ledger**: Double-entry style event ledger (`ALLOCATE`, `RESERVE`, `COMMIT`, `RELEASE`, `SPEND`) with balance reconciliation (`src/datagen/budget.py`).
- **Lifecycle History**: Complete state machine transition tracking across PR, RFQ, PO, and Delivery (`src/datagen/events.py`).
- **Centralized Derived Fields Engine**: Recalculates line totals, request totals, quote landed costs, composite scores, PO totals, delivery fulfillments, and budget balances (`src/datagen/derive.py`).
- **Comprehensive Independent Validation Suite**: 7-domain auditing covering primary keys, foreign keys, arithmetic reconciliation, lifecycle state continuity, date chronology, approvals & awards, and budget ledgers (`src/validate/checks.py`, `src/validate/models.py`).
- **End-to-End Orchestration**: Seamless pipeline coordination with clean-path validation (`src/datagen/workflow.py`).

### System Boundaries (Scheduled for Subsequent Phases)
- Phase 5: Data export and storage engine (CSV, JSON, and bulk relational SQLite database).
- Phase 6: Controlled anomaly injection (split POs, phantom vendors, budget overruns, late shipments) and ground truth labeling.
- Phase 7: End-to-end validation, audit reporting, and test bench verification.

---

## 2. Python Package Structure (src-layout)

```
procure-to-pay-datagen/
├── .gitignore
├── pyproject.toml              # Packaging, build configuration & metadata
├── requirements.txt            # Pinned dependencies
├── README.md                   # Project overview & operator documentation
├── config/
│   └── default.yaml            # Centralized system, scale, distribution & seasonality config
├── src/
│   ├── datagen/                # Core generator package
│   │   ├── __init__.py         # Package exports & entry points
│   │   ├── __main__.py         # datagen execution entry point
│   │   ├── cli.py              # CLI argument parser (argparse)
│   │   ├── config.py           # Strict YAML config parser & validator
│   │   ├── ids.py              # Centralized deterministic IDFactory
│   │   ├── fx.py               # Deterministic Decimal FX engine
│   │   ├── masters.py          # Master data generator (Depts, Budgets, Reqs, Sups, Apps)
│   │   ├── requests.py         # Purchase requests & lines with log-normal pricing
│   │   ├── approvals.py        # Multi-level approval engine
│   │   ├── sourcing.py         # Sourcing, RFQs, quotes, landed costs & scoring
│   │   ├── orders.py           # Purchase orders & PO lines
│   │   ├── delivery.py         # Deliveries & partial shipments
│   │   ├── budget.py           # Budget event ledger & balance reconciliation
│   │   ├── events.py           # Status event lifecycle history
│   │   ├── derive.py           # Centralized derived fields recalculation engine
│   │   └── workflow.py         # Workflow orchestration & clean-path validation
│   └── validate/               # Quality assurance & verification package
│       ├── __init__.py         # Package exports
│       ├── __main__.py         # CLI execution entry point
│       ├── models.py           # ValidationCheckResult & ValidationReport models
│       └── checks.py           # 7-domain independent auditing engine & SQLite checks
├── data/
│   ├── csv/                    # Target directory for CSV exports (.gitkeep)
│   ├── json/                   # Target directory for JSON exports (.gitkeep)
│   └── sql/
│       ├── schema.sql          # Canonical DDL with strict relational constraints
│       └── seed.sql            # Seed SQL script placeholder
├── docs/                       # Architecture, data dictionary, & technical specifications
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── assumptions.md
│   ├── validation_summary.md
│   ├── validation_summary.json
│   ├── reproducibility.md
│   ├── source_manifest.md
│   └── AI_USAGE.md
├── tests/                      # Automated pytest suite (112 passing tests)
│   ├── __init__.py
│   ├── test_approvals.py       # Approval thresholds & roles
│   ├── test_budget.py          # Budget event ledger & reconciliation
│   ├── test_config.py          # Configuration loading & validation
│   ├── test_delivery.py        # Delivery fulfillment & partial shipments
│   ├── test_derive.py          # Centralized derived fields unit tests (11 functions)
│   ├── test_determinism.py     # Determinism & seed reproducibility
│   ├── test_distributions.py   # Price & seasonality distribution verification
│   ├── test_fx.py              # Decimal FX conversion
│   ├── test_ids.py             # Centralized IDFactory
│   ├── test_masters.py         # Master data generation
│   ├── test_orders.py          # Purchase order & line reconciliation
│   ├── test_quotes.py          # Quotations, landed cost & scoring
│   ├── test_requests.py        # Purchase requests & request lines
│   ├── test_schema.py          # SQLite schema & constraints
│   ├── test_sourcing.py        # Sourcing classification & RFQ invites
│   ├── test_status_events.py   # State machine transitions
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
        └── 04_phase4_derived_validation.md
```

---

## 3. End-to-End Procurement Workflow Pipeline

```mermaid
flowchart TD
    subgraph MasterData["1. Master Data"]
        Depts["Departments"] --> Budgets["Budgets"]
        Depts --> Reqs["Requesters (DAG Tree)"]
        Depts --> Approvers["Approvers"]
        Sups["Suppliers"]
    end

    subgraph Requisition["2. Requisition Engine"]
        Reqs --> PRs["Purchase Requests\n(Seasonality 2026)"]
        Budgets --> PRs
        PRs --> Lines["Request Lines\n(Log-Normal Pricing)"]
    end

    subgraph ApprovalEngine["3. Approval Engine"]
        PRs --> Apps["Multi-Tier Approvals\n(Line Mgr, Dept Head, Finance)"]
        Approvers --> Apps
        Apps --> Decision{"Decision"}
        Decision -- Rejected --> PR_Rej["PR Rejected\n(Halted, Budget Released)"]
        Decision -- Approved --> PR_App["PR Approved"]
    end

    subgraph Sourcing["4. Sourcing & Evaluation"]
        PR_App --> Classify{"Sourcing Path"}
        Classify -- "> $2k: Competitive" --> RFQs["RFQs"]
        Classify -- "<= $2k: Catalogue / Direct" --> DirectPO["Direct Sourcing"]
        
        RFQs --> Invites["Supplier Invites (3-6)"]
        Sups --> Invites
        Invites --> Quotes["Multi-Currency Quotes"]
        Quotes --> LandedCost["Landed Cost Calculation\n(Base + Freight + Duty + Tax)"]
        LandedCost --> Scoring["Multicriteria Scoring\n(60% Cost, 25% Lead, 15% Risk)"]
        Scoring --> Award["Lowest Score Awarded"]
    end

    subgraph Purchasing["5. Purchase Orders"]
        Award --> CompPO["Competitive PO"]
        DirectPO --> NonCompPO["Non-Competitive PO"]
        CompPO --> POLines["PO Lines (Quote Lines)"]
        NonCompPO --> POLines["PO Lines (Request Lines)"]
    end

    subgraph Fulfillment["6. Fulfillment & Ledger"]
        POLines --> Shipments["Deliveries\n(80% On-Time, 10% Late, 10% Partial)"]
        Shipments --> Ledger["Budget Event Ledger\n(ALLOCATE, RESERVE, COMMIT, SPEND)"]
        Ledger --> Reconcile["Reconciled Budget Balances"]
        Shipments --> Audit["Status Event History\n(Lifecycle State Transitions)"]
    end
```

---

## 4. Determinism & Traceability Guarantees

1. **Single Random Generator**: Exactly one `numpy.random.default_rng(seed)` is initialized at entry and passed down the pipeline.
2. **State-Isolated Sequence Counters**: Identifiers for all 18 entities are produced deterministically through `IDFactory`.
3. **Double-Entry Budget Integrity**: `budget_events` tracks every financial movement, ensuring `allocated >= reserved + committed + spent`.
4. **State Machine Consistency**: Status changes are tracked in `status_events`, guaranteeing chronological validity.

---

## 5. Derived Fields Engine & Comprehensive Validation Architecture (Phase 4)

Phase 4 introduces a strict separation of concerns between **derivation** (`src/datagen/derive.py`) and **independent validation** (`src/validate/checks.py`, `src/validate/models.py`).

### A. Centralized Derived Fields Engine (`derive.py`)
Provides pure, non-circular mathematical and relational recalculation directly from raw source records:
1. `derive_request_line_totals`: Computes exact line totals in integer cents from quantity and estimated unit price.
2. `derive_purchase_request_totals`: Aggregates itemized request lines to derive total estimated amounts and USD values.
3. `derive_quote_landed_costs`: Calculates native currency totals, base USD conversions, freight, duty, tax, and landed costs.
4. `derive_supplier_scores`: Executes min-max normalization across competing quotes and computes weighted composite scores.
5. `derive_purchase_order_totals`: Derives binding purchase order totals directly from PO line items.
6. `derive_delivery_summaries`: Aggregates cumulative receipts per PO, evaluating full delivery and late arrival flags.
7. `derive_current_statuses`: Resolves current entity status from the latest valid `StatusEvent`.
8. `derive_budget_balances`: Reconstructs active `reserved`, `committed`, `spent`, and `available` balances from the double-entry event ledger.
9. `derive_delivery_metrics`: Computes operational performance metrics (on-time rate, average lead times, average delay days).

### B. Independent Validation Architecture (`src/validate/`)
The validation framework operates independently of `derive.py` to prevent circular verification. Expected values are recalculated autonomously from primary source transactions:
- **Primary Key & ID Auditing**: Verifies non-nullness, uniqueness, and adherence to `ID_REGEX_MAP` patterns across all 18 entities.
- **Foreign Key & Cross-Entity Integrity**: Validates every relational reference, including compound rules (e.g. quoting suppliers must be invited, PR departments must match requester departments).
- **Financial Arithmetic Reconciliation**: Verifies exact multiplication, summation, landed cost formulas, and scoring bounds.
- **Lifecycle State Machine Verification**: Audits status sequence continuity, disallowing illegal jumps and prohibiting orders on rejected requisitions.
- **Date Ordering & Chronology**: Validates the end-to-end timeline: $\text{Requisition} \le \text{Approval} \le \text{RFQ} \le \text{Quote} \le \text{Award} \le \text{PO} \le \text{Delivery}$.
- **Approval & Procurement Business Rules**: Audits monetary delegation thresholds, required approver roles, and objective lowest-score award criteria.
- **Double-Entry Budget Reconciliation**: Audits event types, positive amounts, initial allocations, and proves 0 budget overruns on clean paths.
- **Machine-Readable Reports**: Automatically emits comprehensive markdown (`docs/validation_summary.md`) and JSON (`docs/validation_summary.json`) reports.
