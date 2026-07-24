"""Reconstruction loader (Phase 4 Architecture Amendment v1.1 SS D):

    fresh SQLite -> migrations -> Calendar -> ETF -> TradingSession -> PriceBar

``Calendar`` before ``ETF``/``TradingSession`` because both carry a
``calendar_id`` foreign key into it. ``ETF`` before ``PriceBar`` because
``PriceBar.etf_id`` is a live FK constraint against ``ETF.etf_id``,
enforced by ``PRAGMA foreign_keys=ON`` on every connection
(``core/store/connection.py``) -- this is the load-order
bug v1.0 had and v1.1 corrects.

All pre-flight validation (SS D.1) runs before the scratch database is
created or touched in any way -- fail fast, matching
``freeze_verifier``'s "never run review logic against unverified state"
precedent. Every failure here is a governance-quality error naming the
specific offending values; a raw ``sqlite3.IntegrityError`` is kept only
as an independent second line of defense (PRAGMA foreign_keys=ON), never
the primary failure mode.
"""

from __future__ import annotations

from pathlib import Path

from core.governance.calendar_definitions import CALENDAR_DEFINITIONS, ensure_calendar
from core.governance.canonical_jsonl import read_canonical_jsonl, sha256_of_file
from core.governance.dataset_manifest import DatasetEntry, DatasetManifest, parse_dataset_manifest
from core.governance.dataset_snapshots import (
    load_etf_snapshot,
    load_price_bar_snapshot,
    load_trading_session_snapshot,
    row_to_etf,
    row_to_price_bar,
    row_to_trading_session,
)
from core.store.connection import connect
from core.store.migrations import run_migrations


class ReconstructionValidationError(RuntimeError):
    """Base class for every pre-flight reconstruction failure. Every
    subclass below is raised before the scratch database is created or
    opened at all."""


class MissingSnapshotArtifactError(ReconstructionValidationError):
    """A dataset_manifest.json entry references a snapshot file that does
    not exist under the cycle directory -- an unresolvable reference,
    not a content mismatch."""


class DatasetHashMismatchError(ReconstructionValidationError):
    """A snapshot file's recomputed sha256 does not match the manifest's
    declared content_hash."""


class DatasetRowCountMismatchError(ReconstructionValidationError):
    """A snapshot file's line count does not match the manifest's
    declared row_count."""


class DuplicateTickerError(ReconstructionValidationError):
    """The ETF snapshot contains more than one row for the same ticker."""


class DuplicateEtfIdError(ReconstructionValidationError):
    """The ETF snapshot contains more than one row for the same etf_id --
    would violate the live ETF.etf_id PRIMARY KEY constraint if loading
    were attempted, caught here instead, offline, by name."""


class UnknownTradingSessionCalendarError(ReconstructionValidationError):
    """A TradingSession snapshot row references a calendar_id with no
    committed Calendar literal definition -- would violate the live
    TradingSession.calendar_id FK constraint if loading were attempted."""


class DuplicateTradingSessionError(ReconstructionValidationError):
    """The TradingSession snapshot contains more than one row for the
    same (calendar_id, session_date) -- would violate the live
    TradingSession PRIMARY KEY constraint if loading were attempted."""


class MalformedSnapshotRowError(ReconstructionValidationError):
    """A snapshot row's canonical JSONL shape does not parse into its
    typed domain object (missing/invalid field) -- caught here, offline,
    in preflight, before the scratch database is created, rather than
    surfacing as a raw exception during the DB-mutation load step."""


class MissingExpectedTickerError(ReconstructionValidationError):
    """The ETF snapshot does not cover a ticker the pinned experiment's
    own universe expects -- a hash match alone confirms the file didn't
    change, not that it still covers the universe the experiment code
    will iterate over."""


class OrphanPriceBarError(ReconstructionValidationError):
    """A PriceBar snapshot row's etf_id does not appear in the ETF
    snapshot -- would violate the live PriceBar.etf_id FK constraint if
    loading were attempted, caught here instead, offline, by name."""


class UnknownEtfCalendarError(ReconstructionValidationError):
    """An ETF snapshot row references a calendar_id with no committed
    Calendar literal definition -- would violate the live ETF.calendar_id
    FK constraint if loading were attempted."""


class ScratchDatabaseExistsError(ReconstructionValidationError):
    """`db_path` already exists. Reconstruction always targets a fresh
    scratch path -- never the live database, never a leftover scratch
    file from a previous attempt."""


def _verify_dataset_integrity(entry: DatasetEntry, cycle_dir: Path) -> Path:
    snapshot_path = cycle_dir / entry.snapshot_path
    if not snapshot_path.is_file():
        raise MissingSnapshotArtifactError(
            f"dataset {entry.dataset_id!r}: snapshot file not found at {snapshot_path}"
        )

    actual_hash = sha256_of_file(snapshot_path)
    if actual_hash != entry.content_hash:
        raise DatasetHashMismatchError(
            f"dataset {entry.dataset_id!r}: content_hash mismatch -- manifest declares "
            f"{entry.content_hash}, snapshot file {snapshot_path} actually hashes to {actual_hash}"
        )

    row_count = len(read_canonical_jsonl(snapshot_path))
    if row_count != entry.row_count:
        raise DatasetRowCountMismatchError(
            f"dataset {entry.dataset_id!r}: manifest declares row_count={entry.row_count}, "
            f"snapshot file {snapshot_path} actually has {row_count} row(s)"
        )
    return snapshot_path


def preflight_validate(
    manifest: DatasetManifest,
    cycle_dir: Path,
    *,
    expected_tickers: set[str] | None = None,
) -> dict[str, Path]:
    """Every check in SS D.1, run purely offline against the manifest and
    snapshot files on disk -- never opens or touches any database.
    Returns the verified snapshot path for each of the three required
    source tables, keyed by source_table."""
    paths = {entry.source_table: _verify_dataset_integrity(entry, cycle_dir) for entry in manifest.datasets}

    etf_rows = read_canonical_jsonl(paths["ETF"])

    ticker_counts: dict[str, int] = {}
    etf_id_counts: dict[str, int] = {}
    for row in etf_rows:
        ticker_counts[row["ticker"]] = ticker_counts.get(row["ticker"], 0) + 1
        etf_id_counts[row["etf_id"]] = etf_id_counts.get(row["etf_id"], 0) + 1
    duplicate_tickers = sorted(ticker for ticker, count in ticker_counts.items() if count > 1)
    if duplicate_tickers:
        raise DuplicateTickerError(f"ETF snapshot has duplicate ticker(s): {duplicate_tickers}")

    duplicate_etf_ids = sorted(etf_id for etf_id, count in etf_id_counts.items() if count > 1)
    if duplicate_etf_ids:
        raise DuplicateEtfIdError(f"ETF snapshot has duplicate etf_id(s): {duplicate_etf_ids}")

    if expected_tickers is not None:
        missing_tickers = sorted(expected_tickers - set(ticker_counts))
        if missing_tickers:
            raise MissingExpectedTickerError(
                "ETF snapshot is missing ticker(s) the pinned experiment's own universe "
                f"expects: {missing_tickers}"
            )

    unknown_calendars = sorted({row["calendar_id"] for row in etf_rows} - set(CALENDAR_DEFINITIONS))
    if unknown_calendars:
        raise UnknownEtfCalendarError(
            f"ETF snapshot references calendar_id(s) with no committed Calendar literal "
            f"definition: {unknown_calendars}"
        )

    for row in etf_rows:
        try:
            row_to_etf(row)
        except (KeyError, ValueError, TypeError) as exc:
            raise MalformedSnapshotRowError(f"ETF snapshot row {row!r} does not parse: {exc}") from exc

    trading_session_rows = read_canonical_jsonl(paths["TradingSession"])

    unknown_session_calendars = sorted(
        {row["calendar_id"] for row in trading_session_rows} - set(CALENDAR_DEFINITIONS)
    )
    if unknown_session_calendars:
        raise UnknownTradingSessionCalendarError(
            "TradingSession snapshot references calendar_id(s) with no committed Calendar "
            f"literal definition: {unknown_session_calendars}"
        )

    session_key_counts: dict[tuple[str, str], int] = {}
    for row in trading_session_rows:
        key = (row["calendar_id"], row["session_date"])
        session_key_counts[key] = session_key_counts.get(key, 0) + 1
    duplicate_session_keys = sorted(key for key, count in session_key_counts.items() if count > 1)
    if duplicate_session_keys:
        raise DuplicateTradingSessionError(
            f"TradingSession snapshot has duplicate (calendar_id, session_date): {duplicate_session_keys}"
        )

    for row in trading_session_rows:
        try:
            row_to_trading_session(row)
        except (KeyError, ValueError, TypeError) as exc:
            raise MalformedSnapshotRowError(
                f"TradingSession snapshot row {row!r} does not parse: {exc}"
            ) from exc

    etf_ids = {row["etf_id"] for row in etf_rows}
    price_bar_rows = read_canonical_jsonl(paths["PriceBar"])
    orphan_etf_ids = sorted({row["etf_id"] for row in price_bar_rows} - etf_ids)
    if orphan_etf_ids:
        raise OrphanPriceBarError(
            f"PriceBar snapshot references etf_id(s) absent from the ETF snapshot: {orphan_etf_ids}"
        )

    for row in price_bar_rows:
        try:
            row_to_price_bar(row)
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            raise MalformedSnapshotRowError(f"PriceBar snapshot row {row!r} does not parse: {exc}") from exc

    return paths


def reconstruct_database(
    db_path: Path,
    migrations_dir: Path,
    cycle_dir: Path,
    manifest_path: Path,
    *,
    calendar_id: str = "XNYS",
    expected_tickers: set[str] | None = None,
) -> None:
    """Build a fresh scratch database from frozen dataset artifacts:
    migrations -> Calendar -> ETF -> TradingSession -> PriceBar.

    Every pre-flight check runs and can raise before `db_path` is ever
    created or opened -- including the `db_path`-already-exists check,
    which runs first of all.
    """
    if db_path.exists():
        raise ScratchDatabaseExistsError(
            f"{db_path} already exists -- reconstruction requires a fresh scratch path, "
            "never the live database and never a leftover scratch file."
        )

    manifest = parse_dataset_manifest(manifest_path)
    snapshot_paths = preflight_validate(manifest, cycle_dir, expected_tickers=expected_tickers)

    conn = connect(db_path)
    try:
        run_migrations(conn, migrations_dir)
        with conn:
            ensure_calendar(conn, calendar_id)
            load_etf_snapshot(conn, snapshot_paths["ETF"])
            load_trading_session_snapshot(conn, snapshot_paths["TradingSession"])
            load_price_bar_snapshot(conn, snapshot_paths["PriceBar"])
    finally:
        conn.close()
