"""Export integrity and cross-format consistency validation engine (Phase 6).

Audits CSV, JSON, SQLite database, and SQL seed script deliverables against
in-memory source records, asserting record count parity, schema conformance,
referential integrity, and ground-truth isolation.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple
import pandas as pd

from datagen.database import DB_TABLES_ORDER as OPERATIONAL_TABLES


class ExportValidationError(Exception):
    """Raised when an exported artifact violates schema, count, or integrity constraints."""
    pass


def validate_csv_exports(
    dataset: Dict[str, Any],
    csv_dir: str | Path = "data/csv",
    tables: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Validate CSV exports for file existence, header matching, and record count parity.

    Args:
        dataset: Source in-memory dataset.
        csv_dir: Directory containing CSV exports.
        tables: Target tables to validate.

    Returns:
        Dict[str, Any]: Validation results per table and overall status.
    """
    path = Path(csv_dir).resolve()
    target_tables = tables or [t for t in OPERATIONAL_TABLES if t in dataset]
    results: List[Dict[str, Any]] = []
    all_passed = True

    for t in target_tables:
        source_rows = dataset.get(t, [])
        file_path = path / f"{t}.csv"

        if not file_path.exists():
            results.append({
                "table": t,
                "check": "file_existence",
                "passed": False,
                "message": f"CSV file missing: {file_path}",
            })
            all_passed = False
            continue

        try:
            df = pd.read_csv(file_path, dtype=str)
            actual_count = len(df)
            expected_count = len(source_rows)
            count_match = (actual_count == expected_count)

            # Check header (excluding internal/transient helper keys)
            expected_headers = [
                k for k in source_rows[0].keys()
                if not (t in ("supplier_quotes", "purchase_orders") and k in ("_lines", "_supplier"))
            ] if source_rows else []
            actual_headers = list(df.columns) if not df.empty else []
            header_match = True
            if expected_headers and actual_headers:
                header_match = set(expected_headers).issubset(set(actual_headers))

            # Primary key uniqueness check
            pk_col = expected_headers[0] if expected_headers else None
            pk_unique = True
            if pk_col and pk_col in df.columns:
                pk_unique = (df[pk_col].nunique() == len(df))

            passed = count_match and header_match and pk_unique
            if not passed:
                all_passed = False

            results.append({
                "table": t,
                "check": "csv_integrity",
                "passed": passed,
                "expected_count": expected_count,
                "actual_count": actual_count,
                "pk_unique": pk_unique,
                "header_match": header_match,
            })
        except Exception as exc:
            all_passed = False
            results.append({
                "table": t,
                "check": "csv_parsing",
                "passed": False,
                "error": str(exc),
            })

    return {
        "format": "CSV",
        "passed": all_passed,
        "total_tables": len(target_tables),
        "results": results,
    }


def validate_json_exports(
    dataset: Dict[str, Any],
    json_dir: str | Path = "data/json",
    tables: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Validate JSON exports for syntax, schema fields, and record count parity.

    Args:
        dataset: Source in-memory dataset.
        json_dir: Directory containing JSON exports.
        tables: Target tables to validate.

    Returns:
        Dict[str, Any]: Validation results per table and overall status.
    """
    path = Path(json_dir).resolve()
    target_tables = tables or [t for t in OPERATIONAL_TABLES if t in dataset]
    results: List[Dict[str, Any]] = []
    all_passed = True

    for t in target_tables:
        source_rows = dataset.get(t, [])
        file_path = path / f"{t}.json"

        if not file_path.exists():
            results.append({
                "table": t,
                "check": "file_existence",
                "passed": False,
                "message": f"JSON file missing: {file_path}",
            })
            all_passed = False
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError(f"JSON root element in {t}.json is not a list")

            actual_count = len(data)
            expected_count = len(source_rows)
            count_match = (actual_count == expected_count)

            # Check primary key uniqueness
            pk_col = next(iter(source_rows[0].keys())) if source_rows else None
            pk_unique = True
            if pk_col and data:
                pk_vals = [r.get(pk_col) for r in data if r.get(pk_col) is not None]
                pk_unique = (len(pk_vals) == len(set(pk_vals)) == len(data))

            passed = count_match and pk_unique
            if not passed:
                all_passed = False

            results.append({
                "table": t,
                "check": "json_integrity",
                "passed": passed,
                "expected_count": expected_count,
                "actual_count": actual_count,
                "pk_unique": pk_unique,
            })
        except Exception as exc:
            all_passed = False
            results.append({
                "table": t,
                "check": "json_parsing",
                "passed": False,
                "error": str(exc),
            })

    return {
        "format": "JSON",
        "passed": all_passed,
        "total_tables": len(target_tables),
        "results": results,
    }


def validate_sqlite_database(
    dataset: Dict[str, Any],
    db_path: str | Path = "data/database/procurement.db",
) -> Dict[str, Any]:
    """Validate SQLite database for table existence, integrity_check, foreign_key_check, and record counts.

    Args:
        dataset: Source in-memory dataset.
        db_path: Path to target SQLite database.

    Returns:
        Dict[str, Any]: SQLite audit results.
    """
    path = Path(db_path).resolve()
    if not path.exists():
        return {
            "format": "SQLITE",
            "passed": False,
            "error": f"Database file missing at: {path}",
        }

    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")

        # 1. PRAGMA integrity_check
        integ = conn.execute("PRAGMA integrity_check;").fetchall()
        integ_ok = (len(integ) == 1 and integ[0][0] == "ok")

        # 2. PRAGMA foreign_key_check
        fk_errs = conn.execute("PRAGMA foreign_key_check;").fetchall()
        fk_ok = (len(fk_errs) == 0)

        # 3. Table counts
        table_results: List[Dict[str, Any]] = []
        all_counts_match = True

        for t in OPERATIONAL_TABLES:
            if t not in dataset:
                continue
            expected_count = len(dataset[t])
            cursor = conn.cursor()
            try:
                actual_count = cursor.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
                match = (actual_count == expected_count)
                if not match:
                    all_counts_match = False
                table_results.append({
                    "table": t,
                    "expected": expected_count,
                    "actual": actual_count,
                    "passed": match,
                })
            except sqlite3.OperationalError as err:
                all_counts_match = False
                table_results.append({
                    "table": t,
                    "passed": False,
                    "error": f"Table missing or query failed: {err}",
                })

        overall_passed = integ_ok and fk_ok and all_counts_match

        return {
            "format": "SQLITE",
            "passed": overall_passed,
            "integrity_ok": integ_ok,
            "integrity_message": integ[0][0] if integ else "no_result",
            "foreign_key_violations": len(fk_errs),
            "table_results": table_results,
        }
    finally:
        conn.close()


def validate_sql_seed_execution(
    dataset: Dict[str, Any],
    schema_path: str | Path = "data/sql/schema.sql",
    seed_path: str | Path = "data/sql/seed.sql",
) -> Dict[str, Any]:
    """Verify that schema.sql and seed.sql execute in a fresh database with 0 FK violations and count parity.

    Args:
        dataset: Source in-memory dataset.
        schema_path: Canonical schema DDL script path.
        seed_path: Populated seed SQL script path.

    Returns:
        Dict[str, Any]: Execution test results.
    """
    s_path = Path(schema_path).resolve()
    sd_path = Path(seed_path).resolve()

    if not s_path.exists() or not sd_path.exists():
        return {
            "format": "SQL_SEED",
            "passed": False,
            "error": "Schema or seed script missing",
        }

    with open(s_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with open(sd_path, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)
        conn.executescript(seed_sql)

        fk_errs = conn.execute("PRAGMA foreign_key_check;").fetchall()
        fk_ok = (len(fk_errs) == 0)

        table_results = []
        all_counts_match = True
        for t in OPERATIONAL_TABLES:
            if t not in dataset:
                continue
            expected = len(dataset[t])
            actual = conn.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
            match = (actual == expected)
            if not match:
                all_counts_match = False
            table_results.append({
                "table": t,
                "expected": expected,
                "actual": actual,
                "passed": match,
            })

        passed = fk_ok and all_counts_match
        return {
            "format": "SQL_SEED",
            "passed": passed,
            "foreign_key_violations": len(fk_errs),
            "table_results": table_results,
        }
    except Exception as exc:
        return {
            "format": "SQL_SEED",
            "passed": False,
            "error": f"Seed execution failed: {exc}",
        }
    finally:
        conn.close()


def validate_ground_truth_isolation(
    ground_truth_dir: str | Path = "data/ground_truth",
    csv_dir: str | Path = "data/csv",
    json_dir: str | Path = "data/json",
) -> Dict[str, Any]:
    """Verify that ground truth records are isolated in data/ground_truth/ and not in operational tables.

    Args:
        ground_truth_dir: Ground truth directory.
        csv_dir: Operational CSV directory.
        json_dir: Operational JSON directory.

    Returns:
        Dict[str, Any]: Ground truth audit results.
    """
    gt_p = Path(ground_truth_dir).resolve()
    c_p = Path(csv_dir).resolve()
    j_p = Path(json_dir).resolve()

    gt_csv = gt_p / "ground_truth.csv"
    gt_json = gt_p / "ground_truth.json"

    files_exist = gt_csv.exists() and gt_json.exists()

    # Check isolation: ground_truth must not be present in operational CSV or JSON files
    isolated_csv = not (c_p / "ground_truth.csv").exists()
    isolated_json = not (j_p / "ground_truth.json").exists()

    gt_count = 0
    anom_ids_unique = True
    if files_exist:
        with open(gt_json, "r", encoding="utf-8") as f:
            gt_data = json.load(f)
        gt_count = len(gt_data)
        anom_ids = [r.get("anomaly_id") for r in gt_data if r.get("anomaly_id")]
        anom_ids_unique = (len(anom_ids) == len(set(anom_ids)) == len(gt_data))

    passed = files_exist and isolated_csv and isolated_json and anom_ids_unique

    return {
        "format": "GROUND_TRUTH",
        "passed": passed,
        "files_exist": files_exist,
        "isolated_from_operational_csv": isolated_csv,
        "isolated_from_operational_json": isolated_json,
        "anomalies_count": gt_count,
        "anom_ids_unique": anom_ids_unique,
    }


def validate_all_exports(
    dataset: Dict[str, Any],
    base_dir: str | Path = "data",
    schema_path: str | Path = "data/sql/schema.sql",
) -> Dict[str, Any]:
    """Execute complete multi-format export integrity and cross-format consistency validation.

    Args:
        dataset: Source in-memory dataset.
        base_dir: Root directory of exported deliverables.
        schema_path: Path to canonical schema.sql.

    Returns:
        Dict[str, Any]: Comprehensive verification audit summary.
    """
    root = Path(base_dir).resolve()
    csv_dir = root / "csv"
    json_dir = root / "json"
    db_path = root / "database" / "procurement.db"
    seed_path = root / "sql" / "seed.sql"
    gt_dir = root / "ground_truth"

    target_schema = (root / "sql" / "schema.sql") if (root / "sql" / "schema.sql").exists() else Path(schema_path)

    csv_audit = validate_csv_exports(dataset, csv_dir=csv_dir)
    json_audit = validate_json_exports(dataset, json_dir=json_dir)
    sqlite_audit = validate_sqlite_database(dataset, db_path=db_path)
    seed_audit = validate_sql_seed_execution(dataset, schema_path=target_schema, seed_path=seed_path)
    gt_audit = validate_ground_truth_isolation(ground_truth_dir=gt_dir, csv_dir=csv_dir, json_dir=json_dir)

    checks = [csv_audit, json_audit, sqlite_audit, seed_audit, gt_audit]
    failed_checks = sum(1 for c in checks if not c.get("passed", False))
    all_passed = (failed_checks == 0)

    return {
        "status": "PASS" if all_passed else "FAIL",
        "total_checks": len(checks),
        "failed_checks": failed_checks,
        "csv_validation": csv_audit,
        "json_validation": json_audit,
        "sqlite_validation": sqlite_audit,
        "seed_validation": seed_audit,
        "ground_truth_validation": gt_audit,
    }
