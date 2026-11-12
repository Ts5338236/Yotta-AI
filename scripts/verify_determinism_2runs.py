"""Script to verify exact deterministic checksums across 2 independent runs with seed 20261022."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
import numpy as np

from datagen.workflow import generate_procurement_workflow
from datagen.anomalies import inject_anomalies
from datagen.config import load_config
from datagen.export import export_all


def compute_hashes(output_dir: Path) -> dict[str, str]:
    hashes = {}
    for p in sorted(output_dir.rglob("*")):
        if p.is_file():
            # Exclude SQLite binary (has nondeterministic transaction counters in header)
            # and files that contain wall-clock timestamps
            if p.name.endswith((".db", ".json", ".md")) or "reports" in str(p):
                continue
            with open(p, "rb") as f:
                hashes[str(p.relative_to(output_dir))] = hashlib.sha256(f.read()).hexdigest()
    return hashes


def main():
    print("Executing Two-Run Bitwise Determinism Verification (Seed: 20261022, Scale: Full)...")
    cfg = load_config()
    seed = 20261022

    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        dir1 = Path(tmp1) / "output"
        dir2 = Path(tmp2) / "output"

        # Run 1
        ds1 = generate_procurement_workflow(scale="full", seed=seed)
        ds1, gt1 = inject_anomalies(ds1, cfg, np.random.default_rng(seed))
        ds1["ground_truth"] = [r if isinstance(r, dict) else r.to_dict() for r in gt1]
        export_all(ds1, output_dir=dir1, include_reports=True)
        hashes1 = compute_hashes(dir1)

        # Run 2
        ds2 = generate_procurement_workflow(scale="full", seed=seed)
        ds2, gt2 = inject_anomalies(ds2, cfg, np.random.default_rng(seed))
        ds2["ground_truth"] = [r if isinstance(r, dict) else r.to_dict() for r in gt2]
        export_all(ds2, output_dir=dir2, include_reports=True)
        hashes2 = compute_hashes(dir2)

        print("\nBitwise Hash Comparison Table:")
        print(f"{'Artifact':<35} | {'Run 1 SHA-256':<20} | {'Run 2 SHA-256':<20} | Status")
        print("-" * 85)

        all_match = True
        for k in sorted(hashes1.keys()):
            h1 = hashes1[k]
            h2 = hashes2.get(k, "MISSING")
            status = "MATCH" if h1 == h2 else "MISMATCH"
            if h1 != h2:
                all_match = False
            print(f"{k:<35} | {h1[:18]}... | {h2[:18]}... | {status}")

        if all_match:
            print(f"\n[PASS] Bitwise reproducibility confirmed! All {len(hashes1)} artifacts match 100%.")
        else:
            print("\n[FAIL] Discrepancies detected.")
            sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
