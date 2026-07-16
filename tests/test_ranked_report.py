from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from core.analytics.domain.models import Score, ScoringProfile, serialize_parameters
from core.analytics.persistence.repository import insert_score, insert_scoring_profile
from core.analytics.ranked_report import RankedETFReportEntry, generate_ranked_etf_report
from core.market_data.domain.models import ETF, Calendar
from core.market_data.persistence.repository import insert_calendar, insert_etf

CALENDAR_ID = "XNYS"
SESSION_DATE = date(2026, 7, 14)


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


def _make_etf(conn: sqlite3.Connection, ticker: str, name: str) -> ETF:
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker=ticker,
        name=name,
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def _make_profile(version: int = 1) -> ScoringProfile:
    return ScoringProfile(
        scoring_profile_id=uuid.uuid4().hex,
        name="REFERENCE",
        version=version,
        parameters=serialize_parameters(
            {"dimensions": {"MOMENTUM": {"indicator_name": "SMA", "indicator_version": 1}}}
        ),
        created_at=datetime.now(timezone.utc),
    )


def _make_score(etf: ETF, profile: ScoringProfile, overall_score: str) -> Score:
    return Score(
        score_id=uuid.uuid4().hex,
        etf_id=etf.etf_id,
        scoring_profile_id=profile.scoring_profile_id,
        session_date=SESSION_DATE,
        overall_score=Decimal(overall_score),
        computed_at=datetime.now(timezone.utc),
    )


def test_generate_ranked_etf_report_basic(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    insert_score(conn, _make_score(etf_a, profile, "90"))
    insert_score(conn, _make_score(etf_b, profile, "70"))

    report = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert len(report) == 2
    assert {entry.etf_id for entry in report} == {etf_a.etf_id, etf_b.etf_id}


def test_generate_ranked_etf_report_preserves_ranking_order(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "ETF_A", "Fund A")
    etf_b = _make_etf(conn, "ETF_B", "Fund B")
    etf_c = _make_etf(conn, "ETF_C", "Fund C")
    # Inserted deliberately out of score order, to prove the report's
    # order comes from rank_scores(), not insertion order.
    insert_score(conn, _make_score(etf_c, profile, "80"))
    insert_score(conn, _make_score(etf_a, profile, "95"))
    insert_score(conn, _make_score(etf_b, profile, "90"))

    report = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert [(entry.rank, entry.ticker) for entry in report] == [
        (1, "ETF_A"),
        (2, "ETF_B"),
        (3, "ETF_C"),
    ]


def test_generate_ranked_etf_report_resolves_etf_identity(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    insert_score(conn, _make_score(etf, profile, "70"))

    [entry] = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert entry == RankedETFReportEntry(
        rank=1,
        etf_id=etf.etf_id,
        ticker="SPY",
        name="SPDR S&P 500",
        overall_score=Decimal("70"),
    )


def test_generate_ranked_etf_report_returns_empty_list_when_no_scores(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    report = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert report == []


def test_generate_ranked_etf_report_is_deterministic(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    insert_score(conn, _make_score(etf_a, profile, "90"))
    insert_score(conn, _make_score(etf_b, profile, "90"))  # tie, exercises tie-break too

    first = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)
    second = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert first == second
