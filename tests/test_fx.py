"""Tests for fixed Foreign Exchange (FX) engine."""

from decimal import Decimal
import pytest

from datagen.config import load_config
from datagen.fx import (
    convert_currency,
    convert_to_base_currency,
    from_minor_units,
    get_exchange_rate,
    NegativeAmountError,
    to_minor_units,
    UnsupportedCurrencyError,
)


@pytest.fixture(scope="module")
def config():
    """Load default configuration for FX conversion tests."""
    return load_config()


def test_usd_to_usd_conversion(config):
    """Verify that identity conversion (USD to USD) is exact."""
    amount = Decimal("150.75")
    converted = convert_currency(amount, "USD", "USD", config)
    assert converted == Decimal("150.75")
    assert converted is not amount  # Returns Decimal


def test_eur_to_usd_conversion(config):
    """Verify EUR to USD conversion using configured rate (1 EUR = 1.08 USD)."""
    # 100 EUR = 108.00 USD
    converted = convert_to_base_currency(Decimal("100.00"), "EUR", config)
    assert converted == Decimal("108.00")


def test_gbp_to_usd_conversion(config):
    """Verify GBP to USD conversion using configured rate (1 GBP = 1.27 USD)."""
    # 50.00 GBP * 1.27 = 63.50 USD
    converted = convert_to_base_currency(Decimal("50.00"), "GBP", config)
    assert converted == Decimal("63.50")


def test_inr_to_usd_conversion(config):
    """Verify INR to USD conversion using configured rate (1 INR = 0.012 USD)."""
    # 10,000 INR * 0.012 = 120.00 USD
    converted = convert_to_base_currency(Decimal("10000.00"), "INR", config)
    assert converted == Decimal("120.00")


def test_jpy_to_usd_conversion(config):
    """Verify JPY to USD conversion using configured rate (1 JPY = 0.0067 USD)."""
    # 10,000 JPY * 0.0067 = 67.00 USD
    converted = convert_to_base_currency(Decimal("10000"), "JPY", config)
    assert converted == Decimal("67.00")


def test_usd_to_inr_conversion(config):
    """Verify USD to INR conversion (100 USD / 0.012 = 8333.33 INR)."""
    converted = convert_currency(Decimal("100.00"), "USD", "INR", config)
    assert converted == Decimal("8333.33")


def test_unsupported_currency_raises_error(config):
    """Verify that unconfigured currencies raise UnsupportedCurrencyError."""
    with pytest.raises(UnsupportedCurrencyError, match="Unsupported source currency: 'AUD'"):
        convert_currency(Decimal("100.00"), "AUD", "USD", config)

    with pytest.raises(UnsupportedCurrencyError, match="Unsupported target currency: 'CAD'"):
        convert_currency(Decimal("100.00"), "USD", "CAD", config)


def test_zero_amount_handling(config):
    """Verify that zero amount converts to exactly 0.00 in target currency."""
    converted = convert_currency(0, "EUR", "USD", config)
    assert converted == Decimal("0.00")

    converted_str = convert_currency("0.00", "USD", "INR", config)
    assert converted_str == Decimal("0.00")


def test_negative_amount_raises_error(config):
    """Verify that negative amounts raise NegativeAmountError."""
    with pytest.raises(NegativeAmountError, match="cannot be negative"):
        convert_currency(Decimal("-50.00"), "USD", "EUR", config)

    with pytest.raises(NegativeAmountError, match="cannot be negative"):
        convert_to_base_currency(-10, "EUR", config)


def test_decimal_precision_and_rounding(config):
    """Verify that 2-decimal rounding with ROUND_HALF_UP behaves predictably."""
    # 12.345 USD -> to_minor_units or convert
    assert to_minor_units(Decimal("12.345")) == 1235
    assert to_minor_units(Decimal("12.344")) == 1234
    assert from_minor_units(1235) == Decimal("12.35")
    assert from_minor_units(1234) == Decimal("12.34")


def test_fx_conversion_determinism(config):
    """Verify that identical inputs produce identical outputs across repeat runs."""
    results = [convert_currency(Decimal("1234.56"), "EUR", "USD", config) for _ in range(50)]
    assert all(r == results[0] for r in results)
    assert results[0] == Decimal("1333.32")
