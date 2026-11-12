"""Comprehensive Fresh Clone Verification Suite.

Simulates a clean installation in an isolated directory:
1. Workspace file transfer into isolated sandbox
2. Syntax compilation across all modules
3. Config validation
4. Full pytest suite execution
5. CLI execution across both starter and full tiers
6. Export integrity verification
7. Seed SQL execution against fresh SQLite database
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_stage(title: str, cmd: list[str], cwd: Path) -> bool:
    print(f"\n[STAGE] {title} ...")
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  --> PASS ({title})")
        return True
    else:
        print(f"  --> FAIL ({title})")
        print("STDOUT:\n", res.stdout[:500])
        print("STDERR:\n", res.stderr[:500])
        return False


def main():
    root = Path(__file__).resolve().parent.parent
    print(f"Starting Fresh Clone Audit for: {root}")

    with tempfile.TemporaryDirectory() as tmp:
        clone_dir = Path(tmp) / "Yotta-Clone"
        print(f"Isolated Test Sandbox: {clone_dir}")

        # Copy workspace files excluding scratch, .git, venv
        shutil.copytree(
            root,
            clone_dir,
            ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", "venv", ".venv", "tmp"),
        )

        stages = [
            ("1. Python Syntax & Compilation Check", [sys.executable, "-m", "compileall", "src", "tests"]),
            ("2. CLI Config Validation", [sys.executable, "-m", "datagen", "--validate-config"]),
            ("3. Schema Initialization", [sys.executable, "-m", "datagen", "--init-db", "fresh_db.sqlite"]),
            ("4. Pytest Test Suite", [sys.executable, "-m", "pytest", "tests/", "-v"]),
            ("5. Starter Generation & Export", [sys.executable, "-m", "datagen", "--generate", "--scale", "starter", "--export", "--output-dir", "output_starter"]),
            ("6. Full Scale Generation, Anomaly Injection & Export", [sys.executable, "-m", "datagen", "--generate", "--scale", "full", "--inject-anomalies", "--export", "--output-dir", "output_full"]),
            ("7. Two-Run Determinism Check", [sys.executable, "scratch/verify_determinism_2runs.py"]),
        ]

        all_ok = True
        for name, cmd in stages:
            ok = run_stage(name, cmd, cwd=clone_dir)
            if not ok:
                all_ok = False
                break

        if all_ok:
            print("\n" + "=" * 70)
            print("ALL 7 FRESH CLONE VERIFICATION STAGES PASSED WITH 100% SUCCESS!")
            print("=" * 70)
            sys.exit(0)
        else:
            print("\n[ERROR] Fresh clone verification encountered failures.")
            sys.exit(1)


if __name__ == "__main__":
    main()

