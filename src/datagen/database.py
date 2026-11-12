"""Database persistence and relational schema management engine (Phase 6).

Handles normalized SQLite database creation, schema execution, transactional bulk data insertion,
foreign-key enforcement, and database integrity verification.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
import numpy as np


# Dependency-ordered insertion sequence ensuring parent records precede dependent records
DB_TABLES_ORDER = [
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
]


class DatabaseError(Exception):
    """Raised when a database schema, transaction, or constraint operation fails."""
    pass


def get_connection(
    db_path: str | Path,
    enable_foreign_keys: bool = True,
    timeout: float = 30.0,
) -> sqlite3.Connection:
    """Create and return a configured SQLite connection.

    Args:
        db_path: Target database file path.
        enable_foreign_keys: Whether to enforce PRAGMA foreign_keys = ON.
        timeout: Lock acquisition timeout in seconds.

    Returns:
        sqlite3.Connection: Configured connection instance.
    """
    path = Path(db_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=timeout)
    if enable_foreign_keys:
        conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_schema(
    db_path: str | Path,
    schema_path: str | Path = "output/sql/schema.sql",
    enable_foreign_keys: bool = True,
) -> Path:
    """Initialize a blank SQLite database executing DDL schema statements.

    Args:
        db_path: Destination SQLite database path.
        schema_path: Path to canonical schema DDL file.
        enable_foreign_keys: Enforce foreign keys during creation.

    Returns:
        Path: Resolved database file path.
    """
    db_file = Path(db_path).resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    if db_file.exists():
        db_file.unlink()

    schema_file = Path(schema_path).resolve()
    if not schema_file.exists():
        alt_schema = Path("output/sql/schema.sql").resolve()
        if alt_schema.exists():
            schema_file = alt_schema
        else:
            raise FileNotFoundError(f"Schema DDL script not found at: {schema_file}")

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection(db_file, enable_foreign_keys=enable_foreign_keys)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    except Exception as exc:
        conn.close()
        if db_file.exists():
            db_file.unlink()
        raise DatabaseError(f"Failed to initialize schema from {schema_file}: {exc}") from exc
    finally:
        conn.close()

    return db_file


def populate_database(
    dataset: Dict[str, Any],
    db_path: str | Path = "output/database/procurement.db",
    schema_path: str | Path = "output/sql/schema.sql",
    enable_foreign_keys: bool = True,
) -> Path:
    """Populate SQLite database from in-memory dataset respecting topological order.

    Uses strict transactional insertion without INSERT OR IGNORE, rolling back
    safely on any constraint violation or type mismatch.

    Args:
        dataset: Source procurement records dictionary.
        db_path: Destination SQLite database path.
        schema_path: Canonical schema DDL path.
        enable_foreign_keys: Enforce foreign keys during insertion.

    Returns:
        Path: Resolved path to populated database.
    """
    db_file = initialize_schema(db_path, schema_path, enable_foreign_keys=enable_foreign_keys)
    conn = get_connection(db_file, enable_foreign_keys=enable_foreign_keys)

    try:
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION;")

        for table in DB_TABLES_ORDER:
            rows = dataset.get(table, [])
            if not rows:
                continue

            col_info = cursor.execute(f"PRAGMA table_info({table});").fetchall()
            valid_cols = [c[1] for c in col_info]
            if not valid_cols:
                continue

            col_names_str = ", ".join(valid_cols)
            placeholders = ", ".join(["?"] * len(valid_cols))
            insert_sql = f"INSERT INTO {table} ({col_names_str}) VALUES ({placeholders});"

            batch_values: List[List[Any]] = []
            for row in rows:
                row_vals: List[Any] = []
                for col in valid_cols:
                    val = row.get(col)
                    if isinstance(val, bool):
                        val = 1 if val else 0
                    elif isinstance(val, (int, np.integer)):
                        val = int(val)
                    elif isinstance(val, (float, np.floating)):
                        val = float(val) if not np.isnan(val) else None
                    elif isinstance(val, (dict, list)):
                        val = json.dumps(val)
                    elif val is None and col == "fx_rate_to_base":
                        val = 1.0  # Preserve schema NOT NULL constraint
                    row_vals.append(val)
                batch_values.append(row_vals)

            try:
                cursor.executemany(insert_sql, batch_values)
            except sqlite3.IntegrityError as err:
                raise DatabaseError(
                    f"Integrity error inserting into table '{table}': {err}"
                ) from err

        conn.commit()
    except Exception as exc:
        conn.rollback()
        conn.close()
        if db_file.exists():
            db_file.unlink()
        raise DatabaseError(f"Database population failed and rolled back: {exc}") from exc
    finally:
        conn.close()

    # Run post-population integrity verification
    integrity = check_database_integrity(db_file)
    if not integrity["integrity_ok"]:
        raise DatabaseError(f"PRAGMA integrity_check failed: {integrity['integrity_result']}")
    if integrity["foreign_key_violations"]:
        raise DatabaseError(
            f"Foreign key violations detected ({len(integrity['foreign_key_violations'])}): {integrity['foreign_key_violations']}"
        )

    return db_file


def check_database_integrity(db_path: str | Path) -> Dict[str, Any]:
    """Execute SQLite integrity and foreign-key check PRAGMAs.

    Args:
        db_path: Path to target SQLite database.

    Returns:
        Dict[str, Any]: Results of integrity and foreign-key checks.
    """
    path = Path(db_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Database not found at: {path}")

    conn = get_connection(path, enable_foreign_keys=True)
    try:
        # PRAGMA integrity_check
        integrity_rows = conn.execute("PRAGMA integrity_check;").fetchall()
        integrity_ok = len(integrity_rows) == 1 and integrity_rows[0][0] == "ok"

        # PRAGMA foreign_key_check
        fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()

        # Query table record counts
        table_counts: Dict[str, int] = {}
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()
        for (t_name,) in tables:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t_name};").fetchone()[0]
            table_counts[t_name] = cnt

        return {
            "database_path": str(path),
            "integrity_ok": integrity_ok,
            "integrity_result": integrity_rows[0][0] if integrity_rows else "unknown",
            "foreign_key_violations_count": len(fk_violations),
            "foreign_key_violations": [
                {"table": v[0], "rowid": v[1], "parent_table": v[2], "fkid": v[3]}
                for v in fk_violations
            ],
            "table_counts": table_counts,
        }
    finally:
        conn.close()


def execute_sql_file(
    db_path: str | Path,
    sql_file_path: str | Path,
    enable_foreign_keys: bool = True,
) -> None:
    """Execute a raw SQL script file against an SQLite database.

    Args:
        db_path: Path to target SQLite database.
        sql_file_path: Path to SQL script.
        enable_foreign_keys: Whether to enforce PRAGMA foreign_keys = ON.
    """
    db_p = Path(db_path).resolve()
    sql_p = Path(sql_file_path).resolve()

    if not sql_p.exists():
        raise FileNotFoundError(f"SQL file not found at: {sql_p}")

    with open(sql_p, "r", encoding="utf-8") as f:
        sql_content = f.read()

    conn = get_connection(db_p, enable_foreign_keys=enable_foreign_keys)
    try:
        conn.executescript(sql_content)
        conn.commit()
    except Exception as exc:
        raise DatabaseError(f"Failed to execute SQL script {sql_p}: {exc}") from exc
    finally:
        conn.close()

