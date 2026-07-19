# REFERENCE H3 — Gate 3 Economic Rationale

Governance document satisfying Gate 3 of
[`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`](REFERENCE_H3_PREVALIDATION_PLAN.md#4-research-decision-gates).
This document establishes, on economic grounds alone, whether the H3
candidate ("relative strength / sector rotation," ranked first in
[`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`](REFERENCE_RESEARCH_ROADMAP_NEXT.md#5-ranked-candidate-directions))
has a mechanism distinct enough from REFERENCE v1's MOMENTUM to justify
spending further research effort on it.

**What this document is not.** It does not define an H3 construction —
no benchmark, no peer-group definition, no ranking formula, no
lookback window, no score, no code. It does not reference, compute, or
reason from any outcome data: no IC, no p-value, no forward return, no
backtest result, from REFERENCE v1, REFERENCE v2 H1, or anywhere else.
Per the Prevalidation Plan's required ordering (Section 4), this
document's conclusions must exist *before* Gate 1's independence check
is run against a frozen construction — nothing here was, or could have
been, shaped by that check's results, because that check has not yet
been performed.

## 1. Candidate mechanism

The candidate idea is that capital rotates across market *segments* —
sectors, geographic regions, investment styles/themes, and broad asset
classes — at a slower, more institutional cadence than the cadence at
which information about any single security is absorbed. Under this
idea, an ETF representing a segment that has recently been relatively
attractive to allocators (relative to its peer segments, or relative
to the broad market) should continue to receive relatively more
capital in the near term than an ETF representing a recently
unattractive segment, because reallocation across segments is a slow,
periodic institutional process rather than an instantaneous one.

The key word is *relative*. The candidate mechanism is not about
whether a given ETF's own price trend continues in isolation — it is
about whether that ETF's standing versus its peer set (other sectors,
other regions, other themes, or the market as a whole) persists for a
period after it is established. This is a claim about the dynamics of
*capital allocation between segments*, not a claim about the speed at
which price discovery happens *within* a segment.

This is a conceptual description only. No specific benchmark, peer
grouping, or scoring formula is proposed or implied by this section —
that is explicitly out of scope for Gate 3 and is reserved for the
frozen specification that would follow a PASS outcome (Prevalidation
Plan, Section 4, Gate 4).

## 2. Literature basis

Three separate literatures converge on a segment-level (rather than
security-level) rotation effect, each identifying a mechanism distinct
from single-asset underreaction:

- **Industry/sector momentum as economically primary.** Moskowitz and
  Grinblatt (1999, *"Do Industry Factors Explain Momentum?"*, *Journal
  of Finance*) found that a large share of individual-stock momentum
  profits is attributable to industry-level momentum — stocks within a
  recently strong industry continue to be strong largely *because*
  the industry itself continues to be strong, not purely because of
  stock-specific underreaction. This literature treats segment-level
  rotation as a phenomenon in its own right, not merely an artifact
  aggregated from independent single-stock effects.
- **Style investing and category-level capital flows.** Barberis and
  Shleifer (2003, *"Style Investing"*, *Journal of Financial
  Economics*) model investors who allocate capital between
  pre-defined *categories* (styles, sectors, asset classes) based on
  the recent relative performance of the category itself, reallocating
  toward categories that have recently outperformed their peer
  categories. This is explicitly a capital-flow mechanism operating
  between groups, not a within-security information-diffusion
  mechanism.
- **Cross-asset and cross-market momentum.** Asness, Moskowitz, and
  Pedersen (2013, *"Value and Momentum Everywhere"*, *Journal of
  Finance*) document momentum effects that operate across country
  equity indices, government bonds, currencies, and commodity futures
  — asset-class-level and segment-level phenomena, structurally
  distinct from single-equity underreaction, that persist across very
  different market microstructures. Because ETFs themselves are
  segment-representing instruments (a sector, a region, a theme, an
  asset class), this literature is the most direct analogue to what an
  ETF-level relative-strength candidate would actually be measuring.

Supporting, secondary literature on *why* the effect should persist
(rather than only *that* it exists) is covered in Section 3.

## 3. Economic mechanism

**Who is creating the inefficiency.** Two distinct investor
populations, both operating at the segment level rather than the
individual-security level:

- **Institutional asset allocators with periodic rebalancing
  mandates.** Pension funds, endowments, and multi-asset mandates
  typically review and adjust sector/region/style tilts on a
  quarterly or annual committee cycle, often using trailing relative
  performance as one explicit input. This is a structurally slow
  process, not a same-day reaction to news.
- **Flow-chasing retail and advisor capital into thematic/sector
  ETFs.** ETF flow data has been shown to chase recent relative
  performance at the fund level (the "dumb money" effect of Frazzini
  and Lamont extended to fund flows), and ETF wrappers make it
  structurally easy to express a segment-level bet (buy a sector or
  theme fund) without needing security-level conviction. This is a
  distinct investor population from the fundamentals-focused analysts
  whose slow updating is the usual explanation for single-stock
  momentum.

**Why the inefficiency persists — why arbitrage does not immediately
remove it.** Segment-level rotation resists fast arbitrage for reasons
that are structurally different from the reasons single-stock
underreaction resists arbitrage:

- **Implementation lag is organizational, not informational.** A
  committee-driven reallocation is slow because of governance process
  (meeting cadence, mandate constraints), not because information is
  slow to reach the committee. An arbitrageur cannot "front-run" this
  lag away in the way they can trade ahead of slow-diffusing news,
  because there is no discrete information event to trade against —
  only a predictable but slow-moving institutional cycle.
- **Basis risk in the arbitrage trade itself.** Betting against a
  "hot" sector or theme requires taking a concentrated, relative-value
  position (long the cold segment, short the hot one, or simply
  avoiding the hot one) that carries real basis risk if the rotation
  continues before it reverses — this is the segment-level analogue of
  the limits-to-arbitrage literature (Shleifer and Vishny, 1997),
  and it is plausibly *more* binding at the segment level than at the
  single-stock level, because a sector or theme ETF cannot be
  hedged against a single, well-defined fundamental value the way a
  mispriced individual stock sometimes can.
- **Segmented investor clienteles.** Thematic and sector ETFs often
  have a different dominant clientele (retail/advisor-driven) than
  broad-market index funds (institutional-core-driven). Capital in one
  clientele does not automatically flow in to correct a rotation
  effect that clientele does not directly observe or trade against,
  which is a structural segmentation argument, not merely a claim
  about slow information diffusion.

## 4. Distinction from MOMENTUM

| | Existing MOMENTUM (REFERENCE v1) | Candidate H3 |
|---|---|---|
| **Core claim** | An ETF's own recent price trend (SMA(20)) predicts its own near-term continuation. | An ETF's standing *relative to its peer segments or the broader market* predicts continued relative outperformance or underperformance. |
| **Unit of analysis** | Single time series, own history only. Exists even considered in isolation, with no peer comparison. | Inherently comparative — undefined without a peer group or benchmark; the claim has no meaning for an ETF considered alone. |
| **Causal story** | Underreaction / delayed information diffusion: new fundamental information about the asset is priced in gradually rather than immediately. | Capital reallocation dynamics between market segments: institutional rebalancing cadence and flow-chasing behavior move capital toward recently-favored segments, independent of how quickly asset-specific fundamental information is priced. |
| **Who is slow** | Analysts/traders updating their view of *this specific asset's* fundamentals. | Committees and allocators deciding *how much to hold of this whole category*, and flow-chasing capital following that decision. |
| **What would make it stop working** | Faster analyst coverage / information diffusion for the specific asset. | Faster or less mandate-constrained institutional rebalancing; convergence of retail and institutional clienteles. |

The distinction is not merely statistical (i.e., "the numbers happen
to differ") — it is that the two mechanisms describe entirely
different economic actors making entirely different kinds of
decisions, at different decision cadences, for different reasons. It
is conceivable, and expected by the literature (Section 2), for the
two to be *correlated* without being the *same mechanism* — a segment
that many individual constituents are independently trending in will
naturally also show relative strength, exactly as the industry-momentum
literature describes. That expected, literature-documented overlap is
precisely why the Prevalidation Plan's Gate 1 (Section 2) treats
"moderate correlation with a written economic explanation" as an
acceptable outcome, rather than requiring near-zero correlation. Gate
3's role is to establish that the *mechanism* is distinct even where
the *statistic* may not be perfectly independent; Gate 1 is the
separate, later, quantitative check on how much overlap actually shows
up in this specific dataset once one construction is frozen. Passing
this Gate 3 assessment does not pre-empt or substitute for Gate 1 — it
only establishes that Gate 1 is a meaningful check to run at all,
rather than a check on an idea already known to be a relabeling.

**Why this is not simply renamed momentum / underreaction / diffusion.**
A construction that merely subtracted a single common benchmark return
from each ETF's own return would collapse to a rank-identical
transformation of absolute-return ranking (proven algebraically in the
Prevalidation Plan, Section 2) and would, in that specific form, be
indistinguishable from MOMENTUM in practice regardless of the economic
story attached to it. That degenerate case is a *construction* risk,
addressed procedurally by Gate 1, not evidence that the underlying
*mechanism* described in Sections 1–3 above is itself a relabeling of
underreaction. The mechanism described here — slow institutional
reallocation and flow-chasing between segments — has no analogue in
the underreaction story at all; underreaction requires no peer group,
no benchmark, and no capital-flow actor, only a single asset and a
single slow-updating analyst population. The risk that a *specific,
naive construction* of H3 could accidentally re-derive MOMENTUM
numerically is real and already documented; the risk that the
*economic mechanism* itself is secretly the same as underreaction is
not supported by anything in the literature reviewed in Section 2 —
each source treats segment-level capital flow and single-asset
underreaction as separate, independently motivated phenomena, testing
for and finding effects at the segment level *net of* whatever
individual-security momentum is already present.

## 5. Falsification criteria

The candidate mechanism would be undermined, in future testing beyond
this document's scope, by findings such as:

- **No detectable relative-strength effect where a same-data
  single-asset momentum effect is detectable.** If the same dataset
  and validation pipeline can detect an own-history momentum-style
  effect but shows nothing resembling persistence in *relative*
  standing, that is evidence against a segment-rotation mechanism
  operating in this universe, even if it says nothing about
  single-asset momentum.
- **No differentiation between style-exposed and style-neutral ETFs.**
  The style-investing mechanism (Section 3) predicts the effect should
  be stronger for ETFs that are natural "categories" investors
  rotate into and out of as a unit (sector, thematic, and regional
  funds) than for broad, diversified index funds that are themselves
  aggregations of many categories (e.g., total-market or all-world
  funds). A finding that shows equally strong (or stronger) apparent
  relative-strength persistence in the broad, non-categorical funds
  than in the categorical ones would be inconsistent with the
  style-investing/rotation story as the operative mechanism, even if
  some other effect were still present.
- **Relative strength reverses rather than persists at the horizon
  studied.** The mechanism in Section 3 predicts continuation over a
  period plausibly aligned with institutional rebalancing cadence. A
  finding of *reversal* rather than continuation at that horizon would
  be more consistent with a short-term liquidity/overreaction
  explanation than with the slow-reallocation mechanism proposed here.
- **The effect is fully attributable to each constituent ETF's own
  absolute momentum once peer-relative structure is accounted for**,
  i.e., a relative-strength measure adds nothing once each ETF's own
  trend is already known. This would suggest the "relative" framing is
  descriptively different but not economically distinct — the
  quantitative form this concern takes is Gate 1's rank-correlation
  and score-overlap check, but the underlying falsifiable claim is
  economic: that segment-level reallocation is a real, separate force
  from within-asset trend continuation.

## 6. Research risks

- **Factor overlap risk.** As established in Section 4 and in the
  Prevalidation Plan's Section 2, some positive correlation between a
  well-motivated H3 construction and MOMENTUM is expected and
  literature-consistent, not automatically disqualifying. The risk is
  that overlap turns out to be large enough, or close enough to the
  provably degenerate single-benchmark case, that the two are not
  practically separable in this specific 25-ETF universe and
  2024–2026 window — a question this document cannot answer and does
  not attempt to, since it would require the frozen construction and
  quantitative check reserved for Gate 1.
- **Data mining / researcher-degrees-of-freedom risk.** Sector
  rotation admits many plausible benchmark choices (broad market,
  equal-weighted peer average, sector-neutral within an asset class),
  many plausible peer-grouping schemes, and many plausible lookback
  windows — a materially larger design space than MOMENTUM's
  single-series SMA. This is precisely why the Prevalidation Plan
  requires the construction to be fixed by economic reasoning *before*
  Gate 1 is attempted, with a maximum of three logged attempts
  (Section 2) and a mandatory pre-log attestation against
  outcome-informed selection. This document does not resolve that
  risk; it only confirms that a defensible starting point for that
  fixed construction exists.
- **Implementation risk.** A genuine relative-strength/rotation
  strategy, unlike a buy-and-hold single-ETF momentum tilt, implies
  ongoing relative rebalancing across multiple segments as their
  relative standing changes — plausibly higher turnover than a simple
  own-trend-following approach. Neither this platform's existing
  validation pipeline (REFERENCE v1, REFERENCE v2 H1) nor this
  document models transaction costs or turnover; this remains an
  open, carried-forward limitation (REFERENCE v1 close-out, Section
  A) that would apply with at least equal force to H3 if it proceeds.
- **ETF investability / concentration risk.** Because ETFs are
  themselves diversified baskets, a segment-rotation score is a bet on
  macro/style factors rather than idiosyncratic security selection —
  and several ETFs in the current 25-ticker universe share overlapping
  thematic exposure (e.g., `XLK`, `SKYY`, `BOTZ`, and `ARKK` all carry
  meaningful technology/innovation exposure). A rotation-style ranking
  could concentrate implied "top-ranked" and "bottom-ranked" groups
  around a small number of correlated macro themes rather than the 25
  independent bets a simple cross-sectional IC calculation implicitly
  assumes, inflating the apparent breadth of any future signal. This
  is a risk to flag for the eventual construction and interpretation
  of results, not something resolved or quantified here.

## 7. Gate 3 recommendation

**PASS.**

**Justification.** A literature-grounded, economically distinct
mechanism exists for H3: slow, mandate-driven institutional
reallocation between market segments (Barberis and Shleifer's style
investing) and flow-chasing capital into recently favored
sector/theme ETFs, reinforced by direct evidence that segment-level
rotation is not merely an aggregation of single-security underreaction
but a partially separate, independently documented phenomenon
(Moskowitz and Grinblatt's industry-momentum finding; Asness,
Moskowitz, and Pedersen's cross-asset momentum evidence). The
mechanism is comparative by construction — it has no meaning for a
single ETF considered in isolation — which is the structural feature
that distinguishes it from MOMENTUM's own-history, underreaction-based
claim. The literature explicitly anticipates and explains *why* some
correlation with single-asset momentum is expected without the two
being the same mechanism, which is consistent with, and gives economic
content to, the Prevalidation Plan's Gate 1 tolerance for moderate,
explained correlation.

This PASS is bounded strictly to Gate 3's own question — whether a
defensible economic reason exists to spend further research effort on
H3. It does not, and cannot, pre-judge Gate 1 (candidate signal
independence, which requires a single frozen construction not yet
chosen), Gate 2 (already separately satisfied per
`research_archive/reference_h3/gate2_independent_review_2026-07-19_post_remediation.md`),
or Gate 4 (no unresolved degrees of freedom). One conditional note for
whoever performs the frozen construction that Gate 1 will test: the
mechanism validated here is explicitly *relative/comparative*
(Sections 1 and 4) — a construction that reduces to subtracting one
common benchmark from every ETF's own return would not merely risk
failing Gate 1's quantitative check, it would also fail to actually
operationalize the mechanism this document validates, since that
mechanism requires genuine peer-relative standing, not a uniform
shift applied identically to every ETF. That observation follows
directly from Section 1's conceptual description and is not itself a
construction choice — no benchmark, peer group, or formula is
specified or implied here.
