# Statistics Domain

**Status:** Phase 1A of `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md`
(Step 2). First populated module. Not a redesign of anything -- every
function below is a behavior-preserving extraction of code that already
existed and already produced REFERENCE v1's, REFERENCE v2 H1's, and
H3's published results.

## Responsibility

Per `docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.3, Statistics is a
pure, stateless computational library: every function takes plain
numeric/sequence inputs and returns plain numeric outputs, with zero
knowledge of ETFs, tickers, hypotheses, gates, or any other
research-specific concept. It is Layer 0 (a foundation) in the
platform's dependency graph, alongside Data -- neither depends on the
other, and Statistics depends on nothing at all.

`core/statistics/significance.py` is a copy (not a move) of the
significance-testing helpers that have lived inside
`experiments/validate_reference_v1_significance.py` since REFERENCE v1.
That script -- and the three later scripts that import these same
functions directly from it (`validate_reference_v2_h1_significance.py`,
`validate_h3_gate1_independence.py`,
`validate_h3_phase6_economic_validation.py`) -- remain completely
unmodified. They are historical, evidence-producing code; this
extraction does not change what "reproduce REFERENCE v1 / REFERENCE v2
H1 / H3" means for any of those three closed cycles.

## Functions provided

All in `core/statistics/significance.py`:

**Ranking and correlation**
- `rank_average_ties(values)` -- ascending rank, ties get the average
  rank (the convention Spearman correlation requires).
- `pearson_correlation(xs, ys)` -- Pearson correlation; `None` if
  either series has zero variance.
- `spearman_correlation(xs, ys)` -- Pearson correlation computed on
  ranks (average-rank tie handling).
- `percentile(sorted_values, pct)` -- linear-interpolation percentile
  of an already-sorted sequence.

**IC calculations**
- `daily_ic_series(panel, score_key)` -- one Spearman correlation per
  period (`score_key`'s cross-section vs. that period's forward
  returns), never pooled across periods.
- `mean_ic(panel, score_key)` -- the mean of `daily_ic_series`.

**Portfolio spread calculations**
- `top_bottom_spread(panel, score_key, bucket_size)` -- average
  (top-bucket minus bottom-bucket) forward return across periods,
  ranked by `score_key`.

**Permutation testing**
- `permutation_null(panel, score_key, statistic_fn, iterations, rng)`
  -- empirical null distribution for `statistic_fn(panel, score_key)`,
  built from independent within-period shuffles of `score_key` only.
- `empirical_p_value(observed, null_distribution)` -- two-sided
  empirical p-value against a null distribution, no theoretical
  distributional assumption.

**Bootstrap confidence intervals**
- `bootstrap_ci(panel, statistic_fn, score_key, block_length,
  iterations, rng)` -- 95% CI via block bootstrap; a whole panel entry
  (all ids for a period) resamples as one unit, never an id
  independently of its peers.

**Multiple testing correction**
- `holm_bonferroni(labeled_p_values)` -- Holm-Bonferroni step-down
  correction across simultaneous `(label, raw_p_value)` pairs.

### The `panel` data shape

`mean_ic`, `top_bottom_spread`, `permutation_null`, and `bootstrap_ci`
operate on a `panel: list[dict]` -- one dict per period, each mapping
opaque entity-id strings to plain numeric values under an arbitrary
`score_key`, plus a fixed `"forward_return"` key and an `"etf_ids"` key
naming that period's set of entity ids. The `"etf_ids"` key name is
inherited verbatim from the source script's data contract; no function
that reads it inspects the ids as anything other than dictionary keys,
so the same contract works for any cross-sectional panel regardless of
asset class.

### Not extracted in Phase 1A

`core/statistics/ranking.py` (`top_bottom_spread` as a
score-agnostic ranking primitive, `rank_entities`, `ic_decay`) was
explicitly deferred by
`docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Section 4: "only if/when
a second caller beyond the ETF-scoring path needs them; otherwise
deferred." No second caller exists yet, so it was not created --
adding it now would be speculative abstraction ahead of a concrete
need, which this repository's own discipline (and the task's explicit
scope) rules out.

## Guarantees

- **Deterministic given explicit inputs.** Every function that involves
  randomness (`permutation_null`, `bootstrap_ci`) takes an explicit
  `random.Random` instance; nothing reads a global or implicit RNG
  state. Two calls with the same seeded `rng` and the same panel
  produce the same result.
- **Behavior-preserving extraction.** Every function's formula, tie
  handling, percentile interpolation, resampling scheme, and
  Holm-Bonferroni construction is unchanged from the original inlined
  implementation. Only four functions were renamed in the process
  (`_spearman` -> `spearman_correlation`, `_pearson` ->
  `pearson_correlation`, `_rank_average_ties` -> `rank_average_ties`,
  `_percentile` -> `percentile`, moving from private-to-a-script to
  public-in-a-library); the renaming changes no numeric behavior, and
  is characterized by `tests/test_statistics_significance.py`'s
  drift-regression tests against the original functions.
- **No I/O, no database, no Clock.** Every function operates on values
  already in memory.
- **No dependency on any other domain.** `core/statistics/` imports
  nothing from `core.market_data`, `core.analytics`,
  `core.governance`, `core.validation`, `core.research`,
  `core.reporting`, or `experiments`. Verified by
  `python -m tools.check_import_boundaries`.

## Explicitly out of scope

- **No dataset access.** Statistics never reads a database, a file, or
  a dataset snapshot -- it is handed plain values by its caller.
- **No knowledge of "acceptance criteria," "gates," or "hypotheses."**
  Those are Validation's and Research's vocabulary (Architecture
  Section 4.2 / 4.1), not Statistics'.
- **No new statistical methods.** Phase 1A copies what already exists;
  it does not add a new test family, a new correction method, or a new
  confidence-interval construction. That is future work against this
  same module, done as an additive function, never an edit to an
  existing one's behavior.
- **No rewiring of the historical scripts.** The four existing
  `experiments/validate_*.py` significance scripts keep importing their
  own (already-shared) implementation from
  `experiments/validate_reference_v1_significance.py`; none of them
  were changed to import from `core.statistics.significance` instead.
  Only code written after Phase 1A is expected to import from this
  module.
