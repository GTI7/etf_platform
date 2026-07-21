"""Code-defined ``Calendar`` literal(s) and the idempotent reconstruction-
loader insert step (Phase 4 Architecture Amendment v1.1 SS A.4, SS D).

``Calendar`` is NOT a frozen dataset. Its only row today (``XNYS``) is a
hardcoded, deterministic module-level literal -- not a ``uuid4``, not
sourced from ``exchange_calendars`` (only the ``TradingSession`` *rows*
are; the ``Calendar`` row's own fields are plain committed strings, see
``experiments/seed_trading_calendar.py``). Two independent runs of the
same committed code produce byte-identical ``Calendar`` rows,
unconditionally -- freezing it as a JSONL snapshot would add hashing,
loading, and provenance machinery for zero risk reduction.

What ``Calendar`` does need, and does not have anywhere else in this
codebase, is a load step usable during reconstruction: no existing
script inserts it except ``experiments/seed_trading_calendar.py``, which
is the deliberate, isolated, ``exchange_calendars``-touching exception
already excluded from the reproduction path. This module is that new,
loader-owned insert step -- idempotent, no external API call, no
``exchange_calendars`` dependency.
"""

from __future__ import annotations

import sqlite3

from core.market_data.domain.models import Calendar
from core.market_data.persistence.repository import insert_calendar

# Mirrors experiments/seed_trading_calendar.py's own literal constants
# exactly -- this is the same calendar, not a redefinition of it.
XNYS = Calendar(
    calendar_id="XNYS",
    name="New York Stock Exchange",
    exchange="NYSE",
    timezone="America/New_York",
)

CALENDAR_DEFINITIONS: dict[str, Calendar] = {XNYS.calendar_id: XNYS}


class UnknownCalendarError(RuntimeError):
    """Raised when the reconstruction loader is asked to ensure a
    calendar_id with no committed literal definition here -- a
    governance-quality failure rather than a downstream FK error at
    ETF-load time."""


def _calendar_exists(conn: sqlite3.Connection, calendar_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM Calendar WHERE calendar_id = ?", (calendar_id,)).fetchone()
    return row is not None


def ensure_calendar(conn: sqlite3.Connection, calendar_id: str) -> Calendar:
    """Idempotently insert `calendar_id`'s committed literal definition if
    it is not already present. Safe to call on every reconstruction run:
    a rerun against an already-seeded database is a no-op."""
    if calendar_id not in CALENDAR_DEFINITIONS:
        raise UnknownCalendarError(
            f"No committed Calendar literal for calendar_id={calendar_id!r}. "
            f"Known calendar_id(s): {sorted(CALENDAR_DEFINITIONS)}"
        )
    definition = CALENDAR_DEFINITIONS[calendar_id]
    if not _calendar_exists(conn, calendar_id):
        insert_calendar(conn, definition)
    return definition
