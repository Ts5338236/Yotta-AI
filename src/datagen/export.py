"""Data export engine for Procure-to-Pay Synthetic Data Generator (Phase 6).

Exports synthetic procurement datasets into CSV, JSON, and normalized SQLite database tables.
Supports export of clean operational data and ground-truth anomaly manifests.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Mapping, Optional, Sequence
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
]


def export_to_csv(
    dataset: Dict[str, Any],
    output_dir: str | Path = "data/csv",
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
    output_dir: str | Path = "data/json",
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
    db_path: str | Path = "data/p2p_procurement.db",
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
        if "ground_truth" in dataset:
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
                    row_vals.append(val)
                batch_data.append(row_vals)

            cursor.executemany(sql, batch_data)

        # Insert ground truth if available
        if "ground_truth" in dataset and dataset["ground_truth"]:
            gt_sql = """
                INSERT OR REPLACE INTO ground_truth
                (anomaly_id, issue_type, entity, record_id, expected_decision, reason, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            gt_data = [
                (
                    gt["anomaly_id"],
                    gt["issue_type"],
                    gt["entity"],
                    gt["record_id"],
                    gt["expected_decision"],
                    gt["reason"],
                    json.dumps(gt.get("metadata", {})) if isinstance(gt.get("metadata"), dict) else str(gt.get("metadata", "")),
                )
                for gt in dataset["ground_truth"]
            ]
            cursor.executemany(gt_sql, gt_data)

        conn.commit()
    finally:
        conn.close()

    return target_db


def export_all(
    dataset: Dict[str, Any],
    csv_dir: str | Path = "data/csv",
    json_dir: str | Path = "data/json",
    db_path: str | Path = "data/p2p_procurement.db",
    schema_path: str | Path = "data/sql/schema.sql",
) -> Dict[str, Any]:
    """Execute complete export pipeline across CSV, JSON, and SQLite database.

    Args:
        dataset: Dictionary containing all procurement entity record lists.
        csv_dir: Destination directory for CSV exports.
        json_dir: Destination directory for JSON exports.
        db_path: Destination path for SQLite database.
        schema_path: Canonical schema DDL path.

    Returns:
        Dict summarizing exported artifact paths and counts.
    """
    csv_files = export_to_csv(dataset, output_dir=csv_dir)
    json_files = export_to_json(dataset, output_dir=json_dir)
    database_file = export_to_sqlite(dataset, db_path=db_path, schema_path=schema_path)

    return {
        "csv_files": {k: str(v) for k, v in csv_files.items()},
        "json_files": {k: str(v) for k, v in json_files.items()},
        "sqlite_db": str(database_file),
        "total_tables_exported": len(csv_files),
    }
