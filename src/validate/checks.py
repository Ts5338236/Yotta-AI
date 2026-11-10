"""Foundational validation checks for Procure-to-Pay Synthetic Data Generator.

Provides basic database integrity, foreign-key enforcement, table existence,
and ID format validation utilities for Phase 1.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from datagen.ids import ID_REGEX_MAP, validate_id as validate_entity_id


EXPECTED_TABLES: Set[str] = {
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
}


class ValidationCheckError(Exception):
    """Raised when a foundational validation check fails."""
    pass


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Connect to SQLite database with foreign keys enabled.

    Args:
        db_path: Filesystem path to SQLite database.

    Returns:
        sqlite3.Connection: SQLite connection object.
    """
    path = Path(db_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {path}")

    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def check_foreign_keys_enabled(conn: sqlite3.Connection) -> bool:
    """Verify that foreign key constraint enforcement is active."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    row = cursor.fetchone()
    return bool(row and row[0] == 1)


def check_schema_integrity(conn: sqlite3.Connection) -> Tuple[bool, List[str]]:
    """Execute PRAGMA integrity_check to verify SQLite database file health.

    Returns:
        Tuple[bool, List[str]]: (Passed boolean, list of integrity error messages).
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    rows = cursor.fetchall()
    messages = [r[0] for r in rows]
    is_ok = len(messages) == 1 and messages[0] == "ok"
    return is_ok, messages


def check_foreign_key_violations(conn: sqlite3.Connection) -> List[Tuple[Any, ...]]:
    """Execute PRAGMA foreign_key_check to detect orphaned references."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    return cursor.fetchall()


def get_existing_tables(conn: sqlite3.Connection) -> Set[str]:
    """Retrieve set of user table names in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return {row[0] for row in cursor.fetchall()}


def check_required_tables_exist(
    conn: sqlite3.Connection,
    expected_tables: Set[str] | None = None,
) -> Tuple[bool, Set[str]]:
    """Check if all required core and auxiliary tables exist.

    Returns:
        Tuple[bool, Set[str]]: (All present boolean, set of missing table names).
    """
    expected = expected_tables or EXPECTED_TABLES
    existing = get_existing_tables(conn)
    missing = expected - existing
    return len(missing) == 0, missing


def validate_id_format(entity_type: str, entity_id: str) -> bool:
    """Validate an ID string against the canonical regex for an entity type."""
    try:
        return validate_entity_id(entity_type, entity_id)
    except KeyError:
        return False


def run_foundational_checks(db_path: str | Path) -> Dict[str, Any]:
    """Execute the full Phase 1 foundational check suite against a database.

    Args:
        db_path: Path to the SQLite database.

    Returns:
        Dict[str, Any]: Summary results of the checks.
    """
    conn = get_connection(db_path)
    try:
        fk_enabled = check_foreign_keys_enabled(conn)
        integrity_ok, integrity_messages = check_schema_integrity(conn)
        tables_ok, missing_tables = check_required_tables_exist(conn)
        fk_violations = check_foreign_key_violations(conn)

        all_passed = fk_enabled and integrity_ok and tables_ok and len(fk_violations) == 0

        return {
            "all_passed": all_passed,
            "foreign_keys_enabled": fk_enabled,
            "integrity_ok": integrity_ok,
            "integrity_messages": integrity_messages,
            "tables_ok": tables_ok,
            "missing_tables": sorted(list(missing_tables)),
            "fk_violations_count": len(fk_violations),
            "fk_violations": fk_violations,
        }
    finally:
        conn.close()


def main() -> None:
    """CLI runner for foundational database validation."""
    parser = argparse.ArgumentParser(description="Foundational SQLite validation checks (Phase 1)")
    parser.add_argument("db_path", help="Path to SQLite database file to validate")
    args = parser.parse_args()

    try:
        results = run_foundational_checks(args.db_path)
        print("=== Foundational Validation Results ===")
        print(f"Foreign Keys Enabled : {results['foreign_keys_enabled']}")
        print(f"Schema Integrity OK  : {results['integrity_ok']}")
        print(f"All Tables Present   : {results['tables_ok']}")
        if not results["tables_ok"]:
            print(f"Missing Tables       : {results['missing_tables']}")
        print(f"FK Violations Count  : {results['fk_violations_count']}")
        print(f"Overall Status       : {'PASSED' if results['all_passed'] else 'FAILED'}")

        if not results["all_passed"]:
            sys.exit(1)
    except Exception as err:
        print(f"Error during validation: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
