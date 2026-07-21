from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from core.governance.identity_verification import (
    FROZEN_IDENTITY_TABLES,
    FrozenIdentityChangedError,
    assert_frozen_identity_unchanged,
    snapshot_identity_state,
)
from core.market_data.domain.models import ETF, Calendar, PriceBar
from core.market_data.persistence.repository import insert_calendar, insert_etf, insert_price_bar
from core.shared.money import Money

CALENDAR_ID = "XNYS"


def _calendar() -> Calendar:
    return Calendar(
        calendar_id=CALENDAR_ID, name="New York Stock Exchange", exchange="NYSE", timezone="America/New_York"
    )


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
        open=Money(Decimal("1.00"), "USD"),
        high=Money(Decimal("1.00"), "USD"),
        low=Money(Decimal("1.00"), "USD"),
        close=Money(Decimal("1.00"), "USD"),
        volume=1,
        source="yahoo_finance",
        ingested_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )


def test_frozen_identity_tables_are_exactly_the_four_named() -> None:
    assert FROZEN_IDENTITY_TABLES == ("Calendar", "ETF", "TradingSession", "PriceBar")


def test_identical_state_passes(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _calendar())
    insert_etf(conn, _etf("SPY", "etf-1"))

    before = snapshot_identity_state(conn)
    after = snapshot_identity_state(conn)

    assert_frozen_identity_unchanged(before, after)  # must not raise


def test_new_etf_row_is_detected_as_a_change(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _calendar())
    before = snapshot_identity_state(conn)

    insert_etf(conn, _etf("SPY", "etf-1"))
    after = snapshot_identity_state(conn)

    with pytest.raises(FrozenIdentityChangedError, match="ETF"):
        assert_frozen_identity_unchanged(before, after)


def test_new_pricebar_row_is_detected_as_a_change(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _calendar())
    insert_etf(conn, _etf("SPY", "etf-1"))
    before = snapshot_identity_state(conn)

    insert_price_bar(conn, _bar("etf-1", date(2026, 7, 13), "bar-1"))
    after = snapshot_identity_state(conn)

    with pytest.raises(FrozenIdentityChangedError, match="PriceBar"):
        assert_frozen_identity_unchanged(before, after)


def test_row_count_delta_is_named_in_the_error(conn: sqlite3.Connection) -> None:
    insert_calendar(conn, _calendar())
    before = snapshot_identity_state(conn)

    insert_etf(conn, _etf("SPY", "etf-1"))
    insert_etf(conn, _etf("QQQ", "etf-2"))
    after = snapshot_identity_state(conn)

    with pytest.raises(FrozenIdentityChangedError, match=r"row_count 0 -> 2"):
        assert_frozen_identity_unchanged(before, after)


def test_derived_table_changes_are_invisible_to_this_check(conn: sqlite3.Connection) -> None:
    """IndicatorValue/Score/DimensionScore are not in FROZEN_IDENTITY_TABLES
    at all -- inserting into them must never be detected here, since they
    are required to gain new rows on every successful run (amendment
    SS F.3's explicit scope boundary)."""
    insert_calendar(conn, _calendar())
    insert_etf(conn, _etf("SPY", "etf-1"))
    before = snapshot_identity_state(conn)

    conn.execute(
        "INSERT INTO IndicatorDefinition (indicator_definition_id, name, version, parameters, created_at) "
        "VALUES ('def-1', 'SMA', 1, '{}', '2026-07-20T00:00:00+00:00')"
    )
    conn.execute(
        "INSERT INTO IndicatorValue (indicator_value_id, indicator_definition_id, etf_id, session_date, "
        "value, computed_at) VALUES ('val-1', 'def-1', 'etf-1', '2026-07-13', '1.0', '2026-07-20T00:00:00+00:00')"
    )
    conn.commit()
    after = snapshot_identity_state(conn)

    assert_frozen_identity_unchanged(before, after)  # must not raise
