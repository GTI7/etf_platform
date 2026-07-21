"""Reproduction-contract tests (Phase 4 Architecture Amendment v1.1).

Covers the mandate's minimum required scenarios end-to-end against
``core.governance.reconstruction_loader``, ``network_guard``, and
``identity_verification`` directly -- no real H4 research cycle exists
in this repository yet (this is infrastructure, not a new hypothesis
cycle), so every fixture here is synthetic, built the same way a real
extraction tool would build one: domain objects -> canonical JSONL rows
-> a hand-built dataset_manifest.json with real recomputed hashes.

Never touches the network, the real research_archive/ directory, or any
experiments/*.py script.
"""

from __future__ import annotations

import json
import socket
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from core.governance.canonical_jsonl import sha256_of_file, write_canonical_jsonl
from core.governance.dataset_manifest import MANIFEST_SCHEMA_VERSION
from core.governance.dataset_snapshots import (
    etf_to_row,
    fetch_all_etfs,
    fetch_all_price_bars,
    price_bar_to_row,
    trading_session_to_row,
)
from core.governance.identity_verification import (
    FrozenIdentityChangedError,
    assert_frozen_identity_unchanged,
    snapshot_identity_state,
)
from core.governance.network_guard import OfflineViolationError, offline_guard
from core.governance.reconstruction_loader import (
    DuplicateTickerError,
    MissingExpectedTickerError,
    OrphanPriceBarError,
    reconstruct_database,
)
from core.market_data.domain.models import ETF, PriceBar, TradingSession
from core.market_data.persistence.database import connect
from core.market_data.persistence.repository import insert_etf
from core.shared.money import Money

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
CALENDAR_ID = "XNYS"


def _etf(ticker: str, etf_id: str) -> ETF:
    return ETF(
        etf_id=etf_id,
        ticker=ticker,
        name=f"{ticker} Fund",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
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


def _session(session_date: date) -> TradingSession:
    return TradingSession(
        calendar_id=CALENDAR_ID, session_date=session_date, is_trading_day=True, close_time_utc=None
    )


def _write_dataset_entry(cycle_dir: Path, source_table: str, filename: str, rows: list[dict]) -> dict:
    path = cycle_dir / "dataset_hashes" / filename
    write_canonical_jsonl(rows, path)
    return {
        "dataset_id": f"{source_table.lower()}_test_v1",
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
    """Build a synthetic cycle directory: three snapshot JSONL files under
    dataset_hashes/ plus a schema-v3 dataset_manifest.json whose hashes
    and row counts are freshly, correctly computed from those files."""
    cycle_dir = tmp_path / "cycle"
    (cycle_dir / "dataset_hashes").mkdir(parents=True)

    entries = [
        _write_dataset_entry(cycle_dir, "ETF", "etf.jsonl", [etf_to_row(e) for e in etfs]),
        _write_dataset_entry(
            cycle_dir, "TradingSession", "trading_session.jsonl",
            [trading_session_to_row(s) for s in (sessions or [])],
        ),
        _write_dataset_entry(
            cycle_dir, "PriceBar", "pricebar.jsonl", [price_bar_to_row(b) for b in (bars or [])]
        ),
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


# --- ETF snapshot loading + ETF FK preservation -----------------------------


def test_etf_snapshot_loads_preserving_etf_id_and_pricebar_fk_holds(tmp_path: Path) -> None:
    frozen_etf_id = "3f2a1b9c4d5e4f6a8b7c9d0e1f2a3b4c"
    cycle_dir, manifest_path = _build_cycle(
        tmp_path,
        etfs=[_etf("SPY", frozen_etf_id)],
        sessions=[_session(date(2026, 7, 13))],
        bars=[_bar(frozen_etf_id, date(2026, 7, 13), "bar-1")],
    )
    db_path = tmp_path / "scratch.db"

    reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    conn = connect(db_path)
    try:
        loaded_etfs = fetch_all_etfs(conn)
        assert len(loaded_etfs) == 1
        assert loaded_etfs[0].etf_id == frozen_etf_id  # never regenerated via uuid4()

        loaded_bars = fetch_all_price_bars(conn)
        assert len(loaded_bars) == 1
        # PriceBar.etf_id FK against ETF.etf_id resolved -- no
        # IntegrityError, because ETF was loaded before PriceBar.
        assert loaded_bars[0].etf_id == frozen_etf_id
    finally:
        conn.close()


# --- Duplicate ticker rejection ----------------------------------------------


def test_duplicate_ticker_in_etf_snapshot_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(
        tmp_path, etfs=[_etf("SPY", "etf-1"), _etf("SPY", "etf-2")]
    )
    db_path = tmp_path / "scratch.db"

    with pytest.raises(DuplicateTickerError, match="SPY"):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()  # must fail before the scratch database is even created


# --- Orphan PriceBar rejection -----------------------------------------------


def test_pricebar_referencing_unknown_etf_id_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(
        tmp_path,
        etfs=[_etf("SPY", "etf-spy")],
        bars=[_bar("etf-does-not-exist", date(2026, 7, 13), "bar-1")],
    )
    db_path = tmp_path / "scratch.db"

    with pytest.raises(OrphanPriceBarError, match="etf-does-not-exist"):
        reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    assert not db_path.exists()


# --- Missing (expected) ETF rejection ----------------------------------------


def test_missing_expected_ticker_is_rejected(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    db_path = tmp_path / "scratch.db"

    with pytest.raises(MissingExpectedTickerError, match="QQQ"):
        reconstruct_database(
            db_path, MIGRATIONS_DIR, cycle_dir, manifest_path, expected_tickers={"SPY", "QQQ"}
        )

    assert not db_path.exists()


# --- Network attempt rejection -----------------------------------------------


def test_network_attempt_during_reproduction_is_rejected() -> None:
    with offline_guard():
        with pytest.raises(OfflineViolationError):
            socket.create_connection(("example.invalid", 80))


# --- Derived tables allowed to change / frozen tables cannot change ----------


def test_derived_tables_are_allowed_to_change_across_a_run(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    db_path = tmp_path / "scratch.db"
    reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    conn = connect(db_path)
    try:
        before = snapshot_identity_state(conn)

        # IndicatorValue/Score/DimensionScore are *required* to gain new
        # rows on every successful reproduction -- simulate that here.
        conn.execute(
            "INSERT INTO IndicatorDefinition (indicator_definition_id, name, version, parameters, created_at) "
            "VALUES ('def-1', 'SMA', 1, '{}', '2026-07-20T00:00:00+00:00')"
        )
        conn.execute(
            "INSERT INTO IndicatorValue (indicator_value_id, indicator_definition_id, etf_id, session_date, "
            "value, computed_at) VALUES "
            "('val-1', 'def-1', 'etf-spy', '2026-07-13', '1.0', '2026-07-20T00:00:00+00:00')"
        )
        conn.commit()
        after = snapshot_identity_state(conn)

        assert_frozen_identity_unchanged(before, after)  # must not raise
    finally:
        conn.close()


def test_frozen_tables_cannot_change_across_a_run(tmp_path: Path) -> None:
    cycle_dir, manifest_path = _build_cycle(tmp_path, etfs=[_etf("SPY", "etf-spy")])
    db_path = tmp_path / "scratch.db"
    reconstruct_database(db_path, MIGRATIONS_DIR, cycle_dir, manifest_path)

    conn = connect(db_path)
    try:
        before = snapshot_identity_state(conn)

        # The exact v1.0 defect this amendment fixes: a silent
        # _ensure_etfs-style insert of a new ETF row during what should
        # be a pure regeneration run against a reconstructed database.
        insert_etf(conn, _etf("QQQ", "etf-qqq-silently-minted"))
        conn.commit()
        after = snapshot_identity_state(conn)

        with pytest.raises(FrozenIdentityChangedError, match="ETF"):
            assert_frozen_identity_unchanged(before, after)
    finally:
        conn.close()
