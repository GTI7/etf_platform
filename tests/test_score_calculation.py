from __future__ import annotations

from decimal import Decimal

import pytest

from core.analytics.domain.models import Dimension
from core.analytics.domain.score_calculation import calculate_score


def test_calculate_score_passes_dimension_values_through_unmodified() -> None:
    dimension_values = {Dimension.MOMENTUM: Decimal("70"), Dimension.VALUE: Decimal("30")}

    dimension_scores, overall_score = calculate_score(dimension_values)

    assert dimension_scores == dimension_values


def test_calculate_score_overall_is_unweighted_mean() -> None:
    dimension_values = {Dimension.MOMENTUM: Decimal("70"), Dimension.VALUE: Decimal("30")}

    _, overall_score = calculate_score(dimension_values)

    assert overall_score == Decimal("50")


def test_calculate_score_single_dimension() -> None:
    dimension_values = {Dimension.MOMENTUM: Decimal("450.123456789")}

    dimension_scores, overall_score = calculate_score(dimension_values)

    assert dimension_scores == dimension_values
    assert overall_score == Decimal("450.123456789")


def test_calculate_score_is_deterministic() -> None:
    dimension_values = {Dimension.MOMENTUM: Decimal("70"), Dimension.VALUE: Decimal("30")}

    first = calculate_score(dimension_values)
    second = calculate_score(dimension_values)

    assert first == second


def test_calculate_score_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        calculate_score({})
