from __future__ import annotations

from decimal import Decimal


def sma(prices: list[Decimal]) -> Decimal:
    """Simple moving average: the arithmetic mean of the given prices.

    Pure and window-size-agnostic: the window is implicit in len(prices).
    Callers are responsible for supplying exactly the N trading-day prices
    the window requires -- see core/analytics/indicator_calculation.py for
    how those N prices are resolved and validated against the
    TradingCalendar before this function ever sees them.
    """
    if not prices:
        raise ValueError("sma() requires at least one price")
    return sum(prices, Decimal("0")) / Decimal(len(prices))
