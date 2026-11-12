"""Validation data models and report representations (Phase 4).

Defines structured check results, severity levels, and comprehensive
machine-readable validation reporting classes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ValidationCheckResult:
    """Represents the outcome of a single validation check rule."""

    check_name: str
    category: str
    passed: bool
    severity: str = "ERROR"  # CRITICAL, ERROR, WARNING, INFO
    entity: Optional[str] = None
    record_id: Optional[str] = None
    field: Optional[str] = None
    actual_value: Any = None
    expected_value: Any = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert check result to serializable dictionary."""
        return {
            "check_name": self.check_name,
            "category": self.category,
            "passed": self.passed,
            "severity": self.severity,
            "entity": self.entity,
            "record_id": self.record_id,
            "field": self.field,
            "actual_value": str(self.actual_value) if self.actual_value is not None else None,
            "expected_value": str(self.expected_value) if self.expected_value is not None else None,
            "description": self.description,
        }


@dataclass
class ValidationReport:
    """Comprehensive aggregation of all executed validation checks."""

    status: str = "PASS"  # PASS or FAIL
    mode: str = "clean"   # clean or anomaly_aware
    summary: Dict[str, int] = field(default_factory=lambda: {
        "total_checks": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
    })
    categories: Dict[str, Dict[str, int]] = field(default_factory=dict)
    entities: Dict[str, int] = field(default_factory=dict)
    checks: List[ValidationCheckResult] = field(default_factory=list)
    failures: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    anomaly_findings: List[Dict[str, Any]] = field(default_factory=list)
    evaluation: Optional[Dict[str, Any]] = None

    def add_result(self, result: ValidationCheckResult) -> None:
        """Register a validation check result and update summary tallies."""
        self.checks.append(result)
        self.summary["total_checks"] += 1

        # Track category stats
        cat = result.category
        if cat not in self.categories:
            self.categories[cat] = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}
        self.categories[cat]["total"] += 1

        if result.passed:
            self.summary["passed"] += 1
            self.categories[cat]["passed"] += 1
        else:
            if result.severity in ("CRITICAL", "ERROR"):
                self.summary["failed"] += 1
                self.categories[cat]["failed"] += 1
                self.failures.append(result.to_dict())
                self.status = "FAIL"
            elif result.severity == "WARNING":
                self.summary["warnings"] += 1
                self.categories[cat]["warnings"] += 1
                self.warnings.append(result.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to serializable dictionary matching PRD specification."""
        out = {
            "status": self.status,
            "mode": self.mode,
            "summary": self.summary,
            "categories": self.categories,
            "entities": self.entities,
            "checks_count": len(self.checks),
            "failures": self.failures,
            "warnings": self.warnings,
        }
        if self.anomaly_findings:
            out["anomaly_findings"] = self.anomaly_findings
        if self.evaluation:
            out["evaluation"] = self.evaluation
        return out

    def to_markdown(self) -> str:
        """Generate GitHub-flavored Markdown validation summary document."""
        lines = [
            "# Data Validation & Integrity Report",
            "",
            f"**Validation Mode**: `{self.mode}`  ",
            f"**Overall Status**: `{self.status}`  ",
            f"**Total Checks Executed**: {self.summary['total_checks']:,}  ",
            f"**Passed Checks**: {self.summary['passed']:,}  ",
            f"**Failed Checks**: {self.summary['failed']:,}  ",
            f"**Warnings**: {self.summary['warnings']:,}  ",
            "",
            "---",
            "",
            "## 1. Summary by Validation Category",
            "",
            "| Category | Total Checks | Passed | Failed | Warnings | Status |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        for cat, stats in sorted(self.categories.items()):
            cat_status = "PASSED" if stats["failed"] == 0 else "FAILED"
            lines.append(
                f"| `{cat}` | {stats['total']:,} | {stats['passed']:,} | {stats['failed']:,} | {stats['warnings']:,} | **{cat_status}** |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 2. Validated Entity Inventory",
            "",
            "| Entity Table | Record Count |",
            "| :--- | :---: |",
        ])

        for ent, count in sorted(self.entities.items()):
            lines.append(f"| `{ent}` | {count:,} |")

        lines.extend([
            "",
            "---",
            "",
            "## 3. Discrepancies and Failures",
            "",
        ])

        if not self.failures and not self.warnings:
            lines.append(
                "> **Zero Discrepancies Detected**: The dataset complies 100% with all relational, "
                "financial, lifecycle, and date chronology business rules."
            )
        else:
            if self.failures:
                lines.extend([
                    "### Critical & Error Failures",
                    "",
                    "| Check Name | Entity | Record ID | Field | Expected | Actual | Description |",
                    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
                ])
                for f in self.failures[:50]:  # Cap at 50 for readability
                    lines.append(
                        f"| `{f['check_name']}` | `{f['entity']}` | `{f['record_id']}` | "
                        f"`{f['field']}` | `{f['expected_value']}` | `{f['actual_value']}` | {f['description']} |"
                    )
                if len(self.failures) > 50:
                    lines.append(f"*(and {len(self.failures) - 50} more failures truncated)*")

            if self.warnings:
                lines.extend([
                    "",
                    "### Warnings",
                    "",
                    "| Check Name | Entity | Record ID | Description |",
                    "| :--- | :--- | :--- | :--- |",
                ])
                for w in self.warnings[:50]:
                    lines.append(
                        f"| `{w['check_name']}` | `{w['entity']}` | `{w['record_id']}` | {w['description']} |"
                    )

        if self.evaluation:
            ev = self.evaluation
            lines.extend([
                "",
                "---",
                "",
                "## 4. Anomaly Detection & Ground Truth Evaluation",
                "",
                f"**Total Ground Truth Anomalies**: {ev.get('total_ground_truth', 0)}  ",
                f"**Total Inferred Detections**: {ev.get('total_detected', 0)}  ",
                f"**True Positives**: {ev.get('true_positives', 0)}  ",
                f"**False Positives**: {ev.get('false_positives', 0)}  ",
                f"**False Negatives**: {ev.get('false_negatives', 0)}  ",
                f"**Overall Precision**: {ev.get('precision', 0.0) * 100:.2f}%  ",
                f"**Overall Recall**: {ev.get('recall', 0.0) * 100:.2f}%  ",
                f"**Overall F1-Score**: {ev.get('f1_score', 0.0):.4f}  ",
                "",
                "### Performance by Anomaly Category",
                "",
                "| Category | Ground Truth | Detected | TP | FP | FN | Precision | Recall | F1 |",
                "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
            ])
            for cat, cstats in sorted(ev.get("by_category", {}).items()):
                gt_cnt = cstats.get("ground_truth", cstats.get("ground_truth_count", 0))
                det_cnt = cstats.get("detected", cstats.get("detected_count", 0))
                lines.append(
                    f"| `{cat}` | {gt_cnt} | {det_cnt} | {cstats['true_positives']} | "
                    f"{cstats['false_positives']} | {cstats['false_negatives']} | {cstats['precision']*100:.1f}% | "
                    f"{cstats['recall']*100:.1f}% | {cstats['f1_score']:.4f} |"
                )

        lines.append("")
        return "\n".join(lines)

    def save_reports(
        self,
        md_path: str | Path = "docs/validation_summary.md",
        json_path: str | Path = "docs/validation_summary.json",
    ) -> None:
        """Write validation report to markdown and JSON files."""
        md_p = Path(md_path).resolve()
        json_p = Path(json_path).resolve()

        md_p.parent.mkdir(parents=True, exist_ok=True)
        json_p.parent.mkdir(parents=True, exist_ok=True)

        with open(md_p, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())

        with open(json_p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

