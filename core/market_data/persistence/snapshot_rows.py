"""Frozen-snapshot row conversion for the Data domain's own aggregates:
``TradingSession`` and ``PriceBar``.

**Why this is here and not in Governance.** It was in
``core.governance.dataset_snapshots`` until 2026-07-27 (Engine Boundary
cleanup item C4). Governance owns the *canonical serialization* of a
frozen dataset -- the JSONL rules, the content hashes, the byte
comparison -- and it owns nothing about what a row means. Constructing a
``PriceBar`` from a row is domain knowledge: it decides that
``open_amount`` plus ``currency`` is a ``Money``, that ``session_date``
is a ``date``, and that a missing ``close_time_utc`` is a real ``None``
rather than an absent key. An auditor that had to know those things in
order to audit could not audit a second asset class without being
rewritten, which is the coupling this move removes.

**The row shapes are frozen, not merely current.** They match
``migrations/0001_initial_schema.sql`` exactly -- no invented columns --
and `research_archive/reference_h4/dataset_hashes/*.jsonl` are sealed
bytes produced by these exact functions (AD-075).
``tests/test_sealed_snapshot_byte_identity.py`` re-serializes the sealed
rows through them on every run and fails on any difference, including
ones an object-equality test would not see: a changed key, a different
``Decimal`` spelling, a timezone offset written another way, an omitted
null. Treat every line below as byte-significant.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Iterable, Mapping

from core.market_data.domain.models import PriceBar, TradingSession
from core.market_data.persistence.repository import insert_price_bar, insert_trading_session
from core.shared.money import Money


def utc_iso8601(dt: datetime) -> str:
    """The one spelling of an instant these snapshots use. Public, and
    imported by `core.analytics.persistence.etf_snapshot` for the ETF
    rows, so the three frozen tables cannot drift into two spellings of
    the same moment."""
    return dt.astimezone(timezone.utc).isoformat()


# --- TradingSession ------------------------------------------------------


def trading_session_to_row(session: TradingSession) -> dict[str, Any]:
    return {
        "calendar_id": session.calendar_id,
        "session_date": session.session_date.isoformat(),
        "is_trading_day": bool(session.is_trading_day),
        # close_time_utc is nullable in the schema; the writer must emit
        # `null` explicitly, never omit the key.
        "close_time_utc": utc_iso8601(session.close_time_utc) if session.close_time_utc else None,
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


def load_trading_session_rows(
    conn: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]
) -> None:
    for row in rows:
        insert_trading_session(conn, row_to_trading_session(row))


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
        "ingested_at": utc_iso8601(bar.ingested_at),
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


def load_price_bar_rows(conn: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> None:
    for row in rows:
        insert_price_bar(conn, row_to_price_bar(row))
