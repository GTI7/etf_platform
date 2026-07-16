from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

import core.market_data.ingestion.pipeline_run as pipeline_run
from core.analytics.domain.models import (
    IndicatorDefinition,
    InsufficientPriceHistoryError,
    serialize_parameters,
)
from core.analytics.indicator_calculation import calculate_sma
from core.analytics.persistence.repository import get_indicator_values, insert_indicator_definition
from core.market_data.domain.models import ETF, Calendar, PriceBar, TradingSession
from core.market_data.persistence.repository import (
    get_last_successful_pipeline_date,
    insert_calendar,
    insert_etf,
    insert_price_bar,
    insert_trading_session,
)
from core.shared.clock import FixedClock
from core.shared.money import Money

CALENDAR_ID = "XNYS"


def _make_etf_with_trading_days(conn: sqlite3.Connection, trading_days: list[date]) -> ETF:
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


def _insert_bar(conn: sqlite3.Connection, etf_id: str, session_date: date, close: str) -> None:
    price = Money(Decimal(close), "USD")
    insert_price_bar(
        conn,
        PriceBar(
            price_bar_id=uuid.uuid4().hex,
            etf_id=etf_id,
            session_date=session_date,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1,
            source="test",
            ingested_at=datetime.now(timezone.utc),
        ),
    )


def _make_definition(window: int = 3) -> IndicatorDefinition:
    return IndicatorDefinition(
        indicator_definition_id=uuid.uuid4().hex,
        name="SMA",
        version=1,
        parameters=serialize_parameters({"window": window}),
        created_at=datetime.now(timezone.utc),
    )


# Thu 2026-07-16, Fri 2026-07-17, [weekend], Mon 2026-07-20.
TRADING_DAYS = [date(2026, 7, 16), date(2026, 7, 17), date(2026, 7, 20)]


def test_calculate_sma_uses_trading_days_not_calendar_days(conn: sqlite3.Connection) -> None:
    etf = _make_etf_with_trading_days(conn, TRADING_DAYS)
    _insert_bar(conn, etf.etf_id, date(2026, 7, 16), "10")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 17), "20")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 20), "30")
    definition = _make_definition(window=3)
    insert_indicator_definition(conn, definition)
    clock = FixedClock(datetime(2026, 7, 20, 21, 0, tzinfo=timezone.utc))

    calculate_sma(conn, clock, etf, definition, date(2026, 7, 20))

    [value] = get_indicator_values(conn, definition.indicator_definition_id, etf.etf_id)
    # (10 + 20 + 30) / 3, using the 3 trading-day closes -- if the weekend
    # gap had been (wrongly) treated as missing trading days, this window
    # would either fail or use different dates entirely.
    assert value.value == Decimal("20")
    pipeline_name = f"indicator:SMA:v1:{etf.ticker}"
    assert get_last_successful_pipeline_date(conn, pipeline_name) == date(2026, 7, 20)


def test_calculate_sma_raises_when_too_few_trading_days(conn: sqlite3.Connection) -> None:
    etf = _make_etf_with_trading_days(conn, [date(2026, 7, 16), date(2026, 7, 17)])  # only 2
    _insert_bar(conn, etf.etf_id, date(2026, 7, 16), "10")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 17), "20")
    definition = _make_definition(window=3)
    insert_indicator_definition(conn, definition)
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    with pytest.raises(InsufficientPriceHistoryError):
        calculate_sma(conn, clock, etf, definition, date(2026, 7, 17))

    assert get_indicator_values(conn, definition.indicator_definition_id, etf.etf_id) == []


def test_calculate_sma_raises_when_pricebar_missing_for_a_trading_day(
    conn: sqlite3.Connection,
) -> None:
    """The calendar has 3 populated trading days, but price ingestion only
    covers 2 of them -- this must fail loudly, not silently average over
    the 2 bars that do exist."""
    etf = _make_etf_with_trading_days(conn, TRADING_DAYS)
    _insert_bar(conn, etf.etf_id, date(2026, 7, 16), "10")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 17), "20")
    # No PriceBar for 2026-07-20.
    definition = _make_definition(window=3)
    insert_indicator_definition(conn, definition)
    clock = FixedClock(datetime(2026, 7, 20, 21, 0, tzinfo=timezone.utc))

    with pytest.raises(InsufficientPriceHistoryError):
        calculate_sma(conn, clock, etf, definition, date(2026, 7, 20))

    assert get_indicator_values(conn, definition.indicator_definition_id, etf.etf_id) == []


def test_calculate_sma_is_idempotent_on_rerun(conn: sqlite3.Connection) -> None:
    etf = _make_etf_with_trading_days(conn, TRADING_DAYS)
    _insert_bar(conn, etf.etf_id, date(2026, 7, 16), "10")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 17), "20")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 20), "30")
    definition = _make_definition(window=3)
    insert_indicator_definition(conn, definition)
    clock = FixedClock(datetime(2026, 7, 20, 21, 0, tzinfo=timezone.utc))

    for _ in range(3):
        calculate_sma(conn, clock, etf, definition, date(2026, 7, 20))

    values = get_indicator_values(conn, definition.indicator_definition_id, etf.etf_id)
    assert len(values) == 1
    assert values[0].value == Decimal("20")


def test_watermark_advance_failure_rolls_back_completion(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure in run_pipeline's own completion step (after calculate_sma's
    body has already succeeded) must still roll back the IndicatorValue
    insert along with the completion update -- the same guarantee Phase 0
    proved generically in test_transaction_boundaries.py, checked here for
    the analytics pipeline family specifically."""
    etf = _make_etf_with_trading_days(conn, TRADING_DAYS)
    _insert_bar(conn, etf.etf_id, date(2026, 7, 16), "10")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 17), "20")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 20), "30")
    definition = _make_definition(window=3)
    insert_indicator_definition(conn, definition)
    clock = FixedClock(datetime(2026, 7, 20, 21, 0, tzinfo=timezone.utc))

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated failure advancing the watermark")

    monkeypatch.setattr(pipeline_run, "advance_pipeline_watermark", _boom)

    with pytest.raises(RuntimeError):
        calculate_sma(conn, clock, etf, definition, date(2026, 7, 20))

    assert get_indicator_values(conn, definition.indicator_definition_id, etf.etf_id) == []
    pipeline_name = f"indicator:SMA:v1:{etf.ticker}"
    assert get_last_successful_pipeline_date(conn, pipeline_name) is None
    status = conn.execute(
        "SELECT status FROM IngestionRun WHERE pipeline_name = ?", (pipeline_name,)
    ).fetchone()["status"]
    assert status == "running"


def test_calculation_failure_rolls_back_partial_write(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression test for the rollback fix in run_pipeline's except branch
    (fixed during Phase 1, verified here for the analytics pipeline family
    specifically, since reusing run_pipeline unmodified is not something to
    assume without its own test). A write that succeeds during the pipeline
    body, followed by a failure in that same body, must not survive: the
    'failed' IngestionRun can never coexist with the IndicatorValue it
    would-be produced."""
    import core.analytics.indicator_calculation as indicator_calculation

    etf = _make_etf_with_trading_days(conn, TRADING_DAYS)
    _insert_bar(conn, etf.etf_id, date(2026, 7, 16), "10")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 17), "20")
    _insert_bar(conn, etf.etf_id, date(2026, 7, 20), "30")
    definition = _make_definition(window=3)
    insert_indicator_definition(conn, definition)
    clock = FixedClock(datetime(2026, 7, 20, 21, 0, tzinfo=timezone.utc))

    real_insert = indicator_calculation.insert_indicator_value

    def _insert_then_fail(conn_: sqlite3.Connection, value: object) -> None:
        real_insert(conn_, value)  # the write genuinely succeeds first ...
        raise RuntimeError("simulated failure after a successful write")  # ... then the run fails

    monkeypatch.setattr(indicator_calculation, "insert_indicator_value", _insert_then_fail)

    with pytest.raises(RuntimeError):
        calculate_sma(conn, clock, etf, definition, date(2026, 7, 20))

    assert get_indicator_values(conn, definition.indicator_definition_id, etf.etf_id) == []
    pipeline_name = f"indicator:SMA:v1:{etf.ticker}"
    assert get_last_successful_pipeline_date(conn, pipeline_name) is None
    status = conn.execute(
        "SELECT status FROM IngestionRun WHERE pipeline_name = ?", (pipeline_name,)
    ).fetchone()["status"]
    assert status == "failed"
