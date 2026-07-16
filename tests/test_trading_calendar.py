from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone

import pytest

from core.market_data.domain.models import ETF, Calendar, TradingSession
from core.market_data.persistence.repository import (
    get_trading_days,
    insert_calendar,
    insert_etf,
    insert_trading_session,
)


def _make_calendar(calendar_id: str = "XNYS") -> Calendar:
    return Calendar(
        calendar_id=calendar_id,
        name="New York Stock Exchange",
        exchange="NYSE",
        timezone="America/New_York",
    )


def test_trading_calendar_excludes_non_trading_sessions(conn: sqlite3.Connection) -> None:
    calendar_id = "XNYS"
    insert_calendar(conn, _make_calendar(calendar_id))
    insert_trading_session(
        conn,
        TradingSession(
            calendar_id=calendar_id,
            session_date=date(2026, 7, 13),
            is_trading_day=True,
            close_time_utc=datetime(2026, 7, 13, 20, 0, tzinfo=timezone.utc),
        ),
    )
    insert_trading_session(
        conn,
        TradingSession(
            calendar_id=calendar_id,
            session_date=date(2026, 7, 14),
            is_trading_day=False,
            close_time_utc=None,
        ),
    )

    assert get_trading_days(conn, calendar_id) == [date(2026, 7, 13)]


def test_trading_session_requires_known_calendar(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        insert_trading_session(
            conn,
            TradingSession(
                calendar_id="UNKNOWN",
                session_date=date(2026, 7, 13),
                is_trading_day=True,
                close_time_utc=None,
            ),
        )


def test_etf_requires_known_calendar(conn: sqlite3.Connection) -> None:
    etf = ETF(
        etf_id="etf-1",
        ticker="SPY",
        name="SPDR S&P 500",
        currency="USD",
        calendar_id="UNKNOWN",
        created_at=datetime.now(timezone.utc),
    )
    with pytest.raises(sqlite3.IntegrityError):
        insert_etf(conn, etf)


def test_etf_references_calendar(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _make_calendar())
    etf = ETF(
        etf_id="etf-1",
        ticker="SPY",
        name="SPDR S&P 500",
        currency="USD",
        calendar_id="XNYS",
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)  # does not raise
