"""ETF half of what `tests/test_governance_dataset_snapshots.py` used to
cover, following its subject to `core.analytics.persistence.etf_snapshot`
(Engine Boundary cleanup item C4).

The file split mirrors the module split, and the module split is the
point: `ETF` is an asset class and `TradingSession`/`PriceBar` are not.
The neutral half is `tests/test_market_data_snapshot_rows.py`.

Snapshot *writing* is composed explicitly here -- fetch, convert, then
`write_canonical_jsonl` -- rather than called through a `write_etf_snapshot`
helper. That helper is gone because it was the composition of a
workload-owned conversion with a Governance-owned serializer, which is
exactly the pairing `etf -> governance` forbids. Composing at the call
site is what the split costs, and it is two lines.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from core.analytics.persistence.etf_snapshot import (
    etf_to_row,
    fetch_all_etfs,
    load_etf_rows,
    row_to_etf,
)
from core.governance.canonical_jsonl import read_canonical_jsonl, write_canonical_jsonl
from core.market_data.domain.models import ETF, Calendar
from core.market_data.persistence.repository import insert_calendar, insert_etf

CALENDAR_ID = "XNYS"


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


def _write_etf_snapshot(conn: sqlite3.Connection, path: Path) -> None:
    write_canonical_jsonl([etf_to_row(etf) for etf in fetch_all_etfs(conn)], path)


def _read_etf_snapshot(path: Path) -> list[ETF]:
    return [row_to_etf(row) for row in read_canonical_jsonl(path)]


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
    _write_etf_snapshot(conn, path)

    etfs = _read_etf_snapshot(path)
    assert [e.ticker for e in etfs] == ["ACWI", "QQQ", "SPY"]


def test_fetch_all_etfs_orders_by_ticker(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _calendar())
    insert_etf(conn, _etf("SPY", "id-spy"))
    insert_etf(conn, _etf("ACWI", "id-acwi"))

    etfs = fetch_all_etfs(conn)

    assert [e.ticker for e in etfs] == ["ACWI", "SPY"]


def test_load_etf_rows_preserves_etf_id_never_regenerates(
    conn: sqlite3.Connection, tmp_path: Path
) -> None:
    insert_calendar(conn, _calendar())
    frozen_etf_id = "3f2a1b9c4d5e4f6a8b7c9d0e1f2a3b4c"
    path = tmp_path / "etf.jsonl"
    write_canonical_jsonl([etf_to_row(_etf("SPY", frozen_etf_id))], path)

    load_etf_rows(conn, read_canonical_jsonl(path))

    loaded = fetch_all_etfs(conn)
    assert len(loaded) == 1
    assert loaded[0].etf_id == frozen_etf_id
