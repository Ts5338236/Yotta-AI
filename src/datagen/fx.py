"""Fixed Foreign Exchange (FX) Engine for Procure-to-Pay Synthetic Data Generator.

Provides deterministic, offline, high-precision currency conversions using Python Decimal.
All exchange rates are sourced strictly from centralized configuration.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping, Union


# Standard two-decimal currency precision
CENTS = Decimal("0.01")


class FXError(Exception):
    """Base exception for foreign exchange errors."""
    pass


class UnsupportedCurrencyError(FXError):
    """Raised when an operation requests an unsupported or unconfigured currency."""
    pass


class NegativeAmountError(FXError, ValueError):
    """Raised when a monetary conversion receives a negative amount."""
    pass


def _extract_fx_rates(config: Mapping[str, Any]) -> Mapping[str, Decimal]:
    """Extract and validate FX rates from configuration mapping as Decimals."""
    if "fx_rates" not in config:
        raise FXError("Configuration dictionary does not contain 'fx_rates'.")

    raw_rates = config["fx_rates"]
    if not isinstance(raw_rates, dict):
        raise FXError("'fx_rates' must be a dictionary of currency code to rate.")

    rates: dict[str, Decimal] = {}
    for code, rate in raw_rates.items():
        curr = str(code).strip().upper()
        try:
            dec_rate = Decimal(str(rate))
            if dec_rate <= 0:
                raise ValueError
            rates[curr] = dec_rate
        except Exception as err:
            raise FXError(f"Invalid FX rate for currency '{curr}': {rate}") from err

    return rates


def _to_decimal(value: Union[Decimal, float, int, str]) -> Decimal:
    """Safely convert numerical amount to Decimal."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        return Decimal(str(value))
    if isinstance(value, float):
        # Convert via repr to preserve literal decimal representation without float inaccuracies
        return Decimal(str(value))
    raise TypeError(f"Amount must be a Decimal, int, float, or str, got: {type(value)}")


def get_exchange_rate(
    source_currency: str,
    target_currency: str,
    config: Mapping[str, Any],
) -> Decimal:
    """Calculate the deterministic exchange rate from source to target currency.

    Exchange rates in configuration are defined as base currency units per one unit
    of the given currency (e.g. USD per EUR).
    Rate(SRC -> TGT) = Rate(SRC) / Rate(TGT).

    Args:
        source_currency: Three-letter ISO currency code of source.
        target_currency: Three-letter ISO currency code of target.
        config: Configuration dictionary containing 'fx_rates'.

    Returns:
        Decimal: Exchange rate factor.

    Raises:
        UnsupportedCurrencyError: If source or target currency is not configured.
    """
    rates = _extract_fx_rates(config)
    src = source_currency.strip().upper()
    tgt = target_currency.strip().upper()

    if src not in rates:
        raise UnsupportedCurrencyError(f"Unsupported source currency: '{source_currency}'")
    if tgt not in rates:
        raise UnsupportedCurrencyError(f"Unsupported target currency: '{target_currency}'")

    if src == tgt:
        return Decimal("1.0")

    src_rate = rates[src]
    tgt_rate = rates[tgt]

    return src_rate / tgt_rate


def convert_currency(
    amount: Union[Decimal, float, int, str],
    source_currency: str,
    target_currency: str,
    config: Mapping[str, Any],
    rounding: str = ROUND_HALF_UP,
) -> Decimal:
    """Convert an amount from source currency to target currency.

    Args:
        amount: Monetary amount to convert. Must be non-negative.
        source_currency: Three-letter currency code.
        target_currency: Three-letter currency code.
        config: Configuration dictionary containing 'fx_rates'.
        rounding: Rounding mode (default: ROUND_HALF_UP).

    Returns:
        Decimal: Converted amount rounded to two decimal places.

    Raises:
        NegativeAmountError: If amount is negative.
        UnsupportedCurrencyError: If source or target currency is unsupported.
    """
    dec_amount = _to_decimal(amount)
    if dec_amount < 0:
        raise NegativeAmountError(f"Monetary conversion amount cannot be negative: {amount}")

    if dec_amount == 0:
        return Decimal("0.00")

    src = source_currency.strip().upper()
    tgt = target_currency.strip().upper()

    if src == tgt:
        return dec_amount.quantize(CENTS, rounding=rounding)

    rate = get_exchange_rate(src, tgt, config)
    converted = dec_amount * rate
    return converted.quantize(CENTS, rounding=rounding)


def convert_to_base_currency(
    amount: Union[Decimal, float, int, str],
    source_currency: str,
    config: Mapping[str, Any],
) -> Decimal:
    """Convert a monetary amount from a source currency to the base currency (USD).

    Args:
        amount: Monetary amount to convert.
        source_currency: Three-letter currency code.
        config: Configuration dictionary containing 'project.base_currency' and 'fx_rates'.

    Returns:
        Decimal: Converted amount in base currency rounded to 2 decimal places.
    """
    base_currency = config.get("project", {}).get("base_currency", "USD")
    return convert_currency(amount, source_currency, base_currency, config)


def to_minor_units(amount: Union[Decimal, float, int, str]) -> int:
    """Convert a 2-decimal currency amount into integer minor units (e.g. cents).

    Example: Decimal("12.50") -> 1250 cents.
    """
    dec = _to_decimal(amount).quantize(CENTS, rounding=ROUND_HALF_UP)
    return int(dec * 100)


def from_minor_units(minor_units: int) -> Decimal:
    """Convert integer minor units back to Decimal with 2 decimal places.

    Example: 1250 -> Decimal("12.50").
    """
    return (Decimal(minor_units) / Decimal("100")).quantize(CENTS)
