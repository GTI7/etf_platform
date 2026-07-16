from __future__ import annotations

from datetime import date

import pytest

from core.market_data.providers.base import ProviderPriceBar
from core.market_data.providers.registry import ProviderRegistry


class _StubProvider:
    def __init__(self, name: str) -> None:
        self.name = name

    def fetch_daily_bars(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[ProviderPriceBar]:
        return []


def test_register_and_get_provider() -> None:
    registry = ProviderRegistry()
    provider = _StubProvider("stub")

    registry.register(provider)

    assert registry.get("stub") is provider


def test_register_duplicate_name_raises() -> None:
    registry = ProviderRegistry()
    registry.register(_StubProvider("stub"))

    with pytest.raises(ValueError):
        registry.register(_StubProvider("stub"))


def test_get_unknown_provider_raises() -> None:
    registry = ProviderRegistry()

    with pytest.raises(KeyError):
        registry.get("does-not-exist")
