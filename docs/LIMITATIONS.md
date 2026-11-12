# Known System Limitations & Constraints

**Project**: YottaFlex Procure-to-Pay Synthetic Data Generator  
**Evaluation Scope**: Architectural Boundaries, Operational Assumptions, and Production Scope

---

## 1. Overview

While the YottaFlex Procure-to-Pay Synthetic Data Generator generates production-grade, relational, and statistically realistic datasets for testing and machine learning, several technical and operational boundaries exist by design.

---

## 2. Technical Limitations

### A. Temporal Scope
- **Calendar Year 2026 Constraint**: All synthetic transactions (requisitions, approvals, RFQs, quotes, purchase orders, deliveries, and ledger events) are temporally anchored within the 2026 fiscal year (`2026-01-01` to `2026-12-31`).
- **Multi-Year History**: Multi-year historical trends spanning across multi-year cycles are not simulated in the default generator runs.

### B. Single-Currency Base Accounting
- **Base Currency**: The system accounting base currency is fixed to `USD`.
- **Foreign Exchange Model**: Multi-currency transactions (EUR, GBP, INR, JPY) are converted using fixed institutional exchange rates rather than continuous live market ticks.

### C. In-Memory Generation Scale
- **Dataset Size**: The generation pipeline is optimized for memory efficiency ($\le 80$ MB peak memory) for dataset tiers up to **Full Scale** (32,076 records across 18 tables).
- **Ultra-Large Datasets**: Generating multi-million record sets would require stream-based batch generators rather than complete in-memory relational graphs.

### D. Single-File SQLite Persistence
- **Concurrency**: Persistence is designed around SQLite 3 (`procurement.db` and `yotta_ai.db`). While ideal for testing, reproducibility, and local development, high-concurrency multi-user writes require migration to client-server RDBMS (PostgreSQL, MySQL).

---

## 3. Business Logic Limitations

### A. Delivery Rejection Workflow
- Deliveries model on-time fulfillments (80%), late deliveries (10%), and partial multi-shipment fulfillments (10%). Return merchandise authorizations (RMA) and vendor credit notes are logged in `exception_logs` but do not generate reverse accounting debit notes.

### B. Tax Jurisdiction Modeling
- Taxes are calculated using a unified non-recoverable tax percentage per line item rather than complex multi-jurisdictional tax trees (e.g. state/provincial VAT/GST splits).

### C. Anomaly Scope
- Seven specific procurement anomalies are injected and audited. While these cover major financial and compliance vulnerabilities, broader forensic scenarios (such as collusion kickbacks or phantom shell companies) are outside the core assignment scope.

