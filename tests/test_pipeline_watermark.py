from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone

import pytest

from core.market_data.ingestion.pipeline_run import run_pipeline
from core.market_data.persistence.repository import get_last_successful_pipeline_date
from core.shared.clock import FixedClock

PIPELINE_NAME = "daily_price_ingestion"


def test_watermark_advances_only_after_success(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) is None

    with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
        pass

    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) == date(2026, 7, 14)


def test_failed_run_does_not_advance_watermark(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
        pass
    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) == date(2026, 7, 14)

    later_clock = FixedClock(datetime(2026, 7, 15, tzinfo=timezone.utc))
    with pytest.raises(RuntimeError):
        with run_pipeline(conn, later_clock, PIPELINE_NAME, date(2026, 7, 15)):
            raise RuntimeError("boom")

    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) == date(2026, 7, 14)


def test_repeated_execution_is_safe(conn: sqlite3.Connection) -> None:
    clock = FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc))

    for _ in range(3):
        with run_pipeline(conn, clock, PIPELINE_NAME, date(2026, 7, 14)):
            pass

    assert get_last_successful_pipeline_date(conn, PIPELINE_NAME) == date(2026, 7, 14)
