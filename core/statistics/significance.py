"""Pure statistical primitives for significance testing.

Extracted (copied, not moved) from
``experiments/validate_reference_v1_significance.py`` per
docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Step 2 / Phase 1A. That
script remains the historical, unmodified, authoritative implementation
for REFERENCE v1's own already-published results; the three other
existing significance scripts (``validate_reference_v2_h1_significance.py``,
``validate_h3_gate1_independence.py``, ``validate_h3_phase6_economic_validation.py``)
already import these exact functions directly from that one module
rather than duplicating them, so this extraction has zero formula
drift to reconcile across the four historical scripts -- there was
only ever one implementation.

Every function here is a straight, behavior-preserving copy: same
formulas, same tie-handling convention, same percentile interpolation,
same permutation/bootstrap resampling scheme, same Holm-Bonferroni
step-down construction, same numeric precision (float, converted once
at the boundary -- see the source script's precision note). No
function's *numeric* behavior was altered during extraction; where a
private helper (``_spearman``, ``_pearson``, ``_rank_average_ties``,
``_percentile`` in the source script) is exposed here under a public
name instead, that is a naming change only, characterized by
``tests/test_statistics_significance.py``'s drift-regression tests
against the original inlined implementations.

Domain-neutral by construction: nothing below knows what an ETF, a
ticker, a hypothesis, or a gate is. The ``panel`` parameter accepted by
``mean_ic``, ``top_bottom_spread``, ``permutation_null``, and
``bootstrap_ci`` is a plain data shape -- a list of per-period
dictionaries, each mapping arbitrary entity-id strings to plain
numeric values under an arbitrary ``score_key`` plus a fixed
``"forward_return"`` key and an ``"etf_ids"`` key naming that period's
set of entity ids. The key name ``"etf_ids"`` is inherited verbatim
from the source script as part of its data contract; the functions
that read it never interpret the ids as anything other than opaque
dictionary keys, so any cross-sectional panel of any asset class can
use this contract unchanged.

Depends on nothing outside the standard library. Per
docs/PLATFORM_ARCHITECTURE_V1.md Section 4.3, this module must never
import from ``core.market_data``, ``core.analytics``, ``core.governance``,
``core.validation``, ``core.research``, ``core.reporting``, or
``experiments`` -- the one hard rule with no exception.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from typing import Any

# ---------------------------------------------------------------------------
# Ranking and correlation
# ---------------------------------------------------------------------------


def rank_average_ties(values: list[float]) -> list[float]:
    """Rank `values` ascending (rank 1 = smallest), average rank assigned
    to ties -- the standard tie-handling convention Spearman correlation
    requires. Pure, deterministic, no I/O."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average_rank = (i + j) / 2 + 1  # 1-indexed
        for k in range(i, j + 1):
            ranks[order[k]] = average_rank
        i = j + 1
    return ranks


def pearson_correlation(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation of two equal-length series, or None if either
    series has zero variance (undefined correlation). Pure, no I/O."""
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return cov / (var_x**0.5 * var_y**0.5)


def spearman_correlation(xs: list[float], ys: list[float]) -> float | None:
    """Spearman rank correlation: Pearson correlation computed on ranks,
    with average-rank tie handling. Pure, no I/O."""
    if len(xs) < 2:
        return None
    return pearson_correlation(rank_average_ties(xs), rank_average_ties(ys))


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolation percentile of an already-sorted list, `pct`
    in [0, 100]. Pure, no I/O -- used for both bootstrap CIs and null
    distribution percentile lookups, deliberately not depending on any
    third-party statistics package."""
    if not sorted_values:
        raise ValueError("percentile() requires at least one value")
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (pct / 100) * (len(sorted_values) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = rank - lower
    return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])


# ---------------------------------------------------------------------------
# IC calculations (information coefficient over a cross-sectional panel)
# ---------------------------------------------------------------------------


def daily_ic_series(panel: list[dict[str, Any]], score_key: str) -> list[float]:
    """One Spearman correlation per period (score_key's cross-section vs.
    that period's forward returns), never pooled across periods.

    Performance note, not a behavior change: forward returns are
    identical across every permutation iteration for a fixed score_key
    (only score_key's id-to-value assignment is shuffled -- see
    ``_shuffle_score_key()``), so ranking them is wasted, repeated work
    across many thousands of calls. When a panel entry has already
    attached a precomputed ``"_return_ranks"`` list, that is reused
    instead of re-ranking forward returns on every call. Falls back to
    computing it fresh when absent (e.g. for a hand-built panel in a
    test), so this optimization can never silently change the result.
    """
    series = []
    for day in panel:
        etf_ids = day["etf_ids"]
        scores = [day[score_key][etf_id] for etf_id in etf_ids]
        score_ranks = rank_average_ties(scores)
        return_ranks = day.get("_return_ranks")
        if return_ranks is None:
            return_ranks = rank_average_ties([day["forward_return"][etf_id] for etf_id in etf_ids])
        ic = pearson_correlation(score_ranks, return_ranks)
        if ic is not None:
            series.append(ic)
    return series


def mean_ic(panel: list[dict[str, Any]], score_key: str) -> float | None:
    return _mean(daily_ic_series(panel, score_key))


# ---------------------------------------------------------------------------
# Portfolio spread calculations
# ---------------------------------------------------------------------------


def top_bottom_spread(panel: list[dict[str, Any]], score_key: str, bucket_size: int) -> float | None:
    """Average (top-bucket average forward return - bottom-bucket average
    forward return) across periods, ranked by score_key."""
    daily_spreads = []
    for day in panel:
        etf_ids = day["etf_ids"]
        if len(etf_ids) < bucket_size * 2:
            continue
        ordered = sorted(etf_ids, key=lambda etf_id: day[score_key][etf_id], reverse=True)
        top = ordered[:bucket_size]
        bottom = ordered[-bucket_size:]
        top_avg = _mean([day["forward_return"][etf_id] for etf_id in top])
        bottom_avg = _mean([day["forward_return"][etf_id] for etf_id in bottom])
        if top_avg is not None and bottom_avg is not None:
            daily_spreads.append(top_avg - bottom_avg)
    return _mean(daily_spreads)


# ---------------------------------------------------------------------------
# Permutation testing
# ---------------------------------------------------------------------------


def _shuffle_score_key(panel: list[dict[str, Any]], score_key: str, rng: random.Random) -> list[dict[str, Any]]:
    """A copy of `panel` with score_key's id-to-value assignment randomly
    reassigned WITHIN each period -- the real set of values observed
    that period is preserved exactly, only which id got which value is
    randomized. Forward returns are untouched."""
    shuffled = []
    for day in panel:
        etf_ids = list(day["etf_ids"])
        values = [day[score_key][etf_id] for etf_id in etf_ids]
        rng.shuffle(values)
        new_day = dict(day)
        new_day[score_key] = dict(zip(etf_ids, values))
        shuffled.append(new_day)
    return shuffled


def permutation_null(
    panel: list[dict[str, Any]],
    score_key: str,
    statistic_fn: Callable[[list[dict[str, Any]], str], float | None],
    iterations: int,
    rng: random.Random,
) -> list[float]:
    """Empirical null distribution for `statistic_fn(panel, score_key)`,
    built from `iterations` independent within-period shuffles of
    score_key only. statistic_fn is called with the same panel-shaped
    argument any statistic function above accepts, so this one function
    serves every statistic without needing a separate permutation
    implementation per statistic."""
    null_values = []
    for _ in range(iterations):
        shuffled_panel = _shuffle_score_key(panel, score_key, rng)
        value = statistic_fn(shuffled_panel, score_key)
        if value is not None:
            null_values.append(value)
    return null_values


def empirical_p_value(observed: float, null_distribution: list[float]) -> float:
    """Two-sided empirical p-value: the fraction of the null distribution
    at least as extreme as the observed value, using the data itself --
    no theoretical distributional assumption."""
    if not null_distribution:
        return 1.0
    extreme = sum(1 for value in null_distribution if abs(value) >= abs(observed))
    return extreme / len(null_distribution)


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------


def _block_bootstrap_resample(
    panel: list[dict[str, Any]], block_length: int, rng: random.Random
) -> list[dict[str, Any]]:
    """One resampled period series, built by drawing contiguous blocks of
    `block_length` consecutive panel entries (with replacement) until
    reaching panel's original length -- every id's data for a given
    resampled period moves together as it was originally observed that
    period, since a whole panel entry is drawn as one unit, never an id
    resampled independently of its peers."""
    n = len(panel)
    resampled: list[dict[str, Any]] = []
    while len(resampled) < n:
        start = rng.randrange(0, n)
        block = [panel[(start + offset) % n] for offset in range(block_length)]
        resampled.extend(block)
    return resampled[:n]


def bootstrap_ci(
    panel: list[dict[str, Any]],
    statistic_fn: Callable[[list[dict[str, Any]], str], float | None],
    score_key: str,
    block_length: int,
    iterations: int,
    rng: random.Random,
) -> tuple[float, float] | None:
    """95% confidence interval for statistic_fn(panel, score_key) via
    block bootstrap at the given block_length. Returns (low, high), or
    None if fewer than 2 resampled estimates were computable."""
    estimates = []
    for _ in range(iterations):
        resampled = _block_bootstrap_resample(panel, block_length, rng)
        value = statistic_fn(resampled, score_key)
        if value is not None:
            estimates.append(value)
    if len(estimates) < 2:
        return None
    estimates.sort()
    return percentile(estimates, 2.5), percentile(estimates, 97.5)


# ---------------------------------------------------------------------------
# Multiple testing correction
# ---------------------------------------------------------------------------


def holm_bonferroni(labeled_p_values: Sequence[tuple[str, float]]) -> dict[str, dict[str, float]]:
    """Holm-Bonferroni step-down correction across the given
    (label, raw_p_value) pairs. Adjusted p-values are monotonically
    non-decreasing in the sort order and capped at 1.0, the standard
    construction -- controls the family-wise error rate across
    simultaneous statistics."""
    n = len(labeled_p_values)
    ordered = sorted(labeled_p_values, key=lambda pair: pair[1])
    results: dict[str, dict[str, float]] = {}
    running_max = 0.0
    for i, (label, raw_p) in enumerate(ordered):
        adjusted = min((n - i) * raw_p, 1.0)
        running_max = max(running_max, adjusted)
        results[label] = {"raw_p_value": raw_p, "adjusted_p_value": running_max}
    return results
