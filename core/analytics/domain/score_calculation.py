from __future__ import annotations

from decimal import Decimal

from core.analytics.domain.calculations import mean
from core.analytics.domain.models import Dimension


def calculate_score(
    dimension_values: dict[Dimension, Decimal],
) -> tuple[dict[Dimension, Decimal], Decimal]:
    """Pure scoring calculation: the Phase 3 reference methodology.

    Each Dimension's score is exactly the (already-resolved) indicator
    value supplied for it, unmodified -- a placeholder methodology that
    proves the scoring engine mechanism (versioning, immutability,
    atomicity, idempotency), not a real scoring model. overall_score is
    the unweighted arithmetic mean across all dimension scores.

    Pure: no database access, no Clock, no current date, no randomness.
    Every input this needs is passed in by the caller -- see
    core/analytics/scoring_pipeline.py for how dimension_values is resolved
    from a ScoringProfile and the relevant IndicatorValues.
    """
    if not dimension_values:
        raise ValueError("calculate_score() requires at least one dimension value")
    dimension_scores = dict(dimension_values)
    overall_score = mean(list(dimension_scores.values()))
    return dimension_scores, overall_score
