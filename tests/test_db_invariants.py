from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

import pytest

from core.market_data.domain.models import ETF, Calendar
from core.market_data.persistence.repository import insert_calendar, insert_etf


def _make_etf(conn: sqlite3.Connection) -> ETF:
    insert_calendar(
        conn,
        Calendar(
            calendar_id="XNYS",
            name="New York Stock Exchange",
            exchange="NYSE",
            timezone="America/New_York",
        ),
    )
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker="SPY",
        name="SPDR S&P 500",
        currency="USD",
        calendar_id="XNYS",
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def test_pricebar_rejects_negative_volume(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO PriceBar (
                price_bar_id, etf_id, session_date,
                open_amount, high_amount, low_amount, close_amount,
                volume, currency, source, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                etf.etf_id,
                "2026-07-14",
                "450.00",
                "450.00",
                "450.00",
                "450.00",
                -1,
                "USD",
                "test",
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def test_pricebar_accepts_zero_volume(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)

    conn.execute(
        """
        INSERT INTO PriceBar (
            price_bar_id, etf_id, session_date,
            open_amount, high_amount, low_amount, close_amount,
            volume, currency, source, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            uuid.uuid4().hex,
            etf.etf_id,
            "2026-07-14",
            "450.00",
            "450.00",
            "450.00",
            "450.00",
            0,
            "USD",
            "test",
            datetime.now(timezone.utc).isoformat(),
        ),
    )  # does not raise


def test_ingestionrun_rejects_running_status_with_completed_at_set(
    conn: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO IngestionRun (
                ingestion_run_id, pipeline_name, pipeline_date, status,
                started_at, completed_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                "daily_price_ingestion",
                "2026-07-14",
                "running",
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),  # invalid: running + completed_at set
                None,
            ),
        )


def test_ingestionrun_rejects_terminal_status_without_completed_at(
    conn: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO IngestionRun (
                ingestion_run_id, pipeline_name, pipeline_date, status,
                started_at, completed_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                "daily_price_ingestion",
                "2026-07-14",
                "success",
                datetime.now(timezone.utc).isoformat(),
                None,  # invalid: terminal status without completed_at
                None,
            ),
        )
