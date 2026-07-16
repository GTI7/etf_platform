from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from core.market_data.domain.models import ETF, Calendar, PriceBar
from core.market_data.persistence.repository import (
    get_price_bars,
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
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker="SPY",
        name="SPDR S&P 500",
        currency="USD",
        calendar_id="XNYS",
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def test_price_bar_round_trip_preserves_high_precision_decimal(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    high_precision = Decimal("450.123456789")
    bar = PriceBar(
        price_bar_id=uuid.uuid4().hex,
        etf_id=etf.etf_id,
        session_date=date(2026, 7, 14),
        open=Money(high_precision, "USD"),
        high=Money(high_precision, "USD"),
        low=Money(high_precision, "USD"),
        close=Money(high_precision, "USD"),
        volume=1000,
        source="test",
        ingested_at=datetime.now(timezone.utc),
    )

    insert_price_bar(conn, bar)

    [round_tripped] = get_price_bars(conn, etf.etf_id)

    assert round_tripped.open.amount == high_precision
    assert round_tripped.high.amount == high_precision
    assert round_tripped.low.amount == high_precision
    assert round_tripped.close.amount == high_precision
    assert round_tripped == bar


def test_get_price_bars_filters_by_date_range(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    price = Money(Decimal("100.00"), "USD")

    for day in (12, 13, 14):
        insert_price_bar(
            conn,
            PriceBar(
                price_bar_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                session_date=date(2026, 7, day),
                open=price,
                high=price,
                low=price,
                close=price,
                volume=1,
                source="test",
                ingested_at=datetime.now(timezone.utc),
            ),
        )

    bars = get_price_bars(
        conn, etf.etf_id, start_date=date(2026, 7, 13), end_date=date(2026, 7, 13)
    )

    assert [b.session_date for b in bars] == [date(2026, 7, 13)]
