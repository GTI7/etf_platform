"""Repository functions for the market_data persistence layer.

These functions only execute SQL against the connection they are given --
none of them commit. The caller owns the transaction boundary: wrap one or
more calls in `with conn:` to make them succeed or fail together. See
core/market_data/ingestion/pipeline_run.py for the canonical example.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal

from core.market_data.domain.models import (
    ETF,
    Calendar,
    IngestionRun,
    IngestionStatus,
    PipelineState,
    PriceBar,
    TradingSession,
)
from core.shared.money import Money


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def insert_etf(conn: sqlite3.Connection, etf: ETF) -> None:
    conn.execute(
        """
        INSERT INTO ETF (etf_id, ticker, name, currency, calendar_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (etf.etf_id, etf.ticker, etf.name, etf.currency, etf.calendar_id, _iso(etf.created_at)),
    )


def get_etf(conn: sqlite3.Connection, etf_id: str) -> ETF | None:
    row = conn.execute(
        "SELECT etf_id, ticker, name, currency, calendar_id, created_at FROM ETF WHERE etf_id = ?",
        (etf_id,),
    ).fetchone()
    if row is None:
        return None
    return ETF(
        etf_id=row["etf_id"],
        ticker=row["ticker"],
        name=row["name"],
        currency=row["currency"],
        calendar_id=row["calendar_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def insert_calendar(conn: sqlite3.Connection, calendar: Calendar) -> None:
    conn.execute(
        "INSERT INTO Calendar (calendar_id, name, exchange, timezone) VALUES (?, ?, ?, ?)",
        (calendar.calendar_id, calendar.name, calendar.exchange, calendar.timezone),
    )


def insert_trading_session(conn: sqlite3.Connection, session: TradingSession) -> None:
    conn.execute(
        """
        INSERT INTO TradingSession (calendar_id, session_date, is_trading_day, close_time_utc)
        VALUES (?, ?, ?, ?)
        """,
        (
            session.calendar_id,
            session.session_date.isoformat(),
            1 if session.is_trading_day else 0,
            _iso(session.close_time_utc) if session.close_time_utc else None,
        ),
    )


def get_trading_days(conn: sqlite3.Connection, calendar_id: str) -> list[date]:
    rows = conn.execute(
        """
        SELECT session_date FROM TradingSession
        WHERE calendar_id = ? AND is_trading_day = 1
        ORDER BY session_date
        """,
        (calendar_id,),
    ).fetchall()
    return [date.fromisoformat(row["session_date"]) for row in rows]


def is_trading_day(conn: sqlite3.Connection, calendar_id: str, session_date: date) -> bool:
    """True only if `session_date` has a TradingSession row for `calendar_id`
    marked as a trading day. An unpopulated date is treated as non-trading
    (safe default: skip rather than guess)."""
    row = conn.execute(
        "SELECT is_trading_day FROM TradingSession WHERE calendar_id = ? AND session_date = ?",
        (calendar_id, session_date.isoformat()),
    ).fetchone()
    return row is not None and bool(row["is_trading_day"])


def insert_price_bar(conn: sqlite3.Connection, bar: PriceBar) -> None:
    if not (bar.open.currency == bar.high.currency == bar.low.currency == bar.close.currency):
        raise ValueError("PriceBar OHLC currencies must match")
    conn.execute(
        """
        INSERT INTO PriceBar (
            price_bar_id, etf_id, session_date,
            open_amount, high_amount, low_amount, close_amount,
            volume, currency, source, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bar.price_bar_id,
            bar.etf_id,
            bar.session_date.isoformat(),
            str(bar.open.amount),
            str(bar.high.amount),
            str(bar.low.amount),
            str(bar.close.amount),
            bar.volume,
            bar.open.currency,
            bar.source,
            _iso(bar.ingested_at),
        ),
    )


def _row_to_price_bar(row: sqlite3.Row) -> PriceBar:
    currency = row["currency"]
    return PriceBar(
        price_bar_id=row["price_bar_id"],
        etf_id=row["etf_id"],
        session_date=date.fromisoformat(row["session_date"]),
        open=Money(Decimal(row["open_amount"]), currency),
        high=Money(Decimal(row["high_amount"]), currency),
        low=Money(Decimal(row["low_amount"]), currency),
        close=Money(Decimal(row["close_amount"]), currency),
        volume=row["volume"],
        source=row["source"],
        ingested_at=datetime.fromisoformat(row["ingested_at"]),
    )


def get_price_bars(
    conn: sqlite3.Connection,
    etf_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[PriceBar]:
    query = "SELECT * FROM PriceBar WHERE etf_id = ?"
    params: list[object] = [etf_id]
    if start_date is not None:
        query += " AND session_date >= ?"
        params.append(start_date.isoformat())
    if end_date is not None:
        query += " AND session_date <= ?"
        params.append(end_date.isoformat())
    query += " ORDER BY session_date"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_price_bar(row) for row in rows]


def start_ingestion_run(conn: sqlite3.Connection, run: IngestionRun) -> None:
    conn.execute(
        """
        INSERT INTO IngestionRun (
            ingestion_run_id, pipeline_name, pipeline_date, status,
            started_at, completed_at, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run.ingestion_run_id,
            run.pipeline_name,
            run.pipeline_date.isoformat(),
            run.status.value,
            _iso(run.started_at),
            None,
            None,
        ),
    )


def complete_ingestion_run(
    conn: sqlite3.Connection,
    ingestion_run_id: str,
    status: IngestionStatus,
    completed_at: datetime,
    error_message: str | None = None,
) -> None:
    if status is IngestionStatus.RUNNING:
        raise ValueError("complete_ingestion_run requires a terminal status")
    conn.execute(
        """
        UPDATE IngestionRun
        SET status = ?, completed_at = ?, error_message = ?
        WHERE ingestion_run_id = ?
        """,
        (status.value, _iso(completed_at), error_message, ingestion_run_id),
    )


def advance_pipeline_watermark(
    conn: sqlite3.Connection,
    pipeline_name: str,
    session_date: date,
    updated_at: datetime,
) -> None:
    """Record that `pipeline_name` has successfully progressed through `session_date`.

    Only ever moves the watermark forward: an out-of-order (e.g. backfill)
    run for an earlier session does not regress a later watermark, and
    repeating the same session is a no-op on the stored value.
    """
    conn.execute(
        """
        INSERT INTO PipelineState (pipeline_name, last_successful_session, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT (pipeline_name) DO UPDATE SET
            last_successful_session = MAX(last_successful_session, excluded.last_successful_session),
            updated_at = excluded.updated_at
        """,
        (pipeline_name, session_date.isoformat(), _iso(updated_at)),
    )


def get_pipeline_state(conn: sqlite3.Connection, pipeline_name: str) -> PipelineState | None:
    row = conn.execute(
        "SELECT pipeline_name, last_successful_session, updated_at FROM PipelineState WHERE pipeline_name = ?",
        (pipeline_name,),
    ).fetchone()
    if row is None:
        return None
    return PipelineState(
        pipeline_name=row["pipeline_name"],
        last_successful_session=date.fromisoformat(row["last_successful_session"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def get_last_successful_pipeline_date(conn: sqlite3.Connection, pipeline_name: str) -> date | None:
    state = get_pipeline_state(conn, pipeline_name)
    return state.last_successful_session if state is not None else None
