from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

from core.market_data.domain.models import ETF, Calendar
from core.market_data.persistence.repository import get_etf, insert_calendar, insert_etf

CALENDAR_ID = "XNYS"


def test_get_etf_round_trip(conn: sqlite3.Connection) -> None:
    insert_calendar(
        conn,
        Calendar(
            calendar_id=CALENDAR_ID,
            name="New York Stock Exchange",
            exchange="NYSE",
            timezone="America/New_York",
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

    assert get_etf(conn, etf.etf_id) == etf


def test_get_etf_returns_none_when_missing(conn: sqlite3.Connection) -> None:
    assert get_etf(conn, "does-not-exist") is None
