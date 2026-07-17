from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from core.analytics.domain.models import Dimension
from core.analytics.domain.ranking import rank_scores
from core.analytics.persistence.repository import get_dimension_scores, get_scores_for_session
from core.market_data.persistence.repository import get_etf
from core.shared.ids import ETFId


@dataclass(frozen=True, slots=True)
class RankedETFReportEntry:
    """One ranked ETF, resolved for display -- no persistence identity
    (no score_id, scoring_profile_id, session_date, or computed_at): just
    what a consumer of the report needs to see.

    dimension_scores exposes the same per-dimension values overall_score
    was already computed from (e.g. {MOMENTUM: ..., VALUE: ...}) -- the
    comparison-by-independent-method view, alongside the existing blended
    figure. No new scoring methodology: rank_scores() and overall_score
    are computed exactly as before."""

    rank: int
    etf_id: ETFId
    ticker: str
    name: str
    overall_score: Decimal
    dimension_scores: dict[Dimension, Decimal]


def generate_ranked_etf_report(
    conn: sqlite3.Connection, scoring_profile_id: str, session_date: date
) -> list[RankedETFReportEntry]:
    """Compose the existing Phase 4 pieces into one usable ranked report:
    get_scores_for_session() -> rank_scores() -> get_etf(), resolving each
    ranked entry's ETF identity (ticker, name) for display.

    Read-only: no writes, no transaction boundary, no new tables. This is
    a composition/use-case function, not a pure domain function -- it
    takes a live connection and calls repository functions directly.

    Ordering is entirely rank_scores()'s: this function does not re-sort,
    re-rank, or apply any business rule of its own -- it only resolves
    identity for whatever order rank_scores() already produced.

    Returns an empty list if no Score exists yet for this
    (scoring_profile_id, session_date) -- a valid, expected outcome (e.g.
    scoring hasn't run for that day), not an error condition.

    Deterministic: for a fixed database state, the same
    (scoring_profile_id, session_date) always produces the same report in
    the same order, inherited from rank_scores()'s own determinism.

    dimension_scores is resolved via the original Score.score_id --
    rank_scores() deliberately drops it (RankedScore carries no
    persistence identity), so a score_id lookup keyed by etf_id is built
    from `scores` before ranking discards it.
    """
    scores = get_scores_for_session(conn, scoring_profile_id, session_date)
    score_id_by_etf = {score.etf_id: score.score_id for score in scores}
    ranked = rank_scores(scores)
    report: list[RankedETFReportEntry] = []
    for ranked_score in ranked:
        etf = get_etf(conn, ranked_score.etf_id)
        dimension_scores = {
            dimension_score.dimension: dimension_score.value
            for dimension_score in get_dimension_scores(conn, score_id_by_etf[ranked_score.etf_id])
        }
        report.append(
            RankedETFReportEntry(
                rank=ranked_score.rank,
                etf_id=ranked_score.etf_id,
                ticker=etf.ticker,
                name=etf.name,
                overall_score=ranked_score.overall_score,
                dimension_scores=dimension_scores,
            )
        )
    return report
