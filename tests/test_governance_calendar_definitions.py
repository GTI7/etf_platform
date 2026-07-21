from __future__ import annotations

import sqlite3

import pytest

from core.governance.calendar_definitions import (
    CALENDAR_DEFINITIONS,
    XNYS,
    UnknownCalendarError,
    ensure_calendar,
)


def test_xnys_matches_seed_trading_calendar_literals() -> None:
    """Must be the same calendar as experiments/seed_trading_calendar.py's
    own module-level constants, not a redefinition of it."""
    assert XNYS.calendar_id == "XNYS"
    assert XNYS.name == "New York Stock Exchange"
    assert XNYS.exchange == "NYSE"
    assert XNYS.timezone == "America/New_York"


def test_ensure_calendar_inserts_when_absent(conn: sqlite3.Connection) -> None:
    ensure_calendar(conn, "XNYS")

    row = conn.execute("SELECT * FROM Calendar WHERE calendar_id = ?", ("XNYS",)).fetchone()
    assert row is not None
    assert row["name"] == "New York Stock Exchange"


def test_ensure_calendar_is_idempotent(conn: sqlite3.Connection) -> None:
    ensure_calendar(conn, "XNYS")
    ensure_calendar(conn, "XNYS")  # must not raise on a rerun

    rows = conn.execute("SELECT * FROM Calendar").fetchall()
    assert len(rows) == 1


def test_ensure_calendar_rejects_unknown_calendar_id(conn: sqlite3.Connection) -> None:
    with pytest.raises(UnknownCalendarError):
        ensure_calendar(conn, "NOT_A_KNOWN_CALENDAR")


def test_calendar_definitions_registry_contains_xnys() -> None:
    assert CALENDAR_DEFINITIONS == {"XNYS": XNYS}
