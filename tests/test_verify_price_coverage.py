from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from maintenance.verify_price_coverage import check_etf_coverage, verify_price_coverage

from core.market_data.domain.models import ETF, Calendar, PriceBar, TradingSession
from core.market_data.persistence.repository import (
    insert_calendar,
    insert_etf,
    insert_price_bar,
    insert_trading_session,
)
from core.shared.money import Money

CALENDAR_ID = "XNYS"


def _make_calendar(conn: sqlite3.Connection) -> None:
    insert_calendar(
        conn,
        Calendar(
            calendar_id=CALENDAR_ID,
            name="New York Stock Exchange",
            exchange="NYSE",
            timezone="America/New_York",
        ),
    )


def _make_etf(conn: sqlite3.Connection, ticker: str = "SPY") -> ETF:
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker=ticker,
        name=f"{ticker} fund",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def _mark_trading_day(conn: sqlite3.Connection, session_date: date, is_trading_day: bool = True) -> None:
    insert_trading_session(
        conn,
        TradingSession(
            calendar_id=CALENDAR_ID,
            session_date=session_date,
            is_trading_day=is_trading_day,
            close_time_utc=None,
        ),
    )


def _insert_bar(conn: sqlite3.Connection, etf_id: str, session_date: date) -> None:
    price = Money(Decimal("100.00"), "USD")
    insert_price_bar(
        conn,
        PriceBar(
            price_bar_id=uuid.uuid4().hex,
            etf_id=etf_id,
            session_date=session_date,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1000,
            source="test",
            ingested_at=datetime.now(timezone.utc),
        ),
    )


def test_valid_dataset_passes_with_no_gaps(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    etf = _make_etf(conn)
    days = [date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 15)]
    for day in days:
        _mark_trading_day(conn, day)
        _insert_bar(conn, etf.etf_id, day)

    report = check_etf_coverage(conn, etf.etf_id, etf.ticker, etf.calendar_id)

    assert report.has_data
    assert report.is_covered
    assert report.missing_dates == []
    assert report.invalid_dates == []
    assert report.bar_count == 3
    assert report.expected_trading_days == 3


def test_missing_trading_day_is_detected(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    etf = _make_etf(conn)
    days = [date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 15)]
    for day in days:
        _mark_trading_day(conn, day)
    # Bar missing for the middle trading day.
    _insert_bar(conn, etf.etf_id, days[0])
    _insert_bar(conn, etf.etf_id, days[2])

    report = check_etf_coverage(conn, etf.etf_id, etf.ticker, etf.calendar_id)

    assert not report.is_covered
    assert report.missing_dates == [days[1].isoformat()]
    assert report.invalid_dates == []


def test_bar_on_non_trading_day_is_detected_as_invalid(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    etf = _make_etf(conn)
    trading_day = date(2026, 7, 13)
    non_trading_day = date(2026, 7, 14)
    _mark_trading_day(conn, trading_day, is_trading_day=True)
    _mark_trading_day(conn, non_trading_day, is_trading_day=False)
    _insert_bar(conn, etf.etf_id, trading_day)
    _insert_bar(conn, etf.etf_id, non_trading_day)

    report = check_etf_coverage(conn, etf.etf_id, etf.ticker, etf.calendar_id)

    assert not report.is_covered
    assert report.missing_dates == []
    assert report.invalid_dates == [non_trading_day.isoformat()]


def test_bar_on_unpopulated_calendar_date_is_also_invalid(conn: sqlite3.Connection) -> None:
    """A date with no TradingSession row at all (a calendar gap, not a
    marked non-trading day) is treated the same as an explicit non-trading
    day -- both mean the row does not belong, per AD-023's existing
    "don't distinguish the two causes" discipline."""
    _make_calendar(conn)
    etf = _make_etf(conn)
    trading_day = date(2026, 7, 13)
    unpopulated_day = date(2026, 7, 14)
    _mark_trading_day(conn, trading_day, is_trading_day=True)
    # unpopulated_day has no TradingSession row at all.
    _insert_bar(conn, etf.etf_id, trading_day)
    _insert_bar(conn, etf.etf_id, unpopulated_day)

    report = check_etf_coverage(conn, etf.etf_id, etf.ticker, etf.calendar_id)

    assert not report.is_covered
    assert report.invalid_dates == [unpopulated_day.isoformat()]


def test_etf_with_no_price_bars_has_no_data_and_is_not_covered(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    etf = _make_etf(conn)

    report = check_etf_coverage(conn, etf.etf_id, etf.ticker, etf.calendar_id)

    assert not report.has_data
    assert not report.is_covered
    assert report.bar_count == 0
    assert report.earliest is None
    assert report.latest is None


def test_verify_price_coverage_aggregates_across_all_etfs(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    covered = _make_etf(conn, ticker="AAA")
    uncovered = _make_etf(conn, ticker="BBB")
    day = date(2026, 7, 13)
    _mark_trading_day(conn, day)
    _insert_bar(conn, covered.etf_id, day)
    # BBB gets no bars at all.

    reports = verify_price_coverage(conn)

    assert set(reports.keys()) == {"AAA", "BBB"}
    assert reports["AAA"].is_covered
    assert not reports["BBB"].is_covered
    assert not reports["BBB"].has_data


def test_historical_remediation_script_is_not_imported() -> None:
    """maintenance/remediate_h3_invalid_pricebar_rows.py is historical,
    one-off, evidence-producing code (docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md
    Section 6) -- this extraction copies its coverage-check logic without
    ever importing from it, so nothing here can cause it to change.
    Verified structurally via the AST: no `import` statement in the new
    module references the remediation module (a prose mention of its
    filename in a docstring, as this module's own module docstring has,
    is expected and is not what this test checks)."""
    import ast

    new_module_path = Path(__file__).resolve().parent.parent / "maintenance" / "verify_price_coverage.py"
    tree = ast.parse(new_module_path.read_text(encoding="utf-8"), filename=str(new_module_path))

    imported_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.append(node.module)

    assert not any("remediate_h3_invalid_pricebar_rows" in name for name in imported_names)
