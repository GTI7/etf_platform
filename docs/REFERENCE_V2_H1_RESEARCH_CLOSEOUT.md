# REFERENCE v2 H1 (Low Volatility) Research Close-Out

This document closes the H1 (low volatility) research cycle. It does
not modify H1's implementation or propose retuning it. See
`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` for the frozen
hypothesis and methodology, `docs/REFERENCE_V2_H1_GO_CHECKPOINT_REPORT.md`
for the pre-implementation data-suitability check, and
`experiments/validate_reference_v2_h1_significance.py` (commit
`8831d54`) for the implementation that produced the results below.

**Final research status: H1 is ARCHIVED.** Neither H1-A (primary) nor
H1-B (secondary diagnostic) survived Holm-Bonferroni-corrected
permutation testing combined with bootstrap robustness across all
three block lengths — the same pre-registered bar REFERENCE v1 was
held to. Unlike REFERENCE v1, where point estimates were directionally
consistent with the hypothesis, **H1's point estimates for both H1-A
and H1-B are permutation-significant but in the direction opposite to
what the hypothesis predicted** — lower realized volatility was
associated with *lower*, not higher, subsequent raw and risk-adjusted
returns in this sample. H1 is not modified, not deleted, and not
promoted.

## A. Research close-out report

### Original hypothesis

H1-A (primary): ETFs ranked lower in trailing (60-day) realized
volatility would show a higher future raw return than ETFs ranked
higher in realized volatility, at a 20-trading-day horizon. H1-B
(secondary diagnostic): the same ranking would show a higher future
risk-adjusted return (raw return ÷ forward realized volatility).
Neither could be promoted on H1-B alone (spec Part 6).

### Experiments performed

1. GO checkpoint (`docs/REFERENCE_V2_H1_GO_CHECKPOINT_REPORT.md`) —
   data suitability only. Result: GO. 25-ETF universe, 421-422 usable
   ranking dates, zero missing-data exclusions, median cross-sectional
   CV of realized volatility 0.4045 (threshold ≥0.20), 100% panel
   feasibility at the 10-ETF minimum.
2. Full significance test (`validate_reference_v2_h1_significance.py`,
   `run()`) — daily cross-sectional Spearman IC for H1-A and H1-B,
   10,000-iteration within-date permutation test per statistic,
   Holm-Bonferroni correction across the 2-statistic family, block
   bootstrap (2,000 iterations at 20/40/60-day blocks) per statistic.
   Real run: 25 ETFs, 421 ranking dates (2024-10-11 to 2026-06-17),
   seed `2026071801`.

### Statistical results

| Statistic | Observed IC | Adjusted p (Holm-Bonferroni) | Significant? | Bootstrap-robust (20/40/60d all exclude 0)? | Passes |
|---|---|---|---|---|---|
| H1-A (raw return) | −0.117225 | 0.0 | Yes | No | No |
| H1-B (risk-adjusted return) | −0.037941 | 0.0001 | Yes | No | No |

Both observed ICs are negative — higher LowVol score (i.e., *lower*
realized volatility) was associated with *lower* subsequent returns in
this sample, opposite to the hypothesized direction in Part 1. Both are
permutation-significant before correction and remain significant after
Holm-Bonferroni correction. Neither statistic's bootstrap CI excludes
zero at any of the three block lengths (20/40/60 days) — full CIs are
recorded in `reference_v2_h1_significance_report.json` (generated,
currently uncommitted — see Section B).

### Audit conclusions

No dedicated, independent verification audit was performed for this
specific run — unlike REFERENCE v1, which received its own separate
audit deliverable. This is a real, disclosed scoping gap, not a
finding of correctness. What can be said without a full audit: the
statistical machinery used (`mean_ic`, `permutation_null`,
`holm_bonferroni`, `bootstrap_ci`, `_statistic_verdict`) is imported
unmodified from REFERENCE v1's own, already-audited implementation —
nothing about the correlation, permutation, correction, or bootstrap
logic is new to this run. What *is* new and unaudited is H1's own
panel construction, the shared `realized_volatility()` function, and
the H1-A/H1-B outcome-separation logic. A future audit, if performed,
should focus specifically on those three pieces, not the reused
statistical core.

### Remaining limitations

- Same effective-sample-size ceiling identified for REFERENCE v1:
  421 overlapping 20-day-horizon ranking dates reduce to roughly the
  same order of magnitude of effective independent windows (~20),
  independent of which factor is tested.
- Single historical regime (2024–2026 window), same as REFERENCE v1 —
  no claim is made about any other period.
- No dedicated code-only audit of this specific run (see above).
- No standardized effect size was computed by the script itself, only
  observed value, null median, and their difference — consistent with
  the same gap noted in REFERENCE v1's own audit.

### Distinguishing the three kinds of evidence

- **Evidence against the implementation**: not identified, but not
  independently confirmed either — see Audit conclusions above. This
  is an open item, not a clean pass.
- **Evidence against the hypothesis**: stronger here than in
  REFERENCE v1's case. Both H1-A and H1-B produced
  permutation-significant point estimates in the direction *opposite*
  to what the frozen hypothesis (Part 1) predicted — not merely
  "no detectable relationship," but a directionally clear signal
  running counter to it in this specific sample.
- **Insufficient statistical power / insufficient evidence**: still
  real and load-bearing. No bootstrap CI, for either statistic at any
  block length, excludes zero — so the reversed-direction point
  estimate cannot be confirmed as robust to the sample's own serial
  dependence either. The honest reading is that this result *leans
  toward* contradicting H1's hypothesized direction more clearly than
  REFERENCE v1's own result leaned toward confirming its hypothesis,
  but it does not clear the same pre-registered bar in either
  direction. It should not be read as a confident disproof of the
  low-volatility anomaly in general — only as a non-confirmation, with
  a directionally adverse point estimate, of this specific 25-ETF,
  ~2-year implementation.

## B. Frozen artifact inventory

- **Source code**: `experiments/validate_reference_v2_h1_significance.py`,
  commit `8831d54` — the exact implementation this result was produced
  against.
- **Documentation**: this file;
  `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md`;
  `docs/REFERENCE_V2_H1_GO_CHECKPOINT_REPORT.md`.
- **Generated output, currently at risk**: `reference_v2_h1_significance_report.json`
  (repo root) — the exact numeric evidence behind this close-out. It is
  **not currently gitignored** (a disclosed gap from implementation),
  meaning it could be accidentally committed as if it were source, or
  silently overwritten by a future rerun with no durable copy
  preserved either way. Recommended, not yet executed: gitignore it
  (mirroring REFERENCE v1's `reference_v1_significance_report.json`
  convention) and copy a dated, frozen snapshot into a new
  `research_archive/reference_v2_h1/` directory (mirroring
  `research_archive/reference_v1/`'s existing structure — dated JSON +
  `COMMIT.txt` + `README.md`), so this specific result survives any
  future H2/H3 run that reuses the same script's default output path.

## C. Lessons learned

- The experiments-only architecture decision (implementation plan,
  Part 1 — no new `IndicatorDefinition`, `ScoringProfile`, or
  persistence) held up cleanly: H1 was built, run, and archived without
  a single `core/` change, confirming that decision was correct for a
  research cycle whose outcome was genuinely unknown in advance.
- Routing both the trailing score and H1-B's forward-volatility
  denominator through one shared `realized_volatility()` function
  eliminated an entire class of potential silent divergence between
  the two calculations — a concrete benefit of the "one function, two
  windows" design decided during implementation review.
- A 2-statistic study (H1-A/H1-B) reused REFERENCE v1's entire
  statistical core unmodified, needing only a thin outcome-key
  adapter (`build_statistic_view`) — validating the "reuse by import,
  not by refactor" approach recommended in REFERENCE v1's own
  Repository Roadmap.
- The `.gitignore` step for a new script's generated output is easy to
  drop when it isn't part of the original approved plan's explicit
  checklist (it was a deferred "at actual implementation time" note,
  and was then missed at actual implementation time) — worth adding to
  any future script's implementation as a concrete, checked step, not
  a note-to-self.

## D. Next steps for the REFERENCE v2 candidate search

H1's archival returns the project to the ranked shortlist already
established in the REFERENCE v2 research strategy document: H3
(relative strength / sector rotation) was ranked second, close behind
H1, and remains untested. Consistent with REFERENCE v1's own entry
criteria (still binding, unaffected by H1's outcome):

- H1's specific results must not be used to tune, select, or bias any
  future candidate's parameters — the same "no tuning against prior
  results" discipline that governed H1's own selection applies
  unchanged to whatever is evaluated next.
- Any future candidate should still satisfy its own written economic
  rationale, its own GO checkpoint, and the same promotion bar
  (Holm-Bonferroni significance and full three-block bootstrap
  robustness) before implementation — none of that changes because H1
  didn't clear it.
- The `.gitignore` and `research_archive/` gaps noted in Section B
  should be closed before a next candidate's script reuses the same
  output-path conventions, to avoid repeating the same gap.
