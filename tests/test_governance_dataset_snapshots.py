from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from core.governance.canonical_jsonl import write_canonical_jsonl
from core.governance.dataset_snapshots import (
    etf_to_row,
    fetch_all_etfs,
    fetch_all_price_bars,
    fetch_all_trading_sessions,
    load_etf_snapshot,
    load_price_bar_snapshot,
    price_bar_to_row,
    read_etf_snapshot,
    read_trading_session_snapshot,
    row_to_etf,
    row_to_price_bar,
    row_to_trading_session,
    trading_session_to_row,
    write_etf_snapshot,
    write_price_bar_snapshot,
    write_trading_session_snapshot,
)
from core.market_data.domain.models import ETF, Calendar, PriceBar, TradingSession
from core.market_data.persistence.repository import (
    insert_calendar,
    insert_etf,
    insert_price_bar,
    insert_trading_session,
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


def test_etf_row_round_trip_preserves_etf_id_exactly() -> None:
    etf = _etf("SPY", "3f2a1b9c4d5e4f6a8b7c9d0e1f2a3b4c")

    row = etf_to_row(etf)
    restored = row_to_etf(row)

    assert row["etf_id"] == "3f2a1b9c4d5e4f6a8b7c9d0e1f2a3b4c"
    assert restored == etf


def test_etf_row_has_exactly_the_six_schema_columns() -> None:
    row = etf_to_row(_etf("SPY", "abc"))

    assert set(row) == {"etf_id", "ticker", "name", "currency", "calendar_id", "created_at"}


def test_write_etf_snapshot_orders_by_ticker(conn: sqlite3.Connection, tmp_path: Path) -> None:
    insert_calendar(conn, _calendar())
    insert_etf(conn, _etf("SPY", "id-spy"))
    insert_etf(conn, _etf("QQQ", "id-qqq"))
    insert_etf(conn, _etf("ACWI", "id-acwi"))

    path = tmp_path / "etf.jsonl"
    write_etf_snapshot(conn, path)

    etfs = read_etf_snapshot(path)
    assert [e.ticker for e in etfs] == ["ACWI", "QQQ", "SPY"]


def test_fetch_all_etfs_orders_by_ticker(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _calendar())
    insert_etf(conn, _etf("SPY", "id-spy"))
    insert_etf(conn, _etf("ACWI", "id-acwi"))

    etfs = fetch_all_etfs(conn)

    assert [e.ticker for e in etfs] == ["ACWI", "SPY"]


def test_load_etf_snapshot_preserves_etf_id_never_regenerates(conn: sqlite3.Connection, tmp_path: Path) -> None:
    insert_calendar(conn, _calendar())
    frozen_etf_id = "3f2a1b9c4d5e4f6a8b7c9d0e1f2a3b4c"
    path = tmp_path / "etf.jsonl"
    write_canonical_jsonl([etf_to_row(_etf("SPY", frozen_etf_id))], path)

    load_etf_snapshot(conn, path)

    loaded = fetch_all_etfs(conn)
    assert len(loaded) == 1
    assert loaded[0].etf_id == frozen_etf_id


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
    write_trading_session_snapshot(conn, path)

    restored = read_trading_session_snapshot(path)
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
    write_price_bar_snapshot(conn, path)

    bars = fetch_all_price_bars(conn)
    assert [(b.etf_id, b.session_date) for b in bars] == [
        ("etf-qqq", date(2026, 7, 13)),
        ("etf-spy", date(2026, 7, 13)),
        ("etf-spy", date(2026, 7, 14)),
    ]


def test_load_price_bar_snapshot_round_trips(tmp_path: Path) -> None:
    source_db_path = tmp_path / "source.db"
    source_conn = connect(source_db_path)
    run_migrations(source_conn, MIGRATIONS_DIR)
    with source_conn:
        insert_calendar(source_conn, _calendar())
        insert_etf(source_conn, _etf("SPY", "etf-spy"))
        insert_price_bar(source_conn, _bar("etf-spy", date(2026, 7, 13), "bar-1"))
    path = tmp_path / "pricebar.jsonl"
    write_price_bar_snapshot(source_conn, path)
    source_conn.close()

    fresh_conn = connect(tmp_path / "fresh.db")
    try:
        run_migrations(fresh_conn, MIGRATIONS_DIR)
        with fresh_conn:
            insert_calendar(fresh_conn, _calendar())
            insert_etf(fresh_conn, _etf("SPY", "etf-spy"))
            load_price_bar_snapshot(fresh_conn, path)
        loaded = fetch_all_price_bars(fresh_conn)
        assert len(loaded) == 1
        assert loaded[0].price_bar_id == "bar-1"
    finally:
        fresh_conn.close()
