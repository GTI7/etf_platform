"""Migration evidence: core.statistics.significance vs. REFERENCE v1's
original implementation.

**This is not a normal unit test suite.** Per
docs/STATISTICS_DOMAIN.md ("Compatibility tests"), these tests exist to
prove -- permanently, not just at the moment of extraction -- that
``core/statistics/significance.py`` (Phase 1A of
docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Step 2) produces results
IDENTICAL to the historical, already-published implementation inlined
in ``experiments/validate_reference_v1_significance.py`` on the same
fixed inputs. REFERENCE v1's published result depends on that inlined
implementation's exact behavior; this file is the standing evidence
that the new domain module is a faithful copy of it, not a
reimplementation that happens to look similar.

This is the only location in this repository allowed to import from an
``experiments/`` script, and only for this purpose (see
``docs/STATISTICS_DOMAIN.md``). ``experiments/validate_reference_v1_significance.py``
itself remains completely unmodified -- these tests read from it, they
never cause it to change.

**Retention.** Kept permanently as migration evidence, not deleted
after Phase 1A review (superseding the original "may be deleted once
Phase 1A is reviewed and accepted" note in
docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Section 7, written before
Phase 1A review actually happened). See
docs/ARCHITECTURE_DECISIONS.md AD-029.
"""

from __future__ import annotations

import random

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
