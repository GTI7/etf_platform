from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.analytics.domain.models import Score
from core.shared.ids import ETFId


@dataclass(frozen=True, slots=True)
class RankedScore:
    """A single ETF's position in a ranking.

    Deliberately flat rather than wrapping Score: ranking only concerns
    itself with which ETF, what score, and what rank -- not scoring_profile_id,
    session_date, score_id, or computed_at, which are Score's persistence
    identity, not ranking's business meaning."""

    etf_id: ETFId
    overall_score: Decimal
    rank: int


def rank_scores(scores: list[Score]) -> list[RankedScore]:
    """Deterministically rank Scores by overall_score descending.

    Tie-break is explicit and stable: etf_id ascending. Two calls with the
    same (possibly differently-ordered) input list always produce the same
    output -- no reliance on timestamps, insertion order, or dict/set
    iteration order.

    Pure: no database access, no Clock, no randomness. Ranking is a
    read-only, on-demand computation over already-immutable Score data;
    nothing here is persisted.
    """
    ordered = sorted(scores, key=lambda score: (-score.overall_score, score.etf_id))
    return [
        RankedScore(etf_id=score.etf_id, overall_score=score.overall_score, rank=position)
        for position, score in enumerate(ordered, start=1)
    ]
