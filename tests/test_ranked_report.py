from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from core.analytics.domain.models import (
    Dimension,
    DimensionScore,
    IndicatorDefinition,
    IndicatorValue,
    Score,
    ScoringProfile,
    serialize_parameters,
)
from core.analytics.persistence.repository import (
    insert_dimension_score,
    insert_indicator_definition,
    insert_indicator_value,
    insert_score,
    insert_scoring_profile,
)
from core.analytics.ranked_report import (
    ETFAnalysisReport,
    MissingScoreError,
    RankedETFReportEntry,
    generate_etf_analysis_report,
    generate_ranked_etf_report,
)
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


def _make_dimension_score(score: Score, dimension: Dimension, value: str) -> DimensionScore:
    return DimensionScore(
        score_id=score.score_id,
        dimension=dimension,
        value=Decimal(value),
        computed_at=datetime.now(timezone.utc),
    )


def _make_risk_definition() -> IndicatorDefinition:
    return IndicatorDefinition(
        indicator_definition_id=uuid.uuid4().hex,
        name="MAX_DRAWDOWN",
        version=1,
        parameters=serialize_parameters({"window": 20}),
        created_at=datetime.now(timezone.utc),
    )


def _make_indicator_value(definition: IndicatorDefinition, etf: ETF, value: str) -> IndicatorValue:
    return IndicatorValue(
        indicator_value_id=uuid.uuid4().hex,
        indicator_definition_id=definition.indicator_definition_id,
        etf_id=etf.etf_id,
        session_date=SESSION_DATE,
        value=Decimal(value),
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
        dimension_scores={},  # no DimensionScore rows seeded in this test
        max_drawdown=None,  # risk_definition_id omitted
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


def test_generate_ranked_etf_report_exposes_dimension_scores(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    score = _make_score(etf, profile, "80")
    insert_score(conn, score)
    insert_dimension_score(conn, _make_dimension_score(score, Dimension.MOMENTUM, "90"))
    insert_dimension_score(conn, _make_dimension_score(score, Dimension.VALUE, "70"))

    [entry] = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert entry.dimension_scores == {
        Dimension.MOMENTUM: Decimal("90"),
        Dimension.VALUE: Decimal("70"),
    }
    # overall_score is untouched -- still whatever Score.overall_score already was,
    # not recomputed from dimension_scores.
    assert entry.overall_score == Decimal("80")


def test_generate_ranked_etf_report_dimension_scores_single_dimension(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    score = _make_score(etf, profile, "70")
    insert_score(conn, score)
    insert_dimension_score(conn, _make_dimension_score(score, Dimension.MOMENTUM, "70"))

    [entry] = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert entry.dimension_scores == {Dimension.MOMENTUM: Decimal("70")}


def test_generate_ranked_etf_report_max_drawdown_omitted_by_default(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    insert_score(conn, _make_score(etf, profile, "70"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf, "-0.15"))

    # risk_definition_id not passed -- max_drawdown must be None even
    # though a MAX_DRAWDOWN IndicatorValue exists for this ETF/session.
    [entry] = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert entry.max_drawdown is None


def test_generate_ranked_etf_report_max_drawdown_populated_when_definition_supplied(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    insert_score(conn, _make_score(etf, profile, "70"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf, "-0.15"))

    [entry] = generate_ranked_etf_report(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        risk_definition_id=risk_definition.indicator_definition_id,
    )

    assert entry.max_drawdown == Decimal("-0.15")


def test_generate_ranked_etf_report_max_drawdown_missing_value_returns_none(
    conn: sqlite3.Connection,
) -> None:
    """risk_definition_id supplied, but no MAX_DRAWDOWN IndicatorValue has
    been computed yet for this ETF/session -- must not fail, must return
    None for that entry."""
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    insert_score(conn, _make_score(etf, profile, "70"))
    # No IndicatorValue inserted for risk_definition/etf.

    [entry] = generate_ranked_etf_report(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        risk_definition_id=risk_definition.indicator_definition_id,
    )

    assert entry.max_drawdown is None


def test_generate_ranked_etf_report_max_drawdown_independent_per_etf(
    conn: sqlite3.Connection,
) -> None:
    """Multiple ETFs in one report each show their own drawdown value,
    including one ETF that has none computed at all."""
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    insert_score(conn, _make_score(etf_a, profile, "90"))
    insert_score(conn, _make_score(etf_b, profile, "80"))
    insert_score(conn, _make_score(etf_c, profile, "70"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_a, "-0.05"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_b, "-0.30"))
    # etf_c: no MAX_DRAWDOWN IndicatorValue -- expect None.

    report = generate_ranked_etf_report(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        risk_definition_id=risk_definition.indicator_definition_id,
    )

    max_drawdown_by_etf = {entry.etf_id: entry.max_drawdown for entry in report}
    assert max_drawdown_by_etf == {
        etf_a.etf_id: Decimal("-0.05"),
        etf_b.etf_id: Decimal("-0.30"),
        etf_c.etf_id: None,
    }


def test_generate_etf_analysis_report_full_analysis(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    score_a = _make_score(etf_a, profile, "80")
    insert_score(conn, score_a)
    insert_score(conn, _make_score(etf_b, profile, "60"))
    insert_dimension_score(conn, _make_dimension_score(score_a, Dimension.MOMENTUM, "90"))
    insert_dimension_score(conn, _make_dimension_score(score_a, Dimension.VALUE, "70"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_a, "-0.12"))

    report = generate_etf_analysis_report(
        conn,
        etf_a.etf_id,
        profile.scoring_profile_id,
        SESSION_DATE,
        risk_definition_id=risk_definition.indicator_definition_id,
    )

    assert report == ETFAnalysisReport(
        etf_id=etf_a.etf_id,
        ticker="AAA",
        name="Fund A",
        analysis_date=SESSION_DATE,
        scoring_profile_id=profile.scoring_profile_id,
        overall_score=Decimal("80"),
        dimension_scores={Dimension.MOMENTUM: Decimal("90"), Dimension.VALUE: Decimal("70")},
        max_drawdown=Decimal("-0.12"),
        rank=1,
        peer_count=2,
    )


def test_generate_etf_analysis_report_context_fields(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    insert_score(conn, _make_score(etf, profile, "70"))

    report = generate_etf_analysis_report(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)

    assert report.analysis_date == SESSION_DATE
    assert report.scoring_profile_id == profile.scoring_profile_id


def test_generate_etf_analysis_report_raises_when_score_missing(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    # No Score inserted for this ETF/profile/session.

    with pytest.raises(MissingScoreError):
        generate_etf_analysis_report(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)


def test_generate_etf_analysis_report_max_drawdown_omitted_by_default(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    insert_score(conn, _make_score(etf, profile, "70"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf, "-0.15"))

    # risk_definition_id not passed -- max_drawdown must be None even
    # though a MAX_DRAWDOWN IndicatorValue exists for this ETF/session.
    report = generate_etf_analysis_report(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)

    assert report.max_drawdown is None


def test_generate_etf_analysis_report_missing_risk_value_returns_none(
    conn: sqlite3.Connection,
) -> None:
    """risk_definition_id supplied, but no MAX_DRAWDOWN IndicatorValue has
    been computed yet -- must not fail, must return None. Score, unlike
    risk, is a required precondition -- see
    test_generate_etf_analysis_report_raises_when_score_missing."""
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    insert_score(conn, _make_score(etf, profile, "70"))
    # No IndicatorValue inserted for risk_definition/etf.

    report = generate_etf_analysis_report(
        conn,
        etf.etf_id,
        profile.scoring_profile_id,
        SESSION_DATE,
        risk_definition_id=risk_definition.indicator_definition_id,
    )

    assert report.max_drawdown is None


def test_generate_etf_analysis_report_ranking_context(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    insert_score(conn, _make_score(etf_a, profile, "95"))
    insert_score(conn, _make_score(etf_b, profile, "90"))
    insert_score(conn, _make_score(etf_c, profile, "80"))

    report_b = generate_etf_analysis_report(conn, etf_b.etf_id, profile.scoring_profile_id, SESSION_DATE)

    assert report_b.rank == 2
    assert report_b.peer_count == 3


def test_generate_etf_analysis_report_single_etf_is_rank_one_of_one(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    insert_score(conn, _make_score(etf, profile, "70"))

    report = generate_etf_analysis_report(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)

    assert report.rank == 1
    assert report.peer_count == 1
