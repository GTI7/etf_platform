from __future__ import annotations

from decimal import Decimal

import pytest

from core.shared.money import CurrencyMismatchError, Money


def test_addition_is_precise_with_decimals() -> None:
    a = Money(Decimal("10.10"), "USD")
    b = Money(Decimal("0.20"), "USD")
    assert a + b == Money(Decimal("10.30"), "USD")


def test_subtraction_is_precise_with_decimals() -> None:
    a = Money(Decimal("5.00"), "USD")
    b = Money(Decimal("1.25"), "USD")
    assert a - b == Money(Decimal("3.75"), "USD")


def test_rejects_non_decimal_amount() -> None:
    with pytest.raises(TypeError):
        Money(1.1, "USD")  # type: ignore[arg-type]


def test_rejects_invalid_currency_code() -> None:
    with pytest.raises(ValueError):
        Money(Decimal("1"), "usd")


def test_currency_mismatch_rejected_on_add() -> None:
    usd = Money(Decimal("10"), "USD")
    eur = Money(Decimal("10"), "EUR")
    with pytest.raises(CurrencyMismatchError):
        usd + eur


def test_currency_mismatch_rejected_on_subtract() -> None:
    usd = Money(Decimal("10"), "USD")
    eur = Money(Decimal("10"), "EUR")
    with pytest.raises(CurrencyMismatchError):
        usd - eur


def test_currency_mismatch_rejected_on_comparison() -> None:
    usd = Money(Decimal("10"), "USD")
    eur = Money(Decimal("10"), "EUR")
    with pytest.raises(CurrencyMismatchError):
        usd < eur


def test_comparison_within_same_currency() -> None:
    assert Money(Decimal("1"), "USD") < Money(Decimal("2"), "USD")
    assert Money(Decimal("2"), "USD") >= Money(Decimal("2"), "USD")
    assert Money(Decimal("2"), "USD") == Money(Decimal("2"), "USD")
