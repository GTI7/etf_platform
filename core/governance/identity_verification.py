"""Post-run frozen-identity verification (Phase 4 Architecture Amendment
v1.1 SS F.3). Scoped exactly to ``{Calendar, ETF, TradingSession,
PriceBar}`` -- the frozen-identity set (SS A.3) -- and must never be
applied to the derived set (``IndicatorValue``, ``Score``,
``DimensionScore``, rankings, reports), which is *required* to gain new
rows on every successful run.

This scope boundary is itself a MUST HAVE, not an incidental detail:
too narrow, and a silent identity regeneration (v1.0's actual defect)
goes uncaught again; too broad, and the checker false-fails every
correct reproduction, since IndicatorValue/Score/DimensionScore are
supposed to change every run (SS A.1.3).
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass

FROZEN_IDENTITY_TABLES: tuple[str, ...] = ("Calendar", "ETF", "TradingSession", "PriceBar")

# Deterministic row order per table -- matches how each table's own
# primary key / natural key already orders it, so two reads of the same
# unchanged table always hash identically regardless of physical
# on-disk row order.
_ORDER_BY: dict[str, str] = {
    "Calendar": "calendar_id",
    "ETF": "etf_id",
    "TradingSession": "calendar_id, session_date",
    "PriceBar": "etf_id, session_date, price_bar_id",
}


class FrozenIdentityChangedError(RuntimeError):
    """Raised when any frozen-identity table's row count or ordered hash
    changed across a reproduction run -- the check that would have
    caught v1.0's actual defect (a silent `_ensure_etfs` insert) as an
    immediate, specific failure instead of a downstream numerical
    discrepancy three steps later."""


@dataclass(frozen=True, slots=True)
class TableIdentitySnapshot:
    row_count: int
    ordered_hash: str


def _hash_table(conn: sqlite3.Connection, table: str) -> TableIdentitySnapshot:
    # `table` is always one of the fixed FROZEN_IDENTITY_TABLES literals
    # above, never external input -- safe to interpolate.
    order_by = _ORDER_BY[table]
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order_by}").fetchall()  # noqa: S608
    hasher = hashlib.sha256()
    for row in rows:
        hasher.update("|".join(str(row[key]) for key in row.keys()).encode("utf-8"))
        hasher.update(b"\n")
    return TableIdentitySnapshot(row_count=len(rows), ordered_hash=hasher.hexdigest())


def snapshot_identity_state(conn: sqlite3.Connection) -> dict[str, TableIdentitySnapshot]:
    """Row count + deterministic ordered hash for each of the four
    frozen-identity tables, as they exist right now in `conn`."""
    return {table: _hash_table(conn, table) for table in FROZEN_IDENTITY_TABLES}


def assert_frozen_identity_unchanged(
    before: dict[str, TableIdentitySnapshot],
    after: dict[str, TableIdentitySnapshot],
) -> None:
    """Raise FrozenIdentityChangedError, naming every table that changed
    and its row-count delta, if any frozen-identity table differs
    between the two snapshots. Never inspects any other table."""
    changed = [
        f"{table}: row_count {before[table].row_count} -> {after[table].row_count}"
        for table in FROZEN_IDENTITY_TABLES
        if before[table] != after[table]
    ]
    if changed:
        raise FrozenIdentityChangedError(
            "Frozen-identity table(s) changed during reproduction (identity must never "
            "regenerate): " + "; ".join(changed)
        )
