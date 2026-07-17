from __future__ import annotations

from decimal import Decimal

import pytest

from core.analytics.domain.calculations import max_drawdown, mean, rsi, sma


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


def test_rsi_known_textbook_example() -> None:
    # Deltas: +3, +3, +3, -3 -> avg_gain=2.25, avg_loss=0.75, RS=3,
    # RSI = 100 - 100/(1+3) = 75. Chosen so every division terminates
    # exactly in Decimal (denominators are powers of 2), not just
    # approximately.
    closes = [Decimal("100"), Decimal("103"), Decimal("106"), Decimal("109"), Decimal("106")]

    assert rsi(closes) == Decimal("75")


def test_rsi_all_gains_is_100() -> None:
    closes = [Decimal("10"), Decimal("12"), Decimal("14"), Decimal("16")]

    assert rsi(closes) == Decimal("100")


def test_rsi_all_losses_is_0() -> None:
    closes = [Decimal("16"), Decimal("14"), Decimal("12"), Decimal("10")]

    assert rsi(closes) == Decimal("0")


def test_rsi_flat_prices_is_50() -> None:
    closes = [Decimal("10"), Decimal("10"), Decimal("10"), Decimal("10")]

    assert rsi(closes) == Decimal("50")


def test_rsi_rejects_fewer_than_two_prices() -> None:
    with pytest.raises(ValueError):
        rsi([])
    with pytest.raises(ValueError):
        rsi([Decimal("10")])


def test_rsi_output_always_within_0_to_100() -> None:
    examples = [
        [Decimal("10"), Decimal("20"), Decimal("15"), Decimal("30"), Decimal("5")],
        [Decimal("50"), Decimal("50.01"), Decimal("49.99"), Decimal("50")],
        [Decimal("100"), Decimal("1")],
        [Decimal("1"), Decimal("100")],
    ]
    for closes in examples:
        value = rsi(closes)
        assert Decimal("0") <= value <= Decimal("100")


def test_max_drawdown_increasing_prices_is_zero() -> None:
    prices = [Decimal("100"), Decimal("110"), Decimal("120")]

    assert max_drawdown(prices) == Decimal("0")


def test_max_drawdown_single_decline() -> None:
    prices = [Decimal("100"), Decimal("90")]

    assert max_drawdown(prices) == Decimal("-0.10")


def test_max_drawdown_decline_and_recovery() -> None:
    prices = [Decimal("100"), Decimal("90"), Decimal("120")]

    assert max_drawdown(prices) == Decimal("-0.10")


def test_max_drawdown_partial_decline_from_peak() -> None:
    prices = [Decimal("100"), Decimal("110"), Decimal("105")]

    assert max_drawdown(prices) == (Decimal("105") - Decimal("110")) / Decimal("110")


def test_max_drawdown_multiple_peaks_uses_worst_decline() -> None:
    # peak 150 -> trough 120: -0.2; then a new peak 300 -> trough 150: -0.5,
    # a worse decline than the first -- proves the running peak is
    # re-established after a recovery, not just the window's global max.
    prices = [
        Decimal("100"),
        Decimal("150"),
        Decimal("120"),
        Decimal("300"),
        Decimal("150"),
        Decimal("400"),
    ]

    assert max_drawdown(prices) == Decimal("-0.5")


def test_max_drawdown_uses_decimal_division_exactly() -> None:
    prices = [Decimal("3"), Decimal("1")]

    assert max_drawdown(prices) == (Decimal("1") - Decimal("3")) / Decimal("3")


def test_max_drawdown_single_price_is_zero() -> None:
    assert max_drawdown([Decimal("100")]) == Decimal("0")


def test_max_drawdown_rejects_empty_list() -> None:
    with pytest.raises(ValueError):
        max_drawdown([])


def test_max_drawdown_output_always_non_positive() -> None:
    examples = [
        [Decimal("10"), Decimal("20"), Decimal("15"), Decimal("30"), Decimal("5")],
        [Decimal("50"), Decimal("50.01"), Decimal("49.99"), Decimal("50")],
        [Decimal("100"), Decimal("1")],
        [Decimal("1"), Decimal("100")],
    ]
    for prices in examples:
        assert max_drawdown(prices) <= Decimal("0")
