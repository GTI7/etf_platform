from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from core.governance.canonical_jsonl import sha256_of_file, write_canonical_jsonl
from core.governance.dataset_manifest import MANIFEST_SCHEMA_VERSION
from core.governance.dataset_snapshots import etf_to_row, price_bar_to_row, trading_session_to_row
from core.governance.reconstruction_loader import (
    DatasetHashMismatchError,
    DatasetRowCountMismatchError,
    DuplicateEtfIdError,
    DuplicateTradingSessionError,
    MalformedSnapshotRowError,
    MissingSnapshotArtifactError,
    ScratchDatabaseExistsError,
    UnknownEtfCalendarError,
    UnknownTradingSessionCalendarError,
    reconstruct_database,
)
from core.market_data.domain.models import ETF, PriceBar, TradingSession
from core.shared.money import Money

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _etf(ticker: str, etf_id: str, calendar_id: str = "XNYS") -> ETF:
    return ETF(
        etf_id=etf_id,
        ticker=ticker,
        name=f"{ticker} Fund",
        currency="USD",
        calendar_id=calendar_id,
        created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )


def _bar(etf_id: str, session_date: date, price_bar_id: str) -> PriceBar:
    return PriceBar(
        price_bar_id=price_bar_id,
        etf_id=etf_id,
        session_date=session_date,
        open=Money(Decimal("1.00"), "USD"),
        high=Money(Decimal("1.00"), "USD"),
        low=Money(Decimal("1.00"), "USD"),
        close=Money(Decimal("1.00"), "USD"),
        volume=1,
        source="yahoo_finance",
        ingested_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )


def _session(session_date: date, calendar_id: str = "XNYS") -> TradingSession:
    return TradingSession(
        calendar_id=calendar_id, session_date=session_date, is_trading_day=True, close_time_utc=None
    )


def _write_entry(cycle_dir: Path, source_table: str, filename: str, rows: list[dict]) -> dict:
    path = cycle_dir / "dataset_hashes" / filename
    write_canonical_jsonl(rows, path)
    return {
        "dataset_id": f"{source_table.lower()}_v1",
        "type": "test_fixture_data",
        "source_table": source_table,
        "row_count": len(rows),
        "snapshot_path": f"dataset_hashes/{filename}",
        "content_hash": sha256_of_file(path),
        "schema_version": 1,
    }


def _build_cycle(
    tmp_path: Path,
    *,
    etfs: list[ETF],
    sessions: list[TradingSession] | None = None,
    bars: list[PriceBar] | None = None,
) -> tuple[Path, Path]:
    cycle_dir = tmp_path / "cycle"
    (cycle_dir / "dataset_hashes").mkdir(parents=True)
    entries = [
        _write_entry(cycle_dir, "ETF", "etf.jsonl", [etf_to_row(e) for e in etfs]),
        _write_entry(
            cycle_dir, "TradingSession", "trading_session.jsonl",
            [trading_session_to_row(s) for s in (sessions or [])],
        ),
        _write_entry(cycle_dir, "PriceBar", "pricebar.jsonl", [price_bar_to_row(b) for b in (bars or [])]),
    ]
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project_id": "test_cycle",
        "generated_at": "2026-08-01T00:00:00+00:00",
        "datasets": entries,
    }
    manifest_path = cycle_dir / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return cycle_dir, manifest_path


def test_content_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    # Corrupt the snapshot file after the manifest's hash was already computed.
    (cycle_dir / "dataset_hashes" / "etf.jsonl").write_bytes(b'{"tampered":true}\n')
    db_path = tmp_path / "scratch.db"

    with pytest.raises(DatasetHashMismatchError):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()


def test_row_count_mismatch_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["datasets"]:
        if entry["source_table"] == "ETF":
            entry["row_count"] = 999  # declared count no longer matches the file
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    db_path = tmp_path / "scratch.db"

    with pytest.raises(DatasetRowCountMismatchError):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()


def test_missing_snapshot_file_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    (cycle_dir / "dataset_hashes" / "etf.jsonl").unlink()
    db_path = tmp_path / "scratch.db"

    with pytest.raises(MissingSnapshotArtifactError):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()


def test_unknown_calendar_id_on_an_etf_row_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(
        tmp_path, etfs=[_etf("SPY", "etf-spy", calendar_id="NOT_A_REAL_CALENDAR")]
    )
    db_path = tmp_path / "scratch.db"

    with pytest.raises(UnknownEtfCalendarError, match="NOT_A_REAL_CALENDAR"):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()


def test_refuses_to_reconstruct_into_an_existing_scratch_path(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    db_path = tmp_path / "scratch.db"
    db_path.write_bytes(b"leftover from a previous attempt")

    with pytest.raises(ScratchDatabaseExistsError):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)


def test_successful_reconstruction_follows_the_full_load_order(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(
        tmp_path,
        etfs=[_etf("SPY", "etf-spy")],
        bars=[_bar("etf-spy", date(2026, 7, 13), "bar-1")],
    )
    db_path = tmp_path / "scratch.db"

    reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert db_path.exists()


def test_duplicate_etf_id_in_etf_snapshot_is_rejected(tmp_path: Path) -> None:
    # Distinct tickers, same etf_id -- duplicate-ticker detection alone
    # would not catch this; the ETF.etf_id PRIMARY KEY would still be
    # violated by a raw sqlite3.IntegrityError at load time if this check
    # didn't exist.
    cycle_dir, manifest_path = _build_cycle(
        tmp_path, etfs=[_etf("SPY", "etf-dup"), _etf("QQQ", "etf-dup")]
    )
    db_path = tmp_path / "scratch.db"

    with pytest.raises(DuplicateEtfIdError, match="etf-dup"):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()


def test_unknown_calendar_id_on_a_trading_session_row_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(
        tmp_path,
        etfs=[_etf("SPY", "etf-spy")],
        sessions=[_session(date(2026, 7, 13), calendar_id="NOT_A_REAL_CALENDAR")],
    )
    db_path = tmp_path / "scratch.db"

    with pytest.raises(UnknownTradingSessionCalendarError, match="NOT_A_REAL_CALENDAR"):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()


def test_duplicate_trading_session_key_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    # Write a TradingSession snapshot with two rows for the same
    # (calendar_id, session_date) directly -- would violate the live
    # TradingSession PRIMARY KEY at load time if not caught in preflight.
    rows = [
        trading_session_to_row(_session(date(2026, 7, 13))),
        trading_session_to_row(_session(date(2026, 7, 13))),
    ]
    path = cycle_dir / "dataset_hashes" / "trading_session.jsonl"
    write_canonical_jsonl(rows, path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["datasets"]:
        if entry["source_table"] == "TradingSession":
            entry["row_count"] = len(rows)
            entry["content_hash"] = sha256_of_file(path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    db_path = tmp_path / "scratch.db"

    with pytest.raises(DuplicateTradingSessionError, match="XNYS"):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()


def test_malformed_pricebar_row_is_rejected_before_db_mutation(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    # A row missing a required field (open_amount) -- must be caught by
    # preflight row-shape parsing, not surface as a raw KeyError/
    # decimal.InvalidOperation while loading into the database.
    bad_row = price_bar_to_row(_bar("etf-spy", date(2026, 7, 13), "bar-1"))
    del bad_row["open_amount"]
    path = cycle_dir / "dataset_hashes" / "pricebar.jsonl"
    write_canonical_jsonl([bad_row], path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["datasets"]:
        if entry["source_table"] == "PriceBar":
            entry["row_count"] = 1
            entry["content_hash"] = sha256_of_file(path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    db_path = tmp_path / "scratch.db"

    with pytest.raises(MalformedSnapshotRowError):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()
