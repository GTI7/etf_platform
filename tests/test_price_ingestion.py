from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

import core.market_data.ingestion.price_ingestion as price_ingestion
from core.market_data.domain.models import ETF, Calendar, TradingSession
from core.market_data.ingestion.price_ingestion import ingest_daily_prices
from core.market_data.persistence.repository import (
    get_last_successful_pipeline_date,
    get_price_bars,
    insert_calendar,
    insert_etf,
    insert_trading_session,
)
from core.market_data.providers.base import ProviderError, ProviderPriceBar
from core.shared.clock import FixedClock

CALENDAR_ID = "XNYS"


def _make_etf(conn: sqlite3.Connection, trading_days: list[date], non_trading_days: list[date]) -> ETF:
    insert_calendar(
        conn,
        Calendar(
            calendar_id=CALENDAR_ID,
            name="New York Stock Exchange",
            exchange="NYSE",
            timezone="America/New_York",
        ),
    )
    for day in trading_days:
        insert_trading_session(
            conn,
            TradingSession(
                calendar_id=CALENDAR_ID, session_date=day, is_trading_day=True, close_time_utc=None
            ),
        )
    for day in non_trading_days:
        insert_trading_session(
            conn,
            TradingSession(
                calendar_id=CALENDAR_ID, session_date=day, is_trading_day=False, close_time_utc=None
            ),
        )
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker="SPY",
        name="SPDR S&P 500",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


class _FakeProvider:
    def __init__(self, name: str, bars: list[ProviderPriceBar]) -> None:
        self.name = name
        self._bars = bars
        self.calls: list[tuple[str, date, date]] = []

    def fetch_daily_bars(self, ticker: str, start_date: date, end_date: date) -> list[ProviderPriceBar]:
        self.calls.append((ticker, start_date, end_date))
        return self._bars


class _FailingProvider:
    name = "failing"

    def fetch_daily_bars(self, ticker: str, start_date: date, end_date: date) -> list[ProviderPriceBar]:
        raise ProviderError("upstream is down")


def test_ingest_daily_prices_writes_bar_and_advances_watermark_on_trading_day(
    conn: sqlite3.Connection,
) -> None:
    session_date = date(2026, 7, 14)
    etf = _make_etf(conn, trading_days=[session_date], non_trading_days=[])
    bar = ProviderPriceBar(
        session_date=session_date,
        open=Decimal("450.12"),
        high=Decimal("452.00"),
        low=Decimal("449.50"),
        close=Decimal("451.75"),
        volume=1_000_000,
        currency="USD",
    )
    provider = _FakeProvider("fake", [bar])
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    ingest_daily_prices(conn, clock, provider, etf, session_date)

    [stored] = get_price_bars(conn, etf.etf_id)
    assert stored.session_date == session_date
    assert stored.open.amount == Decimal("450.12")
    assert stored.source == "fake"
    assert get_last_successful_pipeline_date(conn, f"price_ingestion:{etf.ticker}") == session_date


def test_ingest_daily_prices_ignores_bars_for_other_dates(conn: sqlite3.Connection) -> None:
    """Defensive check: a provider that returns bars outside the requested
    session (e.g. it ignored the date filter, or returned a wider range)
    must not have those extra bars mapped in -- only the exact session_date
    requested is ever written."""
    session_date = date(2026, 7, 14)
    etf = _make_etf(conn, trading_days=[session_date], non_trading_days=[])
    wrong_day_bar = ProviderPriceBar(
        session_date=date(2026, 7, 13),
        open=Decimal("1"),
        high=Decimal("1"),
        low=Decimal("1"),
        close=Decimal("1"),
        volume=1,
        currency="USD",
    )
    provider = _FakeProvider("fake", [wrong_day_bar])
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    ingest_daily_prices(conn, clock, provider, etf, session_date)

    assert get_price_bars(conn, etf.etf_id) == []
    assert get_last_successful_pipeline_date(conn, f"price_ingestion:{etf.ticker}") == session_date


def test_ingest_daily_prices_is_a_noop_on_non_trading_day(conn: sqlite3.Connection) -> None:
    session_date = date(2026, 7, 12)  # a Sunday, marked non-trading
    etf = _make_etf(conn, trading_days=[], non_trading_days=[session_date])
    provider = _FakeProvider("fake", bars=[])
    clock = FixedClock(datetime(2026, 7, 12, 21, 0, tzinfo=timezone.utc))

    ingest_daily_prices(conn, clock, provider, etf, session_date)

    assert get_price_bars(conn, etf.etf_id) == []
    assert provider.calls == []  # never even asked the provider
    # the watermark still advances: the session was correctly processed as
    # "nothing to ingest", which is a successful outcome.
    assert get_last_successful_pipeline_date(conn, f"price_ingestion:{etf.ticker}") == session_date


def test_ingest_daily_prices_records_failure_when_provider_raises(conn: sqlite3.Connection) -> None:
    session_date = date(2026, 7, 14)
    etf = _make_etf(conn, trading_days=[session_date], non_trading_days=[])
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    with pytest.raises(ProviderError):
        ingest_daily_prices(conn, clock, _FailingProvider(), etf, session_date)

    assert get_price_bars(conn, etf.etf_id) == []
    assert get_last_successful_pipeline_date(conn, f"price_ingestion:{etf.ticker}") is None
    status = conn.execute(
        "SELECT status FROM IngestionRun WHERE pipeline_name = ?",
        (f"price_ingestion:{etf.ticker}",),
    ).fetchone()["status"]
    assert status == "failed"


def test_partial_price_bar_writes_are_rolled_back_on_ingestion_failure(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression test for the rollback fix in run_pipeline's except branch.

    Before the fix, a PriceBar insert that succeeded before a later failure
    in the same pipeline body would still be committed once the 'failed'
    IngestionRun status was written, because the except branch entered its
    own `with conn:` without first discarding the pending transaction.
    """
    session_date = date(2026, 7, 14)
    etf = _make_etf(conn, trading_days=[session_date], non_trading_days=[])
    bar_a = ProviderPriceBar(
        session_date=session_date,
        open=Decimal("1"),
        high=Decimal("1"),
        low=Decimal("1"),
        close=Decimal("1"),
        volume=10,
        currency="USD",
    )
    bar_b = ProviderPriceBar(
        session_date=session_date,
        open=Decimal("2"),
        high=Decimal("2"),
        low=Decimal("2"),
        close=Decimal("2"),
        volume=20,
        currency="USD",
    )
    provider = _FakeProvider("flaky", [bar_a, bar_b])
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    real_insert = price_ingestion.insert_price_bar
    call_count = {"n": 0}

    def _flaky_insert(conn_: sqlite3.Connection, bar) -> None:  # type: ignore[no-untyped-def]
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("simulated failure inserting the second bar")
        real_insert(conn_, bar)

    monkeypatch.setattr(price_ingestion, "insert_price_bar", _flaky_insert)

    with pytest.raises(RuntimeError):
        ingest_daily_prices(conn, clock, provider, etf, session_date)

    # The first insert succeeded before the failure -- it must not survive.
    assert get_price_bars(conn, etf.etf_id) == []
    assert get_last_successful_pipeline_date(conn, f"price_ingestion:{etf.ticker}") is None
    status = conn.execute(
        "SELECT status, completed_at FROM IngestionRun WHERE pipeline_name = ?",
        (f"price_ingestion:{etf.ticker}",),
    ).fetchone()
    assert status["status"] == "failed"
    assert status["completed_at"] is not None
