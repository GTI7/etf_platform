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


def mean(values: list[Decimal]) -> Decimal:
    """Arithmetic mean of the given values. Pure, no I/O.

    Separate from sma(): sma is a price-window concept, this is the
    general-purpose primitive used wherever a plain average of Decimals is
    needed (e.g. combining dimension scores into an overall score).
    """
    if not values:
        raise ValueError("mean() requires at least one value")
    return sum(values, Decimal("0")) / Decimal(len(values))


def rsi(closes: list[Decimal]) -> Decimal:
    """Relative Strength Index: a bounded [0, 100] momentum oscillator.

    Reference/simplified variant: average gain and average loss are each a
    plain arithmetic mean over the window (not Wilder's exponential
    smoothing). Input is period+1 consecutive closing prices,
    oldest-to-newest -- N deltas require N+1 raw prices, one more than
    sma() needs for the same window size. Pure, no I/O.

    Zero-average-loss convention (defined explicitly, not left ambiguous):
    - avg_loss == 0 and avg_gain > 0  -> RSI = 100 (all gains)
    - avg_loss == 0 and avg_gain == 0 -> RSI = 50  (flat, no change at all)

    0 <= RSI <= 100 always holds: RS = avg_gain / avg_loss is never
    negative (gains and losses are each clamped to >= 0 before averaging),
    so 100 / (1 + RS) is always in (0, 100], and RSI = 100 - that term is
    always in [0, 100).
    """
    if len(closes) < 2:
        raise ValueError("rsi() requires at least 2 prices")
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for previous, current in zip(closes, closes[1:]):
        delta = current - previous
        gains.append(max(delta, Decimal("0")))
        losses.append(max(-delta, Decimal("0")))
    avg_gain = mean(gains)
    avg_loss = mean(losses)
    if avg_loss == 0:
        return Decimal("100") if avg_gain > 0 else Decimal("50")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def max_drawdown(prices: list[Decimal]) -> Decimal:
    """The largest peak-to-trough fractional decline within `prices`.

    Convention (defined explicitly, same discipline as rsi()'s zero-loss
    case): Decimal("0") means no drawdown occurred -- prices never fell
    below a prior peak; Decimal("-0.20") means a 20% decline from the
    previous peak. Tracks a running peak across the window, not just the
    first or global price, so a decline-recovery-decline pattern is
    measured correctly at each trough relative to the peak that preceded
    it, not just the window's single highest price. Always <= 0. Pure, no
    I/O, same style as sma()/rsi().
    """
    if not prices:
        raise ValueError("max_drawdown() requires at least one price")
    peak = prices[0]
    worst = Decimal("0")
    for price in prices:
        peak = max(peak, price)
        worst = min(worst, (price - peak) / peak)
    return worst
