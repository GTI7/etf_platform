#!/usr/bin/env python3
"""Experiment runner: daily update of a ~25-ETF research universe.

This is NOT part of the production CLI (etf update / etf status / etf
analyze) and does not modify core/ or adapters/ in any way. It only
calls the platform's existing write pipeline
(core.analytics.write_pipeline.run_write_pipeline_for_etfs) once per
ETF in ETF_UNIVERSE below, exactly as that function already exists.

Purpose: collect real, daily ETF price/indicator/score history across a
balanced research universe so there is real data to look at before any
future UI or feature decisions are made. See experiments/README.md for
more context and out-of-scope boundaries.

Usage:
    python experiments/daily_etf_universe_update.py

Prerequisite: a valid trading Calendar and its TradingSession rows must
already exist for CALENDAR_ID (see experiments/README.md for why this
script deliberately does not generate one). First run still creates
the database file, ETF records, indicator definitions, and scoring
profile automatically -- that bootstrap is plain experiment
configuration, not market-data domain truth, so it stays here. Every
step is idempotent (checked with a get_*() lookup before inserting,
exactly the same pattern the platform itself uses), so running this
daily never fails on "already exists" and never duplicates data.

This script produces a factual execution summary only (which tickers
succeeded, which failed and why). It does not rank, recommend, or
advise -- that stays entirely inside core/analytics, unmodified.
"""

from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

# Makes core/ importable when this script is run directly
# (`python experiments/daily_etf_universe_update.py`) rather than as a
# package module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.analytics.domain.models import (  # noqa: E402
    IndicatorDefinition,
    ScoringProfile,
    serialize_parameters,
)
from core.analytics.persistence.repository import (  # noqa: E402
    get_indicator_definition,
    get_scoring_profile,
    insert_indicator_definition,
    insert_scoring_profile,
)
from core.analytics.write_pipeline import run_write_pipeline_for_etfs  # noqa: E402
from core.market_data.domain.models import ETF  # noqa: E402
from core.market_data.persistence.database import connect  # noqa: E402
from core.market_data.persistence.migrations import run_migrations  # noqa: E402
from core.market_data.persistence.repository import (  # noqa: E402
    get_etf_by_ticker,
    get_trading_days,
    insert_etf,
)
from core.market_data.providers.yahoo_finance import YahooFinanceProvider  # noqa: E402
from core.shared.clock import SystemClock  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration -- edit freely. Plain constants, no new config framework.
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

CALENDAR_ID = "XNYS"

# Indicator definitions used for this experiment run.
SMA_NAME, SMA_VERSION, SMA_WINDOW = "SMA", 1, 20
RSI_NAME, RSI_VERSION, RSI_PERIOD = "RSI", 1, 14

# Scoring profile used for this experiment run.
PROFILE_NAME, PROFILE_VERSION = "REFERENCE", 1

# Balanced real-world research universe, ~25 liquid, well-known ETFs.
# Not a recommendation of what to hold or buy -- this only decides which
# tickers the existing pipeline is run for. Edit this list freely; it
# has no effect on scoring or ranking logic, both of which live
# entirely in core/analytics and are untouched by this script.
ETF_UNIVERSE = [
    # -- Global equity --------------------------------------------------
    ("VT", "Vanguard Total World Stock ETF"),
    ("ACWI", "iShares MSCI ACWI ETF"),
    # -- US equity --------------------------------------------------------
    ("SPY", "SPDR S&P 500 ETF Trust"),
    ("VTI", "Vanguard Total Stock Market ETF"),
    ("QQQ", "Invesco QQQ Trust"),
    ("IWM", "iShares Russell 2000 ETF"),
    # -- Regional equity ----------------------------------------------------
    ("EFA", "iShares MSCI EAFE ETF"),
    ("VGK", "Vanguard FTSE Europe ETF"),
    ("EWJ", "iShares MSCI Japan ETF"),
    ("EEM", "iShares MSCI Emerging Markets ETF"),
    # -- Sectors -----------------------------------------------------------
    ("XLK", "Technology Select Sector SPDR Fund"),
    ("XLF", "Financial Select Sector SPDR Fund"),
    ("XLE", "Energy Select Sector SPDR Fund"),
    ("XLV", "Health Care Select Sector SPDR Fund"),
    # -- Themes --------------------------------------------------------------
    ("ARKK", "ARK Innovation ETF"),
    ("ICLN", "iShares Global Clean Energy ETF"),
    ("SKYY", "First Trust Cloud Computing ETF"),
    ("HACK", "ETFMG Prime Cyber Security ETF"),
    ("BOTZ", "Global X Robotics & Artificial Intelligence ETF"),
    # -- Defensive assets ------------------------------------------------
    ("GLD", "SPDR Gold Shares"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF"),
    ("BND", "Vanguard Total Bond Market ETF"),
    ("VNQ", "Vanguard Real Estate ETF"),
    ("USMV", "iShares MSCI USA Min Vol Factor ETF"),
    ("SCHD", "Schwab U.S. Dividend Equity ETF"),
]


def _ensure_etfs(conn, universe: list[tuple[str, str]]) -> list[ETF]:
    etfs = []
    for ticker, name in universe:
        etf = get_etf_by_ticker(conn, ticker)
        if etf is None:
            etf = ETF(
                etf_id=uuid.uuid4().hex,
                ticker=ticker,
                name=name,
                currency="USD",
                calendar_id=CALENDAR_ID,
                created_at=datetime.now(timezone.utc),
            )
            insert_etf(conn, etf)
        etfs.append(etf)
    return etfs


def _ensure_indicator_definitions(conn) -> tuple[IndicatorDefinition, IndicatorDefinition]:
    sma = get_indicator_definition(conn, SMA_NAME, SMA_VERSION)
    if sma is None:
        sma = IndicatorDefinition(
            indicator_definition_id=uuid.uuid4().hex,
            name=SMA_NAME,
            version=SMA_VERSION,
            parameters=serialize_parameters({"window": SMA_WINDOW}),
            created_at=datetime.now(timezone.utc),
        )
        insert_indicator_definition(conn, sma)

    rsi = get_indicator_definition(conn, RSI_NAME, RSI_VERSION)
    if rsi is None:
        rsi = IndicatorDefinition(
            indicator_definition_id=uuid.uuid4().hex,
            name=RSI_NAME,
            version=RSI_VERSION,
            parameters=serialize_parameters({"period": RSI_PERIOD}),
            created_at=datetime.now(timezone.utc),
        )
        insert_indicator_definition(conn, rsi)

    return sma, rsi


def _ensure_scoring_profile(conn) -> ScoringProfile:
    profile = get_scoring_profile(conn, PROFILE_NAME, PROFILE_VERSION)
    if profile is None:
        profile = ScoringProfile(
            scoring_profile_id=uuid.uuid4().hex,
            name=PROFILE_NAME,
            version=PROFILE_VERSION,
            parameters=serialize_parameters(
                {
                    "dimensions": {
                        "MOMENTUM": {"indicator_name": SMA_NAME, "indicator_version": SMA_VERSION},
                        "VALUE": {"indicator_name": RSI_NAME, "indicator_version": RSI_VERSION},
                    }
                }
            ),
            created_at=datetime.now(timezone.utc),
        )
        insert_scoring_profile(conn, profile)
    return profile


def _format_summary(etfs: list[ETF], results: dict, session_date: date) -> str:
    successes = [etf for etf in etfs if not isinstance(results[etf.etf_id], Exception)]
    failures = [etf for etf in etfs if isinstance(results[etf.etf_id], Exception)]

    lines = ["ETF Universe Update", f"Session date: {session_date.isoformat()}", ""]

    lines.append("Successful:")
    for etf in successes:
        lines.append(f"- {etf.ticker}")
    if not successes:
        lines.append("- (none)")

    lines.append("")
    lines.append("Failed:")
    for etf in failures:
        lines.append(f"- {etf.ticker}")
        lines.append(f"  Error: {results[etf.etf_id]}")
    if not failures:
        lines.append("- (none)")

    lines.append("")
    lines.append("No recommendations.")
    lines.append("No ranking.")
    lines.append("No investment advice.")

    return "\n".join(lines)


def run(
    db_path: Path = DB_PATH,
    session_date: date | None = None,
    universe: list[tuple[str, str]] | None = None,
) -> int:
    """Run the experiment for one session date.

    `universe` defaults to the module-level ETF_UNIVERSE; pass a shorter
    list (e.g. for a 3-ETF smoke test) without editing the file.

    Prerequisite: a valid trading Calendar (CALENDAR_ID) with its
    TradingSession rows must already exist in this database. This
    function does not create one -- see experiments/README.md.
    """
    session_date = session_date or date.today()
    universe = universe if universe is not None else ETF_UNIVERSE
    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        if not get_trading_days(conn, CALENDAR_ID):
            print(
                f"No trading calendar found for calendar_id={CALENDAR_ID!r}. "
                "This experiment runner assumes a valid trading calendar "
                "already exists and does not generate one -- populate a "
                "Calendar and its TradingSession rows for this calendar_id "
                "before running (see experiments/README.md).",
                file=sys.stderr,
            )
            return 1

        with conn:
            etfs = _ensure_etfs(conn, universe)
            sma_definition, rsi_definition = _ensure_indicator_definitions(conn)
            profile = _ensure_scoring_profile(conn)

        results = run_write_pipeline_for_etfs(
            conn,
            SystemClock(),
            YahooFinanceProvider(),
            etfs,
            session_date,
            sma_definition,
            rsi_definition,
            profile,
        )

        print(_format_summary(etfs, results, session_date))

        failures = sum(1 for outcome in results.values() if isinstance(outcome, Exception))
        return 1 if failures else 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(run())
