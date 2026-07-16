from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from core.analytics.domain.models import Score
from core.analytics.domain.ranking import RankedScore, rank_scores

_SESSION_DATE = date(2026, 7, 14)
_COMPUTED_AT = datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc)


def _score(etf_id: str, overall_score: str, score_id: str = "score") -> Score:
    return Score(
        score_id=score_id,
        etf_id=etf_id,
        scoring_profile_id="profile",
        session_date=_SESSION_DATE,
        overall_score=Decimal(overall_score),
        computed_at=_COMPUTED_AT,
    )


def test_rank_scores_empty_input_returns_empty_list() -> None:
    assert rank_scores([]) == []


def test_rank_scores_single_score_is_rank_one() -> None:
    scores = [_score("etf-a", "70")]

    ranked = rank_scores(scores)

    assert ranked == [RankedScore(etf_id="etf-a", overall_score=Decimal("70"), rank=1)]


def test_rank_scores_orders_by_overall_score_descending() -> None:
    scores = [_score("etf-low", "30"), _score("etf-high", "90"), _score("etf-mid", "60")]

    ranked = rank_scores(scores)

    assert [r.etf_id for r in ranked] == ["etf-high", "etf-mid", "etf-low"]
    assert [r.rank for r in ranked] == [1, 2, 3]


def test_rank_scores_tie_break_is_etf_id_ascending() -> None:
    scores = [_score("etf-z", "50"), _score("etf-a", "50"), _score("etf-m", "50")]

    ranked = rank_scores(scores)

    assert [r.etf_id for r in ranked] == ["etf-a", "etf-m", "etf-z"]
    assert [r.rank for r in ranked] == [1, 2, 3]


def test_rank_scores_is_deterministic_regardless_of_input_order() -> None:
    a = _score("etf-a", "70")
    b = _score("etf-b", "70")
    c = _score("etf-c", "40")

    first = rank_scores([a, b, c])
    second = rank_scores([c, b, a])

    assert first == second


def test_rank_scores_identical_input_produces_identical_output() -> None:
    scores = [_score("etf-a", "70"), _score("etf-b", "40")]

    first = rank_scores(scores)
    second = rank_scores(scores)

    assert first == second
