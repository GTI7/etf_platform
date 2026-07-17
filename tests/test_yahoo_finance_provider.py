from __future__ import annotations

import json
import urllib.error
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from core.market_data.providers.base import ProviderError
from core.market_data.providers.yahoo_finance import YahooFinanceProvider, _build_url, _http_get


def _ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, 14, 30, tzinfo=timezone.utc).timestamp())


def _chart_payload(currency: str = "USD") -> dict:
    days = [date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 15)]
    return {
        "chart": {
            "result": [
                {
                    "meta": {"currency": currency},
                    "timestamp": [_ts(d) for d in days],
                    "indicators": {
                        "quote": [
                            {
                                # 2026-07-15 is a gap day: Yahoo nulls it out.
                                "open": [450.12, 451.5, None],
                                "high": [452.0, 452.75, None],
                                "low": [449.5, 450.9, None],
                                "close": [451.75, 452.1, None],
                                "volume": [1_000_000, 1_200_000, None],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }


def test_fetch_daily_bars_parses_response_and_skips_gap_days() -> None:
    payload = _chart_payload()

    def fake_fetch(url: str) -> bytes:
        return json.dumps(payload).encode("utf-8")

    provider = YahooFinanceProvider(fetch=fake_fetch)

    bars = provider.fetch_daily_bars("SPY", date(2026, 7, 13), date(2026, 7, 15))

    assert [b.session_date for b in bars] == [date(2026, 7, 13), date(2026, 7, 14)]
    assert bars[0].open == Decimal("450.12")
    assert bars[0].high == Decimal("452.0")
    assert bars[0].low == Decimal("449.5")
    assert bars[0].close == Decimal("451.75")
    assert bars[0].volume == 1_000_000
    assert bars[0].currency == "USD"


def test_fetch_daily_bars_raises_on_chart_error() -> None:
    payload = {"chart": {"result": None, "error": {"code": "Not Found", "description": "no data"}}}

    def fake_fetch(url: str) -> bytes:
        return json.dumps(payload).encode("utf-8")

    provider = YahooFinanceProvider(fetch=fake_fetch)

    with pytest.raises(ProviderError):
        provider.fetch_daily_bars("BADTICKER", date(2026, 7, 13), date(2026, 7, 13))


def test_fetch_daily_bars_raises_on_empty_result() -> None:
    payload = {"chart": {"result": [], "error": None}}

    def fake_fetch(url: str) -> bytes:
        return json.dumps(payload).encode("utf-8")

    provider = YahooFinanceProvider(fetch=fake_fetch)

    with pytest.raises(ProviderError):
        provider.fetch_daily_bars("SPY", date(2026, 7, 13), date(2026, 7, 13))


def test_fetch_daily_bars_translates_url_error_into_provider_error() -> None:
    """A transport-level failure (DNS, connection refused, ...) must reach
    the caller as ProviderError, never as a raw urllib exception."""

    def failing_fetch(url: str) -> bytes:
        raise urllib.error.URLError("connection refused")

    provider = YahooFinanceProvider(fetch=failing_fetch)

    with pytest.raises(ProviderError, match="Yahoo Finance request failed"):
        provider.fetch_daily_bars("SPY", date(2026, 7, 13), date(2026, 7, 13))


def test_fetch_daily_bars_translates_http_error_into_provider_error() -> None:
    """HTTPError (e.g. a 429 rate-limit response) is a URLError subclass --
    it must be translated the same way as any other transport failure."""

    def failing_fetch(url: str) -> bytes:
        raise urllib.error.HTTPError(url, 429, "Too Many Requests", hdrs=None, fp=None)

    provider = YahooFinanceProvider(fetch=failing_fetch)

    with pytest.raises(ProviderError, match="Yahoo Finance request failed"):
        provider.fetch_daily_bars("SPY", date(2026, 7, 13), date(2026, 7, 13))


def test_fetch_daily_bars_translates_invalid_json_into_provider_error() -> None:
    """An upstream response that isn't valid JSON (e.g. an HTML rate-limit
    or CAPTCHA page) must also reach the caller as ProviderError, never as
    a raw json.JSONDecodeError."""

    def fake_fetch(url: str) -> bytes:
        return b"<html>not json</html>"

    provider = YahooFinanceProvider(fetch=fake_fetch)

    with pytest.raises(ProviderError, match="Yahoo Finance returned invalid JSON"):
        provider.fetch_daily_bars("SPY", date(2026, 7, 13), date(2026, 7, 13))


def test_provider_name_is_yahoo_finance() -> None:
    assert YahooFinanceProvider().name == "yahoo_finance"


def test_build_url_includes_ticker_and_range_params() -> None:
    url = _build_url("SPY", date(2026, 7, 13), date(2026, 7, 14))

    assert url.startswith("https://query1.finance.yahoo.com/v8/finance/chart/SPY?")
    assert "interval=1d" in url
    assert "period1=" in url
    assert "period2=" in url


def test_default_fetch_uses_real_http_get(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_http_get(url: str) -> bytes:
        captured["url"] = url
        return json.dumps(_chart_payload()).encode("utf-8")

    monkeypatch.setattr("core.market_data.providers.yahoo_finance._http_get", fake_http_get)

    provider = YahooFinanceProvider()
    bars = provider.fetch_daily_bars("SPY", date(2026, 7, 13), date(2026, 7, 14))

    assert "query1.finance.yahoo.com" in captured["url"]
    assert len(bars) == 2


def test_http_get_reads_urlopen_response_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercises _http_get's own body (never invoked by the other tests,
    which all inject a fake fetch instead) without making a real network
    call: urlopen itself is replaced with an in-memory fake response."""

    class _FakeResponse:
        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *exc_info: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true}'

    def fake_urlopen(url: str, timeout: int) -> _FakeResponse:
        assert timeout == 10
        return _FakeResponse()

    monkeypatch.setattr(
        "core.market_data.providers.yahoo_finance.urllib.request.urlopen", fake_urlopen
    )

    assert _http_get("https://example.invalid") == b'{"ok": true}'
