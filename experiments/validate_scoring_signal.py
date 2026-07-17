#!/usr/bin/env python3
"""Scoring Signal Research.

This is a **research script**, not a backtesting framework, not a
validation engine, and not a platform capability. It exists to answer
exactly one question, using data this platform has already computed:

    "Over this historical period, did higher-ranked ETFs have
    different subsequent returns than lower-ranked ETFs?"

It reuses existing code unchanged -- no core/, adapters/, or migrations
file is touched or needed by this script:

- daily_etf_universe_update.run(db_path, session_date=...) -- to make
  sure a Score exists for each historical date in range. Already
  idempotent and already accepts an explicit session_date; called here
  exactly as it already exists, in a loop.
- core.analytics.ranked_report.generate_ranked_etf_report() -- to
  reconstruct each historical date's ranking. Already has no "today"
  assumption anywhere in it; used here for past dates exactly as it
  already works for the present one.
- Existing repository functions (get_trading_days, get_price_bars,
  get_scoring_profile) -- read-only, unmodified.

The only new code in this file is a private forward_return() helper
(pure, Decimal, no database access, no Clock, no randomness -- same
discipline as core.analytics.domain.calculations.max_drawdown()) and
the loop/aggregation logic that composes the above into one report.
None of it is published as a reusable interface; nothing outside this
file imports from it.

Scope, deliberately minimal: one scoring profile, one ETF universe, one
fixed forward-return horizon, a top-k vs. bottom-k bucket comparison.
No benchmark comparison, no multiple horizons, no parameter sweep, no
persistence of results, no CLI command. This is the smallest version
that can answer the one question above; anything more is a later,
separately-considered addition, not bundled in here.

Prerequisites:
- A valid trading Calendar/TradingSession set for CALENDAR_ID (see
  seed_trading_calendar.py).
- Real historical PriceBar depth covering [start_date, end_date] plus
  the forward-return horizon beyond end_date, for every ETF in the
  universe (see backfill_price_history.py). Without this, most or all
  historical dates will have no Score (InsufficientPriceHistoryError
  internally) and this script will report very few or zero observed
  ranking dates -- a factual, correctly-reported outcome, not a crash.

Usage:
    python experiments/validate_scoring_signal.py

Dependency requirements: none beyond what this project already uses.
No third-party package is required to run this script.
"""

from __future__ import annotations

import contextlib
import io
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Makes core/ (and this directory's own daily_etf_universe_update.py)
# importable when this script is run directly
# (`python experiments/validate_scoring_signal.py`) rather than as a
# package module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.analytics.persistence.repository import get_scoring_profile  # noqa: E402
from core.analytics.ranked_report import generate_ranked_etf_report  # noqa: E402
from core.market_data.persistence.database import connect  # noqa: E402
from core.market_data.persistence.migrations import run_migrations  # noqa: E402
from core.market_data.persistence.repository import get_price_bars, get_trading_days  # noqa: E402

from experiments.daily_etf_universe_update import (  # noqa: E402
    CALENDAR_ID,
    PROFILE_NAME,
    PROFILE_VERSION,
)
from experiments.daily_etf_universe_update import run as run_daily_update  # noqa: E402
from experiments.daily_etf_universe_update import ETF_UNIVERSE  # noqa: E402

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

DEFAULT_DAYS_BACK = 730
HORIZON_TRADING_DAYS = 20
BUCKET_SIZE = 5


def forward_return(start_price: Decimal, end_price: Decimal) -> Decimal:
    """Simple forward return: (end_price / start_price) - 1.

    Pure and deterministic -- no database access, no Clock, no
    randomness. Decimal in, Decimal out, same discipline
    core.analytics.domain.calculations.max_drawdown() already uses.
    """
    return (end_price / start_price) - 1


def _resolve_close(conn, etf_id: str, session_date: date) -> Decimal | None:
    """The closing price for one ETF on one exact date, or None if no
    PriceBar exists for it -- a valid, expected outcome near the edges
    of the available history, not an error."""
    bars = get_price_bars(conn, etf_id, start_date=session_date, end_date=session_date)
    return bars[0].close.amount if bars else None


def run(
    db_path: Path = DB_PATH,
    universe: list[tuple[str, str]] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    horizon_trading_days: int = HORIZON_TRADING_DAYS,
    bucket_size: int = BUCKET_SIZE,
) -> int:
    """`universe` defaults to the module-level ETF_UNIVERSE (the same
    default/override convention daily_etf_universe_update.run() and
    backfill_price_history.run() already use); pass a shorter list for
    a small-subset smoke test without editing the file. `bucket_size`
    must satisfy len(universe) >= bucket_size * 2 for any date to
    produce an observation -- the default (5) assumes the full
    25-ETF universe; pass a smaller value for a smaller test universe.
    """
    universe = universe if universe is not None else ETF_UNIVERSE
    today = date.today()
    end_date = end_date or (today - timedelta(days=1))
    start_date = start_date or (end_date - timedelta(days=DEFAULT_DAYS_BACK))

    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        trading_days = sorted(d for d in get_trading_days(conn, CALENDAR_ID) if start_date <= d <= end_date)

        # Make sure a Score exists for each date in range, reusing the
        # existing, unmodified daily runner exactly as it already
        # works -- idempotent, so re-running this over dates that
        # already have scores writes nothing new. This is also what
        # creates the REFERENCE scoring profile on a fresh database
        # (the same bootstrap daily_etf_universe_update.py already
        # does on its own first run), which is why the profile lookup
        # below happens after this loop, not before it. Its own
        # per-date "ETF Universe Update" report is suppressed here so
        # this script's own factual report is the only visible output;
        # the runner itself is not modified in any way to do this.
        with contextlib.redirect_stdout(io.StringIO()):
            for session_date in trading_days:
                run_daily_update(db_path=db_path, session_date=session_date, universe=universe)

        profile = get_scoring_profile(conn, PROFILE_NAME, PROFILE_VERSION)
        if profile is None:
            print(
                f"No scoring profile found for name {PROFILE_NAME!r} version {PROFILE_VERSION}",
                file=sys.stderr,
            )
            return 1

        index_by_date = {d: i for i, d in enumerate(trading_days)}

        top_returns: list[Decimal] = []
        bottom_returns: list[Decimal] = []
        ranking_dates_observed = 0

        for session_date in trading_days:
            report = generate_ranked_etf_report(conn, profile.scoring_profile_id, session_date)
            if len(report) < bucket_size * 2:
                continue  # not enough ranked ETFs this date to form both buckets -- excluded, not an error

            forward_index = index_by_date[session_date] + horizon_trading_days
            if forward_index >= len(trading_days):
                continue  # not enough future trading days in range yet -- excluded, not an error
            forward_date = trading_days[forward_index]

            top_entries = report[:bucket_size]
            bottom_entries = report[-bucket_size:]

            date_had_observation = False
            for entry in top_entries:
                start_price = _resolve_close(conn, entry.etf_id, session_date)
                end_price = _resolve_close(conn, entry.etf_id, forward_date)
                if start_price is None or end_price is None:
                    continue
                top_returns.append(forward_return(start_price, end_price))
                date_had_observation = True

            for entry in bottom_entries:
                start_price = _resolve_close(conn, entry.etf_id, session_date)
                end_price = _resolve_close(conn, entry.etf_id, forward_date)
                if start_price is None or end_price is None:
                    continue
                bottom_returns.append(forward_return(start_price, end_price))
                date_had_observation = True

            if date_had_observation:
                ranking_dates_observed += 1

        top_average = sum(top_returns) / len(top_returns) if top_returns else None
        bottom_average = sum(bottom_returns) / len(bottom_returns) if bottom_returns else None
        difference = (top_average - bottom_average) if (top_average is not None and bottom_average is not None) else None

        print("Scoring Signal Research")
        print(f"Scoring profile: {PROFILE_NAME} v{PROFILE_VERSION}")
        print(f"Period: {start_date.isoformat()} to {end_date.isoformat()}")
        print(f"Forward return horizon: {horizon_trading_days} trading days")
        print(f"ETF universe size: {len(universe)}")
        print(f"Ranking dates observed: {ranking_dates_observed}")
        print()
        print(f"Top bucket: top {bucket_size} of {len(universe)} ranked ETFs per date")
        print(f"Bottom bucket: bottom {bucket_size} of {len(universe)} ranked ETFs per date")
        print()
        print(f"Top bucket average forward return: {top_average if top_average is not None else 'N/A'}")
        print(f"Bottom bucket average forward return: {bottom_average if bottom_average is not None else 'N/A'}")
        print(f"Difference (top - bottom): {difference if difference is not None else 'N/A'}")
        print()
        print("Limitations:")
        print("- Observations are not independent because rankings move slowly and forward windows overlap.")
        print("- This represents one historical regime only.")
        print("- The ETF universe was selected from currently existing ETFs and therefore contains survivorship bias.")
        print()
        print(
            "This is an observed measurement over a limited historical sample. It does not "
            "confirm, validate, or prove predictive value. No recommendation, no ranking "
            "judgment, no investment advice."
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    # Guarded inline self-checks for forward_return() -- cheap, run
    # every time, catch a broken formula before it silently produces a
    # meaningless report.
    assert forward_return(Decimal("100"), Decimal("110")) == Decimal("0.1")
    assert forward_return(Decimal("100"), Decimal("90")) == Decimal("-0.1")
    assert forward_return(Decimal("50"), Decimal("50")) == Decimal("0")

    raise SystemExit(run())
