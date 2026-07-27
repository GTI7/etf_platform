"""The two callables `core.governance.reconstruction_loader` is handed
for this workload's three frozen tables.

Governance verifies a frozen dataset -- hashes, row counts, structural
duplicates, canonical JSONL -- and then needs two things it must not know
how to do itself: *does this row parse into the object it claims to be*,
and *put these rows in the database*. Both are domain knowledge. This
module supplies them, and is the one place that knows all three tables
belong to the same reconstruction.

**Why it can sit here and Governance cannot call it.** `core.analytics`
is the ``etf`` domain (AD-068), which may depend on ``data`` -- so it may
import both `etf_snapshot` (its own) and
`core.market_data.persistence.snapshot_rows` (Data's). Governance may not
depend on ``etf`` at all, which is exactly why these are passed *in* as
callables by whoever composes a reconstruction, rather than imported by
the module that runs one. The composition roots today are
`tools/reproduce_cycle.py` and the reconstruction tests.

**Not a registry.** ``_ROW_PARSERS`` below is a three-entry dict over
three names fixed by `core.governance.dataset_manifest.REQUIRED_SOURCE_TABLES`
and by `migrations/0001_initial_schema.sql`. Nothing registers into it at
runtime, nothing discovers it, and an unknown ``source_table`` raises
rather than being skipped. A fourth frozen table is a schema change and
an edit to this file, which is the intended cost.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Callable, Mapping, Sequence

from core.analytics.persistence.etf_snapshot import load_etf_rows, row_to_etf
from core.market_data.persistence.snapshot_rows import (
    load_price_bar_rows,
    load_trading_session_rows,
    row_to_price_bar,
    row_to_trading_session,
)

_ROW_PARSERS: dict[str, Callable[[Mapping[str, Any]], Any]] = {
    "ETF": row_to_etf,
    "TradingSession": row_to_trading_session,
    "PriceBar": row_to_price_bar,
}


class UnknownSourceTableError(KeyError):
    """A snapshot declares a ``source_table`` this workload has no
    conversion for. Raised rather than skipped: a table nobody can parse
    must not pass validation by being invisible to it."""


def parse_snapshot_row(source_table: str, row: Mapping[str, Any]) -> None:
    """Raise if `row` does not parse into `source_table`'s domain object.

    Discards the object it builds -- the construction *is* the check, and
    keeping the result would tempt a caller into loading through the
    validation path rather than the load path. Governance calls this once
    per row during preflight, offline, before the scratch database
    exists, and wraps whatever this raises in `MalformedSnapshotRowError`.
    """
    try:
        parser = _ROW_PARSERS[source_table]
    except KeyError as exc:
        raise UnknownSourceTableError(
            f"no row parser for source_table {source_table!r}; known tables: "
            f"{sorted(_ROW_PARSERS)}"
        ) from exc
    parser(row)


def load_snapshot_rows(
    conn: sqlite3.Connection, rows_by_source_table: Mapping[str, Sequence[Mapping[str, Any]]]
) -> None:
    """Insert all three frozen tables in foreign-key order.

    ``ETF`` before ``PriceBar`` because ``PriceBar.etf_id`` is a live FK
    against ``ETF.etf_id`` under ``PRAGMA foreign_keys=ON``. ``Calendar``
    is not here: it is a code-defined literal inserted by Governance
    before this is called, not a frozen dataset (amendment §A.4).
    """
    load_etf_rows(conn, rows_by_source_table["ETF"])
    load_trading_session_rows(conn, rows_by_source_table["TradingSession"])
    load_price_bar_rows(conn, rows_by_source_table["PriceBar"])
