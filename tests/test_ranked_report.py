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
    ETFScreeningCriteria,
    InvalidScreeningCriteriaError,
    MissingScoreError,
    RankedETFReportEntry,
    compare_etfs,
    generate_etf_analysis_report,
    generate_ranked_etf_report,
    get_top_candidates,
    screen_etfs,
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


def test_screen_etfs_with_no_criteria_matches_generate_ranked_etf_report(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    insert_score(conn, _make_score(etf_a, profile, "90"))
    insert_score(conn, _make_score(etf_b, profile, "70"))

    screened = screen_etfs(conn, profile.scoring_profile_id, SESSION_DATE)
    ranked = generate_ranked_etf_report(conn, profile.scoring_profile_id, SESSION_DATE)

    assert screened == ranked


def test_screen_etfs_candidate_etf_ids_restricts_output(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    insert_score(conn, _make_score(etf_a, profile, "90"))
    insert_score(conn, _make_score(etf_b, profile, "80"))
    insert_score(conn, _make_score(etf_c, profile, "70"))

    result = screen_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        candidate_etf_ids=[etf_a.etf_id, etf_b.etf_id],
    )

    assert {entry.etf_id for entry in result} == {etf_a.etf_id, etf_b.etf_id}


def test_screen_etfs_candidate_without_score_is_excluded_silently(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")  # no Score inserted for this ETF
    insert_score(conn, _make_score(etf_a, profile, "90"))

    result = screen_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        candidate_etf_ids=[etf_a.etf_id, etf_b.etf_id],
    )

    assert [entry.etf_id for entry in result] == [etf_a.etf_id]


def test_screen_etfs_min_overall_score_threshold(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_at_threshold = _make_etf(conn, "ATT", "At Threshold")
    etf_below_threshold = _make_etf(conn, "BEL", "Below Threshold")
    insert_score(conn, _make_score(etf_at_threshold, profile, "70"))
    insert_score(conn, _make_score(etf_below_threshold, profile, "69.99"))

    result = screen_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        criteria=ETFScreeningCriteria(min_overall_score=Decimal("70")),
    )

    assert [entry.etf_id for entry in result] == [etf_at_threshold.etf_id]


def test_screen_etfs_min_dimension_scores_excludes_missing_dimension(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_has_dimension = _make_etf(conn, "HAS", "Has Dimension")
    etf_missing_dimension = _make_etf(conn, "MIS", "Missing Dimension")
    score_has = _make_score(etf_has_dimension, profile, "80")
    score_missing = _make_score(etf_missing_dimension, profile, "80")
    insert_score(conn, score_has)
    insert_score(conn, score_missing)
    insert_dimension_score(conn, _make_dimension_score(score_has, Dimension.MOMENTUM, "65"))
    # etf_missing_dimension: no DimensionScore rows at all.

    result = screen_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        criteria=ETFScreeningCriteria(min_dimension_scores={Dimension.MOMENTUM: Decimal("60")}),
    )

    assert [entry.etf_id for entry in result] == [etf_has_dimension.etf_id]


def test_screen_etfs_max_drawdown_threshold(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    etf_ok = _make_etf(conn, "OKD", "OK Drawdown")
    etf_worse = _make_etf(conn, "WRS", "Worse Drawdown")
    etf_missing = _make_etf(conn, "MDD", "Missing Drawdown")
    insert_score(conn, _make_score(etf_ok, profile, "80"))
    insert_score(conn, _make_score(etf_worse, profile, "80"))
    insert_score(conn, _make_score(etf_missing, profile, "80"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_ok, "-0.20"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_worse, "-0.25"))
    # etf_missing: no MAX_DRAWDOWN IndicatorValue.

    result = screen_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        criteria=ETFScreeningCriteria(max_drawdown=Decimal("-0.20")),
        risk_definition_id=risk_definition.indicator_definition_id,
    )

    assert [entry.etf_id for entry in result] == [etf_ok.etf_id]


def test_screen_etfs_raises_when_max_drawdown_criteria_supplied_without_risk_definition(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    with pytest.raises(InvalidScreeningCriteriaError):
        screen_etfs(
            conn,
            profile.scoring_profile_id,
            SESSION_DATE,
            criteria=ETFScreeningCriteria(max_drawdown=Decimal("-0.20")),
        )


def test_screen_etfs_returns_empty_list_when_no_candidates_match(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    insert_score(conn, _make_score(etf, profile, "50"))

    result = screen_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        criteria=ETFScreeningCriteria(min_overall_score=Decimal("70")),
    )

    assert result == []


def test_screen_etfs_ranks_are_local_to_survivors(conn: sqlite3.Connection) -> None:
    """Filtering removes the globally-highest-scored ETF from the
    candidate set (via candidate_etf_ids, not criteria) -- the remaining
    two must receive clean, gapless local ranks (1, 2), not their rank
    within the full universe (which would have been 2, 3)."""
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")  # globally rank 1, excluded as a candidate
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    insert_score(conn, _make_score(etf_a, profile, "95"))
    insert_score(conn, _make_score(etf_b, profile, "80"))
    insert_score(conn, _make_score(etf_c, profile, "70"))

    result = screen_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        candidate_etf_ids=[etf_b.etf_id, etf_c.etf_id],
    )

    assert [(entry.rank, entry.etf_id) for entry in result] == [
        (1, etf_b.etf_id),
        (2, etf_c.etf_id),
    ]


def test_screen_etfs_multiple_criteria_require_all_to_pass(conn: sqlite3.Connection) -> None:
    """Four ETFs, each failing exactly one of three criteria (or none) --
    only the one satisfying all three should survive, proving AND
    semantics rather than any-match-passes."""
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)

    etf_passes_all = _make_etf(conn, "ALL", "Passes All")
    etf_fails_score = _make_etf(conn, "FSC", "Fails Score")
    etf_fails_dimension = _make_etf(conn, "FDM", "Fails Dimension")
    etf_fails_drawdown = _make_etf(conn, "FDD", "Fails Drawdown")

    score_all = _make_score(etf_passes_all, profile, "80")
    score_fails_score = _make_score(etf_fails_score, profile, "50")
    score_fails_dimension = _make_score(etf_fails_dimension, profile, "80")
    score_fails_drawdown = _make_score(etf_fails_drawdown, profile, "80")
    for score in (score_all, score_fails_score, score_fails_dimension, score_fails_drawdown):
        insert_score(conn, score)

    insert_dimension_score(conn, _make_dimension_score(score_all, Dimension.MOMENTUM, "65"))
    insert_dimension_score(conn, _make_dimension_score(score_fails_score, Dimension.MOMENTUM, "65"))
    insert_dimension_score(conn, _make_dimension_score(score_fails_dimension, Dimension.MOMENTUM, "40"))
    insert_dimension_score(conn, _make_dimension_score(score_fails_drawdown, Dimension.MOMENTUM, "65"))

    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_passes_all, "-0.10"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_fails_score, "-0.10"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_fails_dimension, "-0.10"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf_fails_drawdown, "-0.30"))

    criteria = ETFScreeningCriteria(
        min_overall_score=Decimal("70"),
        min_dimension_scores={Dimension.MOMENTUM: Decimal("60")},
        max_drawdown=Decimal("-0.20"),
    )

    result = screen_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        criteria=criteria,
        risk_definition_id=risk_definition.indicator_definition_id,
    )

    assert [entry.etf_id for entry in result] == [etf_passes_all.etf_id]


def test_get_top_candidates_truncates_to_limit(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    insert_score(conn, _make_score(etf_a, profile, "95"))
    insert_score(conn, _make_score(etf_b, profile, "90"))
    insert_score(conn, _make_score(etf_c, profile, "80"))

    result = get_top_candidates(conn, profile.scoring_profile_id, SESSION_DATE, limit=2)

    assert len(result) == 2


def test_get_top_candidates_preserves_screen_etfs_ordering(conn: sqlite3.Connection) -> None:
    """Proves get_top_candidates() performs no ranking of its own: its
    result is exactly the first N entries of the unbounded screen_etfs()
    result, in the same order."""
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    # Inserted out of score order, same as
    # test_generate_ranked_etf_report_preserves_ranking_order.
    insert_score(conn, _make_score(etf_c, profile, "80"))
    insert_score(conn, _make_score(etf_a, profile, "95"))
    insert_score(conn, _make_score(etf_b, profile, "90"))

    unbounded = screen_etfs(conn, profile.scoring_profile_id, SESSION_DATE)
    result = get_top_candidates(conn, profile.scoring_profile_id, SESSION_DATE, limit=2)

    assert result == unbounded[:2]


def test_get_top_candidates_limit_at_survivor_count_returns_all_no_padding(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    insert_score(conn, _make_score(etf_a, profile, "90"))
    insert_score(conn, _make_score(etf_b, profile, "70"))

    result = get_top_candidates(conn, profile.scoring_profile_id, SESSION_DATE, limit=10)

    assert len(result) == 2
    assert {entry.etf_id for entry in result} == {etf_a.etf_id, etf_b.etf_id}


def test_get_top_candidates_candidate_etf_ids_passthrough(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    insert_score(conn, _make_score(etf_a, profile, "90"))
    insert_score(conn, _make_score(etf_b, profile, "80"))
    insert_score(conn, _make_score(etf_c, profile, "70"))

    result = get_top_candidates(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        limit=10,
        candidate_etf_ids=[etf_a.etf_id, etf_b.etf_id],
    )

    assert {entry.etf_id for entry in result} == {etf_a.etf_id, etf_b.etf_id}


def test_get_top_candidates_criteria_filters_before_limiting(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_at_threshold = _make_etf(conn, "ATT", "At Threshold")
    etf_below_threshold = _make_etf(conn, "BEL", "Below Threshold")
    insert_score(conn, _make_score(etf_at_threshold, profile, "70"))
    insert_score(conn, _make_score(etf_below_threshold, profile, "69.99"))

    result = get_top_candidates(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        limit=10,
        criteria=ETFScreeningCriteria(min_overall_score=Decimal("70")),
    )

    assert [entry.etf_id for entry in result] == [etf_at_threshold.etf_id]


def test_get_top_candidates_raises_when_max_drawdown_criteria_supplied_without_risk_definition(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    with pytest.raises(InvalidScreeningCriteriaError):
        get_top_candidates(
            conn,
            profile.scoring_profile_id,
            SESSION_DATE,
            limit=10,
            criteria=ETFScreeningCriteria(max_drawdown=Decimal("-0.20")),
        )


def test_get_top_candidates_rejects_zero_limit(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    with pytest.raises(ValueError):
        get_top_candidates(conn, profile.scoring_profile_id, SESSION_DATE, limit=0)


def test_get_top_candidates_rejects_negative_limit(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    with pytest.raises(ValueError):
        get_top_candidates(conn, profile.scoring_profile_id, SESSION_DATE, limit=-1)


def test_get_top_candidates_returns_empty_list_when_no_candidates_match(
    conn: sqlite3.Connection,
) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    insert_score(conn, _make_score(etf, profile, "50"))

    result = get_top_candidates(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        limit=10,
        criteria=ETFScreeningCriteria(min_overall_score=Decimal("70")),
    )

    assert result == []


def test_compare_etfs_returns_requested_scored_etfs(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    insert_score(conn, _make_score(etf_a, profile, "90"))
    insert_score(conn, _make_score(etf_b, profile, "80"))
    insert_score(conn, _make_score(etf_c, profile, "70"))

    result = compare_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        etf_ids=[etf_a.etf_id, etf_b.etf_id, etf_c.etf_id],
    )

    assert {entry.etf_id for entry in result} == {etf_a.etf_id, etf_b.etf_id, etf_c.etf_id}


def test_compare_etfs_ranks_are_local_to_compared_set(conn: sqlite3.Connection) -> None:
    """Excludes the globally-highest-scored ETF from the compared set --
    the remaining two must receive clean, gapless local ranks (1, 2), not
    their rank within the full universe (which would have been 2, 3)."""
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")  # globally rank 1, not compared
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    insert_score(conn, _make_score(etf_a, profile, "95"))
    insert_score(conn, _make_score(etf_b, profile, "80"))
    insert_score(conn, _make_score(etf_c, profile, "70"))

    result = compare_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        etf_ids=[etf_b.etf_id, etf_c.etf_id],
    )

    assert [(entry.rank, entry.etf_id) for entry in result] == [
        (1, etf_b.etf_id),
        (2, etf_c.etf_id),
    ]


def test_compare_etfs_ordering_matches_screen_etfs(conn: sqlite3.Connection) -> None:
    """Proves compare_etfs() performs no ranking of its own: its result is
    exactly what screen_etfs(candidate_etf_ids=etf_ids) already produces,
    in the same order."""
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")
    etf_c = _make_etf(conn, "CCC", "Fund C")
    # Inserted out of score order, same precedent as
    # test_generate_ranked_etf_report_preserves_ranking_order.
    insert_score(conn, _make_score(etf_c, profile, "80"))
    insert_score(conn, _make_score(etf_a, profile, "95"))
    insert_score(conn, _make_score(etf_b, profile, "90"))

    etf_ids = [etf_a.etf_id, etf_b.etf_id, etf_c.etf_id]
    expected = screen_etfs(conn, profile.scoring_profile_id, SESSION_DATE, candidate_etf_ids=etf_ids)
    result = compare_etfs(conn, profile.scoring_profile_id, SESSION_DATE, etf_ids=etf_ids)

    assert result == expected


def test_compare_etfs_missing_score_is_excluded_silently(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf_a = _make_etf(conn, "AAA", "Fund A")
    etf_b = _make_etf(conn, "BBB", "Fund B")  # no Score inserted for this ETF
    insert_score(conn, _make_score(etf_a, profile, "90"))

    result = compare_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        etf_ids=[etf_a.etf_id, etf_b.etf_id],
    )

    assert [entry.etf_id for entry in result] == [etf_a.etf_id]


def test_compare_etfs_single_etf_is_rank_one_of_one(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    insert_score(conn, _make_score(etf, profile, "70"))

    [entry] = compare_etfs(conn, profile.scoring_profile_id, SESSION_DATE, etf_ids=[etf.etf_id])

    assert entry.rank == 1


def test_compare_etfs_empty_list_returns_empty_list(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    result = compare_etfs(conn, profile.scoring_profile_id, SESSION_DATE, etf_ids=[])

    assert result == []


def test_compare_etfs_risk_definition_id_passthrough(conn: sqlite3.Connection) -> None:
    _make_calendar(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    etf = _make_etf(conn, "SPY", "SPDR S&P 500")
    risk_definition = _make_risk_definition()
    insert_indicator_definition(conn, risk_definition)
    insert_score(conn, _make_score(etf, profile, "70"))
    insert_indicator_value(conn, _make_indicator_value(risk_definition, etf, "-0.15"))

    without_risk = compare_etfs(conn, profile.scoring_profile_id, SESSION_DATE, etf_ids=[etf.etf_id])
    [without_risk_entry] = without_risk
    with_risk = compare_etfs(
        conn,
        profile.scoring_profile_id,
        SESSION_DATE,
        etf_ids=[etf.etf_id],
        risk_definition_id=risk_definition.indicator_definition_id,
    )
    [with_risk_entry] = with_risk

    assert without_risk_entry.max_drawdown is None
    assert with_risk_entry.max_drawdown == Decimal("-0.15")
