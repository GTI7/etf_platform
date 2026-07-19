# REFERENCE H3 — Construction Attempt 1 Specification

**Status: research-definition artifact only. This is attempt 1 of the
maximum three permitted under
[`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`](../../docs/REFERENCE_H3_PREVALIDATION_PLAN.md)
Section 2 ("Construction attempt log"). It freezes one candidate H3
construction so that Gate 1 (candidate signal independence) can later be
run against it. It is not Gate 1 itself, not an implementation, not a
backtest, and not a performance or IC calculation of any kind. No forward
return, IC, p-value, or other outcome variable is read, computed, or
referenced anywhere in this document.**

This document exists because Gate 3 (economic rationale) and Gate 2
(historical data adequacy) are both independently confirmed PASS —
[`docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`](../../docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md),
confirmed by
[`gate3_independent_review_2026-07-19.md`](gate3_independent_review_2026-07-19.md);
[`gate2_independent_review_2026-07-19_post_remediation.md`](gate2_independent_review_2026-07-19_post_remediation.md)
— and the Prevalidation Plan's required ordering (Section 4) states the
economic rationale must be frozen and the construction chosen *before*
Gate 1's independence check is run. This document is that required,
single, frozen construction. Gates 1 and 4 remain open until this
artifact is reviewed.

---

## 1. Hypothesis definition

**What H3 claims.** ETFs whose recent return has been relatively strong
compared to their own peer market segment will continue to show
relatively strong returns compared to that same peer segment in the
near term, and symmetrically for relatively weak ETFs — because capital
reallocates *between* market segments (sectors, regions, styles, themes,
asset classes) at a slower cadence than the cadence at which
security-specific information is absorbed. This is a claim about the
*persistence of relative standing within a peer segment*, not a claim
about the direction of any ETF's own absolute price trend.

**Why this mechanism should exist.** Per
[`docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`](../../docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md)
Sections 2–3 (not re-derived here, only summarized): two segment-level
investor populations — institutional allocators executing slow,
committee-driven, mandate-constrained rebalancing cycles, and
flow-chasing retail/advisor capital moving into recently-favored
sector/theme ETF wrappers — reallocate capital toward segments that have
recently stood out favorably relative to their peer segments. The
resulting reallocation lag is organizational (governance cadence), not
informational, and resists fast arbitrage because of basis risk in the
hedge and segmented investor clienteles (Gate 3 Section 3). This
mechanism is literature-grounded in industry momentum (Moskowitz and
Grinblatt, 1999), style investing (Barberis and Shleifer, 2003), and
cross-asset/segment momentum (Asness, Moskowitz, and Pedersen, 2013).

**Why it differs from MOMENTUM.** REFERENCE v1's MOMENTUM dimension is
the raw, unnormalized 20-day simple moving average of an ETF's own
closing price (`SMA(20)`, `core/analytics/domain/calculations.py:6-17`,
bound to the `MOMENTUM` dimension via
`core/analytics/scoring_pipeline.py:37`). It is a single-series,
own-history quantity: fully defined for one ETF considered in complete
isolation, requiring no peer, no benchmark, and no group of any kind.
Its economic story (per `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md` and
Gate 3 Section 4) is underreaction/delayed diffusion of
asset-specific information by analysts and traders following that one
asset. H3, as stated above, is a comparative claim by construction — it
has no meaning for an ETF considered alone, and its proposed mechanism
involves different actors (allocators and flow-chasing fund capital)
making a different kind of decision (how much to hold of an entire
category) for a different reason (slow governance cadence, not slow
information diffusion). This distinction is argued in full, and was
independently reviewed, in Gate 3 Section 4 and
`gate3_independent_review_2026-07-19.md` Section 3.1; it is restated
here only as the required hypothesis statement, not re-argued.

---

## 2. Economic mechanism mapping

**Actors involved.**

- Institutional asset allocators (pension funds, endowments, multi-asset
  mandates) who review and adjust sector/region/style tilts on a
  periodic (quarterly-to-annual) committee cycle, using trailing
  relative segment performance as one explicit input.
- Flow-chasing retail and advisor capital entering sector, thematic, and
  regional ETF wrappers specifically because those wrappers make a
  segment-level bet easy to express without security-level conviction.

These are the same two populations named in Gate 3 Section 3 — this
section maps them onto the specific universe and construction, it does
not introduce new actors.

**Capital flow mechanism.** Capital moves *between* the segments a
committee or a flow-chasing investor can name and select (a sector, a
region, a style, an asset class) rather than being redistributed
continuously and instantaneously across all possible allocations. A
segment that has recently stood out favorably against its peer segments
is more likely to receive a larger share of the next round of
allocation decisions than a segment that has recently lagged its peers,
simply because "recently favorable relative to peers" is a legible,
low-cost input to a periodic allocation review — legibility and low
review cost, not any claim about superior forecasting skill, is what
drives the flow.

**Expected persistence mechanism.** Persistence is expected to hold
only until the next review/rebalancing cycle resets or confirms the
allocation, or until the relative standing itself reverses. This is a
governance-cadence-bound persistence claim (Gate 3 Section 3,
"Implementation lag is organizational, not informational"), not an
indefinite trend — the falsification criteria in Gate 3 Section 5
already state that *reversal* rather than continuation at the studied
horizon would count as evidence against this mechanism, and that
carries forward unchanged to this construction.

**Why relative segment rotation is the relevant abstraction.** In this
platform's 25-ETF universe, almost every constituent already
*represents* a distinct market segment on its own — a single sector, a
single region, a single investment theme, or a single broad asset
class — rather than being one of many securities within a segment (see
`experiments/daily_etf_universe_update.py:89-120`, whose inline
category comments already partition the universe this way for
documentation purposes, unrelated to H3). Because of this, "relative
segment rotation" and "relative ETF rotation" are operationally the
same abstraction for this specific universe: comparing an ETF's recent
return against the recent returns of the other ETFs occupying
comparable segment roles *is* comparing segments against each other.
This is what makes relative standing (not absolute, own-history trend)
the right unit for this mechanism and this universe, and it is why the
construction below is built around peer-segment groups rather than
single-security comparisons.

---

## 3. Construction definition

Every design choice below is fixed exactly once. None of it was chosen,
adjusted, or checked against REFERENCE v1's or REFERENCE v2 H1's
observed results, against any forward return, or against any measured
correlation with MOMENTUM — see Section 5's attestation.

### 3.1 Universe

The existing REFERENCE v1 25-ETF universe, unchanged, in full:
`experiments/daily_etf_universe_update.py:89-120`. This is not a
subset, superset, or reordering — using the identical universe means no
re-scoping of the independence check is required under the
Prevalidation Plan's Section 3 "universe change dependency" clause,
since existing MOMENTUM scores already cover every ticker used here.

### 3.2 Peer-segment grouping (frozen)

Six segments, defined by reusing — not re-authoring — the inline
category boundaries already present as comments in
`experiments/daily_etf_universe_update.py:89-120`. These boundaries
predate this document and were authored for universe-documentation
purposes unrelated to H3; reusing them here, rather than proposing a
new taxonomy, removes one entire researcher degree of freedom that
would otherwise need separate justification:

| Segment | Members |
|---|---|
| Global equity | `VT`, `ACWI` |
| US equity | `SPY`, `VTI`, `QQQ`, `IWM` |
| Regional equity | `EFA`, `VGK`, `EWJ`, `EEM` |
| Sectors | `XLK`, `XLF`, `XLE`, `XLV` |
| Themes | `ARKK`, `ICLN`, `SKYY`, `HACK`, `BOTZ` |
| Defensive / alternative assets | `GLD`, `TLT`, `BND`, `VNQ`, `USMV`, `SCHD` |

Every ETF belongs to exactly one segment; the six segments partition the
full 25-ETF universe with no overlap and no residual.

### 3.3 Required inputs

Daily close-to-close prices for all 25 ETFs — the same input data
REFERENCE v1's MOMENTUM already consumes, already available per Gate 2
(`gate2_independent_review_2026-07-19_post_remediation.md`: 2016-09-13
to 2026-07-17, 0 missing, 0 surplus, all 25 ETFs). No new data source,
provider, or field is introduced.

### 3.4 Signal family

Peer-segment-relative excess return: a comparative, cross-sectional
family, structurally distinct from MOMENTUM's single-series family
(Section 1). The score is undefined for an ETF considered without its
segment peers.

### 3.5 Score definition (frozen)

For ETF *i*, in segment *S(i)*, on ranking date *t*:

> `own_return_i(t)` = cumulative close-to-close log return over the
> trailing 60-trading-day window ending at *t* (identical log-return
> methodology to `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md`
> Part 3 — reused, not reinvented).
>
> `peer_return_i(t)` = equal-weighted mean of `own_return_j(t)` over all
> ETFs *j* in segment *S(i)*, *j ≠ i* (the ETF being scored excludes
> itself from its own peer average).
>
> `H3_score_i(t) = own_return_i(t) − peer_return_i(t)`

**Lookback window: 60 trading days, frozen.** Justified on two
independent, non-outcome grounds, not fitted:

1. It matches the institutional review cadence Gate 3 Section 3 itself
   cites as the mechanism's source ("quarterly or annual committee
   cycle") — 60 trading days is approximately one calendar quarter.
2. It reuses, rather than re-derives, the identical 60-day window
   already independently justified for this platform in
   `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 3 (there,
   argued as long enough to reduce estimation noise relative to a
   20-day window while short enough to track current-regime behavior,
   and explicitly distinct from the 20-day forward horizon used
   elsewhere on this platform). Reusing a previously-justified,
   already-frozen window is a research convention, not a fresh
   unconstrained choice made for H3.

This value is deliberately *not* set to 20 trading days to match
MOMENTUM's own `SMA(20)` window. Matching it would risk exactly the
"gaming the independence check" failure mode the Prevalidation Plan
warns against in Section 5 — choosing a construction because it looks
different from MOMENTUM, for no economic reason. The 60-day choice here
is justified independently of MOMENTUM's window entirely (points 1–2
above); that it also happens to differ from MOMENTUM's 20 days is a
byproduct of that independent justification, not the reason for it.

### 3.6 Ranking concept

Cross-sectional ordinal rank of `H3_score_i(t)` across all ETFs with a
valid score on date *t* (descending: higher relative-strength score
ranks higher). Ties are handled by the existing average-rank convention
already used for this platform's Spearman calculations — no new tie
rule is introduced.

### 3.7 Portfolio formation logic

Not computed or implemented by this document. If and when a future,
separately-scoped validation phase (explicitly out of this document's
scope) needs a top-vs-bottom comparison, it would reuse this platform's
already-frozen bucket convention (`bucket_size = 5`, i.e., top-5 vs.
bottom-5 ranked ETFs by `H3_score`, per
`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 6's
inherited minimum-panel rule) rather than a new bucket size chosen for
H3. No such comparison, bucket spread, or portfolio weight is computed
here.

### 3.8 Rebalance concept

The score is conceptually recomputed once per trading day, matching the
existing daily `Score` cadence already implemented in
`core/analytics/scoring_pipeline.py` — no new computation cadence is
introduced. The separate question of what forward holding horizon a
future validation phase would use to test this score is explicitly not
decided here; Gate 1 requires only the score itself (a same-date,
score-to-score comparison against MOMENTUM, per Prevalidation Plan
Section 2), not a forward horizon, so fixing one now would be an
unresolved degree of freedom introduced for no reason this document
needs.

### 3.9 Missing-data handling (frozen)

An ETF is included in a date's cross-section only if (a) all 60
trailing days needed for its own `own_return_i(t)` have a resolvable
close price, and (b) at least one other member of its segment also
satisfies (a) on that date, so `peer_return_i(t)` is computable.
Otherwise the ETF is excluded from that date's cross-section entirely —
no forward-fill, no interpolation, no partial-window calculation,
identical in spirit to
`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 3's
convention.

### 3.10 Disclosed limitation of this frozen construction

The Global equity segment has only 2 members (`VT`, `ACWI`). For either
one, `peer_return_i(t)` is therefore the trailing return of the single
other member, not an average across several peers. This is disclosed
here as a known structural weak point of this specific attempt, not
silently fixed — regrouping segments to avoid it would itself be a
construction change requiring a new logged attempt, and is exactly the
kind of after-the-fact adjustment Section 5 below attests was not made.

---

## 4. Independence declaration

No correlation, rank-overlap, or any other quantitative Gate 1
calculation was performed to produce this section — it is a
construction-level, qualitative declaration only, consistent with the
Prevalidation Plan's requirement that the construction be frozen
*before* Gate 1's independence check is run against it.

**What overlaps with MOMENTUM.**

- Same raw input data: both are ultimately derived from the same daily
  close-to-close price history for the same 25 ETFs.
- Both use a trailing lookback window of price history ending at the
  ranking date (20 days for MOMENTUM, 60 days for H3).
- Both are, in the broadest sense, persistence claims — something
  observed in the trailing window is claimed to predict near-term
  continuation. Some resulting positive correlation between the two
  scores is expected and literature-anticipated (Gate 3 Section 4): a
  segment whose constituent-level trend is broadly up will often also
  show positive peer-relative excess return, since the two are related
  but not identical statistical descriptions of the same underlying
  price moves.

**What does not overlap.**

- MOMENTUM's score is a **price level** (the raw `SMA(20)`, unnormalized
  — `core/analytics/domain/calculations.py:6-17`), not a return, and is
  well-defined for one ETF in total isolation. H3's score is a
  **peer-relative excess return**, undefined without a segment peer
  group.
- MOMENTUM's cross-sectional ranking on a given date is, by its own
  documented construction, dominated by each ETF's absolute price
  level, since no normalization is applied
  (`docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`, "unnormalized-MOMENTUM ...
  scale mismatch"). H3's score never uses price level at all — only
  returns (ratios of prices), which are scale-invariant.
- H3's peer subtraction is **not** the mathematically degenerate case
  the Prevalidation Plan proves in Section 2 (a single common value
  subtracted from every ETF, which is rank-identical to absolute-return
  ranking). This was checked algebraically before this construction was
  frozen, not assumed: a "leave-one-out universe average"
  (`own_return_i − mean of all other 24 ETFs' own_return`) was
  considered and rejected for exactly this reason — for any date, that
  quantity reduces algebraically to `own_return_i × (25/24) − (constant
  same for every i)`, a strictly increasing affine transform of
  `own_return_i` alone, and is therefore also rank-identical to plain
  absolute-return ranking despite superficially looking like a
  "relative" measure. The frozen segment-grouped construction (Section
  3.5) does not reduce this way: two ETFs with an identical
  `own_return` in different segments can receive different
  `H3_score` values, because they are compared against different,
  segment-specific peer averages — this is a structural, provable
  difference from the degenerate case, independent of any measured
  correlation.

**Within-group algebraic structure (documented before Gate 1, no
correlation computed).** This is a further algebraic property of the
frozen construction (Section 3.5), stated here — before any Gate 1
correlation is computed — for the same reason the leave-one-out
rejection above was stated before any correlation was computed: so
that an explanation exists on the record before any future Gate 1
finding, rather than being written after the fact to fit a number.

For any segment *S* with *n* members, and any member *i* of *S* on
ranking date *t*, let `R_S(t)` denote the sum of `own_return_j(t)` over
every *j* in *S* on that date — a fixed, already-observed value on that
date, not a free variable. By the score definition in Section 3.5:

> `peer_return_i(t) = (R_S(t) − own_return_i(t)) / (n − 1)`
>
> `H3_score_i(t) = own_return_i(t) − peer_return_i(t)`
> `             = own_return_i(t) · [n / (n − 1)] − R_S(t) / (n − 1)`

For every ETF *i* in the same segment *S* on the same date *t*, the
coefficient `n / (n − 1)` and the term `R_S(t) / (n − 1)` are the same
fixed number for every such *i* — they depend only on the segment and
the date, never on which member is being scored. `H3_score_i(t)` is
therefore, within any single peer group on any single date, a strictly
increasing affine transformation of `own_return_i(t)` alone (`n / (n −
1)` is positive for every segment size in Section 3.2, including the
2-member case). A strictly increasing transformation cannot change
relative order.

**Consequence.** Ranking the members of any one peer group against
each other by `H3_score` is mathematically identical to ranking that
same group by absolute `own_return` — the two orderings cannot differ,
for any segment, on any date, regardless of what any future correlation
figure shows. This is the identical algebraic identity already used
above to reject leave-one-out universe subtraction, applied here at the
peer-group level instead of the universe level: subtracting a
same-for-every-member quantity and scaling by a same-for-every-member
positive constant cannot reorder the members it is applied to.

**Why this does not make the frozen construction degenerate.** The
coefficient `n / (n − 1)` and the constant `R_S(t) / (n − 1)` are
segment-specific and date-specific — they differ across peer groups
(different segment size `n`, different segment-total return `R_S(t)`),
so the within-group affine transform above holds only *inside* one peer
group. Comparing an ETF in one segment against an ETF in a different
segment applies two different affine transforms (different slope,
different intercept), and nothing in the algebra guarantees those two
transforms preserve the ordering that absolute return alone would
produce. Only comparisons *between* different peer groups can therefore
produce a full-universe H3 ranking that diverges from a full-universe
absolute-return ranking; comparisons *within* one peer group never can.

**Status of this property.** This is a purely algebraic consequence of
the frozen score definition (Section 3.5) and the frozen peer-segment
grouping (Section 3.2) — it follows from the formula alone, for any
input data whatsoever, and required no price, return, correlation, or
other outcome figure to derive or verify. It is documented here, before
Gate 1 is run, to satisfy the Prevalidation Plan's requirement (Section
2, "Acceptable interpretation boundaries") that an explanation be
available for any measured H3/MOMENTUM correlation before that
correlation is interpreted — so that, in particular, any future finding
that H3 tracks MOMENTUM more closely within densely-populated segments
than across segments already has a documented, non-outcome-dependent
explanation on record, rather than one constructed after seeing the
figure.

**Why this is not momentum renamed.** MOMENTUM's persistence claim
(underreaction/diffusion of asset-specific information, Gate 3 Section
4) requires no peer group, no benchmark, and no second actor beyond a
single slow-updating analyst population following one asset. H3's claim
requires a peer segment and a capital-reallocation actor (allocators and
flow-chasing fund investors) that has no role in MOMENTUM's story at
all. A score that is undefined without a peer group cannot be a mere
relabeling of a score that is fully defined without one — this
structural distinction (Gate 3 Section 4's "Unit of analysis" row,
independently confirmed in `gate3_independent_review_2026-07-19.md`
Section 3.1) holds for this specific frozen construction, not only for
the abstract mechanism. Whether the two scores turn out to be
*correlated* in this dataset is exactly, and only, what Gate 1 exists to
measure — this declaration does not pre-empt that measurement, and
Section 3.10 and the segment sizes above are disclosed precisely so a
Gate 1 reviewer has full visibility into where correlation might
plausibly be higher than elsewhere (e.g., the 2-member Global equity
segment).

---

## 5. Attempt log entry

Per `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 2 ("Construction
attempt log" and "Pre-log attestation").

- **Attempt number:** 1 of a maximum of 3.
- **Date:** 2026-07-19.
- **Researcher:** AI research assistant (Claude), in a session with no
  conversational continuity to any prior REFERENCE v1, REFERENCE v2 H1,
  or REFERENCE H3 Gate 1/2/3 session. This session began by reading, in
  order: `docs/REFERENCE_H3_PREVALIDATION_PLAN.md`,
  `docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`, the full contents of
  `research_archive/reference_h3/`, and the existing MOMENTUM
  implementation (`core/analytics/domain/calculations.py`,
  `core/analytics/scoring_pipeline.py`,
  `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`) before drafting any part of
  this construction.
- **Construction description (economic terms):** an ETF's trailing
  60-trading-day return, measured relative to the equal-weighted average
  trailing 60-trading-day return of the other ETFs occupying the same
  market-segment role (global equity, US equity, regional equity,
  sector, theme, or defensive/alternative asset class) — operationalizing
  the slow, segment-level capital-reallocation mechanism described in
  Gate 3.
- **Gate 1 outcome:** not yet evaluated. This document freezes the
  construction; it does not run or report the independence check.

**Pre-log attestation.**

1. This construction was derived from economic reasoning alone —
   specifically, the mechanism and literature already frozen and
   independently confirmed in
   `docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md` and
   `gate3_independent_review_2026-07-19.md` — and from the structural
   fact (Section 2 above) that this platform's 25-ETF universe already
   consists of segment-representing instruments.
2. No alternative candidate construction was evaluated against any
   outcome data (forward return, risk-adjusted return, IC, p-value, or
   any other outcome variable) before this one was submitted. No
   outcome data of any kind was read or computed in the course of
   drafting this document.
3. No alternative construction was selected or discarded based on its
   correlation with MOMENTUM, or on REFERENCE v1's or REFERENCE v2 H1's
   observed results, before this one was submitted. The one algebraic
   check performed (Section 4, the leave-one-out rejection) is a
   construction-logic proof about rank-identity to absolute-return
   ranking, established without computing, inspecting, or estimating
   any actual correlation figure for this dataset.
4. Alternative constructions informally considered, and why each was
   rejected, on economic/construction-logic grounds only:
   - **Single common benchmark subtraction** (e.g., every ETF's return
     minus a single named benchmark such as `SPY` or an equal-weighted
     universe average). Rejected because the Prevalidation Plan Section
     2 already proves this form is mathematically rank-identical to
     absolute-return ranking — a categorical, algebraic disqualification
     stated in the governing plan itself, not an economic judgment call
     made here.
   - **Leave-one-out universe mean subtraction** (`own_return_i` minus
     the mean of all other 24 ETFs' `own_return`). Considered as a way
     to avoid naming a specific external benchmark. Rejected after the
     algebraic check in Section 4 above showed it reduces to an affine
     transform of `own_return_i` alone and is therefore also
     rank-identical to absolute-return ranking — a construction-logic
     rejection, reached without computing any correlation against
     MOMENTUM or any outcome variable.
   - **Sector-only rotation**, restricting H3 to only the four GICS-style
     sector ETFs (`XLK`, `XLF`, `XLE`, `XLV`), the most literature-direct
     form of industry momentum (Moskowitz and Grinblatt, 1999). Rejected
     because it would require narrowing the universe below the existing
     25-ETF set, triggering the Prevalidation Plan Section 3 "universe
     change dependency" re-scoping requirement, and because a 4-member
     peer group was judged too small to produce a stable peer average
     across all its own members being excluded in turn — a structural,
     statistical-design objection, not an outcome-based one.
   - **Momentum-of-momentum**, defining H3 as each ETF's own MOMENTUM
     (`SMA(20)`) value ranked relative to its peers, i.e., building H3
     directly on top of MOMENTUM's own indicator output rather than raw
     price/return data. Rejected because deriving H3 from MOMENTUM's
     own output — rather than independently from price history — was
     judged, on construction-logic grounds alone, to conflate the two
     signals by design, before any correlation could even be measured;
     using independent raw-return inputs (Section 3.5) was preferred
     specifically to avoid this structural coupling.

   None of the above alternatives were assigned a score, a correlation
   estimate, or any other number before being set aside; all four
   rejections rest on the reasoning stated above, not on any impression
   of how each alternative might correlate with MOMENTUM or with any
   outcome variable.

---

## 6. Freeze statement

This document freezes Construction Attempt 1 in full: the universe
(Section 3.1), the peer-segment grouping (Section 3.2), the score
formula and its 60-day lookback (Section 3.5), the ranking convention
(Section 3.6), portfolio-formation and rebalance concepts (Sections
3.7–3.8), and the missing-data handling rule (Section 3.9). No part of
this construction may be changed, tuned, or reinterpreted without
opening a new, separately logged attempt against the Prevalidation
Plan's Section 2 cap of three — including the lookback window, the
segment boundaries, the peer-averaging method, or the exclusion of the
ETF itself from its own peer average. A change made for any reason,
including a reason discovered during Gate 1 review, is a new attempt,
not an edit to this one.

Gate 1 review of the REFERENCE H3 independence check, when it is
performed, must evaluate this exact artifact — the construction as
written above, on the date above — not a paraphrase, an improved
version, or a version with any parameter adjusted after this document
was written. If Gate 1 finds this construction degenerate or
insufficiently distinct from MOMENTUM, the correct response, per the
Prevalidation Plan Section 2's required ordering, is to revisit the
*economic* reasoning in Section 1–2 above and ask why sound reasoning
produced a degenerate result — not to mechanically adjust a parameter
in Section 3 and resubmit it as though it were still Attempt 1.

This document performs no implementation, no experiment, no backtest,
no parameter optimization, no return calculation, no IC calculation, no
performance comparison, and selects no "best" construction — it defines
exactly one candidate for later, independent Gate 1 review.
