# Reproducibility & Determinism Guide

Ensuring 100% deterministic, byte-for-byte reproducible dataset generation across varied execution environments is a core foundational requirement of the Procure-to-Pay Synthetic Data Generator.

---

## 1. Determinism Principles

Synthetic datasets used for benchmark testing, machine learning evaluation, and data pipeline QA are identical when generated with the same parameters:

1. **No Uncontrolled Randomness**:
   - Standard library `random.random()`, `uuid.uuid4()`, and unseeded NumPy RNG calls are strictly forbidden in generation logic.
   - All generation functions utilize a single dedicated `numpy.random.Generator` initialized via `numpy.random.default_rng(seed)` passed explicitly through the entire generation pipeline.
2. **Deterministic Sequence Identifiers**:
   - All entity IDs are generated sequentially via `datagen.ids.IDFactory`.
   - An independent monotonic counter is maintained per entity type, preventing race conditions or execution-order variance.
3. **Deterministic Timestamps & Dates**:
   - `datetime.now()` or `datetime.today()` are never used to generate business transaction dates.
   - All dates derive from the base date (`2026-01-01`) via deterministic business-calendar offsets and seasonality curves.
4. **Exact Monetary Calculations**:
   - Floating-point calculations (`float`) are prohibited for financial calculations and ledger balances.
   - Python `decimal.Decimal` with explicit `ROUND_HALF_UP` quantization and SQLite integer minor units (cents) ensure exact cross-platform consistency.

---

## 2. Environment Specifications

To reproduce the exact operational and test environment:

- **Operating System**: Windows 10/11, macOS 13+, or Linux (Ubuntu 22.04+).
- **Python Runtime**: Python 3.12 (compatible with Python >= 3.11).
- **Package Manager**: `pip` with dependencies pinned in `requirements.txt`:
  - `numpy==2.2.3`
  - `pandas==2.2.3`
  - `PyYAML==6.0.3`
  - `pytest==9.2.0`

---

## 3. Verification Protocol

To verify reproducibility:

1. Clone or extract the repository into a clean workspace.
2. Configure dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Set the Python path:
   ```bash
   export PYTHONPATH=src   # Linux/macOS
   $env:PYTHONPATH="src"   # Windows PowerShell
   ```
4. Run the complete automated test suite (167 tests):
   ```bash
   python -m pytest tests/ -v
   ```
5. Verify bitwise determinism across two independent runs with seed `20261022`:
   ```bash
   python scripts/verify_determinism_2runs.py
   ```
   All exported CSV, SQL, and ground truth artifacts output `MATCH` with identical SHA-256 hashes.
6. Execute the automated fresh clone verification harness in an isolated temporary sandbox:
   ```bash
   python scripts/fresh_clone_audit.py
   ```
   All verification stages output `PASS`.
