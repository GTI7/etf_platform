"""Tests for core/statistics/significance.py.

Two kinds of test live here, per
docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Section 7:

1. Characterization tests against known, hand-computable inputs --
   proving the extracted functions behave the way the Statistics
   domain is supposed to (correct math, correct edge cases).
2. Drift-regression tests proving the new ``core.statistics.significance``
   functions produce results IDENTICAL to the original inlined
   implementations in ``experiments/validate_reference_v1_significance.py``
   on the same fixed inputs -- the only tests in this repository allowed
   to import from an ``experiments/`` script, and only to prove the copy
   is faithful. Per Section 7, these exist to confirm the extraction is
   correct and are not a permanent coupling; they may be deleted once
   Phase 1A is reviewed and accepted.
"""

from __future__ import annotations

import random

import pytest

from core.statistics.significance import (
    bootstrap_ci,
    daily_ic_series,
    empirical_p_value,
    holm_bonferroni,
    mean_ic,
    pearson_correlation,
    percentile,
    permutation_null,
    rank_average_ties,
    spearman_correlation,
    top_bottom_spread,
)
from experiments.validate_reference_v1_significance import (
    _pearson as old_pearson,
)
from experiments.validate_reference_v1_significance import (
    _percentile as old_percentile,
)
from experiments.validate_reference_v1_significance import (
    _rank_average_ties as old_rank_average_ties,
)
from experiments.validate_reference_v1_significance import (
    _spearman as old_spearman,
)
from experiments.validate_reference_v1_significance import (
    bootstrap_ci as old_bootstrap_ci,
)
from experiments.validate_reference_v1_significance import (
    daily_ic_series as old_daily_ic_series,
)
from experiments.validate_reference_v1_significance import (
    empirical_p_value as old_empirical_p_value,
)
from experiments.validate_reference_v1_significance import (
    holm_bonferroni as old_holm_bonferroni,
)
from experiments.validate_reference_v1_significance import (
    mean_ic as old_mean_ic,
)
from experiments.validate_reference_v1_significance import (
    permutation_null as old_permutation_null,
)
from experiments.validate_reference_v1_significance import (
    top_bottom_spread as old_top_bottom_spread,
)

# ---------------------------------------------------------------------------
# Characterization tests -- known inputs, known correct outputs.
# ---------------------------------------------------------------------------


def test_rank_average_ties_no_ties_is_1_indexed() -> None:
    assert rank_average_ties([30.0, 10.0, 20.0]) == [3.0, 1.0, 2.0]


def test_rank_average_ties_ties_get_average_rank() -> None:
    # Two values tied for ranks 2 and 3 -> both get 2.5.
    assert rank_average_ties([10.0, 20.0, 20.0, 30.0]) == [1.0, 2.5, 2.5, 4.0]


def test_pearson_correlation_perfect_positive() -> None:
    assert pearson_correlation([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)


def test_pearson_correlation_zero_variance_is_none() -> None:
    assert pearson_correlation([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) is None


def test_spearman_correlation_perfect_monotonic() -> None:
    assert spearman_correlation([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == pytest.approx(1.0)
    assert spearman_correlation([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) == pytest.approx(-1.0)


def test_spearman_correlation_zero_variance_is_none() -> None:
    assert spearman_correlation([1, 1, 1], [1, 2, 3]) is None


def test_percentile_median_of_odd_length() -> None:
    assert percentile([1.0, 2.0, 3.0], 50) == 2.0


def test_percentile_single_value() -> None:
    assert percentile([7.0], 50) == 7.0


def test_percentile_empty_raises() -> None:
    with pytest.raises(ValueError):
        percentile([], 50)


def _panel(*, score_key: str = "score") -> list[dict]:
    return [
        {
            "etf_ids": ["a", "b", "c", "d"],
            score_key: {"a": 4.0, "b": 3.0, "c": 2.0, "d": 1.0},
            "forward_return": {"a": 0.04, "b": 0.03, "c": 0.02, "d": 0.01},
        },
        {
            "etf_ids": ["a", "b", "c", "d"],
            score_key: {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0},
            "forward_return": {"a": 0.01, "b": 0.02, "c": 0.03, "d": 0.04},
        },
    ]


def test_daily_ic_series_perfect_rank_agreement_each_day() -> None:
    panel = _panel()
    series = daily_ic_series(panel, "score")
    assert len(series) == 2
    assert all(value == pytest.approx(1.0) for value in series)


def test_mean_ic_averages_daily_ic() -> None:
    assert mean_ic(_panel(), "score") == pytest.approx(1.0)


def test_top_bottom_spread_positive_when_score_predicts_return() -> None:
    spread = top_bottom_spread(_panel(), "score", bucket_size=1)
    assert spread == pytest.approx(0.03)


def test_permutation_null_returns_requested_iteration_count() -> None:
    panel = _panel()
    rng = random.Random(1)
    null = permutation_null(panel, "score", mean_ic, iterations=25, rng=rng)
    assert len(null) == 25
    assert all(-1.0 <= value <= 1.0 for value in null)


def test_empirical_p_value_extreme_observed_is_small() -> None:
    null = [0.0] * 100
    assert empirical_p_value(1.0, null) == 0.0
    assert empirical_p_value(0.0, [0.0] * 5) == 1.0


def test_empirical_p_value_empty_null_is_one() -> None:
    assert empirical_p_value(0.5, []) == 1.0


def test_bootstrap_ci_returns_ordered_interval() -> None:
    panel = _panel() * 10  # long enough for a block bootstrap to run
    rng = random.Random(2)
    ci = bootstrap_ci(panel, mean_ic, "score", block_length=2, iterations=50, rng=rng)
    assert ci is not None
    low, high = ci
    assert low <= high


def test_bootstrap_ci_none_when_insufficient_estimates() -> None:
    # A single-entry panel can never form a usable block resample of
    # length > 1 producing >= 2 distinct estimates is still possible,
    # so force insufficiency via iterations=0 instead.
    panel = _panel()
    rng = random.Random(3)
    ci = bootstrap_ci(panel, mean_ic, "score", block_length=2, iterations=0, rng=rng)
    assert ci is None


def test_holm_bonferroni_known_textbook_example() -> None:
    result = holm_bonferroni([("a", 0.01), ("b", 0.04), ("c", 0.03), ("d", 0.005)])
    assert result["d"]["adjusted_p_value"] == 0.02  # 0.005 * 4
    assert result["a"]["adjusted_p_value"] == 0.03  # max(0.02, 0.01 * 3)
    assert result["c"]["adjusted_p_value"] == 0.06  # max(0.03, 0.03 * 2)
    assert result["b"]["adjusted_p_value"] == 0.06  # max(0.06, 0.04 * 1)


# ---------------------------------------------------------------------------
# Drift-regression tests -- new core.statistics.significance output must
# equal the original inlined experiments/ implementation's output, on the
# same fixed inputs. Per Section 7, these are the extraction's proof of
# correctness and may be retired once Phase 1A is reviewed.
# ---------------------------------------------------------------------------


def test_rank_average_ties_matches_original() -> None:
    values = [30.0, 10.0, 20.0, 20.0, 5.0]
    assert rank_average_ties(values) == old_rank_average_ties(values)


def test_pearson_correlation_matches_original() -> None:
    xs = [1.0, 5.0, 3.0, 2.0, 4.0]
    ys = [2.0, 3.0, 3.0, 1.0, 5.0]
    assert pearson_correlation(xs, ys) == old_pearson(xs, ys)


def test_spearman_correlation_matches_original() -> None:
    xs = [1.0, 5.0, 3.0, 2.0, 4.0]
    ys = [2.0, 3.0, 3.0, 1.0, 5.0]
    assert spearman_correlation(xs, ys) == old_spearman(xs, ys)


def test_percentile_matches_original() -> None:
    values = sorted([3.1, 1.2, 9.9, 4.4, 2.2, 7.7])
    for pct in (0, 2.5, 25, 50, 75, 97.5, 100):
        assert percentile(values, pct) == old_percentile(values, pct)


def test_daily_ic_series_matches_original() -> None:
    panel = _panel(score_key="raw_blend")
    assert daily_ic_series(panel, "raw_blend") == old_daily_ic_series(panel, "raw_blend")


def test_mean_ic_matches_original() -> None:
    panel = _panel(score_key="raw_blend")
    assert mean_ic(panel, "raw_blend") == old_mean_ic(panel, "raw_blend")


def test_top_bottom_spread_matches_original() -> None:
    panel = _panel(score_key="raw_blend")
    assert top_bottom_spread(panel, "raw_blend", 1) == old_top_bottom_spread(panel, "raw_blend", 1)


def test_permutation_null_matches_original_given_same_seed() -> None:
    panel = _panel(score_key="raw_blend") * 5
    new_null = permutation_null(panel, "raw_blend", mean_ic, iterations=200, rng=random.Random(42))
    old_null = old_permutation_null(panel, "raw_blend", old_mean_ic, iterations=200, rng=random.Random(42))
    assert new_null == old_null


def test_empirical_p_value_matches_original() -> None:
    null = [0.1, -0.2, 0.3, -0.4, 0.05]
    assert empirical_p_value(0.25, null) == old_empirical_p_value(0.25, null)


def test_bootstrap_ci_matches_original_given_same_seed() -> None:
    panel = _panel(score_key="raw_blend") * 10
    new_ci = bootstrap_ci(panel, mean_ic, "raw_blend", block_length=3, iterations=100, rng=random.Random(7))
    old_ci = old_bootstrap_ci(panel, old_mean_ic, "raw_blend", block_length=3, iterations=100, rng=random.Random(7))
    assert new_ci == old_ci


def test_holm_bonferroni_matches_original() -> None:
    labeled = [("a", 0.01), ("b", 0.04), ("c", 0.03), ("d", 0.005), ("e", 0.2)]
    assert holm_bonferroni(labeled) == old_holm_bonferroni(labeled)
