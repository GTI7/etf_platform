from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Callable

from core.market_data.providers.base import ProviderError, ProviderPriceBar

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"


def _http_get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310
        return response.read()


def _build_url(ticker: str, start_date: date, end_date: date) -> str:
    period1 = int(datetime.combine(start_date, time.min, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime.combine(end_date, time.max, tzinfo=timezone.utc).timestamp())
    query = urllib.parse.urlencode({"period1": period1, "period2": period2, "interval": "1d"})
    return f"{_CHART_URL.format(ticker=urllib.parse.quote(ticker))}?{query}"


def _parse_chart_response(payload: dict[str, Any]) -> list[ProviderPriceBar]:
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise ProviderError(f"Yahoo Finance error: {chart['error']}")

    results = chart.get("result") or []
    if not results:
        raise ProviderError("Yahoo Finance returned no result for this ticker")

    result = results[0]
    currency = result["meta"]["currency"]
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    opens, highs, lows, closes, volumes = (
        quote["open"],
        quote["high"],
        quote["low"],
        quote["close"],
        quote["volume"],
    )

    bars: list[ProviderPriceBar] = []
    for i, ts in enumerate(timestamps):
        o, h, l, c, v = opens[i], highs[i], lows[i], closes[i], volumes[i]
        if None in (o, h, l, c, v):
            # Yahoo represents a missing/gap session as nulls in the arrays.
            continue
        bars.append(
            ProviderPriceBar(
                session_date=datetime.fromtimestamp(ts, tz=timezone.utc).date(),
                # Decimal(str(x)), never Decimal(x): x is a JSON float, and
                # going through repr/str avoids baking in binary-float noise
                # (e.g. Decimal(450.12) != Decimal("450.12")).
                open=Decimal(str(o)),
                high=Decimal(str(h)),
                low=Decimal(str(l)),
                close=Decimal(str(c)),
                volume=int(v),
                currency=currency,
            )
        )
    return bars


class YahooFinanceProvider:
    name = "yahoo_finance"

    def __init__(self, fetch: Callable[[str], bytes] | None = None) -> None:
        self._fetch = fetch or _http_get

    def fetch_daily_bars(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[ProviderPriceBar]:
        url = _build_url(ticker, start_date, end_date)
        try:
            raw = self._fetch(url)
        except urllib.error.URLError as exc:
            # Covers HTTPError too (a URLError subclass) -- any transport-level
            # failure (rate limiting, DNS, connection refused, ...) is exactly
            # the "upstream error response" case ProviderError already exists
            # for; this only translates the exception type, never swallows it.
            raise ProviderError(f"Yahoo Finance request failed: {exc}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            # E.g. an HTML rate-limit/CAPTCHA page returned instead of JSON --
            # a malformed upstream response, the other case ProviderError's
            # docstring already names.
            raise ProviderError(f"Yahoo Finance returned invalid JSON: {exc}") from exc

        return _parse_chart_response(payload)
