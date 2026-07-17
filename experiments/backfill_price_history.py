#!/usr/bin/env python3
"""Research prerequisite utility: bulk historical price backfill.

This is a **setup utility**, not a research runner and not the daily
production pipeline. It exists for exactly one reason: research scripts
in this directory (e.g. validate_scoring_signal.py) need many days of
real PriceBar history to work with, and the platform's own daily
pipeline (ingest_daily_prices, called via
daily_etf_universe_update.run()) deliberately ingests one session-day
per call -- correct and sufficient for daily production use, but far
too slow (one HTTP request per ETF per day) to build up months or years
of history without risking exactly the kind of provider rate-limiting
this project has already hit once for real (see the v0.15.1/v0.15.2
Yahoo Finance fixes in core/market_data/providers/yahoo_finance.py).

This script does not add a new capability to solve that: it calls the
platform's existing, already-general DataProvider.fetch_daily_bars()
directly with a real [start_date, end_date] range -- one HTTP request
per ETF for the whole range, not one per day -- and inserts each
returned bar via the existing insert_price_bar() repository function.
Nothing here is new machinery; it is the same two already-existing,
unmodified functions already used, one call at a time, throughout this
project's own manual verification work, wrapped in a reusable script.

Single responsibility: price bars only. This script does NOT calculate
SMA/RSI/scores, does NOT seed a Calendar or TradingSession rows (see
seed_trading_calendar.py for that), and does NOT modify
ingest_daily_prices() or introduce any provider abstraction -- it calls
YahooFinanceProvider directly, exactly as the platform's own code
already does.

Prerequisites:
- A valid trading Calendar/TradingSession set for CALENDAR_ID must
  already exist (see seed_trading_calendar.py).
- ETF rows must already exist for the tickers you want backfilled (see
  daily_etf_universe_update.py, which creates them on first run). This
  script does not register ETFs -- a ticker with no ETF row is reported
  as skipped, not created.

Usage:
    python experiments/backfill_price_history.py

Idempotent: existing PriceBar rows for a given (etf, session_date) are
never re-inserted or duplicated -- each ETF's existing date range is
read once via get_price_bars() before fetching, and only genuinely new
dates from the provider response are inserted. Running this again over
the same or a wider range reports the already-present rows as skipped,
inserts only what's new.

Dependency requirements: none beyond what this project already uses
(urllib-based YahooFinanceProvider, stdlib). No third-party package is
required to run this script.
"""

from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Makes core/ (and this directory's own daily_etf_universe_update.py)
# importable when this script is run directly
# (`python experiments/backfill_price_history.py`) rather than as a
# package module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.market_data.domain.models import PriceBar  # noqa: E402
from core.market_data.persistence.database import connect  # noqa: E402
from core.market_data.persistence.migrations import run_migrations  # noqa: E402
from core.market_data.persistence.repository import (  # noqa: E402
    get_etf_by_ticker,
    get_price_bars,
    insert_price_bar,
)
from core.market_data.providers.yahoo_finance import YahooFinanceProvider  # noqa: E402
from core.shared.money import Money  # noqa: E402

from experiments.daily_etf_universe_update import ETF_UNIVERSE  # noqa: E402

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

DEFAULT_DAYS_BACK = 730


def run(
    db_path: Path = DB_PATH,
    universe: list[tuple[str, str]] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> int:
    """Backfill real historical PriceBar rows for `universe` (defaults
    to ETF_UNIVERSE) over [start_date, end_date] (defaults to roughly
    two years back, through yesterday -- today's bar is the daily
    pipeline's own job, not this script's).
    """
    universe = universe if universe is not None else ETF_UNIVERSE
    today = date.today()
    end_date = end_date or (today - timedelta(days=1))
    start_date = start_date or (end_date - timedelta(days=DEFAULT_DAYS_BACK))

    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)
        provider = YahooFinanceProvider()

        per_ticker_results: list[tuple[str, int, int]] = []
        missing_etfs: list[str] = []
        total_inserted = 0
        total_skipped = 0

        for ticker, _name in universe:
            etf = get_etf_by_ticker(conn, ticker)
            if etf is None:
                missing_etfs.append(ticker)
                continue

            existing_bars = get_price_bars(conn, etf.etf_id, start_date=start_date, end_date=end_date)
            existing_dates = {bar.session_date for bar in existing_bars}

            provider_bars = provider.fetch_daily_bars(ticker, start_date, end_date)

            inserted = 0
            skipped = 0
            with conn:
                for provider_bar in provider_bars:
                    if provider_bar.session_date in existing_dates:
                        skipped += 1
                        continue
                    bar = PriceBar(
                        price_bar_id=uuid.uuid4().hex,
                        etf_id=etf.etf_id,
                        session_date=provider_bar.session_date,
                        open=Money(provider_bar.open, provider_bar.currency),
                        high=Money(provider_bar.high, provider_bar.currency),
                        low=Money(provider_bar.low, provider_bar.currency),
                        close=Money(provider_bar.close, provider_bar.currency),
                        volume=provider_bar.volume,
                        source=provider.name,
                        ingested_at=datetime.now(timezone.utc),
                    )
                    insert_price_bar(conn, bar)
                    inserted += 1

            per_ticker_results.append((ticker, inserted, skipped))
            total_inserted += inserted
            total_skipped += skipped

        print("Price history backfill")
        print(f"Requested range: {start_date.isoformat()} to {end_date.isoformat()}")
        print()
        for ticker, inserted, skipped in per_ticker_results:
            print(f"{ticker}: inserted={inserted} skipped={skipped}")

        if missing_etfs:
            print()
            print("No ETF record found (not backfilled):")
            for ticker in missing_etfs:
                print(f"- {ticker}")

        print()
        print(f"Total inserted: {total_inserted}")
        print(f"Total skipped (already present): {total_skipped}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(run())
