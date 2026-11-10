"""Configuration management module for Procure-to-Pay Synthetic Data Generator.

Loads, validates, and provides access to centralized project settings from YAML.
Adheres to strict validation: never silently replaces invalid values with defaults.
"""

from __future__ import annotations

import datetime
import math
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


REQUIRED_SECTIONS = (
    "project",
    "generation",
    "scale",
    "approval_thresholds",
    "supplier_scoring",
    "anomalies",
    "procurement",
    "fx_rates",
)

REQUIRED_SCALE_KEYS = (
    "requesters",
    "suppliers",
    "departments",
    "purchase_requests",
    "rfqs",
    "quotes",
    "purchase_orders",
)


def _validate_project_section(project: Any) -> None:
    if not isinstance(project, dict):
        raise ConfigValidationError("'project' section must be a dictionary.")

    for field in ("name", "version", "base_currency", "fiscal_year", "base_date"):
        if field not in project:
            raise ConfigValidationError(f"Missing required field '{field}' in 'project' section.")

    if not isinstance(project["name"], str) or not project["name"].strip():
        raise ConfigValidationError("project.name must be a non-empty string.")

    if not isinstance(project["version"], str) or not project["version"].strip():
        raise ConfigValidationError("project.version must be a non-empty string.")

    if not isinstance(project["base_currency"], str) or len(project["base_currency"].strip()) != 3:
        raise ConfigValidationError("project.base_currency must be a 3-letter currency code (e.g. 'USD').")

    if not isinstance(project["fiscal_year"], int) or project["fiscal_year"] < 2000:
        raise ConfigValidationError("project.fiscal_year must be an integer >= 2000.")

    base_date = project["base_date"]
    if isinstance(base_date, datetime.date):
        # YAML parser may parse YYYY-MM-DD directly as date
        pass
    elif isinstance(base_date, str):
        try:
            datetime.date.fromisoformat(base_date)
        except ValueError as err:
            raise ConfigValidationError(f"project.base_date must be valid ISO date (YYYY-MM-DD): {err}") from err
    else:
        raise ConfigValidationError("project.base_date must be a date or ISO string (YYYY-MM-DD).")


def _validate_generation_section(generation: Any, scales: Any) -> None:
    if not isinstance(generation, dict):
        raise ConfigValidationError("'generation' section must be a dictionary.")

    if "default_seed" not in generation or not isinstance(generation["default_seed"], int):
        raise ConfigValidationError("generation.default_seed must be an integer.")

    default_scale = generation.get("default_scale")
    if not isinstance(default_scale, str) or not default_scale.strip():
        raise ConfigValidationError("generation.default_scale must be a non-empty string.")

    if isinstance(scales, dict) and default_scale not in scales:
        raise ConfigValidationError(
            f"generation.default_scale '{default_scale}' is not defined in 'scale' configurations."
        )


def _validate_scale_section(scale: Any) -> None:
    if not isinstance(scale, dict) or not scale:
        raise ConfigValidationError("'scale' section must be a non-empty dictionary.")

    for scale_name, scale_config in scale.items():
        if not isinstance(scale_config, dict):
            raise ConfigValidationError(f"Scale tier '{scale_name}' must be a dictionary.")

        for key in REQUIRED_SCALE_KEYS:
            if key not in scale_config:
                raise ConfigValidationError(f"Missing '{key}' in scale tier '{scale_name}'.")
            val = scale_config[key]
            if not isinstance(val, int) or val <= 0:
                raise ConfigValidationError(
                    f"Scale tier '{scale_name}.{key}' must be a positive integer, got: {val}"
                )


def _validate_approval_thresholds(thresholds: Any) -> None:
    if not isinstance(thresholds, dict):
        raise ConfigValidationError("'approval_thresholds' must be a dictionary.")

    for field in ("manager_limit", "department_head_limit"):
        if field not in thresholds:
            raise ConfigValidationError(f"Missing required threshold '{field}'.")
        val = thresholds[field]
        if not isinstance(val, (int, float)) or val <= 0:
            raise ConfigValidationError(f"approval_thresholds.{field} must be a positive number, got: {val}")

    if thresholds["department_head_limit"] <= thresholds["manager_limit"]:
        raise ConfigValidationError(
            "approval_thresholds.department_head_limit must be strictly greater than manager_limit."
        )


def _validate_supplier_scoring(scoring: Any) -> None:
    if not isinstance(scoring, dict):
        raise ConfigValidationError("'supplier_scoring' must be a dictionary.")

    weights = ("landed_cost_weight", "lead_time_weight", "risk_weight")
    total_weight = 0.0
    for w in weights:
        if w not in scoring:
            raise ConfigValidationError(f"Missing required scoring weight '{w}'.")
        val = scoring[w]
        if not isinstance(val, (int, float)) or val < 0:
            raise ConfigValidationError(f"supplier_scoring.{w} must be a non-negative number, got: {val}")
        total_weight += float(val)

    if not math.isclose(total_weight, 1.0, rel_tol=1e-5, abs_tol=1e-5):
        raise ConfigValidationError(
            f"supplier_scoring weights must sum to 1.0, got {total_weight:.4f}"
        )


def _validate_anomalies(anomalies: Any) -> None:
    if not isinstance(anomalies, dict):
        raise ConfigValidationError("'anomalies' must be a dictionary.")

    for f in ("target_rate_min", "target_rate_max"):
        if f not in anomalies:
            raise ConfigValidationError(f"Missing required anomaly rate field '{f}'.")
        val = anomalies[f]
        if not isinstance(val, (int, float)) or not (0.0 <= val <= 1.0):
            raise ConfigValidationError(f"anomalies.{f} must be a float between 0.0 and 1.0, got: {val}")

    if anomalies["target_rate_max"] < anomalies["target_rate_min"]:
        raise ConfigValidationError(
            "anomalies.target_rate_max cannot be less than anomalies.target_rate_min."
        )


def _validate_procurement(procurement: Any) -> None:
    if not isinstance(procurement, dict):
        raise ConfigValidationError("'procurement' must be a dictionary.")

    for field in ("minimum_quotes", "maximum_quotes", "default_invites"):
        if field not in procurement:
            raise ConfigValidationError(f"Missing required procurement field '{field}'.")
        val = procurement[field]
        if not isinstance(val, int) or val <= 0:
            raise ConfigValidationError(f"procurement.{field} must be a positive integer, got: {val}")

    if procurement["maximum_quotes"] < procurement["minimum_quotes"]:
        raise ConfigValidationError(
            "procurement.maximum_quotes cannot be less than procurement.minimum_quotes."
        )


def _validate_fx_rates(fx_rates: Any, base_currency: str) -> None:
    if not isinstance(fx_rates, dict) or not fx_rates:
        raise ConfigValidationError("'fx_rates' must be a non-empty dictionary.")

    for curr, rate in fx_rates.items():
        if not isinstance(curr, str) or len(curr.strip()) != 3:
            raise ConfigValidationError(f"Currency code '{curr}' in fx_rates must be a 3-letter string.")
        if not isinstance(rate, (int, float)) or rate <= 0:
            raise ConfigValidationError(f"FX rate for '{curr}' must be a positive number, got: {rate}")

    if base_currency not in fx_rates:
        raise ConfigValidationError(
            f"Base currency '{base_currency}' must have an entry in 'fx_rates'."
        )

    if not math.isclose(float(fx_rates[base_currency]), 1.0, rel_tol=1e-5):
        raise ConfigValidationError(
            f"Base currency '{base_currency}' rate in 'fx_rates' must equal 1.0, got: {fx_rates[base_currency]}"
        )


def _validate_category_distributions(category_distributions: Any) -> None:
    if category_distributions is None:
        return
    if not isinstance(category_distributions, dict) or not category_distributions:
        raise ConfigValidationError("'category_distributions' must be a non-empty dictionary.")

    for category, dist in category_distributions.items():
        if not isinstance(dist, dict):
            raise ConfigValidationError(f"Distribution parameters for '{category}' must be a dictionary.")
        for field in ("log_mean", "log_sigma", "min_price", "max_price"):
            if field not in dist:
                raise ConfigValidationError(f"Missing '{field}' in category_distributions['{category}'].")
            val = dist[field]
            if not isinstance(val, (int, float)):
                raise ConfigValidationError(f"'{field}' in category '{category}' must be numeric, got: {val}")
        if dist["log_sigma"] <= 0:
            raise ConfigValidationError(f"log_sigma for category '{category}' must be positive, got {dist['log_sigma']}")
        if dist["min_price"] <= 0:
            raise ConfigValidationError(f"min_price for category '{category}' must be positive, got {dist['min_price']}")
        if dist["max_price"] < dist["min_price"]:
            raise ConfigValidationError(
                f"max_price ({dist['max_price']}) cannot be less than min_price ({dist['min_price']}) for category '{category}'."
            )


def _validate_seasonality(seasonality: Any) -> None:
    if seasonality is None:
        return
    if not isinstance(seasonality, dict):
        raise ConfigValidationError("'seasonality' section must be a dictionary.")
    if "monthly_weights" not in seasonality:
        raise ConfigValidationError("Missing 'monthly_weights' in 'seasonality' section.")
    weights = seasonality["monthly_weights"]
    if not isinstance(weights, dict):
        raise ConfigValidationError("'monthly_weights' must be a dictionary.")
    for month in range(1, 13):
        val = weights.get(month) if month in weights else weights.get(str(month))
        if val is None:
            raise ConfigValidationError(f"Missing monthly weight for month {month}.")
        if not isinstance(val, (int, float)) or val <= 0:
            raise ConfigValidationError(f"Weight for month {month} must be a positive number, got: {val}")


def validate_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a loaded configuration dictionary against project specifications.

    Args:
        config: Raw configuration dictionary parsed from YAML.

    Returns:
        Dict[str, Any]: Validated configuration dictionary.

    Raises:
        ConfigValidationError: If any required section or rule is violated.
    """
    if not isinstance(config, dict):
        raise ConfigValidationError("Configuration root must be a dictionary.")

    for section in REQUIRED_SECTIONS:
        if section not in config:
            raise ConfigValidationError(f"Missing required configuration section: '{section}'.")

    _validate_project_section(config["project"])
    _validate_scale_section(config["scale"])
    _validate_generation_section(config["generation"], config["scale"])
    _validate_approval_thresholds(config["approval_thresholds"])
    _validate_supplier_scoring(config["supplier_scoring"])
    _validate_anomalies(config["anomalies"])
    _validate_procurement(config["procurement"])
    _validate_fx_rates(config["fx_rates"], config["project"]["base_currency"])
    _validate_category_distributions(config.get("category_distributions"))
    _validate_seasonality(config.get("seasonality"))

    return dict(config)


def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """Load and validate configuration from a YAML file.

    Args:
        config_path: Path to YAML configuration file. If None, defaults to config/default.yaml.

    Returns:
        Dict[str, Any]: Validated configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        ConfigValidationError: If the YAML contents fail validation.
    """
    if config_path is None:
        # Default to config/default.yaml relative to current working directory or package root
        project_root = Path(__file__).resolve().parent.parent.parent
        resolved_path = project_root / "config" / "default.yaml"
    else:
        resolved_path = Path(config_path).resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {resolved_path}")

    with open(resolved_path, "r", encoding="utf-8") as f:
        try:
            raw_config = yaml.safe_load(f)
        except yaml.YAMLError as err:
            raise ConfigValidationError(f"Failed to parse YAML file: {err}") from err

    return validate_config(raw_config)

