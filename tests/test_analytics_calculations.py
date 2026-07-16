from __future__ import annotations

from decimal import Decimal

import pytest

from core.analytics.domain.calculations import mean, sma


def test_sma_averages_prices() -> None:
    prices = [Decimal("10"), Decimal("20"), Decimal("30")]

    assert sma(prices) == Decimal("20")


def test_sma_uses_decimal_division_exactly() -> None:
    prices = [Decimal("1"), Decimal("2")]

    assert sma(prices) == Decimal("1.5")


def test_sma_single_price_is_itself() -> None:
    assert sma([Decimal("450.123456789")]) == Decimal("450.123456789")


def test_sma_rejects_empty_list() -> None:
    with pytest.raises(ValueError):
        sma([])


def test_mean_averages_values() -> None:
    assert mean([Decimal("10"), Decimal("20"), Decimal("30")]) == Decimal("20")


def test_mean_single_value_is_itself() -> None:
    assert mean([Decimal("450.123456789")]) == Decimal("450.123456789")


def test_mean_rejects_empty_list() -> None:
    with pytest.raises(ValueError):
        mean([])
