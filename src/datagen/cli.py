"""Command-line interface for Procure-to-Pay Synthetic Data Generator.

Provides commands to inspect configuration, initialize database schemas,
and run Phase 2 master and requisition data generation.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from datagen import __version__, generate_procurement_workflow
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
        description="Procure-to-Pay Synthetic Data Generator (Phase 2 Master & Requisition)",
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
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Execute in-memory synthetic data generation",
    )
    parser.add_argument(
        "--inject-anomalies",
        action="store_true",
        help="Inject controlled procurement anomalies into generated dataset",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Persist generated dataset to CSV, JSON, and SQLite database",
    )
    parser.add_argument(
        "--scale",
        type=str,
        choices=["starter", "full"],
        default=None,
        help="Scale tier to generate (starter or full)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic generation",
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

    if args.generate:
        try:
            dataset = generate_procurement_workflow(
                config_path=args.config,
                scale=args.scale,
                seed=args.seed,
            )
            meta = dataset["metadata"]
            total_spend = sum(po["value"] for po in dataset["purchase_orders"])

            gt_records = []
            if args.inject_anomalies:
                from datagen.anomalies import inject_anomalies
                import numpy as np
                cfg = load_config(args.config)
                rng = np.random.default_rng(meta["seed"])
                dataset, gt_records = inject_anomalies(dataset, cfg, rng)

            print("=== Procurement Workflow Generation Successful ===")
            print(f"Scale Tier        : {meta['scale']}")
            print(f"Random Seed       : {meta['seed']}")
            print(f"Departments       : {len(dataset['departments'])}")
            print(f"Budgets           : {len(dataset['budgets'])}")
            print(f"Requesters        : {len(dataset['requesters'])}")
            print(f"Suppliers         : {len(dataset['suppliers'])}")
            print(f"Approvers         : {len(dataset['approvers'])}")
            print(f"Purchase Requests : {len(dataset['purchase_requests'])}")
            print(f"Approvals         : {len(dataset['approvals'])}")
            print(f"RFQs              : {len(dataset['rfqs'])}")
            print(f"Supplier Invites  : {len(dataset['rfq_supplier_invites'])}")
            print(f"Supplier Quotes   : {len(dataset['supplier_quotes'])}")
            print(f"Quote Lines       : {len(dataset['quote_lines'])}")
            print(f"Purchase Orders   : {len(dataset['purchase_orders'])} (Competitive: {meta['competitive_pos_count']}, Non-Competitive: {meta['non_competitive_pos_count']})")
            print(f"PO Lines          : {len(dataset['purchase_order_lines'])}")
            print(f"Deliveries        : {len(dataset['deliveries'])}")
            print(f"Budget Events     : {len(dataset['budget_events'])}")
            print(f"Status Events     : {len(dataset['status_events'])}")
            print(f"Total PO Spend    : ${total_spend:,.2f} {meta['base_currency']}")

            if args.inject_anomalies:
                print(f"\nInjected Anomalies: {len(gt_records)}")
                from collections import Counter
                counts = Counter(r["issue_type"] if isinstance(r, dict) else r.issue_type for r in gt_records)
                for itype, cnt in sorted(counts.items()):
                    print(f"  - {itype}: {cnt}")

            if args.export:
                from datagen.export import export_all
                print("\n=== Persisting Dataset to Disk ===")
                exp_res = export_all(dataset)
                print(f"CSV Tables Exported: {exp_res['total_tables_exported']} -> data/csv/")
                print(f"JSON Files Exported: {len(exp_res['json_files'])} -> data/json/")
                print(f"SQLite DB Created  : {exp_res['sqlite_db']}")

            sys.exit(0)
        except Exception as err:
            print(f"Generation error: {err}", file=sys.stderr)
            sys.exit(1)

    # Default help summary
    print("Procure-to-Pay Synthetic Data Generator - Phase 2")
    print("Use --generate [--scale starter|full] to run in-memory data generation.")
    print("Use --init-db <path> to initialize SQLite database schema.")
    print("Use --validate-config to verify YAML configuration.")


if __name__ == "__main__":
    main()
