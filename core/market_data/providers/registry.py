from __future__ import annotations

from core.market_data.providers.base import DataProvider


class ProviderRegistry:
    """An explicit, in-memory map from provider name to DataProvider
    instance. No auto-discovery: callers register what they need."""

    def __init__(self) -> None:
        self._providers: dict[str, DataProvider] = {}

    def register(self, provider: DataProvider) -> None:
        if provider.name in self._providers:
            raise ValueError(f"Provider already registered: {provider.name}")
        self._providers[provider.name] = provider

    def get(self, name: str) -> DataProvider:
        try:
            return self._providers[name]
        except KeyError:
            raise KeyError(f"No provider registered under name: {name!r}") from None
