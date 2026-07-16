from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from core.analytics.domain.models import (
    IndicatorDefinition,
    IndicatorValue,
    serialize_parameters,
)
from core.analytics.persistence.repository import (
    get_indicator_definition,
    get_indicator_values,
    insert_indicator_definition,
    insert_indicator_value,
)
from core.market_data.domain.models import ETF, Calendar
from core.market_data.persistence.repository import insert_calendar, insert_etf

CALENDAR_ID = "XNYS"


def _make_etf(conn: sqlite3.Connection) -> ETF:
    insert_calendar(
        conn,
        Calendar(
            calendar_id=CALENDAR_ID,
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
        calendar_id=CALENDAR_ID,
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def _make_definition(name: str = "SMA", version: int = 1, window: int = 20) -> IndicatorDefinition:
    return IndicatorDefinition(
        indicator_definition_id=uuid.uuid4().hex,
        name=name,
        version=version,
        parameters=serialize_parameters({"window": window}),
        created_at=datetime.now(timezone.utc),
    )


def test_insert_and_get_indicator_definition(conn: sqlite3.Connection) -> None:
    definition = _make_definition()
    insert_indicator_definition(conn, definition)

    fetched = get_indicator_definition(conn, "SMA", 1)

    assert fetched == definition


def test_get_indicator_definition_returns_none_when_missing(conn: sqlite3.Connection) -> None:
    assert get_indicator_definition(conn, "SMA", 99) is None


def test_indicator_definition_duplicate_rejected(conn: sqlite3.Connection) -> None:
    insert_indicator_definition(conn, _make_definition())

    with pytest.raises(sqlite3.IntegrityError):
        insert_indicator_definition(conn, _make_definition())


def test_indicator_definition_different_version_is_independent(conn: sqlite3.Connection) -> None:
    insert_indicator_definition(conn, _make_definition(version=1))
    insert_indicator_definition(conn, _make_definition(version=2))  # does not raise

    assert get_indicator_definition(conn, "SMA", 1) is not None
    assert get_indicator_definition(conn, "SMA", 2) is not None


def test_indicator_value_round_trip_preserves_decimal_precision(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    definition = _make_definition()
    insert_indicator_definition(conn, definition)
    value = IndicatorValue(
        indicator_value_id=uuid.uuid4().hex,
        indicator_definition_id=definition.indicator_definition_id,
        etf_id=etf.etf_id,
        session_date=date(2026, 7, 14),
        value=Decimal("450.123456789"),
        computed_at=datetime.now(timezone.utc),
    )

    insert_indicator_value(conn, value)

    [fetched] = get_indicator_values(conn, definition.indicator_definition_id, etf.etf_id)
    assert fetched == value


def test_indicator_value_duplicate_insert_is_idempotent(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    definition = _make_definition()
    insert_indicator_definition(conn, definition)
    session_date = date(2026, 7, 14)

    for _ in range(3):
        insert_indicator_value(
            conn,
            IndicatorValue(
                indicator_value_id=uuid.uuid4().hex,
                indicator_definition_id=definition.indicator_definition_id,
                etf_id=etf.etf_id,
                session_date=session_date,
                value=Decimal("100"),
                computed_at=datetime.now(timezone.utc),
            ),
        )

    values = get_indicator_values(conn, definition.indicator_definition_id, etf.etf_id)
    assert len(values) == 1


def test_indicator_value_rejects_update(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    definition = _make_definition()
    insert_indicator_definition(conn, definition)
    value_id = uuid.uuid4().hex
    insert_indicator_value(
        conn,
        IndicatorValue(
            indicator_value_id=value_id,
            indicator_definition_id=definition.indicator_definition_id,
            etf_id=etf.etf_id,
            session_date=date(2026, 7, 14),
            value=Decimal("100"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE IndicatorValue SET value = ? WHERE indicator_value_id = ?",
            ("999", value_id),
        )


def test_indicator_value_rejects_delete(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    definition = _make_definition()
    insert_indicator_definition(conn, definition)
    value_id = uuid.uuid4().hex
    insert_indicator_value(
        conn,
        IndicatorValue(
            indicator_value_id=value_id,
            indicator_definition_id=definition.indicator_definition_id,
            etf_id=etf.etf_id,
            session_date=date(2026, 7, 14),
            value=Decimal("100"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM IndicatorValue WHERE indicator_value_id = ?", (value_id,))


def test_get_indicator_values_filters_by_date_range(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    definition = _make_definition()
    insert_indicator_definition(conn, definition)

    for day in (12, 13, 14):
        insert_indicator_value(
            conn,
            IndicatorValue(
                indicator_value_id=uuid.uuid4().hex,
                indicator_definition_id=definition.indicator_definition_id,
                etf_id=etf.etf_id,
                session_date=date(2026, 7, day),
                value=Decimal("100"),
                computed_at=datetime.now(timezone.utc),
            ),
        )

    values = get_indicator_values(
        conn,
        definition.indicator_definition_id,
        etf.etf_id,
        start_date=date(2026, 7, 13),
        end_date=date(2026, 7, 13),
    )

    assert [v.session_date for v in values] == [date(2026, 7, 13)]
