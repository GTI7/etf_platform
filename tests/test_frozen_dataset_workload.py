"""`core.analytics.persistence.frozen_dataset` -- the two callables
Governance is handed for this workload's frozen tables (Engine Boundary
cleanup item C4).

Small surface, but it is the seam the whole separation rests on: if
`parse_snapshot_row` silently accepted a table it has no parser for, a
malformed snapshot would pass preflight and surface as a raw
`sqlite3` error during the DB-mutation step, which is precisely the
"fail fast, offline, before the scratch database exists" property
`reconstruction_loader` was written to have.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from core.analytics.persistence.etf_snapshot import etf_to_row, fetch_all_etfs
from core.analytics.persistence.frozen_dataset import (
    UnknownSourceTableError,
    load_snapshot_rows,
    parse_snapshot_row,
)
from core.market_data.domain.models import ETF, Calendar, PriceBar, TradingSession
from core.market_data.persistence.repository import insert_calendar
from core.market_data.persistence.snapshot_rows import (
    fetch_all_price_bars,
    fetch_all_trading_sessions,
    price_bar_to_row,
    trading_session_to_row,
)
from core.shared.money import Money

CALENDAR_ID = "XNYS"


def _calendar() -> Calendar:
    return Calendar(
        calendar_id=CALENDAR_ID, name="New York Stock Exchange", exchange="NYSE", timezone="America/New_York"
    )


def _rows() -> dict[str, list[dict]]:
    etf = ETF(
        etf_id="etf-spy",
        ticker="SPY",
        name="SPY Fund",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )
    session = TradingSession(CALENDAR_ID, date(2026, 7, 13), True, None)
    bar = PriceBar(
        price_bar_id="bar-1",
        etf_id="etf-spy",
        session_date=date(2026, 7, 13),
        open=Money(Decimal("1.00"), "USD"),
        high=Money(Decimal("1.00"), "USD"),
        low=Money(Decimal("1.00"), "USD"),
        close=Money(Decimal("1.00"), "USD"),
        volume=1,
        source="yahoo_finance",
        ingested_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )
    return {
        "ETF": [etf_to_row(etf)],
        "TradingSession": [trading_session_to_row(session)],
        "PriceBar": [price_bar_to_row(bar)],
    }


@pytest.mark.parametrize("source_table", ["ETF", "TradingSession", "PriceBar"])
def test_parse_snapshot_row_accepts_a_well_formed_row(source_table: str) -> None:
    parse_snapshot_row(source_table, _rows()[source_table][0])


@pytest.mark.parametrize("source_table", ["ETF", "TradingSession", "PriceBar"])
def test_parse_snapshot_row_rejects_a_row_missing_a_field(source_table: str) -> None:
    row = dict(_rows()[source_table][0])
    row.pop(next(iter(row)))

    with pytest.raises((KeyError, ValueError, TypeError)):
        parse_snapshot_row(source_table, row)


def test_parse_snapshot_row_refuses_an_unknown_source_table() -> None:
    """Refused, never skipped. A table nobody can parse must not pass
    validation by being invisible to it."""
    with pytest.raises(UnknownSourceTableError):
        parse_snapshot_row("Portfolio", {"anything": 1})


def test_load_snapshot_rows_inserts_all_three_tables(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _calendar())

    load_snapshot_rows(conn, _rows())

    assert [e.ticker for e in fetch_all_etfs(conn)] == ["SPY"]
    assert len(fetch_all_trading_sessions(conn)) == 1
    assert [b.price_bar_id for b in fetch_all_price_bars(conn)] == ["bar-1"]


def test_load_snapshot_rows_loads_etf_before_price_bar(conn: sqlite3.Connection) -> None:
    """``PriceBar.etf_id`` is a live FK against ``ETF.etf_id`` under
    ``PRAGMA foreign_keys=ON``, so a loader that inserted price bars
    first would fail on a database that enforces it. Asserted by loading
    for real rather than by reading the source order."""
    insert_calendar(conn, _calendar())

    load_snapshot_rows(conn, _rows())  # would raise sqlite3.IntegrityError if reordered

    assert len(fetch_all_price_bars(conn)) == 1
