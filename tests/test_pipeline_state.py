from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone

import pytest

from core.market_data.domain.models import IngestionStatus
from core.market_data.ingestion.pipeline_run import run_pipeline
from core.market_data.persistence.repository import (
    get_last_successful_pipeline_date,
    get_latest_ingestion_run,
    get_pipeline_state,
)
from core.shared.clock import FixedClock

PIPELINE_NAME = "daily_price_ingestion"


def _success_count(conn: sqlite3.Connection, pipeline_name: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM IngestionRun WHERE pipeline_name = ? AND status = 'success'",
        (pipeline_name,),
    ).fetchone()
    return row["n"]


def test_pipeline_state_created_only_after_success(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    assert get_pipeline_state(conn, PIPELINE_NAME) is None

    with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
        pass

    state = get_pipeline_state(conn, PIPELINE_NAME)
    assert state is not None
    assert state.last_successful_session == date(2026, 7, 14)


def test_pipeline_state_untouched_on_failure(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    with pytest.raises(RuntimeError):
        with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
            raise RuntimeError("boom")

    assert get_pipeline_state(conn, PIPELINE_NAME) is None
    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) is None


def test_duplicate_successful_runs_of_same_session_are_idempotent(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    for _ in range(3):
        with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
            pass

    # PipelineState collapses to a single row / value ...
    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) == date(2026, 7, 14)
    # ... while IngestionRun keeps the full history of every attempt.
    assert _success_count(conn, PIPELINE_NAME) == 3


def test_ingestion_run_history_is_preserved_across_pipeline_state_updates(
    conn: sqlite3.Connection,
) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
        pass

    later_clock = FixedClock(datetime(2026, 7, 15, tzinfo=timezone.utc))
    with run_pipeline(conn, later_clock, PIPELINE_NAME, date(2026, 7, 15)):
        pass

    rows = conn.execute(
        "SELECT pipeline_date, status FROM IngestionRun WHERE pipeline_name = ? ORDER BY pipeline_date",
        (PIPELINE_NAME,),
    ).fetchall()
    assert [(r["pipeline_date"], r["status"]) for r in rows] == [
        ("2026-07-14", "success"),
        ("2026-07-15", "success"),
    ]


def test_pipeline_watermarks_are_independent_per_pipeline(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    with run_pipeline(conn, clock, "daily_price_ingestion", date(2026, 7, 14)):
        pass
    with run_pipeline(conn, clock, "daily_macro_ingestion", date(2026, 7, 10)):
        pass

    assert get_last_successful_pipeline_date(conn, "daily_price_ingestion") == date(2026, 7, 14)
    assert get_last_successful_pipeline_date(conn, "daily_macro_ingestion") == date(2026, 7, 10)


def test_watermark_does_not_regress_on_out_of_order_backfill(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))
    with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
        pass

    backfill_clock = FixedClock(datetime(2026, 7, 15, tzinfo=timezone.utc))
    with run_pipeline(conn, backfill_clock, PIPELINE_NAME, date(2026, 7, 10)):
        pass

    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) == date(2026, 7, 14)


def test_get_latest_ingestion_run_returns_none_when_no_run_exists(
    conn: sqlite3.Connection,
) -> None:
    assert get_latest_ingestion_run(conn, PIPELINE_NAME) is None


def test_get_latest_ingestion_run_returns_successful_run(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
        pass

    run = get_latest_ingestion_run(conn, PIPELINE_NAME)
    assert run is not None
    assert run.pipeline_name == PIPELINE_NAME
    assert run.pipeline_date == date(2026, 7, 14)
    assert run.status == IngestionStatus.SUCCESS
    assert run.completed_at is not None
    assert run.error_message is None


def test_get_latest_ingestion_run_returns_failed_run_with_error_message(
    conn: sqlite3.Connection,
) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    with pytest.raises(RuntimeError):
        with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
            raise RuntimeError("boom")

    run = get_latest_ingestion_run(conn, PIPELINE_NAME)
    assert run is not None
    assert run.status == IngestionStatus.FAILED
    assert run.error_message == "boom"


def test_get_latest_ingestion_run_returns_most_recently_started_attempt(
    conn: sqlite3.Connection,
) -> None:
    """A later out-of-order backfill run for an earlier session_date is
    still the most recently *started* attempt -- get_latest_ingestion_run
    must reflect that, not the latest pipeline_date processed."""
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))
    with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
        pass

    backfill_clock = FixedClock(datetime(2026, 7, 15, tzinfo=timezone.utc))
    with run_pipeline(conn, backfill_clock, PIPELINE_NAME, date(2026, 7, 10)):
        pass

    run = get_latest_ingestion_run(conn, PIPELINE_NAME)
    assert run is not None
    assert run.pipeline_date == date(2026, 7, 10)
    assert run.started_at == datetime(2026, 7, 15, tzinfo=timezone.utc)


def test_get_latest_ingestion_run_isolates_by_pipeline_name(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))
    with run_pipeline(conn, clock, "daily_price_ingestion", date(2026, 7, 14)):
        pass

    assert get_latest_ingestion_run(conn, "daily_macro_ingestion") is None
    other_run = get_latest_ingestion_run(conn, "daily_price_ingestion")
    assert other_run is not None
    assert other_run.pipeline_name == "daily_price_ingestion"
