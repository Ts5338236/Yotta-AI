"""Command-line interface for Procure-to-Pay Synthetic Data Generator.

Provides commands to inspect configuration and initialize database schemas.
Data generation commands are scheduled for Phase 2 through Phase 7.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from datagen import __version__
from datagen.config import ConfigValidationError, load_config


def init_database(db_path: str | Path, schema_path: str | Path | None = None) -> None:
    """Initialize SQLite database from the canonical schema.sql script.

    Args:
        db_path: Path where the SQLite database file should be created/updated.
        schema_path: Optional custom path to schema.sql. Defaults to data/sql/schema.sql.
    """
    target_db = Path(db_path).resolve()
    target_db.parent.mkdir(parents=True, exist_ok=True)

    if schema_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        resolved_schema = project_root / "data" / "sql" / "schema.sql"
    else:
        resolved_schema = Path(schema_path).resolve()

    if not resolved_schema.exists():
        raise FileNotFoundError(f"Schema file not found at: {resolved_schema}")

    with open(resolved_schema, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(target_db))
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="p2p-datagen",
        description="Procure-to-Pay Synthetic Data Generator (Phase 1 Foundation)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration file (default: config/default.yaml)",
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate the specified or default configuration file and exit",
    )
    parser.add_argument(
        "--init-db",
        type=str,
        metavar="DB_PATH",
        help="Initialize SQLite database schema at the specified path and exit",
    )

    args = parser.parse_args(argv)

    if args.validate_config:
        try:
            cfg = load_config(args.config)
            print(f"Configuration valid! Project: {cfg['project']['name']} (v{cfg['project']['version']})")
            sys.exit(0)
        except (ConfigValidationError, FileNotFoundError) as err:
            print(f"Configuration error: {err}", file=sys.stderr)
            sys.exit(1)

    if args.init_db:
        try:
            init_database(args.init_db)
            print(f"Successfully initialized SQLite database schema at: {args.init_db}")
            sys.exit(0)
        except Exception as err:
            print(f"Failed to initialize database: {err}", file=sys.stderr)
            sys.exit(1)

    # Default message when invoked without specific action flags in Phase 1
    print("Procure-to-Pay Synthetic Data Generator - Phase 1 Foundation")
    print("Use --init-db <path> to create database schema, or --validate-config to test YAML config.")
    print("Synthetic data generation modules will be activated in Phase 2.")


if __name__ == "__main__":
    main()
