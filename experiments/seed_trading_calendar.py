#!/usr/bin/env python3
"""Setup utility: seed a real, exchange-accurate trading calendar.

This is NOT a research runner (unlike daily_etf_universe_update.py in
this same directory) and does not collect, accumulate, or report any
ETF scoring history. It is a one-time (or occasionally re-run) setup
utility: it populates Calendar/TradingSession rows -- data the write
pipeline and every CLI command require to exist before they can run
correctly -- and then it is done. See experiments/README.md for the
research-runner-vs-setup-utility distinction this directory now makes
explicit.

Why this exists: an earlier version of daily_etf_universe_update.py
generated TradingSession rows itself, using a naive "every weekday is a
trading day" heuristic. That silently mismarked real NYSE closures
(Juneteenth, the pre-July-4th half day) as trading days, producing
incorrect SMA/RSI windows until manually corrected. That generation
logic was deliberately removed from the research runner -- calendar
correctness is market-data domain truth, not something a downstream
consumer should invent -- and nothing replaced it. This script is that
replacement: a real, external, exchange-accurate calendar source,
kept entirely outside core/ and adapters/, exactly as
experiments/daily_etf_universe_update.py already keeps its own
ETF/IndicatorDefinition/ScoringProfile bootstrap outside core/.

Prerequisite (external tool dependency, not a platform runtime
dependency): this script requires the `exchange_calendars` package,
which is NOT installed by any part of this platform and must be
installed separately before running this script:

    pip install exchange_calendars

core/ and adapters/ have zero third-party runtime dependencies, and
this script's use of exchange_calendars does not change that -- nothing
outside this file imports it, and it is never added to any project-
wide dependency declaration.

Usage:
    python experiments/seed_trading_calendar.py

Idempotent: only inserts a Calendar row if none exists yet (checked via
get_trading_days(), the same get_*()-before-insert pattern the rest of
this project already uses -- there is no get_calendar() repository
function, by design, so this mirrors exactly how the platform's own
code already handles this), and only inserts a TradingSession row for a
session date not already present. Running this again to extend the
calendar further into the future -- or to re-seed a fresh database --
never fails on "already exists" and never duplicates rows.

Not exhaustive forever: the default range (roughly two years back, one
year forward from today) is generous but finite, and is further clamped
to whatever range exchange_calendars itself has precomputed (its own
first_session/last_session) -- the effective range actually used is
always printed, never silently narrowed. When coverage runs out,
consumers fail loud and clean (InsufficientPriceHistoryError, or "No
trading calendar found" -- never a silent guess), exactly as intended;
re-run this script (and/or upgrade exchange_calendars, which precomputes
further forward over time) to extend coverage.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

# Makes core/ importable when this script is run directly
# (`python experiments/seed_trading_calendar.py`) rather than as a
# package module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import exchange_calendars as xcals  # noqa: E402

from core.market_data.domain.models import Calendar, TradingSession  # noqa: E402
from core.market_data.persistence.database import connect  # noqa: E402
from core.market_data.persistence.migrations import run_migrations  # noqa: E402
from core.market_data.persistence.repository import (  # noqa: E402
    get_trading_days,
    insert_calendar,
    insert_trading_session,
)

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

CALENDAR_ID = "XNYS"
CALENDAR_NAME = "New York Stock Exchange"
EXCHANGE = "NYSE"
TIMEZONE = "America/New_York"

DEFAULT_DAYS_BACK = 730
DEFAULT_DAYS_FORWARD = 365


def run(
    db_path: Path = DB_PATH,
    start_date: date | None = None,
    end_date: date | None = None,
) -> int:
    """Seed real TradingSession rows for CALENDAR_ID over [start_date,
    end_date] (inclusive), sourced from exchange_calendars rather than
    any heuristic. Defaults to roughly two years back, one year forward
    from today when the range is omitted.
    """
    today = date.today()
    start_date = start_date or today - timedelta(days=DEFAULT_DAYS_BACK)
    end_date = end_date or today + timedelta(days=DEFAULT_DAYS_FORWARD)

    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        existing_days = set(get_trading_days(conn, CALENDAR_ID))
        with conn:
            if not existing_days:
                insert_calendar(
                    conn,
                    Calendar(
                        calendar_id=CALENDAR_ID,
                        name=CALENDAR_NAME,
                        exchange=EXCHANGE,
                        timezone=TIMEZONE,
                    ),
                )

            calendar = xcals.get_calendar(CALENDAR_ID)
            # exchange_calendars precomputes a bounded session range (its
            # own first_session/last_session); requesting outside it
            # raises rather than silently extrapolating. Clamp to what
            # the library actually knows rather than guessing further,
            # the same "don't invent data" discipline this script exists
            # to apply to the platform's own calendar consumers.
            lower_bound = calendar.first_session.date()
            upper_bound = calendar.last_session.date()
            requested_start, requested_end = start_date, end_date
            start_date = max(start_date, lower_bound)
            end_date = min(end_date, upper_bound)
            sessions = calendar.sessions_in_range(start_date.isoformat(), end_date.isoformat())

            inserted = 0
            for session in sessions:
                session_date = session.date()
                if session_date in existing_days:
                    continue
                insert_trading_session(
                    conn,
                    TradingSession(
                        calendar_id=CALENDAR_ID,
                        session_date=session_date,
                        is_trading_day=True,
                        close_time_utc=None,
                    ),
                )
                inserted += 1

        print("Trading calendar seed")
        print(f"Calendar: {CALENDAR_ID} ({CALENDAR_NAME})")
        print(f"Requested range: {requested_start.isoformat()} to {requested_end.isoformat()}")
        if (start_date, end_date) != (requested_start, requested_end):
            print(
                f"Clamped to calendar's known range: {start_date.isoformat()} to "
                f"{end_date.isoformat()} (exchange_calendars has no data outside this)"
            )
        print(f"Real trading sessions in range: {len(sessions)}")
        print(f"New TradingSession rows inserted: {inserted}")
        print(f"Already present (unchanged): {len(sessions) - inserted}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(run())
