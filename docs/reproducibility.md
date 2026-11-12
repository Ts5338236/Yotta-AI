# Reproducibility & Determinism Guide

Ensuring 100% deterministic, byte-for-byte reproducible dataset generation across varied execution environments is a core design requirement of the Procure-to-Pay Synthetic Data Generator.

---

## 1. Determinism Principles

Synthetic datasets used for benchmark testing, machine learning evaluation, and data pipeline QA must be identical when generated with the same parameters:

1. **No Uncontrolled Randomness**:
   - Standard library `random.random()`, `uuid.uuid4()`, or unseeded NumPy RNG calls are strictly forbidden in generation logic.
   - Future generation phases will initialize a dedicated `numpy.random.Generator` using `numpy.random.default_rng(seed)`.
2. **Deterministic Sequence Identifiers**:
   - All entity IDs are generated sequentially via `datagen.ids.IDFactory`.
   - An independent monotonic counter is maintained per entity type, preventing race conditions or execution-order variance.
3. **Deterministic Timestamps & Dates**:
   - `datetime.now()` or `datetime.today()` are never used to generate business transaction dates.
   - All dates derive from the base date (`2026-01-01`) via deterministic business-calendar offsets.
4. **Exact Monetary Calculations**:
   - Floating-point calculations (`float`) are prohibited for financial calculations.
   - Python `decimal.Decimal` with explicit `ROUND_HALF_UP` quantization ensures cross-platform consistency.

---

## 2. Environment Specifications

To reproduce the exact Phase 1 test and operational environment:

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
2. Initialize and configure dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Run the complete automated test suite (166 tests):
   ```powershell
   python -m pytest tests/ -v
   ```
4. Verify bitwise determinism across two independent runs with seed `20261022`:
   ```powershell
   python scratch/verify_determinism_2runs.py
   ```
   All 20 exported CSV, SQL, and ground truth artifacts will output `MATCH` with identical SHA-256 hashes.
5. Execute the automated 7-stage fresh clone verification harness in an isolated temporary sandbox:
   ```powershell
   python scratch/fresh_clone_audit.py
   ```
   All 7 stages must output `PASS`.
