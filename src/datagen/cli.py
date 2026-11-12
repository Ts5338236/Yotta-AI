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
        help="Persist generated dataset to CSV, JSON, SQLite database, DDL schema, and seed script",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Root directory for exported artifacts (default: data)",
    )
    parser.add_argument(
        "--validate-exports",
        action="store_true",
        help="Run export integrity and cross-format consistency validation on exported deliverables",
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
                dataset["ground_truth"] = [r if isinstance(r, dict) else r.to_dict() for r in gt_records]

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
            print(f"Exception Logs    : {len(dataset.get('exception_logs', []))}")
            print(f"Total PO Spend    : ${total_spend:,.2f} {meta['base_currency']}")

            if args.inject_anomalies:
                print(f"\nInjected Anomalies: {len(gt_records)}")
                from collections import Counter
                counts = Counter(r["issue_type"] if isinstance(r, dict) else r.issue_type for r in gt_records)
                for itype, cnt in sorted(counts.items()):
                    print(f"  - {itype}: {cnt}")

            if args.export:
                from datagen.export import export_all
                from validate.checks import validate_dataset
                from validate.anomaly_checks import detect_all_anomalies, evaluate_detections
                from validate.export_checks import validate_all_exports
                import json

                out_root = Path(args.output_dir).resolve()
                print(f"\n=== Persisting Dataset to Disk ({out_root}) ===")
                exp_res = export_all(dataset, base_dir=out_root, ground_truth=gt_records)
                print(f"CSV Tables Exported: {exp_res['total_tables_exported']} -> {out_root}/csv/")
                print(f"JSON Files Exported: {len(exp_res['json_files'])} -> {out_root}/json/")
                print(f"SQLite DB Created  : {exp_res['sqlite_db']}")
                print(f"DDL Schema Exported: {exp_res['schema_ddl']}")
                print(f"SQL Seed Generated : {exp_res['seed_sql']}")
                if exp_res["ground_truth_files"]:
                    print(f"Ground Truth Files : {exp_res['ground_truth_files']}")
                print(f"Source Manifest    : {exp_res['manifest']}")

                rep_dir = Path("docs").resolve()
                rep_dir.mkdir(parents=True, exist_ok=True)

                # Generate validation report
                val_report = validate_dataset(dataset)
                with open(rep_dir / "validation_summary.json", "w", encoding="utf-8") as f:
                    json.dump(val_report.to_dict(), f, indent=2)
                with open(rep_dir / "validation_summary.md", "w", encoding="utf-8") as f:
                    f.write(val_report.to_markdown())
                print(f"Validation Report  : {rep_dir}/validation_summary.md (Status: {val_report.status})")

                # Generate anomaly evaluation report if ground truth present
                if gt_records:
                    findings = detect_all_anomalies(dataset)
                    eval_metrics = evaluate_detections(findings, gt_records)
                    with open(rep_dir / "anomaly_evaluation_report.json", "w", encoding="utf-8") as f:
                        json.dump(eval_metrics, f, indent=2)

                    md_anom = [
                        "# Anomaly Detection Evaluation Report",
                        "",
                        f"- **Total Ground Truth**: `{eval_metrics['total_ground_truth']}`",
                        f"- **Total Detected**: `{eval_metrics['total_detected']}`",
                        f"- **True Positives**: `{eval_metrics['true_positives']}`",
                        f"- **False Positives**: `{eval_metrics['false_positives']}`",
                        f"- **False Negatives**: `{eval_metrics['false_negatives']}`",
                        f"- **Overall Precision**: `{eval_metrics['precision']:.4f}`",
                        f"- **Overall Recall**: `{eval_metrics['recall']:.4f}`",
                        f"- **Overall F1 Score**: `{eval_metrics['f1_score']:.4f}`",
                        "",
                        "## Metrics by Anomaly Category",
                        "",
                        "| Category | Ground Truth | Detected | TP | FP | FN | Precision | Recall | F1 Score |",
                        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
                    ]
                    for cat, c_met in eval_metrics.get("by_category", {}).items():
                        md_anom.append(
                            f"| `{cat}` | {c_met['ground_truth_count']} | {c_met['detected_count']} | "
                            f"{c_met['true_positives']} | {c_met['false_positives']} | {c_met['false_negatives']} | "
                            f"{c_met['precision']:.4f} | {c_met['recall']:.4f} | {c_met['f1_score']:.4f} |"
                        )
                    with open(rep_dir / "anomaly_evaluation_report.md", "w", encoding="utf-8") as f:
                        f.write("\n".join(md_anom) + "\n")
                    print(f"Anomaly Evaluation : {rep_dir}/anomaly_evaluation_report.md (F1: {eval_metrics['f1_score']:.4f})")

                if args.validate_exports:
                    export_audit = validate_all_exports(dataset, base_dir=out_root)
                    print(f"Export Audit Status: {export_audit['status']}")
                    with open(rep_dir / "export_integrity_report.json", "w", encoding="utf-8") as f:
                        json.dump(export_audit, f, indent=2)

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
