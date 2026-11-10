"""Validation package for Procure-to-Pay Synthetic Data Generator (Phase 4)."""

from validate.checks import (
    EXPECTED_TABLES,
    ValidationCheckError,
    check_foreign_key_violations,
    check_foreign_keys_enabled,
    check_required_tables_exist,
    check_schema_integrity,
    get_connection,
    run_foundational_checks,
    validate_approvals_and_business_rules,
    validate_budget_ledger,
    validate_dataset,
    validate_date_ordering,
    validate_financial_reconciliation,
    validate_foreign_keys,
    validate_id_format,
    validate_lifecycle_state_machine,
    validate_primary_keys_and_ids,
)
from validate.models import ValidationCheckResult, ValidationReport

__version__ = "2.0.0"
__all__ = [
    "EXPECTED_TABLES",
    "ValidationCheckError",
    "ValidationCheckResult",
    "ValidationReport",
    "check_foreign_key_violations",
    "check_foreign_keys_enabled",
    "check_required_tables_exist",
    "check_schema_integrity",
    "get_connection",
    "run_foundational_checks",
    "validate_approvals_and_business_rules",
    "validate_budget_ledger",
    "validate_dataset",
    "validate_date_ordering",
    "validate_financial_reconciliation",
    "validate_foreign_keys",
    "validate_id_format",
    "validate_lifecycle_state_machine",
    "validate_primary_keys_and_ids",
]
