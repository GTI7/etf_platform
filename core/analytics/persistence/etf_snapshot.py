"""Frozen-snapshot row conversion for the ``ETF`` aggregate.

Separate from `core.market_data.persistence.snapshot_rows` -- which holds
the same three functions for ``TradingSession`` and ``PriceBar`` -- for
one reason: ``ETF`` is an **asset class**, and `core.analytics` is the
package AD-068 maps to the ``etf`` domain. `TradingSession` and
`PriceBar` are asset-class-neutral Data-domain aggregates and stay there.
Splitting the file along that line is the whole point; keeping the three
together in one module would have forced the module into whichever domain
was more contaminating.

**Why neither half is in Governance any more.** Until 2026-07-27 all
three lived in ``core.governance.dataset_snapshots``, which imported
``ETF`` and ``insert_etf`` -- the two `governance -> etf` violations
pinned by AD-068's inventory. A Governance audit that constructs the
audited asset class cannot be run against a different one. Governance now
reads and verifies canonical snapshot *rows* and hands them here; this
module turns them into objects and inserts them.

**The one rule this module exists to keep true** (Phase 4 Architecture
Amendment v1.1 §A.3): loading an ``ETF`` snapshot preserves ``etf_id``
exactly as extracted. Nothing here calls ``uuid4()`` -- not at load time,
not at extraction time, not at any other point in reproduction. That is
what makes a reproduction run comparable to the original.

Row shapes match ``migrations/0001_initial_schema.sql`` exactly (no
invented ``exchange``/``type`` columns, per amendment §C.1) and are
byte-significant: `research_archive/reference_h4/dataset_hashes/ETF.jsonl`
is sealed under AD-075, and `tests/test_sealed_snapshot_byte_identity.py`
re-serializes it through these functions on every run.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Iterable, Mapping

from core.market_data.domain.models import ETF
from core.market_data.persistence.repository import insert_etf
from core.market_data.persistence.snapshot_rows import utc_iso8601


def etf_to_row(etf: ETF) -> dict[str, Any]:
    return {
        "etf_id": etf.etf_id,
        "ticker": etf.ticker,
        "name": etf.name,
        "currency": etf.currency,
        "calendar_id": etf.calendar_id,
        "created_at": utc_iso8601(etf.created_at),
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


def load_etf_rows(conn: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> None:
    """Insert every row of a frozen ETF snapshot, preserving etf_id
    exactly -- never uuid4() at load time, at extraction time, or at any
    other point in reproduction."""
    for row in rows:
        insert_etf(conn, row_to_etf(row))
