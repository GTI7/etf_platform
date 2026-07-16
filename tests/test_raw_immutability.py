from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from core.market_data.domain.models import ETF, Calendar, PriceBar
from core.market_data.persistence.repository import (
    insert_calendar,
    insert_etf,
    insert_price_bar,
)
from core.shared.money import Money


def _make_etf(conn: sqlite3.Connection) -> ETF:
    insert_calendar(
        conn,
        Calendar(
            calendar_id="XNYS",
            name="New York Stock Exchange",
            exchange="NYSE",
            timezone="America/New_York",
        ),
    )
    return ETF(
        etf_id=uuid.uuid4().hex,
        ticker="SPY",
        name="SPDR S&P 500",
        currency="USD",
        calendar_id="XNYS",
        created_at=datetime.now(timezone.utc),
    )


def _make_price_bar(etf_id: str) -> PriceBar:
    price = Money(Decimal("450.00"), "USD")
    return PriceBar(
        price_bar_id=uuid.uuid4().hex,
        etf_id=etf_id,
        session_date=date(2026, 7, 14),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=1000,
        source="test",
        ingested_at=datetime.now(timezone.utc),
    )


def test_raw_update_fails(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    insert_etf(conn, etf)
    bar = _make_price_bar(etf.etf_id)
    insert_price_bar(conn, bar)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE PriceBar SET close_amount = ? WHERE price_bar_id = ?",
            ("999.00", bar.price_bar_id),
        )


def test_raw_delete_fails(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    insert_etf(conn, etf)
    bar = _make_price_bar(etf.etf_id)
    insert_price_bar(conn, bar)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM PriceBar WHERE price_bar_id = ?", (bar.price_bar_id,))
