from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from adapters.cli.formatting import (
    format_etf_analysis_report,
    format_ranked_report,
    format_score_history,
    format_status,
    format_update_result,
)
from core.analytics.domain.models import InsufficientPriceHistoryError, MissingIndicatorValueError
from core.analytics.persistence.repository import get_indicator_definition, get_scoring_profile
from core.analytics.ranked_report import (
    MissingScoreError,
    compare_etfs,
    generate_etf_analysis_report,
    generate_ranked_etf_report,
    get_score_history,
)
from core.analytics.write_pipeline import run_write_pipeline
from core.market_data.persistence.repository import get_etf_by_ticker, get_latest_ingestion_run
from core.market_data.providers.base import DataProvider, ProviderError
from core.market_data.providers.yahoo_finance import YahooFinanceProvider
from core.shared.clock import Clock, SystemClock
from core.shared.pipeline_names import (
    indicator_pipeline_name,
    price_ingestion_pipeline_name,
    scoring_pipeline_name,
)
from core.store.connection import connect
from core.store.migrations import run_migrations

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="etf",
        description="ETF Intelligence Platform command-line interface.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze",
        description=(
            "Print a single-ETF analysis report for one ticker, scoring "
            "profile, and session date. Every argument is required -- "
            "there are no defaults."
        ),
        help="Print a single-ETF analysis report.",
    )
    analyze_parser.add_argument("ticker", help="ETF ticker, e.g. SPY")
    analyze_parser.add_argument("profile_name", help="Scoring profile name, e.g. REFERENCE")
    analyze_parser.add_argument("profile_version", type=int, help="Scoring profile version, e.g. 1")
    analyze_parser.add_argument(
        "session_date",
        type=date.fromisoformat,
        help="Session date in ISO format, e.g. 2026-07-14",
    )
    analyze_parser.add_argument("db_path", help="Path to the SQLite database file")

    update_parser = subparsers.add_parser(
        "update",
        description=(
            "Ingest prices, compute SMA/RSI, and compute a score for one "
            "ETF and session date, using the existing write pipeline. "
            "Every identifier is required -- there are no defaults, no "
            "hidden profiles, and no automatic selection."
        ),
        help="Run the existing write pipeline for one ETF and session.",
    )
    update_parser.add_argument("--ticker", required=True, help="ETF ticker, e.g. SPY")
    update_parser.add_argument(
        "--sma-name", dest="sma_name", required=True, help="SMA indicator definition name"
    )
    update_parser.add_argument(
        "--sma-version",
        dest="sma_version",
        required=True,
        type=int,
        help="SMA indicator definition version",
    )
    update_parser.add_argument(
        "--rsi-name", dest="rsi_name", required=True, help="RSI indicator definition name"
    )
    update_parser.add_argument(
        "--rsi-version",
        dest="rsi_version",
        required=True,
        type=int,
        help="RSI indicator definition version",
    )
    update_parser.add_argument(
        "--profile-name", dest="profile_name", required=True, help="Scoring profile name"
    )
    update_parser.add_argument(
        "--profile-version",
        dest="profile_version",
        required=True,
        type=int,
        help="Scoring profile version",
    )
    update_parser.add_argument(
        "--session-date",
        dest="session_date",
        required=True,
        type=date.fromisoformat,
        help="Session date in ISO format, e.g. 2026-07-14",
    )
    update_parser.add_argument(
        "--db-path", dest="db_path", required=True, help="Path to the SQLite database file"
    )

    status_parser = subparsers.add_parser(
        "status",
        description=(
            "Report the most recent run of each write-pipeline stage "
            "(price ingestion, SMA, RSI, scoring) for one ETF, indicator "
            "definition pair, and scoring profile. Every identifier is "
            "required -- there is no default and no 'latest' identifier "
            "selection; only the reported run itself is the latest one."
        ),
        help="Report the latest write-pipeline run for one ETF.",
    )
    status_parser.add_argument("--ticker", required=True, help="ETF ticker, e.g. SPY")
    status_parser.add_argument(
        "--sma-name", dest="sma_name", required=True, help="SMA indicator definition name"
    )
    status_parser.add_argument(
        "--sma-version",
        dest="sma_version",
        required=True,
        type=int,
        help="SMA indicator definition version",
    )
    status_parser.add_argument(
        "--rsi-name", dest="rsi_name", required=True, help="RSI indicator definition name"
    )
    status_parser.add_argument(
        "--rsi-version",
        dest="rsi_version",
        required=True,
        type=int,
        help="RSI indicator definition version",
    )
    status_parser.add_argument(
        "--profile-name", dest="profile_name", required=True, help="Scoring profile name"
    )
    status_parser.add_argument(
        "--profile-version",
        dest="profile_version",
        required=True,
        type=int,
        help="Scoring profile version",
    )
    status_parser.add_argument(
        "--db-path", dest="db_path", required=True, help="Path to the SQLite database file"
    )

    rank_parser = subparsers.add_parser(
        "rank",
        description=(
            "Print every ETF with a Score for one scoring profile and session "
            "date, ranked, using the existing ranked report. Every identifier "
            "is required -- there is no default profile and no 'latest' date. "
            "--risk-name/--risk-version are optional and only enable "
            "max_drawdown display; omitting them omits max_drawdown, exactly "
            "as generate_ranked_etf_report() already does."
        ),
        help="Print the ranked report for one scoring profile and session date.",
    )
    rank_parser.add_argument(
        "--date",
        dest="session_date",
        required=True,
        type=date.fromisoformat,
        help="Session date in ISO format, e.g. 2026-07-14",
    )
    rank_parser.add_argument(
        "--profile-name", dest="profile_name", required=True, help="Scoring profile name"
    )
    rank_parser.add_argument(
        "--profile-version",
        dest="profile_version",
        required=True,
        type=int,
        help="Scoring profile version",
    )
    rank_parser.add_argument(
        "--risk-name",
        dest="risk_name",
        help="Optional risk indicator definition name (enables max_drawdown; requires --risk-version too)",
    )
    rank_parser.add_argument(
        "--risk-version",
        dest="risk_version",
        type=int,
        help="Optional risk indicator definition version (enables max_drawdown; requires --risk-name too)",
    )
    rank_parser.add_argument(
        "--db-path", dest="db_path", required=True, help="Path to the SQLite database file"
    )

    compare_parser = subparsers.add_parser(
        "compare",
        description=(
            "Print the given tickers, ranked locally among just themselves, "
            "for one scoring profile and session date, using the existing "
            "compare_etfs(). Zero or one ticker is a valid comparison, same as "
            "compare_etfs() itself. Every identifier is required -- there is "
            "no default profile and no 'latest' date. --risk-name/--risk-version "
            "are optional and only enable max_drawdown display."
        ),
        help="Compare specific tickers for one scoring profile and session date.",
    )
    compare_parser.add_argument(
        "tickers", nargs="*", help="ETF tickers to compare, e.g. SPY QQQ VTI (zero or more)"
    )
    compare_parser.add_argument(
        "--date",
        dest="session_date",
        required=True,
        type=date.fromisoformat,
        help="Session date in ISO format, e.g. 2026-07-14",
    )
    compare_parser.add_argument(
        "--profile-name", dest="profile_name", required=True, help="Scoring profile name"
    )
    compare_parser.add_argument(
        "--profile-version",
        dest="profile_version",
        required=True,
        type=int,
        help="Scoring profile version",
    )
    compare_parser.add_argument(
        "--risk-name",
        dest="risk_name",
        help="Optional risk indicator definition name (enables max_drawdown; requires --risk-version too)",
    )
    compare_parser.add_argument(
        "--risk-version",
        dest="risk_version",
        type=int,
        help="Optional risk indicator definition version (enables max_drawdown; requires --risk-name too)",
    )
    compare_parser.add_argument(
        "--db-path", dest="db_path", required=True, help="Path to the SQLite database file"
    )

    history_parser = subparsers.add_parser(
        "history",
        description=(
            "Print one ETF's own Score history under one scoring profile, "
            "using the existing get_score_history(). Every identifier is "
            "required -- there is no default profile. --start-date/--end-date "
            "are optional; omitting either omits that bound, exactly as "
            "get_score_history() already does."
        ),
        help="Print one ETF's score history for one scoring profile.",
    )
    history_parser.add_argument("--ticker", required=True, help="ETF ticker, e.g. SPY")
    history_parser.add_argument(
        "--profile-name", dest="profile_name", required=True, help="Scoring profile name"
    )
    history_parser.add_argument(
        "--profile-version",
        dest="profile_version",
        required=True,
        type=int,
        help="Scoring profile version",
    )
    history_parser.add_argument(
        "--start-date",
        dest="start_date",
        type=date.fromisoformat,
        help="Optional start date (ISO format) to restrict history",
    )
    history_parser.add_argument(
        "--end-date",
        dest="end_date",
        type=date.fromisoformat,
        help="Optional end date (ISO format) to restrict history",
    )
    history_parser.add_argument(
        "--db-path", dest="db_path", required=True, help="Path to the SQLite database file"
    )

    return parser


def _run_analyze(args: argparse.Namespace) -> int:
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


def _run_update(args: argparse.Namespace, clock: Clock, provider: DataProvider) -> int:
    conn = connect(args.db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        etf = get_etf_by_ticker(conn, args.ticker)
        if etf is None:
            print(f"No ETF found for ticker {args.ticker}", file=sys.stderr)
            return 1

        sma_definition = get_indicator_definition(conn, args.sma_name, args.sma_version)
        if sma_definition is None:
            print(
                f"No indicator definition found for name {args.sma_name!r} "
                f"version {args.sma_version}",
                file=sys.stderr,
            )
            return 1

        rsi_definition = get_indicator_definition(conn, args.rsi_name, args.rsi_version)
        if rsi_definition is None:
            print(
                f"No indicator definition found for name {args.rsi_name!r} "
                f"version {args.rsi_version}",
                file=sys.stderr,
            )
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
            result = run_write_pipeline(
                conn,
                clock,
                provider,
                etf,
                args.session_date,
                sma_definition,
                rsi_definition,
                profile,
            )
        except (ProviderError, InsufficientPriceHistoryError, MissingIndicatorValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print(format_update_result(args.ticker, args.session_date, result))
        return 0
    finally:
        conn.close()


def _run_status(args: argparse.Namespace) -> int:
    conn = connect(args.db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        etf = get_etf_by_ticker(conn, args.ticker)
        if etf is None:
            print(f"No ETF found for ticker {args.ticker}", file=sys.stderr)
            return 1

        sma_definition = get_indicator_definition(conn, args.sma_name, args.sma_version)
        if sma_definition is None:
            print(
                f"No indicator definition found for name {args.sma_name!r} "
                f"version {args.sma_version}",
                file=sys.stderr,
            )
            return 1

        rsi_definition = get_indicator_definition(conn, args.rsi_name, args.rsi_version)
        if rsi_definition is None:
            print(
                f"No indicator definition found for name {args.rsi_name!r} "
                f"version {args.rsi_version}",
                file=sys.stderr,
            )
            return 1

        profile = get_scoring_profile(conn, args.profile_name, args.profile_version)
        if profile is None:
            print(
                f"No scoring profile found for name {args.profile_name!r} "
                f"version {args.profile_version}",
                file=sys.stderr,
            )
            return 1

        price_ingestion_run = get_latest_ingestion_run(
            conn, price_ingestion_pipeline_name(etf.ticker)
        )
        sma_run = get_latest_ingestion_run(
            conn, indicator_pipeline_name(sma_definition.name, sma_definition.version, etf.ticker)
        )
        rsi_run = get_latest_ingestion_run(
            conn, indicator_pipeline_name(rsi_definition.name, rsi_definition.version, etf.ticker)
        )
        score_run = get_latest_ingestion_run(
            conn, scoring_pipeline_name(profile.name, profile.version, etf.ticker)
        )

        print(format_status(args.ticker, price_ingestion_run, sma_run, rsi_run, score_run))
        return 0
    finally:
        conn.close()


def _resolve_optional_risk_definition_id(
    conn, risk_name: str | None, risk_version: int | None
) -> tuple[str | None, str | None]:
    """Resolve an optional risk IndicatorDefinition for max_drawdown display.

    Returns (risk_definition_id, None) on success -- risk_definition_id is
    None if neither --risk-name nor --risk-version was supplied, the same
    "omitted means no max_drawdown" behavior generate_ranked_etf_report()/
    compare_etfs() already default to. Returns (None, error_message) if
    only one of the pair was supplied, or if the pair doesn't resolve to
    an existing IndicatorDefinition -- the same factual "not found" style
    every other identifier lookup in this module already uses.
    """
    if risk_name is None and risk_version is None:
        return None, None
    if risk_name is None or risk_version is None:
        return None, "Both --risk-name and --risk-version are required together"
    risk_definition = get_indicator_definition(conn, risk_name, risk_version)
    if risk_definition is None:
        return None, f"No indicator definition found for name {risk_name!r} version {risk_version}"
    return risk_definition.indicator_definition_id, None


def _run_rank(args: argparse.Namespace) -> int:
    conn = connect(args.db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        profile = get_scoring_profile(conn, args.profile_name, args.profile_version)
        if profile is None:
            print(
                f"No scoring profile found for name {args.profile_name!r} "
                f"version {args.profile_version}",
                file=sys.stderr,
            )
            return 1

        risk_definition_id, error = _resolve_optional_risk_definition_id(
            conn, args.risk_name, args.risk_version
        )
        if error is not None:
            print(error, file=sys.stderr)
            return 1

        report = generate_ranked_etf_report(
            conn, profile.scoring_profile_id, args.session_date, risk_definition_id
        )

        print(format_ranked_report("Ranked ETF report", args.session_date, report))
        return 0
    finally:
        conn.close()


def _run_compare(args: argparse.Namespace) -> int:
    conn = connect(args.db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        profile = get_scoring_profile(conn, args.profile_name, args.profile_version)
        if profile is None:
            print(
                f"No scoring profile found for name {args.profile_name!r} "
                f"version {args.profile_version}",
                file=sys.stderr,
            )
            return 1

        etf_ids = []
        for ticker in args.tickers:
            etf = get_etf_by_ticker(conn, ticker)
            if etf is None:
                print(f"No ETF found for ticker {ticker}", file=sys.stderr)
                return 1
            etf_ids.append(etf.etf_id)

        risk_definition_id, error = _resolve_optional_risk_definition_id(
            conn, args.risk_name, args.risk_version
        )
        if error is not None:
            print(error, file=sys.stderr)
            return 1

        report = compare_etfs(
            conn, profile.scoring_profile_id, args.session_date, etf_ids, risk_definition_id
        )

        header = f"ETF comparison: {', '.join(args.tickers)}" if args.tickers else "ETF comparison: (no tickers)"
        print(format_ranked_report(header, args.session_date, report))
        return 0
    finally:
        conn.close()


def _run_history(args: argparse.Namespace) -> int:
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

        history = get_score_history(
            conn, etf.etf_id, profile.scoring_profile_id, args.start_date, args.end_date
        )

        print(format_score_history(args.ticker, history))
        return 0
    finally:
        conn.close()


def main(
    argv: list[str] | None = None,
    clock: Clock | None = None,
    provider: DataProvider | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(args)
    if args.command == "update":
        return _run_update(args, clock or SystemClock(), provider or YahooFinanceProvider())
    if args.command == "status":
        return _run_status(args)
    if args.command == "rank":
        return _run_rank(args)
    if args.command == "compare":
        return _run_compare(args)
    if args.command == "history":
        return _run_history(args)
    raise AssertionError(f"unreachable: argparse restricts command to a known subcommand, got {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
