from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from adapters.cli.formatting import format_etf_analysis_report
from core.analytics.persistence.repository import get_scoring_profile
from core.analytics.ranked_report import MissingScoreError, generate_etf_analysis_report
from core.market_data.persistence.database import connect
from core.market_data.persistence.migrations import run_migrations
from core.market_data.persistence.repository import get_etf_by_ticker

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="etf-analysis-report",
        description=(
            "Print a single-ETF analysis report for one ticker, scoring "
            "profile, and session date. Every argument is required -- "
            "there are no defaults."
        ),
    )
    parser.add_argument("ticker", help="ETF ticker, e.g. SPY")
    parser.add_argument("profile_name", help="Scoring profile name, e.g. REFERENCE")
    parser.add_argument("profile_version", type=int, help="Scoring profile version, e.g. 1")
    parser.add_argument(
        "session_date",
        type=date.fromisoformat,
        help="Session date in ISO format, e.g. 2026-07-14",
    )
    parser.add_argument("db_path", help="Path to the SQLite database file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    conn = connect(args.db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        etf = get_etf_by_ticker(conn, args.ticker)
        if etf is None:
            print(f"No ETF found for ticker {args.ticker}", file=sys.stderr)
            return 1

        profile = get_scoring_profile(conn, args.profile_name, args.profile_version)
        if profile is None:
            print(
                f"No scoring profile found for name {args.profile_name!r} "
                f"version {args.profile_version}",
                file=sys.stderr,
            )
            return 1

        try:
            report = generate_etf_analysis_report(
                conn, etf.etf_id, profile.scoring_profile_id, args.session_date
            )
        except MissingScoreError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print(format_etf_analysis_report(report))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
