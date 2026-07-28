# `reference_h2` — Construction Attempt 1 Specification

**Status: research-definition artifact only. This is Attempt 1 of the
maximum three permitted under
[`research_archive/reference_h2/prevalidation_plan.md`](prevalidation_plan.md)
Section 2 ("Construction attempt policy"). It freezes one candidate H2
construction so that Gate 1 (signal independence) can later be run
against it. It is not Gate 1 itself, not an implementation, not a
backtest, and not a performance, correlation, or IC calculation of any
kind. No forward return, correlation figure, overlap figure, p-value, or
other outcome/evidence figure is read, computed, produced, or referenced
anywhere in this document. This document does not execute
`experiments/validate_h2_gate1_independence.py`, does not interpret any
prior run of it (none has occurred), and does not modify
`research_archive/reference_h2/transition_records.jsonl` or any
lifecycle code.**

This document exists because
`research_archive/reference_h2/prevalidation_plan.md` Section 1 states
that logging a construction attempt is "a future, separate act under
Section 2," and Section 2 of that plan requires the attempt cap, the
exact definition of an attempt, and the pre-log attestation to be
defined *before* any attempt is logged — all of which the prevalidation
plan already satisfies. This document is that future, separate act: the
first logged construction attempt. Gates 1 through 4 of the
prevalidation plan remain entirely open after this document; nothing
below satisfies any of them.

---

## 1. Purpose

This document freezes Construction Attempt #1 for `reference_h2`: one
fully specified candidate scoring construction, submitted together with
its mandatory pre-log attestation (Section 3, below), so that a future,
separately performed Gate 1 evaluation has a single, fixed artifact to
evaluate.

**No Gate 1 evaluation is performed by this document.** This document
does not compute, report, or reference:

- any cross-sectional Spearman rank correlation between this
  construction and `reference_v1`'s MOMENTUM (`SMA(20)`) score;
- any ranking-extreme overlap fraction;
- any degenerate-case, moderate-correlation, or low-correlation
  determination;
- any output of `experiments/validate_h2_gate1_independence.py`, run or
  unrun;
- any Gate 1, Gate 2, Gate 3, or Gate 4 outcome, partial or final.

Freezing this construction is a necessary precondition for Gate 1 (per
the prevalidation plan's Section 3 Gate 1 "Ordering requirement": the
economic rationale and construction must be frozen before the
independence check is run against it) — it is not Gate 1 work itself,
exactly as `research_archive/reference_h3/attempt_001_specification.md`
Section 6 states of its own equivalent artifact ("This document performs
no implementation, no experiment, no backtest... it defines exactly one
candidate for later, independent Gate 1 review").

---

## 2. Frozen construction

Every element below is fixed exactly once, for Attempt #1 only. None of
it was chosen, adjusted, or checked against any measured correlation
with MOMENTUM, against `reference_v1`'s or `reference_v2_h1`'s or
`reference_h3`'s observed results, or against any other outcome or
evidence figure — see Section 3's attestation. This section fixes only
the elements a Gate 1 independence check requires (a same-date,
score-to-score construction); it does not fix, and explicitly leaves
open, the elements Gate 4's checklist reserves for Methodology Freeze
alone (forecast horizon, evaluation metrics, rejection/promotion
criteria — see "What remains open," below).

### 2.1 Universe

The existing `reference_v1` 25-ETF universe, unchanged:
`experiments/daily_etf_universe_update.py:89-120` (`ETF_UNIVERSE`). Not a
subset, superset, or reordering. Using the identical universe means no
re-scoping of Gate 1's independence check is required under the
prevalidation plan Section 3's "universe change dependency" clause,
since existing MOMENTUM scores already cover every ticker used here.

### 2.2 Required inputs

Daily close-to-close prices for all 25 ETFs — the same input data
`reference_v1`'s MOMENTUM already consumes. No new data source,
provider, or field is introduced. A fresh, dated Gate 2 data-adequacy
check remains separate, future, unperformed work (prevalidation plan
Section 3, Gate 2); this document does not perform it and does not
assume its outcome.

### 2.3 Signal family

Absolute trailing-return rank: for each ETF, a single-series,
own-history quantity (unlike `reference_h3`'s peer-relative
construction), computed from that ETF's own price history alone, with
no peer group, benchmark subtraction, or segment grouping of any kind.
This matches the plain "trailing-12-1-month-return-rank" construction
already named, but not evaluated, in
`research_archive/reference_h2/prevalidation_plan.md` Section 3 Gate 1
("Component 1 — SMA(20)-rank vs. trailing-12-1-month-return-rank
correlation check") and in
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` Section 1 item 2.
Freezing this document to the already-named construction, rather than a
newly invented one, means Attempt #1 tests the exact candidate those
prior documents already identified as the relevant Gate 1 evidence item
— it does not select a construction the correlation is expected to
favor, since no correlation for any candidate has been computed under
this cycle.

### 2.4 Score definition (frozen)

For ETF *i*, on ranking date *t*, with trading-day index *t* in the
platform's trading-day calendar:

> `H2_score_i(t)` = close-to-close cumulative log return of ETF *i* from
> trading day `(t − SKIP_TRADING_DAYS − FORMATION_TRADING_DAYS)` to
> trading day `(t − SKIP_TRADING_DAYS)`.

- **Formation window: 252 trading days, frozen** (approximately 12
  calendar months). Justified on a disclosed convention-reuse ground,
  not fitted to any outcome: 252 trading days is this platform's own
  already-used 252-trading-day-year convention (the same implicit
  convention `SMA(20)`'s own name already uses for "20 trading days ≈ 1
  month"), and matches the trailing-12-month formation length the
  hypothesis document already names as its research question's subject
  ("a trailing, multi-month cumulative return measure,"
  `research_archive/reference_h2/hypothesis.md`, "Research Question").
- **Skip period: 21 trading days, frozen** (approximately 1 calendar
  month). Justified on the same literature ground
  `research_archive/reference_h2/hypothesis.md`'s "Economic Mechanism"
  section already states for why a skip interval exists at all: to
  separate the underreaction/diffusion effect this construction targets
  from short-horizon reversal dynamics operating on a shorter timescale.
  21 trading days is this platform's own 21-trading-day-month convention
  (the literature-standard "12-1" formation/skip framework named in
  `hypothesis.md`'s mechanism section), not a value chosen by observing
  any correlation or return figure.
- **Return basis: close-to-close log return, frozen.** Chosen for
  consistency with this platform's existing convention for return-based
  constructions (`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md`
  Part 3; `research_archive/reference_h3/attempt_001_specification.md`
  Section 3.5) — reused, not reinvented, and not selected because it
  produces a more or less favorable correlation with MOMENTUM, which has
  not been measured for this or any alternative return basis.
- **Dividend/distribution treatment: price return, frozen (disclosed
  limitation, not silently assumed).** This construction uses raw close
  price only; it does not adjust for dividends or other distributions.
  This is fixed for Attempt #1 on a data-availability ground, not an
  economic preference: no dividend or distribution field exists in the
  current schema (`ETF`, `TradingSession`, `PriceBar`, indicators) —
  the identical data-absence finding already recorded, for the same
  schema, in `research_archive/reference_h2/research_proposal.md`
  Section 4's rejection of the H5 (carry/yield) candidate ("No yield
  field exists in the current schema"). A future total-return
  construction is not foreclosed, but would require new data
  provenance work (per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §6) before
  it could be logged as a different attempt; it is not attempted here.
  Disclosed here as a known limitation of this specific frozen
  construction, consistent with
  `research_archive/reference_h3/attempt_001_specification.md` Section
  3.10's convention of disclosing a construction's structural weak
  points rather than silently deciding around them.

### 2.5 Ranking methodology (frozen)

Cross-sectional ordinal rank of `H2_score_i(t)` across all ETFs with a
valid score on date *t* (descending: a higher trailing return ranks
higher). This is a raw-value ordinal rank, not a z-score or percentile
transform — chosen because Gate 1's Spearman rank correlation check
(prevalidation plan Section 3, "Component 1") is itself rank-based and
therefore invariant to any monotonic rescaling of the underlying score;
introducing a z-score or percentile step ahead of that rank comparison
would add a design choice with no effect on Gate 1's own evidence, for
no economic reason (see Section 4, "Rejected alternatives," below).

### 2.6 Tie handling (frozen)

The existing average-rank convention already used platform-wide for
this project's Spearman rank correlation calculations
(`experiments/validate_reference_v1_significance.py`'s
`_rank_average_ties()`, reused unmodified by
`experiments/validate_h2_gate1_independence.py`). No new tie rule is
introduced for H2.

### 2.7 Missing-data handling (frozen)

An ETF is included in a date's cross-section only if both required
close prices — the formation-start date and the skip-end date — are
directly resolvable from `PriceBar`. No forward-fill, no interpolation,
no partial-window calculation, no synthetic value. This mirrors
`research_archive/reference_h3/attempt_001_specification.md` Section
3.9's identical discipline and
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §6 item 1's immutable-dataset
principle (no ad hoc backfill against data already in use).

### 2.8 Minimum cross-sectional panel size (frozen)

A ranking date is included in Gate 1's reported evidence only if at
least 10 ETFs have both a resolvable H2 candidate score and a resolvable
MOMENTUM score on that date — the same `bucket_size × 2 = 10` minimum-
panel convention already used by
`experiments/validate_reference_v1_significance.py` and
`experiments/validate_h3_gate1_independence.py` (bucket size 5, per
Section 2.9 below). This resolves the prevalidation plan's Gate 4
checklist row "Minimum panel size ... depends on Gate 2's ranking-date
panel span decision" for the specific, narrower purpose of *this*
Gate 1 evidence check only — it is not a Methodology Freeze decision
about the eventual validation panel span, which remains a separate,
future Gate 2/Phase 4 matter (see "What remains open," below).

### 2.9 Ranking-extreme overlap bucket size (frozen)

5, matching the platform's existing `bucket_size` convention reused
across `reference_v1`, `reference_v2_h1`, and `reference_h3` evidence
code. Governs Gate 1 Component 2's top/bottom overlap fraction only.

### 2.10 Evaluation basis for Gate 1 (frozen)

Same-date score-to-score comparison over `reference_v1`'s own analysis
window, 2024-07-17 to 2026-07-17 (`research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json`,
`config.period_start` / `config.period_end`) — the identical window
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` Section 1 item 2
names as "a shared date range." This is a same-date comparison basis,
not a forward-looking evaluation period; no outcome data is touched by
using it.

### What remains open (not fixed by this document)

Consistent with `research_archive/reference_h2/prevalidation_plan.md`
Section 3 Gate 4's checklist and Section 4's "Deferred decisions
boundary," the following remain **Deferred — Methodology Freeze**, and
are neither fixed nor implied by this document, because Gate 1's
same-date, no-outcome-data check does not require them:

- Forecast/holding horizon.
- Statistical test design, significance and robustness protocol.
- Promotion/rejection (acceptance) criteria.
- The Gate 2 ranking-date panel span decision (A/B/C, per the
  prevalidation plan Section 3), which remains separate future Gate 2
  work this document does not perform or assume the outcome of.

---

## 3. Mandatory pre-log attestation

Per `research_archive/reference_h2/prevalidation_plan.md` Section 2,
"Mandatory pre-log attestation." Restated here in full, for this
specific attempt, without weakening or paraphrasing any of the four
required points:

1. **Economic reasoning existed before evaluation.** This construction
   was derived from the economic mechanism already stated in
   `research_archive/reference_h2/hypothesis.md` ("Economic Mechanism":
   underreaction / slow-information-diffusion, with a skip interval
   separating this effect from short-horizon reversal) — not
   reverse-engineered to produce a construction that happens to pass
   Gate 1. The formation window and skip length (Section 2.4, above)
   were fixed by reference to that mechanism's own literature basis (the
   12-1 momentum formation/skip framework named in `hypothesis.md`) and
   to this platform's existing trading-day-convention precedent, not by
   observing any measured relationship with MOMENTUM or any other score.
2. **No forward/outcome data used for selection.** No forward return,
   risk-adjusted return, Information Coefficient, p-value, or any other
   outcome variable was read, computed, or referenced in selecting this
   construction, at any point before or during its submission. No output
   of `experiments/validate_h2_gate1_independence.py` was read,
   generated, or consulted in the drafting of this document; that
   script has not been executed under this cycle.
3. **No selection based on correlation outcome.** No alternative
   construction was selected or discarded based on its cross-sectional
   correlation with `reference_v1`'s MOMENTUM score, or on any other
   already-tested cycle's observed results, before this attempt was
   submitted. No correlation figure of any kind — for this construction
   or any alternative — has been computed under this cycle at the time
   of this attestation.
4. **Alternatives considered and why rejected.** Every alternative
   construction informally considered before this one was submitted is
   disclosed in Section 4, below, by name, together with why each was
   set aside — and each rejection rests on economic or construction-
   logic reasoning only, never on an impression of how a construction
   might correlate with MOMENTUM or with any outcome variable, as
   Section 4 states explicitly for each entry.

This attestation is made by the same session that drafted this
document — Claude Sonnet 5, self-review only (Level 1, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4). It is not, and is not
represented as, Level 2 or Level 3 review. The prevalidation plan's
Section 6 Level 2 confirmation duties for Gate 1 — including independent
reproduction of both Gate 1 components — remain entirely outstanding and
are not performed, claimed, or anticipated by this document.

---

## 4. Alternatives considered

Every alternative below was set aside on economic or construction-logic
reasoning alone, before this attempt was submitted, and before any
correlation, overlap, or other outcome/evidence figure existed for any
candidate under this cycle:

- **No-skip formation (12-month trailing return with no skip
  interval).** Considered as a simpler construction with one fewer
  parameter. Rejected because `research_archive/reference_h2/hypothesis.md`'s
  own "Economic Mechanism" section states the skip interval's purpose
  explicitly: separating the underreaction/diffusion effect from
  short-horizon reversal dynamics. Omitting the skip interval would
  conflate the mechanism this hypothesis targets with a distinct,
  shorter-timescale phenomenon the hypothesis is not about — an
  economic-scope objection, not a numeric one.
- **Shorter formation window (e.g., 126 trading days / ~6 months, matching
  `reference_h3`'s 60-trading-day peer-relative lookback in spirit but
  scaled to an absolute-return construction).** Considered as a way to
  reduce the trailing-history requirement. Rejected because `hypothesis.md`'s
  Research Question specifically names "a trailing, multi-month
  cumulative return measure" formed over a period long enough for the
  literature's underreaction mechanism to operate, and the 12-1
  formation/skip framework is the specific literature form the
  hypothesis's Economic Mechanism section cites; shortening the window
  materially would depart from the mechanism the hypothesis states it is
  testing, not merely adjust a free parameter within it.
- **Simple (arithmetic) return basis instead of log return.** Considered
  as the more literally "cumulative return" reading of `hypothesis.md`'s
  research question. Rejected in favor of log return for internal
  consistency with this platform's existing return-based construction
  convention (`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md`
  Part 3 and `research_archive/reference_h3/attempt_001_specification.md`
  Section 3.5, both log-return-based) — a methodological-consistency
  ground, not a numeric preference based on how either basis happens to
  correlate with MOMENTUM, which was not computed for either basis.
- **Total-return (dividend-adjusted) basis.** Considered, since the
  hypothesis's underlying economic mechanism (price-adjustment
  diffusion) does not conceptually distinguish price return from total
  return. Rejected for Attempt #1 on a data-availability ground: no
  dividend or distribution field exists in the current schema, the same
  finding already recorded for the H5 candidate in
  `research_archive/reference_h2/research_proposal.md` Section 4.
  Constructing a total-return series would require new data provenance
  work under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §6 before it could be
  logged as an attempt; that work has not been done, so it is disclosed
  here as a limitation of this specific attempt (Section 2.4), not
  silently assumed to be immaterial.
- **Z-scored or percentile-normalized score instead of a raw-value
  ordinal rank.** Considered as a way to make cross-date score
  magnitudes comparable. Rejected because Gate 1's evaluation
  methodology (prevalidation plan Section 3, "Component 1") is itself a
  rank correlation, which is invariant to any monotonic transform of the
  underlying score; a normalization step ahead of a rank-based check
  would add a design choice with no effect on Gate 1's own evidence, for
  no economic reason — a parsimony/degrees-of-freedom objection, not an
  outcome-based one.
- **A peer-segment-relative construction, analogous to `reference_h3`'s
  frozen peer-relative design (`research_archive/reference_h3/attempt_001_specification.md`
  Section 3.2, 3.5).** Considered because it is a proven, already-frozen
  pattern on this platform. Rejected because it would conflate H2's
  mechanism with `reference_h3`'s: `hypothesis.md`'s "Novelty Boundary"
  section already distinguishes H2 (a single-series, own-history return
  measure) from `reference_h3`'s explicitly comparative, peer-group-
  dependent mechanism, and adopting a peer-relative form for H2 would
  erode exactly that distinction the hypothesis document already
  established — an economic-distinctness objection, not a numeric one.

None of the above alternatives were assigned a correlation estimate, an
overlap figure, or any other number before being set aside; every
rejection above rests on the reasoning stated, not on any impression of
how any alternative might correlate with MOMENTUM or with any outcome
variable — consistent with Section 3's attestation point 4.

---

## 5. Governance statements

- **This is Attempt #1 of the maximum three** permitted under
  `research_archive/reference_h2/prevalidation_plan.md` Section 2. Two
  further attempts remain available under that cap if a future,
  separately performed Gate 1 evaluation of this attempt does not clear
  Gate 1 and the correct response (per the prevalidation plan's
  "Ordering requirement") is to revisit Gate 3's economic reasoning
  rather than mechanically adjust a parameter.
- **Gate 1 has not yet been evaluated.** No rank correlation, no
  ranking-extreme overlap, and no degenerate-case, moderate-correlation,
  or low-correlation determination has been made for this construction,
  by this document or otherwise, under this cycle.
- **No evidence results are reported.** This document contains no
  figure, statistic, distribution, or output from
  `experiments/validate_h2_gate1_independence.py` or any other
  evidence-generation code. That script has not been executed as part of
  producing this document.
- **No PASS/FAIL/INCONCLUSIVE determination is made.** This document
  makes no gate-level or cycle-level determination of any kind. It is
  not, and does not purport to be, an instance of
  `research_archive/reference_h2/prevalidation_plan.md` Section 7's
  final-determination template.
- **No lifecycle transition occurs.** No `advance_phase()` call, no
  `DecisionRecorder.append()` call, and no append to
  `research_archive/reference_h2/transition_records.jsonl` is made or
  implied by this document. `reference_h2` remains in PRE_VALIDATION,
  exactly as recorded at sequence 1 of that file
  (`RESEARCH_PROPOSAL → PRE_VALIDATION`, commit `4030d86`).

---

## 6. Traceability

This document is a construction-attempt artifact under, and does not
supersede, override, or restate independently of:

- [`research_archive/reference_h2/hypothesis.md`](hypothesis.md) —
  Phase 1, the economic mechanism (underreaction / slow-information-
  diffusion with a skip interval) this construction implements, and the
  "Novelty Boundary" and "Known Open Questions" this attempt resolves
  only for the narrow purpose of Gate 1, not more broadly.
- [`research_archive/reference_h2/research_proposal.md`](research_proposal.md) —
  Phase 2, the candidate-selection and rejected-alternatives record
  (Sections 3–4) and the H5 data-availability finding (Section 4) this
  document's dividend-treatment disclosure (Section 2.4) relies on.
- [`research_archive/reference_h2/prevalidation_plan.md`](prevalidation_plan.md) —
  Phase 3, Section 2's construction-attempt policy and mandatory
  pre-log attestation this document satisfies, and Section 3's Gate 1
  methodology and Gate 4 checklist this document's frozen elements
  (Section 2, above) map onto.

No other document authorizes, supersedes, or is superseded by this one.
