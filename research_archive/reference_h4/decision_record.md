# `reference_h4` — Phase 7: Decision Record

**Outcome: PASS**

**Date:** 2026-07-25

**Reviewers and independence level:**
- Claude Sonnet 5 (this session), Level 1 (self-review) — hypothesis,
  research proposal, pre-validation, methodology freeze, implementation,
  and every non-gated transition's authorization.
- Claude Sonnet 5, separate session (no conversational continuity), Level
  2 (AI-assisted adversarial review, procedurally independent, **not**
  organizationally independent per `docs/RESEARCH_GOVERNANCE_STANDARD.md`
  Section 4) — independently re-derived the statistical result and
  re-checked the freeze against Standard §3's checklist.
- **Level 3 (independent external review): unavailable.** No
  organizationally independent human reviewer exists on this platform.
  Disclosed here explicitly, per Standard §7's requirement for a PASS
  outcome, rather than silently substituted or omitted. This Decision is
  made at Level 2 as the maximum review tier this platform can currently
  provide.

**Freeze commit in effect:** `7b0e816dc4a8e8321f556d2b52b1ce3818a0f479`
(`methodology.md`, `dataset_manifest.json`, `dataset_hashes/`) — real
`verify_freeze()` result `VERIFIED` at every subsequent bracket through
this Decision, unchanged throughout.

## Result against the frozen criterion

`methodology.md` §7 froze exactly one decision rule: **PASS iff the
bootstrap CI's lower bound for the cross-sectional median excess kurtosis
is strictly greater than 0.**

- Cross-sectional median excess kurtosis: **9.995185801839456**
- 95% bootstrap CI (10,000 iterations, seed 20260725): **[7.611023804796089, 15.26846242545566]**
- Lower bound (7.611) **> 0** → **PASS**, per the frozen rule, applied
  exactly as written, with no post-hoc adjustment.

Independently re-derived and confirmed bit-for-bit by the Level 2 review
(`reviewer_reports/2026-07-25_level2_adversarial_review.md`) and verified
reproducible end-to-end by `core.governance.reproduction_runner.run_reproduction()`
(`reproduction_record.json`, outcome `VERIFIED`).

## Synthesis rationale

The result is unambiguous and not a near-miss: the CI lower bound (7.611)
is well clear of the zero threshold, and all 25 individual ETFs in the
universe show positive point-estimate excess kurtosis (range: 2.93 to
35.51, per `experiment_results/kurtosis_results_2026-07-25.json`) — the
finding is not driven by a small subset of the universe. This is
consistent with the well-established prior literature on fat-tailed
financial returns cited in `hypothesis.md`.

**Disclosed limitation carried into this Decision** (from
`prevalidation_plan.md` / `methodology.md`, refined by the Level 2
review): `PriceBar.close` is not confirmed dividend-adjusted. The Level 2
review's empirical spot-check found no evidence of unadjusted-split jumps
in this data (Yahoo's `close` field appears already split-adjusted in
practice), narrowing the open risk to the smaller, unconfirmed
dividend-adjustment component. Given the CI lower bound's large margin
above zero, this residual limitation is not sufficient to change the
PASS outcome — even a modest kurtosis inflation from unadjusted dividends
would need to explain nearly the entire 7.6-point margin to flip the
result, which the disclosed effect size (typically low-single-digit
percentage moves at ex-dividend dates) cannot plausibly do. This
reasoning is stated explicitly here rather than left implicit, per
Standard §7's requirement that a PASS record state a synthesis rationale
connecting evidence to outcome.

## Terminal discipline

Per Standard §7, this PASS outcome and its evidence package are final for
this specific cycle; the next allowed action is Phase 8 Archive.

## This cycle's stated purpose (recap)

Per `hypothesis.md`: this cycle's purpose was proving the Phase A–E
governance machinery end-to-end against the real repository for the first
time — not an alpha search and not a claim of tradeable value. The PASS
outcome here certifies that the frozen methodology and its acceptance
criterion were met; it does not, by itself, constitute or authorize any
downstream use (capital allocation, production scoring, or otherwise),
which Standard §7's PASS-path explicitly leaves to "whatever separate
deployment process exists outside this standard's scope."
