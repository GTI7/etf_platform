# Phase 5 Hypothesis Selection Review

**Status.** Governance summary. **This document is not an ADR.** It
documents a review-board decision (candidate selection for the next
research cycle) and the transition from Phase 4's close to Phase 5's
research-selection activity. It authorizes no implementation, no code
change, and no governed lifecycle transition — `core/research/lifecycle.py`
recognizes no phase this document could advance. Where it summarizes a
closed cycle's own close-out document, that close-out's text governs in
case of any discrepancy.

**Date.** 2026-07-27. **Author basis.** Level 1 — one reader with
repository access (this session), compiled from
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`,
`docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`,
`docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md`,
`docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md`,
`research_archive/reference_h4/hypothesis.md`, and
`docs/ARCHITECTURE_DECISIONS.md` (AD-072). Not an independent review; see
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4 on what Level 1 does and does
not establish. Every factual claim below was checked against the cited
source document before this text was written, not carried forward from
an earlier summary without re-verification.

---

## 1. Executive Summary

This document records a preliminary, conditional candidate selection for
the next REFERENCE research cycle: **H2 (long-term momentum, 12-1
month)**. The selection follows a pre-research candidate review
(`docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`) conducted after three
prior hypothesis candidates from the same shortlist closed without
producing a validated signal, and after a fourth, unrelated cycle
(`reference_h4`) exercised the platform's governed research lifecycle for
the first time without itself constituting alpha research. H2 is
selected on the basis of comparative readiness against four other
remaining candidates (H5, H6, H7, H8) — not on any expectation, stated or
implied, that it will validate. The selection is **preliminary** and is
explicitly conditioned on three mandatory gates (Section 5) that have not
yet been executed. No hypothesis content has been frozen, no Research
Proposal exists, and no phase of `docs/RESEARCH_GOVERNANCE_STANDARD.md`'s
lifecycle has been opened for H2 by this document.

## 2. Research Context

### 2.1 Three closed empirical attempts

Three hypothesis-candidate cycles, drawn from the same REFERENCE v2
shortlist, have run to closure. All three closed **without a validated
signal**:

- **`reference_v1`** (MOMENTUM = `SMA(20)`, unnormalized; VALUE =
  `RSI(14)`, bounded 0–100). Closed **"Implementation correct. Evidence
  insufficient to validate REFERENCE v1 for promotion."** Four of five
  tested statistics were nominally
  permutation-significant and directionally consistent with the
  hypothesis, but none survived the pre-registered bootstrap-robustness
  requirement across all three block lengths. The binding constraint was
  an effective sample size of roughly 23 independent 20-trading-day
  windows behind 463 overlapping ranking dates — a data-volume ceiling,
  not a disproof (`docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`).
- **`reference_v2_h1`** (LOW VOLATILITY = `−1 × 60-day trailing realized
  volatility`, sample stdev of close-to-close log returns). Closed
  **ARCHIVED**. Both H1-A (raw return, observed IC −0.117225) and H1-B
  (risk-adjusted return, observed IC −0.037941) were
  Holm-Bonferroni-significant but **directionally opposite** to the
  hypothesis — lower realized volatility was associated with lower, not
  higher, subsequent returns. Neither statistic's bootstrap CI excluded
  zero at any block length, so the reversed point estimate could not be
  confirmed robust either (`docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md`).
- **`reference_h3`** (RELATIVE STRENGTH — an ETF's cross-sectional
  standing relative to its own peer market segment). Closed **"CLOSED —
  EVIDENCE AGAINST,"** the strongest-evidence outcome of the three. H3-B
  (top-5/bottom-5 portfolio spread, 60-day horizon) was Holm-Bonferroni
  significant and **reversed** (observed −0.00573): ETFs ranked in H3's
  bottom five outperformed the top five over the following 60 trading
  days. Under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's Decision
  Framework, a significant reversal on an implementable statistic is
  recorded as evidence against the mechanism, not mere non-confirmation.
  Effective sample size was thinner than the two prior cycles — roughly
  7–8 independent windows at the pre-registered non-overlapping 60-day
  horizon (`docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md`).

No statement above extends beyond what its cited close-out states. In
particular, none of the three findings constitutes a confident disproof
of ETF-level predictability in general; each is a specific, documented
outcome for a specific, frozen construction tested against one ~2-year
sample.

### 2.2 `reference_h4`: a governance exercise, not alpha validation

`reference_h4` is a fourth, closed research-archive cycle, but it is
**not** a candidate from the REFERENCE v2 shortlist and is not read as
evidence for or against H2 or any other candidate discussed here. Its own
registration document states its purpose without qualification: "This
cycle's explicit purpose is to exercise the Phase A–E governance
machinery end-to-end for the first time against the real repository...
It is **not** an alpha search"
(`research_archive/reference_h4/hypothesis.md`). Its tested claim —
excess kurtosis in ETF daily log returns relative to a Gaussian null —
was selected specifically because it carries "essentially no researcher
degrees of freedom," not because it was a candidate for capital
allocation. Its Decision-phase gate passed (median excess kurtosis
9.995185801839456, 95% bootstrap CI [7.611023804796089,
15.26846242545566]), confirming a well-documented stylized fact about
return distributions. This document does not treat that outcome as
informative about H2, H5, H6, H7, or H8, and does not cite it as
governance-relevant to their selection or rejection.

What `reference_h4` does establish, and what this review does rely on,
is procedural: it is the first cycle to run the governed research
lifecycle for real, and AD-072 (accepted 2026-07-25, after `reference_h4`
closed) now imposes a Level 2 review floor on most lifecycle transitions
— a floor `reference_h4`'s own five self-review transitions would not
have satisfied had AD-072 existed at the time, by AD-072's own worked
example (`docs/ARCHITECTURE_DECISIONS.md`, AD-072). This procedural fact
shapes the mandatory gates in Section 5; it does not shape which
candidate was selected.

## 3. Candidate Selection

**H2 — long-term momentum (12-1 month) is selected as a conditional,
preliminary candidate for the next hypothesis cycle.**

This selection is not a Hypothesis-phase registration under
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2. No Research Proposal, no
Pre-validation gate, and no Methodology Freeze has been opened or
scheduled by this document. Selection reflects a comparative judgment
across five remaining shortlist candidates (H2, H5, H6, H7, H8) on the
same four factors used throughout this project's prior candidate reviews
— economic rationale, independence from closed constructs, data
feasibility, and degrees-of-freedom risk — not an assessment of expected
outcome.

H2's basis for selection, and the specific weaknesses that keep it
conditional rather than final:

- **Economic rationale.** Literature-grounded (12-month formation,
  1-month skip to avoid short-term reversal contamination), a
  well-replicated cross-sectional anomaly construction distinct in
  formation length and mechanics from `reference_v1`'s `SMA(20)`
  MOMENTUM signal.
- **Open independence question (not yet resolved).** H2 and
  `reference_v1`'s MOMENTUM share the same underlying mechanism label —
  trend continuation via underreaction — differing in formation window
  and construction type but not in economic category. This is the
  single largest risk to H2's legitimacy as a "genuinely different
  hypothesis" under `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md` §D item 1's
  entry requirement, and is not resolved by this document. It is
  deferred to Gate 1 (Section 5).
- **Open data-feasibility question (not yet resolved).** H2's required
  trailing window (≥13 months: 12-month formation plus 1-month skip)
  exceeds what the platform's current backfilled history supports for a
  usable share of ranking dates. Deferred to Gate 2 (Section 5).

No claim is made here, or anywhere in this document, that H2's economic
mechanism operates in this platform's specific universe, sample, or
regime. The literature basis establishes plausibility of a general
mechanism, not evidence for this platform's data.

## 4. Candidate Rejection Rationale

The following four candidates, drawn from the same shortlist as H2, were
considered and are not carried forward as the preliminary selection. Each
rejection is a readiness or risk determination, not a claim that the
underlying mechanism is implausible.

- **H5 — Carry / yield.** Rejected on data readiness. No yield field
  exists in the current schema (`ETF`, `TradingSession`, `PriceBar`,
  indicators); a new external data source, with its own provenance and
  hash-tracking obligations under `docs/RESEARCH_GOVERNANCE_STANDARD.md`
  §6, would be required before any Phase 1–2 work could begin. Universe
  fit — whether the platform's curated sector/theme/regional universe
  exhibits meaningful, comparable yield dispersion — is unverified and
  not verifiable without that data. Economic rationale and
  degrees-of-freedom profile were both assessed favorably; readiness was
  the disqualifying factor.
- **H6 — Long-horizon reversal (3–6 month).** Rejected on two grounds.
  First, an independence concern specific to this candidate:
  `reference_h3`'s own closed result (H3-B) is already a
  Holm-Bonferroni-significant reversal under a related construction
  (Section 2.1); a long-horizon reversal hypothesis risks substantially
  overlapping with evidence the archive already contains, rather than
  testing a genuinely separate question. Second, a data-feasibility
  concern: a non-overlapping 3–6 month horizon consumes calendar history
  faster than shorter-horizon candidates, leaving as few as 4–8
  independent windows even after a historical-depth extension — worse
  than H2's constraint, and not fully correctable by the same remedy.
- **H7 — Correlation-regime / idiosyncrasy.** Rejected on economic
  rationale and freeze discipline, not on data or independence, both of
  which were assessed as the strongest in the shortlist. No a priori
  predicted direction has been established for this candidate in this
  project's record. Committing to a sign in order to run a one-sided
  test would itself introduce an undisclosed researcher degree of
  freedom — the specific failure mode
  `docs/RESEARCH_GOVERNANCE_STANDARD.md`'s freeze discipline exists to
  prevent. Retained informally as a fallback only if H2's Gate 1 (novelty
  review) fails and a genuinely pre-registered directional mechanism can
  be written for H7 independently.
- **H8 — Macro-conditional beta exposure.** Rejected on readiness.
  Requires both a new external macro data source (no provenance path
  exists for it) and new statistical infrastructure beyond the
  `mean_ic` / `permutation_null` / `holm_bonferroni` / `bootstrap_ci`
  machinery reused unmodified across all three closed cycles to date.
  Carries the highest degrees-of-freedom exposure of any candidate
  considered — macro variable choice, conditional model form, and
  regime-detection method are all currently undetermined. Assessed as
  having the strongest independence and among the strongest economic
  rationale of the shortlist, but the furthest from executable.

## 5. Mandatory Gates Before Hypothesis Freeze

H2's selection remains preliminary until each of the following is
completed and recorded. None is satisfied by this document.

1. **Novelty review versus `reference_v1` MOMENTUM.** A written,
   independently reviewable argument establishing that 12-1 month
   cross-sectional momentum is economically and constructionally
   distinct from `reference_v1`'s `SMA(20)` MOMENTUM signal — addressing
   directly the shared "trend continuation" mechanism label noted in
   Section 3, not merely asserting a different formation window. Must
   exist as a reviewed artifact prior to Phase 1 (Hypothesis) opening,
   consistent with the entry requirement `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`
   §4 states against prior closed cycles.
2. **Historical depth assessment.** A quantitative determination of
   whether the platform's backfilled price history — extended if
   necessary — supports a defensible count of independent or
   block-correctable ranking windows for H2's ≥13-month trailing
   requirement. Not an assumption; a checked figure, produced before
   Phase 1 proceeds.
3. **Forecast horizon freeze.** A pre-registered, written decision on
   H2's forecast horizon (retaining the existing pipeline's 20-day
   default, or adopting an alternative with its own stated
   justification), fixed before any outcome data is examined and not
   subject to revision after a first result is seen.

Governance review level for each downstream lifecycle transition, once
Phase 1 opens, is set by AD-072 (`docs/ARCHITECTURE_DECISIONS.md`), not
by this document: Level 2 is the floor for Research Proposal →
Pre-validation, Pre-validation → Methodology Freeze, Methodology Freeze →
Implementation, Validation → Decision, and Decision → Archive; Level 1
suffices only for Implementation → Validation.

## 6. Explicit Statement on Interpretation

**Selection does not imply expected validity; a null result remains an
acceptable outcome.**

Nothing in this document, or in the review it summarizes, asserts that
H2 — or any rejected candidate — carries alpha potential, will pass any
future promotion bar, or is more likely than not to validate. Three of
three prior candidates from the same shortlist closed without a
validated signal (Section 2.1); this history informs the gates in
Section 5, not an expectation of a different outcome for H2. A
disciplined non-result, reached through the same frozen, pre-registered
process used for `reference_v1`, `reference_v2_h1`, and `reference_h3`,
is a legitimate and sufficient outcome of the next cycle.

---

This document authorizes no implementation, no code change, no ADR, and
no lifecycle-phase transition. It records a preliminary, conditional
selection and the rationale for the candidates not selected, for the
governance record.
