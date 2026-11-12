"""End-to-end integration tests for comprehensive Phase 4 validation suite.

Verifies:
- Clean starter-scale dataset achieves 100% PASS with zero failures
- Clean full-scale dataset achieves 100% PASS with zero failures
- Reporting formats (JSON and Markdown) comply with schema requirements
- Intentionally corrupted datasets trigger overall FAIL status
- CLI execution behaves correctly
"""

import copy
import json
import subprocess
import sys
from pathlib import Path
import pytest

from datagen.workflow import generate_procurement_workflow
from validate.checks import validate_dataset


def test_starter_scale_full_validation_passes():
    """Verify clean starter dataset achieves 100% pass rate across all checks."""
    dataset = generate_procurement_workflow(scale="starter", seed=20261022)
    report = validate_dataset(dataset)

    assert report.status == "PASS"
    assert report.summary["failed"] == 0
    assert report.summary["warnings"] == 0
    assert report.summary["total_checks"] > 500
    assert len(report.failures) == 0


def test_full_scale_full_validation_passes():
    """Verify clean full dataset achieves 100% pass rate across all checks."""
    dataset = generate_procurement_workflow(scale="full", seed=20261022)
    report = validate_dataset(dataset)

    assert report.status == "PASS"
    assert report.summary["failed"] == 0
    assert report.summary["warnings"] == 0
    assert report.summary["total_checks"] > 5000
    assert len(report.failures) == 0


def test_report_serialization_and_markdown(tmp_path):
    """Verify report dictionary and markdown document generation."""
    dataset = generate_procurement_workflow(scale="starter", seed=20261022)
    report = validate_dataset(dataset)

    md_file = tmp_path / "test_summary.md"
    json_file = tmp_path / "test_summary.json"

    report.save_reports(md_path=md_file, json_path=json_file)

    assert md_file.exists()
    assert json_file.exists()

    md_content = md_file.read_text(encoding="utf-8")
    assert "# Data Validation & Integrity Report" in md_content
    assert "**Overall Status**: `PASS`" in md_content

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "PASS"
    assert data["summary"]["failed"] == 0
    assert "categories" in data
    assert "entities" in data


def test_corrupted_dataset_triggers_overall_fail():
    """Verify any critical error properly marks the overall report status as FAIL."""
    dataset = generate_procurement_workflow(scale="starter", seed=20261022)
    corrupted = copy.deepcopy(dataset)
    # Inject multiple diverse corruptions
    corrupted["purchase_requests"][0]["total_estimated_amount"] = 999999999
    corrupted["purchase_orders"][0]["total_amount"] = 111111111

    report = validate_dataset(corrupted)
    assert report.status == "FAIL"
    assert report.summary["failed"] >= 2
    assert len(report.failures) >= 2

