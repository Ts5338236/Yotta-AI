"""Data export engine for Procure-to-Pay Synthetic Data Generator (Phase 6).

Exports synthetic procurement datasets into CSV, JSON, normalized SQLite database tables,
and self-contained SQL seed scripts in full alignment with assignment specifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence
import numpy as np
import pandas as pd


# Order of table insertion respecting foreign-key dependencies
EXPORT_TABLES_ORDER = [
    "departments",
    "budgets",
    "requesters",
    "approvers",
    "suppliers",
    "purchase_requests",
    "request_lines",
    "rfqs",
    "rfq_supplier_invites",
    "supplier_quotes",
    "quote_lines",
    "approvals",
    "purchase_orders",
    "purchase_order_lines",
    "deliveries",
    "status_events",
    "budget_events",
    "exception_logs",
    "ground_truth",
]


def _compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 cryptographic hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def export_to_csv(
    dataset: Dict[str, Any],
    output_dir: str | Path = "output/csv",
) -> Dict[str, Path]:
    """Export all dataset entity lists to individual CSV files in output_dir.

    Args:
        dataset: Dictionary containing all procurement entity record lists.
        output_dir: Destination folder path.

    Returns:
        Dict mapping table names to their exported CSV file paths.
    """
    out_p = Path(output_dir).resolve()
    out_p.mkdir(parents=True, exist_ok=True)
    exported_files: Dict[str, Path] = {}

    for table_name, records in dataset.items():
        if isinstance(records, list) and records and isinstance(records[0], dict):
            csv_path = out_p / f"{table_name}.csv"
            df = pd.DataFrame(records)
            df.to_csv(csv_path, index=False, encoding="utf-8")
            exported_files[table_name] = csv_path

    return exported_files


def export_to_json(
    dataset: Dict[str, Any],
    output_dir: str | Path = "output/json",
) -> Dict[str, Path]:
    """Export all dataset entity lists to individual JSON files in output_dir.

    Args:
        dataset: Dictionary containing all procurement entity record lists.
        output_dir: Destination folder path.

    Returns:
        Dict mapping table names to their exported JSON file paths.
    """
    out_p = Path(output_dir).resolve()
    out_p.mkdir(parents=True, exist_ok=True)
    exported_files: Dict[str, Path] = {}

    for table_name, records in dataset.items():
        if isinstance(records, list) and records and isinstance(records[0], dict):
            json_path = out_p / f"{table_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, default=str)
            exported_files[table_name] = json_path

    # Export metadata if present
    if "metadata" in dataset and isinstance(dataset["metadata"], dict):
        meta_path = out_p / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(dataset["metadata"], f, indent=2, default=str)
        exported_files["metadata"] = meta_path

    return exported_files


def export_to_sqlite(
    dataset: Dict[str, Any],
    db_path: str | Path = "output/database/procurement.db",
    schema_path: str | Path = "data/sql/schema.sql",
    enable_fk: bool = True,
) -> Path:
    """Initialize an SQLite database from schema.sql and populate with dataset records.

    Args:
        dataset: Dictionary containing all procurement entity record lists.
        db_path: File path of the target SQLite database.
        schema_path: File path of the canonical schema.sql script.
        enable_fk: Whether to enforce PRAGMA foreign_keys = ON.

    Returns:
        Path to the populated SQLite database file.
    """
    target_db = Path(db_path).resolve()
    target_db.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database file if present to guarantee fresh population
    if target_db.exists():
        target_db.unlink()

    resolved_schema = Path(schema_path).resolve()
    if not resolved_schema.exists():
        raise FileNotFoundError(f"Schema file not found at: {resolved_schema}")

    with open(resolved_schema, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(target_db))
    try:
        if enable_fk:
            conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)

        # Ensure ground_truth table exists if ground truth is present
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ground_truth (
                anomaly_id TEXT PRIMARY KEY,
                issue_type TEXT NOT NULL,
                entity TEXT NOT NULL,
                record_id TEXT NOT NULL,
                expected_decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor = conn.cursor()

        # Insert records in dependency order
        for table in EXPORT_TABLES_ORDER:
            rows = dataset.get(table, [])
            if not rows:
                continue

            # Query table columns from sqlite_master
            col_info = cursor.execute(f"PRAGMA table_info({table})").fetchall()
            valid_cols = [c[1] for c in col_info]
            if not valid_cols:
                continue

            col_names_str = ", ".join(valid_cols)
            placeholders = ", ".join(["?"] * len(valid_cols))
            sql = f"INSERT OR REPLACE INTO {table} ({col_names_str}) VALUES ({placeholders})"

            batch_data = []
            for row in rows:
                row_vals = []
                for col in valid_cols:
                    val = row.get(col)
                    # Convert boolean to integer for SQLite compatibility
                    if isinstance(val, bool):
                        val = 1 if val else 0
                    elif val is None and col == "fx_rate_to_base":
                        val = 1.0  # Fallback for SQLite schema NOT NULL constraint on currency mismatch anomalies
                    elif isinstance(val, dict):
                        val = json.dumps(val)
                    row_vals.append(val)
                batch_data.append(row_vals)

            cursor.executemany(sql, batch_data)

        conn.commit()
    finally:
        conn.close()

    return target_db


def export_to_sql_seed(
    dataset: Dict[str, Any],
    output_path: str | Path = "output/sql/seed.sql",
    schema_path: str | Path = "data/sql/schema.sql",
) -> Path:
    """Generate self-contained SQL seed script with INSERT statements in FK order.

    Args:
        dataset: Dictionary containing all procurement entity record lists.
        output_path: File path of the target seed.sql script.
        schema_path: File path of canonical schema.sql for table inspection.

    Returns:
        Path to the generated seed.sql script.
    """
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Introspect column names using an in-memory database
    resolved_schema = Path(schema_path).resolve()
    with open(resolved_schema, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    mem_conn = sqlite3.connect(":memory:")
    mem_conn.executescript(schema_sql)
    mem_conn.execute("""
        CREATE TABLE IF NOT EXISTS ground_truth (
            anomaly_id TEXT PRIMARY KEY,
            issue_type TEXT NOT NULL,
            entity TEXT NOT NULL,
            record_id TEXT NOT NULL,
            expected_decision TEXT NOT NULL,
            reason TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    mem_cur = mem_conn.cursor()

    lines: List[str] = [
        "-- ============================================================================",
        "-- Procure-to-Pay Synthetic Dataset: Deterministic Seed Script",
        "-- Foreign keys are preserved via strict topological insertion order.",
        "-- ============================================================================",
        "",
        "PRAGMA foreign_keys = OFF;",
        "BEGIN TRANSACTION;",
        "",
    ]

    for table in EXPORT_TABLES_ORDER:
        rows = dataset.get(table, [])
        if not rows:
            continue

        col_info = mem_cur.execute(f"PRAGMA table_info({table})").fetchall()
        valid_cols = [c[1] for c in col_info]
        if not valid_cols:
            continue

        lines.append(f"-- ----------------------------------------------------------------------------")
        lines.append(f"-- Table: {table} ({len(rows)} records)")
        lines.append(f"-- ----------------------------------------------------------------------------")

        cols_clause = ", ".join(valid_cols)
        batch_size = 200

        for batch_start in range(0, len(rows), batch_size):
            batch = rows[batch_start : batch_start + batch_size]
            val_tuples: List[str] = []

            for row in batch:
                formatted_vals: List[str] = []
                for col in valid_cols:
                    v = row.get(col)
                    if v is None:
                        if col == "fx_rate_to_base":
                            formatted_vals.append("1.0")
                        else:
                            formatted_vals.append("NULL")
                    elif isinstance(v, bool):
                        formatted_vals.append("1" if v else "0")
                    elif isinstance(v, (int, np.integer)):
                        formatted_vals.append(str(int(v)))
                    elif isinstance(v, (float, np.floating)):
                        if np.isnan(v):
                            formatted_vals.append("NULL")
                        else:
                            formatted_vals.append(str(round(float(v), 4)))
                    elif isinstance(v, dict):
                        escaped = json.dumps(v).replace("'", "''")
                        formatted_vals.append(f"'{escaped}'")
                    else:
                        escaped = str(v).replace("'", "''")
                        formatted_vals.append(f"'{escaped}'")
                val_tuples.append(f"  ({', '.join(formatted_vals)})")

            lines.append(f"INSERT OR REPLACE INTO {table} ({cols_clause}) VALUES")
            lines.append(",\n".join(val_tuples) + ";")
            lines.append("")

    lines.append("COMMIT;")
    lines.append("PRAGMA foreign_keys = ON;")
    lines.append("")

    mem_conn.close()

    with open(out_p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return out_p


def export_to_sql_schema(
    schema_src: str | Path = "data/sql/schema.sql",
    output_path: str | Path = "output/sql/schema.sql",
) -> Path:
    """Export canonical schema DDL to target destination.

    Args:
        schema_src: Path to canonical schema.sql.
        output_path: Target path for output/sql/schema.sql.

    Returns:
        Path to output schema file.
    """
    src = Path(schema_src).resolve()
    dst = Path(output_path).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


def generate_source_manifest(
    dataset: Dict[str, Any],
    output_path: str | Path = "output/source_manifest.json",
    exported_files: Optional[Dict[str, Path]] = None,
) -> Dict[str, Any]:
    """Generate comprehensive provenance, environment, and cryptographic checksum manifest.

    Args:
        dataset: Procurement dataset.
        output_path: Destination manifest file path.
        exported_files: Optional mapping of artifact identifiers to file paths.

    Returns:
        Dict representing manifest content.
    """
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    metadata = dataset.get("metadata", {})
    scale = metadata.get("scale", "full")
    seed = metadata.get("seed", 20261022)

    record_counts = {
        table: len(records)
        for table, records in dataset.items()
        if isinstance(records, list)
    }

    file_checksums: Dict[str, Dict[str, Any]] = {}
    if exported_files:
        for name, path in exported_files.items():
            p = Path(path).resolve()
            if p.exists() and p.is_file():
                file_checksums[name] = {
                    "path": str(p.relative_to(p.parent.parent)),
                    "size_bytes": p.stat().st_size,
                    "sha256": _compute_sha256(p),
                }

    manifest: Dict[str, Any] = {
        "manifest_version": "1.0.0",
        "project": "YottaFlex Procure-to-Pay Synthetic Data Generator",
        "repository": "https://github.com/Ts5338236/Yotta-AI.git",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_provenance": {
            "synthetic": True,
            "external_proprietary_data": False,
            "external_web_apis_used": False,
            "real_world_pii_present": False,
            "generation_method": "Deterministic Algorithmic Simulation via isolated NumPy Seeded RNG",
            "certification": "100% synthetically generated data; zero external datasets imported",
        },
        "reproducibility": {
            "default_seed": seed,
            "scale_tier": scale,
            "deterministic": True,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "record_counts": record_counts,
        "exported_artifacts": file_checksums,
    }

    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Also copy to workspace root ./source_manifest.json if output_path is in output/
    root_manifest = Path("source_manifest.json").resolve()
    if out_p != root_manifest:
        shutil.copyfile(out_p, root_manifest)

    return manifest


def verify_export_integrity(
    dataset: Dict[str, Any],
    output_dir: str | Path = "output",
    schema_path: str | Path = "data/sql/schema.sql",
) -> Dict[str, Any]:
    """Verify that all exported artifacts match dataset counts and pass database integrity checks.

    Args:
        dataset: Source in-memory dataset.
        output_dir: Root output directory.
        schema_path: Path to canonical schema.

    Returns:
        Dict detailing verification results and overall status.
    """
    out_root = Path(output_dir).resolve()
    csv_dir = out_root / "csv"
    json_dir = out_root / "json"
    db_file = out_root / "database" / "procurement.db"
    seed_file = out_root / "sql" / "seed.sql"

    checks: List[Dict[str, Any]] = []
    overall_passed = True

    # 1. Verify CSV files
    for table in EXPORT_TABLES_ORDER:
        rows = dataset.get(table, [])
        if not rows:
            continue
        csv_file = csv_dir / f"{table}.csv"
        if not csv_file.exists():
            checks.append({"artifact": f"csv/{table}.csv", "check": "file_exists", "passed": False})
            overall_passed = False
            continue

        df = pd.read_csv(csv_file)
        count_match = len(df) == len(rows)
        checks.append({
            "artifact": f"csv/{table}.csv",
            "check": "record_count_match",
            "expected": len(rows),
            "actual": len(df),
            "passed": count_match,
        })
        if not count_match:
            overall_passed = False

    # 2. Verify JSON files
    for table in EXPORT_TABLES_ORDER:
        rows = dataset.get(table, [])
        if not rows:
            continue
        j_file = json_dir / f"{table}.json"
        if not j_file.exists():
            checks.append({"artifact": f"json/{table}.json", "check": "file_exists", "passed": False})
            overall_passed = False
            continue

        with open(j_file, "r", encoding="utf-8") as f:
            j_data = json.load(f)
        count_match = len(j_data) == len(rows)
        checks.append({
            "artifact": f"json/{table}.json",
            "check": "record_count_match",
            "expected": len(rows),
            "actual": len(j_data),
            "passed": count_match,
        })
        if not count_match:
            overall_passed = False

    # 3. Verify SQLite DB
    if db_file.exists():
        conn = sqlite3.connect(str(db_file))
        try:
            # PRAGMA integrity_check
            integ = conn.execute("PRAGMA integrity_check;").fetchall()
            integ_passed = len(integ) == 1 and integ[0][0] == "ok"
            checks.append({"artifact": "procurement.db", "check": "integrity_check", "passed": integ_passed})
            if not integ_passed:
                overall_passed = False

            # PRAGMA foreign_key_check
            fk_errs = conn.execute("PRAGMA foreign_key_check;").fetchall()
            fk_passed = len(fk_errs) == 0
            checks.append({
                "artifact": "procurement.db",
                "check": "foreign_key_check",
                "violations_count": len(fk_errs),
                "passed": fk_passed,
            })
            if not fk_passed:
                overall_passed = False
        finally:
            conn.close()
    else:
        checks.append({"artifact": "procurement.db", "check": "file_exists", "passed": False})
        overall_passed = False

    # 4. Verify seed.sql execution against clean in-memory database
    if seed_file.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        with open(seed_file, "r", encoding="utf-8") as f:
            seed_sql = f.read()

        test_conn = sqlite3.connect(":memory:")
        try:
            test_conn.execute("PRAGMA foreign_keys = ON;")
            test_conn.executescript(schema_sql)
            test_conn.executescript(seed_sql)
            fk_errs = test_conn.execute("PRAGMA foreign_key_check;").fetchall()
            seed_ok = (len(fk_errs) == 0)
            checks.append({
                "artifact": "seed.sql",
                "check": "execution_against_clean_schema",
                "foreign_key_violations": len(fk_errs),
                "passed": seed_ok,
            })
            if not seed_ok:
                overall_passed = False
        except Exception as e:
            checks.append({
                "artifact": "seed.sql",
                "check": "execution_against_clean_schema",
                "error": str(e),
                "passed": False,
            })
            overall_passed = False
        finally:
            test_conn.close()
    else:
        checks.append({"artifact": "seed.sql", "check": "file_exists", "passed": False})
        overall_passed = False

    report = {
        "status": "PASS" if overall_passed else "FAIL",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "total_checks": len(checks),
        "passed_checks": len([c for c in checks if c["passed"]]),
        "failed_checks": len([c for c in checks if not c["passed"]]),
        "checks": checks,
    }

    # Save reports to output/reports/
    rep_dir = out_root / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    with open(rep_dir / "export_integrity_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md_lines = [
        "# Export Integrity Verification Report",
        "",
        f"- **Status**: `{report['status']}`",
        f"- **Verified At**: `{report['verified_at']}`",
        f"- **Passed Checks**: `{report['passed_checks']} / {report['total_checks']}`",
        "",
        "| Artifact | Check | Passed | Details |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for c in checks:
        details = f"expected={c.get('expected')}, actual={c.get('actual')}" if "expected" in c else c.get("error", "OK")
        pass_badge = "PASS" if c["passed"] else "FAIL"
        md_lines.append(f"| `{c['artifact']}` | `{c['check']}` | **{pass_badge}** | {details} |")

    with open(rep_dir / "export_integrity_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    return report


def generate_dataset_statistics(
    dataset: Dict[str, Any],
    output_dir: str | Path = "output",
) -> Dict[str, Any]:
    """Generate dataset statistics report in JSON and Markdown formats.

    Args:
        dataset: Source procurement dataset.
        output_dir: Root output directory.

    Returns:
        Dict of statistical metrics.
    """
    out_root = Path(output_dir).resolve()
    rep_dir = out_root / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)

    prs = dataset.get("purchase_requests", [])
    pos = dataset.get("purchase_orders", [])
    quotes = dataset.get("supplier_quotes", [])
    suppliers = dataset.get("suppliers", [])
    deliveries = dataset.get("deliveries", [])
    anomalies = dataset.get("ground_truth", [])

    total_pr_estimate = sum(pr.get("total_estimate_usd", 0.0) for pr in prs)
    total_po_value = sum(po.get("total_amount_usd", 0.0) for po in pos)

    comp_pos = [po for po in pos if po.get("sourcing_path") == "competitive"]
    non_comp_pos = [po for po in pos if po.get("sourcing_path") != "competitive"]

    stats: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary_counts": {
            "departments": len(dataset.get("departments", [])),
            "budgets": len(dataset.get("budgets", [])),
            "requesters": len(dataset.get("requesters", [])),
            "suppliers": len(suppliers),
            "approvers": len(dataset.get("approvers", [])),
            "purchase_requests": len(prs),
            "request_lines": len(dataset.get("request_lines", [])),
            "rfqs": len(dataset.get("rfqs", [])),
            "supplier_quotes": len(quotes),
            "quote_lines": len(dataset.get("quote_lines", [])),
            "approvals": len(dataset.get("approvals", [])),
            "purchase_orders": len(pos),
            "purchase_order_lines": len(dataset.get("purchase_order_lines", [])),
            "deliveries": len(deliveries),
            "status_events": len(dataset.get("status_events", [])),
            "budget_events": len(dataset.get("budget_events", [])),
            "ground_truth_anomalies": len(anomalies),
        },
        "financial_totals": {
            "total_estimated_spend_usd": round(total_pr_estimate, 2),
            "total_committed_po_value_usd": round(total_po_value, 2),
            "average_po_value_usd": round(total_po_value / len(pos), 2) if pos else 0.0,
            "competitive_pos_count": len(comp_pos),
            "competitive_pos_value_usd": round(sum(p.get("total_amount_usd", 0.0) for p in comp_pos), 2),
            "non_competitive_pos_count": len(non_comp_pos),
            "non_competitive_pos_value_usd": round(sum(p.get("total_amount_usd", 0.0) for p in non_comp_pos), 2),
        },
        "supplier_breakdown": {
            "active": len([s for s in suppliers if s.get("status") == "ACTIVE"]),
            "preferred": len([s for s in suppliers if s.get("status") == "PREFERRED"]),
            "probation": len([s for s in suppliers if s.get("status") == "PROBATION"]),
            "inactive": len([s for s in suppliers if s.get("status") == "INACTIVE"]),
        },
        "anomaly_breakdown": {
            "total_anomalies": len(anomalies),
            "by_type": {},
        },
    }

    for anom in anomalies:
        itype = anom.get("issue_type", "UNKNOWN")
        stats["anomaly_breakdown"]["by_type"][itype] = stats["anomaly_breakdown"]["by_type"].get(itype, 0) + 1

    with open(rep_dir / "dataset_statistics.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    md_lines = [
        "# Dataset Summary Statistics",
        "",
        f"- **Generated At**: `{stats['generated_at']}`",
        f"- **Total Purchase Requests**: `{stats['summary_counts']['purchase_requests']}`",
        f"- **Total Purchase Orders**: `{stats['summary_counts']['purchase_orders']}`",
        f"- **Total Committed PO Value**: `${stats['financial_totals']['total_committed_po_value_usd']:,.2f}`",
        f"- **Total Injected Anomalies**: `{stats['anomaly_breakdown']['total_anomalies']}`",
        "",
        "## Entity Record Counts",
        "",
        "| Entity Name | Record Count |",
        "| :--- | :--- |",
    ]
    for ent, cnt in stats["summary_counts"].items():
        md_lines.append(f"| `{ent}` | {cnt:,} |")

    md_lines.extend([
        "",
        "## Financial Summary",
        "",
        f"- **Total PR Estimate**: `${stats['financial_totals']['total_estimated_spend_usd']:,.2f}`",
        f"- **Total PO Committed**: `${stats['financial_totals']['total_committed_po_value_usd']:,.2f}`",
        f"- **Competitive Orders**: {stats['financial_totals']['competitive_pos_count']} (${stats['financial_totals']['competitive_pos_value_usd']:,.2f})",
        f"- **Non-Competitive Orders**: {stats['financial_totals']['non_competitive_pos_count']} (${stats['financial_totals']['non_competitive_pos_value_usd']:,.2f})",
        "",
        "## Injected Anomaly Distribution",
        "",
        "| Anomaly Type | Count |",
        "| :--- | :--- |",
    ])
    for itype, cnt in stats["anomaly_breakdown"]["by_type"].items():
        md_lines.append(f"| `{itype}` | {cnt} |")

    with open(rep_dir / "dataset_statistics.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    return stats


def export_all(
    dataset: Dict[str, Any],
    output_dir: str | Path = "output",
    csv_dir: Optional[str | Path] = None,
    json_dir: Optional[str | Path] = None,
    db_path: Optional[str | Path] = None,
    schema_path: str | Path = "data/sql/schema.sql",
    seed_path: Optional[str | Path] = None,
    include_reports: bool = True,
) -> Dict[str, Any]:
    """Execute complete export pipeline across CSV, JSON, SQLite DB, DDL schema, and seed script.

    Args:
        dataset: Dictionary containing all procurement entity record lists.
        output_dir: Primary root destination directory (defaults to 'output').
        csv_dir: Optional custom CSV destination directory.
        json_dir: Optional custom JSON destination directory.
        db_path: Optional custom SQLite database path.
        schema_path: Canonical schema DDL path.
        seed_path: Optional custom seed.sql path.
        include_reports: Whether to generate integrity verification and statistics reports.

    Returns:
        Dict summarizing exported artifact paths and counts.
    """
    out_root = Path(output_dir).resolve()
    target_csv = Path(csv_dir).resolve() if csv_dir else out_root / "csv"
    target_json = Path(json_dir).resolve() if json_dir else out_root / "json"
    target_db = Path(db_path).resolve() if db_path else out_root / "database" / "procurement.db"
    target_schema = out_root / "sql" / "schema.sql"
    target_seed = Path(seed_path).resolve() if seed_path else out_root / "sql" / "seed.sql"

    # 1. Export CSV
    csv_files = export_to_csv(dataset, output_dir=target_csv)

    # 2. Export JSON
    json_files = export_to_json(dataset, output_dir=target_json)

    # 3. Export SQLite database
    database_file = export_to_sqlite(dataset, db_path=target_db, schema_path=schema_path)

    # 4. Export DDL schema
    schema_file = export_to_sql_schema(schema_src=schema_path, output_path=target_schema)

    # 5. Export SQL seed
    seed_file = export_to_sql_seed(dataset, output_path=target_seed, schema_path=schema_path)

    # Compile artifact tracking map for manifest
    tracked_artifacts: Dict[str, Path] = {
        "sqlite_db": database_file,
        "schema_ddl": schema_file,
        "seed_sql": seed_file,
    }
    for k, p in csv_files.items():
        tracked_artifacts[f"csv_{k}"] = p
    for k, p in json_files.items():
        tracked_artifacts[f"json_{k}"] = p

    # 6. Generate reports & manifest
    integrity_report = None
    stats_report = None
    if include_reports:
        integrity_report = verify_export_integrity(dataset, output_dir=out_root, schema_path=schema_path)
        stats_report = generate_dataset_statistics(dataset, output_dir=out_root)

    manifest = generate_source_manifest(
        dataset,
        output_path=out_root / "source_manifest.json",
        exported_files=tracked_artifacts,
    )

    return {
        "output_dir": str(out_root),
        "csv_files": {k: str(v) for k, v in csv_files.items()},
        "json_files": {k: str(v) for k, v in json_files.items()},
        "sqlite_db": str(database_file),
        "schema_ddl": str(schema_file),
        "seed_sql": str(seed_file),
        "manifest": str(out_root / "source_manifest.json"),
        "integrity_report": integrity_report,
        "statistics": stats_report,
        "total_tables_exported": len(csv_files),
    }
