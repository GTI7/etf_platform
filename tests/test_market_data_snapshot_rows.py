"""Asset-class-neutral half of what
`tests/test_governance_dataset_snapshots.py` used to cover, following its
subject to `core.market_data.persistence.snapshot_rows` (Engine Boundary
cleanup item C4). The ETF half is `tests/test_etf_snapshot_rows.py`.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from core.governance.canonical_jsonl import read_canonical_jsonl, write_canonical_jsonl
from core.market_data.domain.models import ETF, Calendar, PriceBar, TradingSession
from core.market_data.persistence.repository import (
    insert_calendar,
    insert_etf,
    insert_price_bar,
    insert_trading_session,
)
from core.market_data.persistence.snapshot_rows import (
    fetch_all_price_bars,
    fetch_all_trading_sessions,
    load_price_bar_rows,
    price_bar_to_row,
    row_to_price_bar,
    row_to_trading_session,
    trading_session_to_row,
)
from core.shared.money import Money
from core.store.connection import connect
from core.store.migrations import run_migrations

CALENDAR_ID = "XNYS"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _calendar() -> Calendar:
    return Calendar(
        calendar_id=CALENDAR_ID, name="New York Stock Exchange", exchange="NYSE", timezone="America/New_York"
    )


def _etf(ticker: str, etf_id: str) -> ETF:
    return ETF(
        etf_id=etf_id,
        ticker=ticker,
        name=f"{ticker} Fund",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime(2024, 1, 3, 14, 30, tzinfo=timezone.utc),
    )


def _bar(etf_id: str, session_date: date, price_bar_id: str) -> PriceBar:
    return PriceBar(
        price_bar_id=price_bar_id,
        etf_id=etf_id,
        session_date=session_date,
        open=Money(Decimal("450.12"), "USD"),
        high=Money(Decimal("452.00"), "USD"),
        low=Money(Decimal("449.50"), "USD"),
        close=Money(Decimal("451.75"), "USD"),
        volume=1_000_000,
        source="yahoo_finance",
        ingested_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )


def _write_trading_session_snapshot(conn: sqlite3.Connection, path: Path) -> None:
    write_canonical_jsonl(
        [trading_session_to_row(s) for s in fetch_all_trading_sessions(conn)], path
    )


def _write_price_bar_snapshot(conn: sqlite3.Connection, path: Path) -> None:
    write_canonical_jsonl([price_bar_to_row(b) for b in fetch_all_price_bars(conn)], path)


def test_trading_session_row_preserves_null_close_time_explicitly() -> None:
    session = TradingSession(
        calendar_id=CALENDAR_ID, session_date=date(2026, 7, 13), is_trading_day=True, close_time_utc=None
    )

    row = trading_session_to_row(session)

    assert "close_time_utc" in row
    assert row["close_time_utc"] is None
    assert row_to_trading_session(row) == session


def test_trading_session_snapshot_orders_by_calendar_then_date(conn: sqlite3.Connection, tmp_path: Path) -> None:
    insert_calendar(conn, _calendar())
    insert_trading_session(conn, TradingSession(CALENDAR_ID, date(2026, 7, 15), True, None))
    insert_trading_session(conn, TradingSession(CALENDAR_ID, date(2026, 7, 13), True, None))

    path = tmp_path / "sessions.jsonl"
    _write_trading_session_snapshot(conn, path)

    restored = [row_to_trading_session(row) for row in read_canonical_jsonl(path)]
    assert [s.session_date for s in restored] == [date(2026, 7, 13), date(2026, 7, 15)]


def test_fetch_all_trading_sessions_can_filter_by_calendar_id(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _calendar())
    insert_trading_session(conn, TradingSession(CALENDAR_ID, date(2026, 7, 13), True, None))

    sessions = fetch_all_trading_sessions(conn, CALENDAR_ID)

    assert len(sessions) == 1


def test_price_bar_row_preserves_decimal_amounts_as_strings() -> None:
    bar = _bar("etf-1", date(2026, 7, 13), "bar-1")

    row = price_bar_to_row(bar)

    assert row["open_amount"] == "450.12"
    assert isinstance(row["open_amount"], str)
    assert row_to_price_bar(row) == bar


def test_price_bar_snapshot_orders_by_etf_then_session_date(conn: sqlite3.Connection, tmp_path: Path) -> None:
    insert_calendar(conn, _calendar())
    insert_etf(conn, _etf("SPY", "etf-spy"))
    insert_etf(conn, _etf("QQQ", "etf-qqq"))
    insert_price_bar(conn, _bar("etf-qqq", date(2026, 7, 13), "bar-1"))
    insert_price_bar(conn, _bar("etf-spy", date(2026, 7, 14), "bar-2"))
    insert_price_bar(conn, _bar("etf-spy", date(2026, 7, 13), "bar-3"))

    path = tmp_path / "pricebar.jsonl"
    _write_price_bar_snapshot(conn, path)

    bars = fetch_all_price_bars(conn)
    assert [(b.etf_id, b.session_date) for b in bars] == [
        ("etf-qqq", date(2026, 7, 13)),
        ("etf-spy", date(2026, 7, 13)),
        ("etf-spy", date(2026, 7, 14)),
    ]


def test_load_price_bar_rows_round_trips(tmp_path: Path) -> None:
    source_db_path = tmp_path / "source.db"
    source_conn = connect(source_db_path)
    run_migrations(source_conn, MIGRATIONS_DIR)
    with source_conn:
        insert_calendar(source_conn, _calendar())
        insert_etf(source_conn, _etf("SPY", "etf-spy"))
        insert_price_bar(source_conn, _bar("etf-spy", date(2026, 7, 13), "bar-1"))
    path = tmp_path / "pricebar.jsonl"
    _write_price_bar_snapshot(source_conn, path)
    source_conn.close()

    fresh_conn = connect(tmp_path / "fresh.db")
    try:
        run_migrations(fresh_conn, MIGRATIONS_DIR)
        with fresh_conn:
            insert_calendar(fresh_conn, _calendar())
            insert_etf(fresh_conn, _etf("SPY", "etf-spy"))
            load_price_bar_rows(fresh_conn, read_canonical_jsonl(path))
        loaded = fetch_all_price_bars(fresh_conn)
        assert len(loaded) == 1
        assert loaded[0].price_bar_id == "bar-1"
    finally:
        fresh_conn.close()
