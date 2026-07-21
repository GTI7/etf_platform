"""Frozen dataset snapshot row conversion and canonical JSONL I/O for the
three frozen-identity tables this design freezes: ``ETF``,
``TradingSession``, ``PriceBar`` (Phase 4 Architecture Amendment v1.1
SS A.3, SS C.1). ``Calendar`` is deliberately absent from this module --
it is a code-defined literal, not a frozen dataset (see
``core.governance.calendar_definitions``).

Row shapes match the actual schema exactly
(``migrations/0001_initial_schema.sql``) -- no invented columns (no
``exchange``/``type`` on ``ETF``, per amendment SS C.1).

The rule this entire amendment exists to make true: loading an ``ETF``
snapshot preserves ``etf_id`` exactly as extracted. Nothing in this
module ever calls ``uuid4()``.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from core.governance.canonical_jsonl import read_canonical_jsonl, write_canonical_jsonl
from core.market_data.domain.models import ETF, PriceBar, TradingSession
from core.market_data.persistence.repository import (
    insert_etf,
    insert_price_bar,
    insert_trading_session,
)
from core.shared.money import Money


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


# --- ETF ---------------------------------------------------------------


def etf_to_row(etf: ETF) -> dict[str, Any]:
    return {
        "etf_id": etf.etf_id,
        "ticker": etf.ticker,
        "name": etf.name,
        "currency": etf.currency,
        "calendar_id": etf.calendar_id,
        "created_at": _iso_utc(etf.created_at),
    }


def row_to_etf(row: Mapping[str, Any]) -> ETF:
    return ETF(
        etf_id=row["etf_id"],
        ticker=row["ticker"],
        name=row["name"],
        currency=row["currency"],
        calendar_id=row["calendar_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def fetch_all_etfs(conn: sqlite3.Connection) -> list[ETF]:
    """All ETF rows, ordered by ticker -- the deterministic row order the
    canonical snapshot uses (amendment SS C.1: ticker is UNIQUE and
    human-legible, unlike the opaque, run-independent etf_id)."""
    rows = conn.execute(
        "SELECT etf_id, ticker, name, currency, calendar_id, created_at FROM ETF ORDER BY ticker"
    ).fetchall()
    return [row_to_etf(row) for row in rows]


def write_etf_snapshot(conn: sqlite3.Connection, path: Path) -> None:
    write_canonical_jsonl([etf_to_row(etf) for etf in fetch_all_etfs(conn)], path)


def read_etf_snapshot(path: Path) -> list[ETF]:
    return [row_to_etf(row) for row in read_canonical_jsonl(path)]


def load_etf_snapshot(conn: sqlite3.Connection, path: Path) -> None:
    """Insert every row of a frozen ETF snapshot, preserving etf_id
    exactly -- never uuid4() at load time, at extraction time, or at any
    other point in reproduction."""
    for etf in read_etf_snapshot(path):
        insert_etf(conn, etf)


# --- TradingSession ------------------------------------------------------


def trading_session_to_row(session: TradingSession) -> dict[str, Any]:
    return {
        "calendar_id": session.calendar_id,
        "session_date": session.session_date.isoformat(),
        "is_trading_day": bool(session.is_trading_day),
        # close_time_utc is nullable in the schema; the writer must emit
        # `null` explicitly, never omit the key.
        "close_time_utc": _iso_utc(session.close_time_utc) if session.close_time_utc else None,
    }


def row_to_trading_session(row: Mapping[str, Any]) -> TradingSession:
    close_time_utc = row["close_time_utc"]
    return TradingSession(
        calendar_id=row["calendar_id"],
        session_date=date.fromisoformat(row["session_date"]),
        is_trading_day=bool(row["is_trading_day"]),
        close_time_utc=datetime.fromisoformat(close_time_utc) if close_time_utc is not None else None,
    )


def fetch_all_trading_sessions(
    conn: sqlite3.Connection, calendar_id: str | None = None
) -> list[TradingSession]:
    query = "SELECT calendar_id, session_date, is_trading_day, close_time_utc FROM TradingSession"
    params: tuple[Any, ...] = ()
    if calendar_id is not None:
        query += " WHERE calendar_id = ?"
        params = (calendar_id,)
    query += " ORDER BY calendar_id, session_date"
    rows = conn.execute(query, params).fetchall()
    return [row_to_trading_session(row) for row in rows]


def write_trading_session_snapshot(
    conn: sqlite3.Connection, path: Path, calendar_id: str | None = None
) -> None:
    sessions = fetch_all_trading_sessions(conn, calendar_id)
    write_canonical_jsonl([trading_session_to_row(s) for s in sessions], path)


def read_trading_session_snapshot(path: Path) -> list[TradingSession]:
    return [row_to_trading_session(row) for row in read_canonical_jsonl(path)]


def load_trading_session_snapshot(conn: sqlite3.Connection, path: Path) -> None:
    for session in read_trading_session_snapshot(path):
        insert_trading_session(conn, session)


# --- PriceBar --------------------------------------------------------------


def price_bar_to_row(bar: PriceBar) -> dict[str, Any]:
    return {
        "price_bar_id": bar.price_bar_id,
        "etf_id": bar.etf_id,
        "session_date": bar.session_date.isoformat(),
        # Decimal-compatible TEXT columns are preserved as strings, never
        # round-tripped through JSON's native number type or float.
        "open_amount": str(bar.open.amount),
        "high_amount": str(bar.high.amount),
        "low_amount": str(bar.low.amount),
        "close_amount": str(bar.close.amount),
        "volume": bar.volume,
        "currency": bar.open.currency,
        "source": bar.source,
        "ingested_at": _iso_utc(bar.ingested_at),
    }


def row_to_price_bar(row: Mapping[str, Any]) -> PriceBar:
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


def fetch_all_price_bars(conn: sqlite3.Connection, etf_ids: list[str] | None = None) -> list[PriceBar]:
    query = (
        "SELECT price_bar_id, etf_id, session_date, open_amount, high_amount, "
        "low_amount, close_amount, volume, currency, source, ingested_at FROM PriceBar"
    )
    params: tuple[Any, ...] = ()
    if etf_ids is not None:
        placeholders = ",".join("?" for _ in etf_ids)
        query += f" WHERE etf_id IN ({placeholders})"
        params = tuple(etf_ids)
    # Matches idx_pricebar_etf_session; price_bar_id as a final tiebreaker
    # keeps the order fully deterministic even if a future change ever
    # allowed more than one bar per (etf_id, session_date).
    query += " ORDER BY etf_id, session_date, price_bar_id"
    rows = conn.execute(query, params).fetchall()
    return [row_to_price_bar(row) for row in rows]


def write_price_bar_snapshot(conn: sqlite3.Connection, path: Path, etf_ids: list[str] | None = None) -> None:
    bars = fetch_all_price_bars(conn, etf_ids)
    write_canonical_jsonl([price_bar_to_row(bar) for bar in bars], path)


def read_price_bar_snapshot(path: Path) -> list[PriceBar]:
    return [row_to_price_bar(row) for row in read_canonical_jsonl(path)]


def load_price_bar_snapshot(conn: sqlite3.Connection, path: Path) -> None:
    for bar in read_price_bar_snapshot(path):
        insert_price_bar(conn, bar)
