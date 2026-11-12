"""Unit tests for Phase 6 Export Determinism.

Verifies:
- Repeated generation and exports with seed 20261022 produce bitwise identical CSV, JSON, and SQL seed files.
- Row ordering is stable across runs.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import pytest

from datagen.export import export_all
from datagen.workflow import generate_procurement_workflow


def hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def test_export_determinism_identical_seed(tmp_path):
    """Verify that exporting two datasets with the same seed yields identical artifact hashes."""
    seed = 20261022
    ds1 = generate_procurement_workflow(scale="starter", seed=seed)
    ds2 = generate_procurement_workflow(scale="starter", seed=seed)

    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    export_all(ds1, base_dir=dir1)
    export_all(ds2, base_dir=dir2)

    # Compare all CSV files
    csv_files = list((dir1 / "csv").glob("*.csv"))
    assert len(csv_files) >= 15

    for f1 in csv_files:
        f2 = dir2 / "csv" / f1.name
        assert f2.exists()
        assert hash_file(f1) == hash_file(f2), f"CSV mismatch in {f1.name}"

    # Compare all JSON files
    json_files = list((dir1 / "json").glob("*.json"))
    for f1 in json_files:
        if f1.name == "metadata.json":
            continue
        f2 = dir2 / "json" / f1.name
        assert f2.exists()
        assert hash_file(f1) == hash_file(f2), f"JSON mismatch in {f1.name}"

    # Compare SQL seed files
    seed1 = dir1 / "sql" / "seed.sql"
    seed2 = dir2 / "sql" / "seed.sql"
    assert hash_file(seed1) == hash_file(seed2), "seed.sql mismatch across runs"

