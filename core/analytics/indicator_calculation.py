from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date
from decimal import Decimal

from core.analytics.domain.calculations import max_drawdown, rsi, sma
from core.analytics.domain.models import IndicatorDefinition, IndicatorValue, InsufficientPriceHistoryError
from core.analytics.persistence.repository import insert_indicator_value
from core.market_data.domain.models import ETF
from core.market_data.ingestion.pipeline_run import run_pipeline
from core.market_data.persistence.repository import get_price_bars, get_trading_days
from core.shared.clock import Clock
from core.shared.pipeline_names import indicator_pipeline_name


def _resolve_trading_window(
    conn: sqlite3.Connection, calendar_id: str, session_date: date, window: int
) -> list[date]:
    """The `window` most recent trading-day dates on or before session_date.

    Raises InsufficientPriceHistoryError if fewer than `window` exist --
    this only tells us the calendar doesn't have enough populated trading
    days; whether that's a genuine early-history gap or a calendar
    population gap is indistinguishable here, and deliberately not
    resolved differently (see InsufficientPriceHistoryError's docstring).
    """
    trading_days = [d for d in get_trading_days(conn, calendar_id) if d <= session_date]
    if len(trading_days) < window:
        raise InsufficientPriceHistoryError(
            f"Only {len(trading_days)} trading day(s) on or before {session_date} "
            f"for calendar {calendar_id!r}, need {window}"
        )
    return trading_days[-window:]


def _load_close_prices(
    conn: sqlite3.Connection, etf_id: str, window_dates: list[date]
) -> list[Decimal]:
    """The close price for every date in window_dates, in order.

    Raises InsufficientPriceHistoryError if any date in the window has no
    PriceBar -- this is the case a trading-day count alone would miss: the
    calendar says these are trading days, but price ingestion hasn't
    covered all of them.
    """
    bars = get_price_bars(conn, etf_id, start_date=window_dates[0], end_date=window_dates[-1])
    bars_by_date = {bar.session_date: bar for bar in bars}
    missing = [d for d in window_dates if d not in bars_by_date]
    if missing:
        raise InsufficientPriceHistoryError(
            f"Missing PriceBar for etf_id={etf_id!r} on trading day(s): {missing}"
        )
    return [bars_by_date[d].close.amount for d in window_dates]


def calculate_sma(
    conn: sqlite3.Connection,
    clock: Clock,
    etf: ETF,
    definition: IndicatorDefinition,
    session_date: date,
) -> str:
    """Compute and store one SMA IndicatorValue for one ETF and session.

    TradingCalendar-aware: the window is `definition.parameters["window"]`
    trading sessions on the ETF's calendar ending at session_date, never
    calendar days. One call is one atomic pipeline run: the IndicatorValue
    insert, run completion, and watermark advance commit or roll back
    together, per run_pipeline's transaction boundary. Idempotent: rerunning
    for the same (definition, etf, session_date) is a no-op insert.
    """
    window = json.loads(definition.parameters)["window"]
    pipeline_name = indicator_pipeline_name(definition.name, definition.version, etf.ticker)
    with run_pipeline(conn, clock, pipeline_name, session_date) as ingestion_run_id:
        window_dates = _resolve_trading_window(conn, etf.calendar_id, session_date, window)
        prices = _load_close_prices(conn, etf.etf_id, window_dates)
        value = sma(prices)
        indicator_value = IndicatorValue(
            indicator_value_id=uuid.uuid4().hex,
            indicator_definition_id=definition.indicator_definition_id,
            etf_id=etf.etf_id,
            session_date=session_date,
            value=value,
            computed_at=clock.now(),
        )
        insert_indicator_value(conn, indicator_value)
    return ingestion_run_id


def calculate_rsi(
    conn: sqlite3.Connection,
    clock: Clock,
    etf: ETF,
    definition: IndicatorDefinition,
    session_date: date,
) -> str:
    """Compute and store one RSI IndicatorValue for one ETF and session.

    TradingCalendar-aware: rsi() needs period+1 consecutive closes to
    produce `definition.parameters["period"]` deltas, so the window
    resolved here is one trading session longer than calculate_sma()'s
    equivalent window for the same period -- everything else (window
    resolution, price loading, transaction boundary, idempotency) reuses
    the exact same machinery calculate_sma() already uses. One call is one
    atomic pipeline run: the IndicatorValue insert, run completion, and
    watermark advance commit or roll back together, per run_pipeline's
    transaction boundary. Idempotent: rerunning for the same (definition,
    etf, session_date) is a no-op insert.
    """
    period = json.loads(definition.parameters)["period"]
    pipeline_name = indicator_pipeline_name(definition.name, definition.version, etf.ticker)
    with run_pipeline(conn, clock, pipeline_name, session_date) as ingestion_run_id:
        window_dates = _resolve_trading_window(conn, etf.calendar_id, session_date, period + 1)
        prices = _load_close_prices(conn, etf.etf_id, window_dates)
        value = rsi(prices)
        indicator_value = IndicatorValue(
            indicator_value_id=uuid.uuid4().hex,
            indicator_definition_id=definition.indicator_definition_id,
            etf_id=etf.etf_id,
            session_date=session_date,
            value=value,
            computed_at=clock.now(),
        )
        insert_indicator_value(conn, indicator_value)
    return ingestion_run_id


def calculate_drawdown(
    conn: sqlite3.Connection,
    clock: Clock,
    etf: ETF,
    definition: IndicatorDefinition,
    session_date: date,
) -> str:
    """Compute and store one MAX_DRAWDOWN IndicatorValue for one ETF and session.

    TradingCalendar-aware: the window is `definition.parameters["window"]`
    trading sessions on the ETF's calendar ending at session_date -- SMA's
    window semantics, not RSI's period+1 (drawdown needs raw price levels
    to track peak-vs-trough, not deltas, so it needs exactly `window`
    prices, the same as calculate_sma()). One call is one atomic pipeline
    run: the IndicatorValue insert, run completion, and watermark advance
    commit or roll back together, per run_pipeline's transaction boundary.
    Idempotent: rerunning for the same (definition, etf, session_date) is
    a no-op insert.

    A comparison metric only: independent of SMA/RSI, not wired into
    run_write_pipeline() or run_write_pipeline_for_etfs() -- it remains a
    separately-callable indicator, the same way SMA and RSI existed
    independently before write-pipeline composition ever wired them in.
    """
    window = json.loads(definition.parameters)["window"]
    pipeline_name = indicator_pipeline_name(definition.name, definition.version, etf.ticker)
    with run_pipeline(conn, clock, pipeline_name, session_date) as ingestion_run_id:
        window_dates = _resolve_trading_window(conn, etf.calendar_id, session_date, window)
        prices = _load_close_prices(conn, etf.etf_id, window_dates)
        value = max_drawdown(prices)
        indicator_value = IndicatorValue(
            indicator_value_id=uuid.uuid4().hex,
            indicator_definition_id=definition.indicator_definition_id,
            etf_id=etf.etf_id,
            session_date=session_date,
            value=value,
            computed_at=clock.now(),
        )
        insert_indicator_value(conn, indicator_value)
    return ingestion_run_id
