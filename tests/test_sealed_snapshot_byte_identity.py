"""Byte-identity regression protection for the sealed `reference_h4`
dataset snapshots -- the safety net the Governance/workload separation
(C4) is not permitted to be attempted without.

**What this asserts.** For each of the three frozen source tables
(`ETF`, `TradingSession`, `PriceBar`), the *current* snapshot
serialization path -- row dict -> domain object -> row dict -> canonical
JSONL -- reproduces `research_archive/reference_h4/dataset_hashes/<T>.jsonl`
**byte for byte**. Not "parses", not "round-trips to an equal object",
not "hashes the same after normalization": the emitted bytes equal the
sealed bytes.

**Why it is stated that way.** C4 moves row/object conversion out of
`core.governance` and into workload-owned code. That refactor touches
every function on the write path of an archive whose bytes are
authoritative under AD-075: `research_archive/reference_h4/` is sealed
against commit `29553b7`, and `dataset_manifest.json`'s `content_hash`
entries are what `core.governance.dataset_integrity` verifies. A
serialization change that survives an object-equality test but shifts a
key order, a `Decimal` string form, a timezone offset spelling, or a null
representation would silently invalidate the seal's own subject. This
test fails on that class of change specifically, before it can be
committed.

**Independence from the modules under refactor.** The conversion
functions are imported here *by name*; the import site is the only line
that changes when they move. It has changed once: this file was written
against `core.governance.dataset_snapshots`, passed there, and now
imports the same functions from
`core.analytics.persistence.etf_snapshot` and
`core.market_data.persistence.snapshot_rows` after C4 moved them. It
passed before and after, against unmodified sealed bytes, which is the
whole reason it was written first. The sealed bytes are read from the archive
and the expected hash from the archive's own `dataset_manifest.json` --
this file hard-codes neither, so it cannot pass by agreeing with a stale
copy of what it is checking. `test_sealed_bytes_match_the_recorded_manifest_hash`
runs first in intent: if the sealed file on disk is not the file the
manifest describes, every comparison below is vacuous, and that is
reported as its own failure rather than folded into the round-trip
result.

**What this does not assert.** Nothing about research validity, nothing
about the Seal's git-tree comparison (that is
`tests/test_sealed_archive_integrity.py`), and nothing about any archive
other than `reference_h4`. It reads the archive; it never writes to it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

import pytest

from core.analytics.persistence.etf_snapshot import etf_to_row, row_to_etf
from core.governance.canonical_jsonl import (
    read_canonical_jsonl,
    sha256_of_file,
    write_canonical_jsonl,
)
from core.governance.dataset_manifest import DatasetEntry, parse_dataset_manifest
from core.market_data.persistence.snapshot_rows import (
    price_bar_to_row,
    row_to_price_bar,
    row_to_trading_session,
    trading_session_to_row,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SEALED_CYCLE_DIR = REPO_ROOT / "research_archive" / "reference_h4"
SEALED_MANIFEST_PATH = SEALED_CYCLE_DIR / "dataset_manifest.json"

# (source_table, row -> domain object, domain object -> row). The pair is
# applied in that order, so a conversion that loses a field on the way in
# cannot be compensated for by one that invents it on the way out.
ROUND_TRIPS: tuple[tuple[str, Callable[[Mapping[str, Any]], Any], Callable[[Any], dict[str, Any]]], ...] = (
    ("ETF", row_to_etf, etf_to_row),
    ("TradingSession", row_to_trading_session, trading_session_to_row),
    ("PriceBar", row_to_price_bar, price_bar_to_row),
)

_SOURCE_TABLES = tuple(source_table for source_table, _, _ in ROUND_TRIPS)


def _manifest_entry(source_table: str) -> DatasetEntry:
    manifest = parse_dataset_manifest(SEALED_MANIFEST_PATH)
    entries = [entry for entry in manifest.datasets if entry.source_table == source_table]
    assert len(entries) == 1, (
        f"expected exactly one {source_table!r} entry in {SEALED_MANIFEST_PATH}, found {len(entries)}"
    )
    return entries[0]


@pytest.mark.parametrize("source_table", _SOURCE_TABLES)
def test_sealed_bytes_match_the_recorded_manifest_hash(source_table: str) -> None:
    """The precondition every other assertion in this file rests on: the
    snapshot file being compared against is the one the sealed manifest
    describes. Without this, replacing a snapshot file with a
    re-serialized copy would make the round-trip tests below pass while
    proving nothing."""
    entry = _manifest_entry(source_table)
    snapshot_path = SEALED_CYCLE_DIR / entry.snapshot_path

    assert snapshot_path.is_file(), f"sealed snapshot missing: {snapshot_path}"
    assert sha256_of_file(snapshot_path) == entry.content_hash
    assert len(read_canonical_jsonl(snapshot_path)) == entry.row_count


@pytest.mark.parametrize(("source_table", "to_object", "to_row"), ROUND_TRIPS)
def test_current_serialization_reproduces_the_sealed_snapshot_bytes(
    source_table: str,
    to_object: Callable[[Mapping[str, Any]], Any],
    to_row: Callable[[Any], dict[str, Any]],
    tmp_path: Path,
) -> None:
    """The C4 gate. Re-serializing the sealed rows through the current
    conversion functions must produce the sealed file's exact bytes."""
    entry = _manifest_entry(source_table)
    snapshot_path = SEALED_CYCLE_DIR / entry.snapshot_path
    sealed_bytes = snapshot_path.read_bytes()

    rows = read_canonical_jsonl(snapshot_path)
    reserialized = [to_row(to_object(row)) for row in rows]

    written = tmp_path / f"{source_table}.jsonl"
    write_canonical_jsonl(reserialized, written)

    assert written.read_bytes() == sealed_bytes, (
        f"current {source_table} snapshot serialization no longer reproduces the sealed "
        f"bytes of {snapshot_path.relative_to(REPO_ROOT).as_posix()}. The sealed archive is "
        "authoritative (AD-075); the serialization change is the defect."
    )


def test_every_sealed_snapshot_table_is_covered() -> None:
    """A fourth frozen table added to the sealed manifest without a
    round-trip pair above would leave that table's serialization
    unprotected while this file still reported success."""
    manifest = parse_dataset_manifest(SEALED_MANIFEST_PATH)

    assert {entry.source_table for entry in manifest.datasets} == set(_SOURCE_TABLES)
