"""Tests for configuration management module."""

import copy
from pathlib import Path
import pytest
import yaml

from datagen.config import ConfigValidationError, load_config, validate_config


@pytest.fixture
def base_valid_config():
    """Load default valid configuration dictionary from config/default.yaml."""
    config_path = Path(__file__).resolve().parent.parent / "config" / "default.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_load_default_config_success():
    """Verify that default.yaml loads and passes all validation rules."""
    cfg = load_config()
    assert cfg["project"]["name"] == "procure-to-pay-datagen"
    assert cfg["project"]["fiscal_year"] == 2026
    assert cfg["project"]["base_currency"] == "USD"
    assert "starter" in cfg["scale"]
    assert "full" in cfg["scale"]
    assert cfg["scale"]["starter"]["requesters"] == 30
    assert cfg["scale"]["full"]["requesters"] == 300


def test_missing_required_section_fails(base_valid_config):
    """Verify that missing a top-level required section raises ConfigValidationError."""
    invalid = copy.deepcopy(base_valid_config)
    del invalid["approval_thresholds"]

    with pytest.raises(ConfigValidationError, match="Missing required configuration section: 'approval_thresholds'"):
        validate_config(invalid)


def test_invalid_approval_thresholds_fail(base_valid_config):
    """Verify that inverted or non-positive approval thresholds raise error."""
    # Test department head limit less than manager limit
    invalid = copy.deepcopy(base_valid_config)
    invalid["approval_thresholds"]["manager_limit"] = 50000
    invalid["approval_thresholds"]["department_head_limit"] = 25000

    with pytest.raises(ConfigValidationError, match="strictly greater than manager_limit"):
        validate_config(invalid)

    # Test negative limit
    invalid2 = copy.deepcopy(base_valid_config)
    invalid2["approval_thresholds"]["manager_limit"] = -100
    with pytest.raises(ConfigValidationError, match="must be a positive number"):
        validate_config(invalid2)


def test_invalid_supplier_scoring_weights_fail(base_valid_config):
    """Verify that supplier scoring weights not summing to 1.0 fail validation."""
    invalid = copy.deepcopy(base_valid_config)
    invalid["supplier_scoring"]["landed_cost_weight"] = 0.50
    invalid["supplier_scoring"]["lead_time_weight"] = 0.20
    invalid["supplier_scoring"]["risk_weight"] = 0.10  # Sum is 0.80 != 1.0

    with pytest.raises(ConfigValidationError, match="weights must sum to 1.0"):
        validate_config(invalid)


def test_invalid_fx_rates_fail(base_valid_config):
    """Verify that invalid FX rates (negative, missing base currency, or non-1.0 base rate) fail."""
    # Negative rate
    invalid = copy.deepcopy(base_valid_config)
    invalid["fx_rates"]["EUR"] = -1.08
    with pytest.raises(ConfigValidationError, match="FX rate for 'EUR' must be a positive number"):
        validate_config(invalid)

    # Missing base currency rate
    invalid2 = copy.deepcopy(base_valid_config)
    del invalid2["fx_rates"]["USD"]
    with pytest.raises(ConfigValidationError, match="Base currency 'USD' must have an entry"):
        validate_config(invalid2)

    # Base currency rate != 1.0
    invalid3 = copy.deepcopy(base_valid_config)
    invalid3["fx_rates"]["USD"] = 1.25
    with pytest.raises(ConfigValidationError, match="rate in 'fx_rates' must equal 1.0"):
        validate_config(invalid3)


def test_invalid_scale_values_fail(base_valid_config):
    """Verify that negative or non-integer scale counts fail validation."""
    invalid = copy.deepcopy(base_valid_config)
    invalid["scale"]["starter"]["requesters"] = 0

    with pytest.raises(ConfigValidationError, match="must be a positive integer"):
        validate_config(invalid)

    # Missing scale key
    invalid2 = copy.deepcopy(base_valid_config)
    del invalid2["scale"]["starter"]["rfqs"]
    with pytest.raises(ConfigValidationError, match="Missing 'rfqs' in scale tier"):
        validate_config(invalid2)


def test_missing_config_file_raises_not_found():
    """Verify that a non-existent config path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_config.yaml")


def test_invalid_category_distributions_fail(base_valid_config):
    """Verify that malformed category distribution parameters raise ConfigValidationError."""
    invalid = copy.deepcopy(base_valid_config)
    invalid["category_distributions"]["IT Hardware"]["max_price"] = 50  # less than min_price (100)

    with pytest.raises(ConfigValidationError, match="cannot be less than min_price"):
        validate_config(invalid)

    invalid2 = copy.deepcopy(base_valid_config)
    invalid2["category_distributions"]["Software"]["log_sigma"] = -0.5
    with pytest.raises(ConfigValidationError, match="log_sigma .* must be positive"):
        validate_config(invalid2)


def test_invalid_seasonality_weights_fail(base_valid_config):
    """Verify that non-positive or missing seasonality monthly weights fail validation."""
    invalid = copy.deepcopy(base_valid_config)
    invalid["seasonality"]["monthly_weights"][12] = -0.1

    with pytest.raises(ConfigValidationError, match="must be a positive number"):
        validate_config(invalid)


