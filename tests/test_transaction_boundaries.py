from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone

import pytest

from core.market_data.ingestion.pipeline_run import run_pipeline
from core.market_data.persistence.repository import get_last_successful_pipeline_date
from core.shared.clock import FixedClock

PIPELINE_NAME = "daily_price_ingestion"


def _ingestion_run_status(conn: sqlite3.Connection, pipeline_name: str) -> str:
    row = conn.execute(
        "SELECT status FROM IngestionRun WHERE pipeline_name = ?", (pipeline_name,)
    ).fetchone()
    assert row is not None
    return row["status"]


def test_watermark_failure_rolls_back_ingestion_run_completion(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reproduces the atomicity bug found in the Phase 0 audit.

    complete_ingestion_run() and advance_pipeline_watermark() must succeed
    or fail together. Before the fix, each committed independently, so a
    failure here would still leave IngestionRun showing 'success' while the
    watermark never advanced -- this test fails against that implementation
    and passes once both writes share one transaction.
    """
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated failure advancing the watermark")

    monkeypatch.setattr(
        "core.market_data.ingestion.pipeline_run.advance_pipeline_watermark", _boom
    )

    with pytest.raises(RuntimeError):
        with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
            pass  # the pipeline body itself succeeds

    # The completion UPDATE must have been rolled back along with the
    # failed watermark advance: the run is left exactly as it was before
    # the (single) completion transaction ran, i.e. still 'running'.
    assert _ingestion_run_status(conn, PIPELINE_NAME) == "running"
    assert _ingestion_run_status(conn, PIPELINE_NAME) != "success"

    # The watermark must not have advanced.
    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) is None
