from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


class ProviderError(Exception):
    """A market data provider could not satisfy a request (bad ticker,
    upstream error response, malformed payload, etc.)."""


@dataclass(frozen=True, slots=True)
class ProviderPriceBar:
    """A raw daily price bar as returned by a market data provider, before
    it is mapped into an immutable PriceBar domain record."""

    session_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    currency: str


class DataProvider(Protocol):
    """A source of raw daily price data for a ticker. Implementations are
    the only place that knows about a specific upstream API."""

    name: str

    def fetch_daily_bars(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[ProviderPriceBar]: ...
