# REFERENCE Research Roadmap — Next Cycle Decision Memo (v2)

**Status.** Review-only decision memo, not an implementation plan and not
an ADR. It supersedes `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` (v1) for
the purpose of choosing the next hypothesis cycle; v1 is not deleted or
edited — it remains the accurate record of the decision made after H1
closed, and is cited throughout below as the source for facts this
document carries forward rather than re-derives.

**Date.** 2026-07-27. **Author basis.** Level 1 — one reader with
repository access (this session), compiled from
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`,
`docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`,
`docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md`,
`docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md`,
`research_archive/reference_h4/hypothesis.md` and `decision_log.md`, and
`docs/ARCHITECTURE_DECISIONS.md` (AD-072). Not an independent review; see
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4 on what Level 1 does and does
not establish.

**Scope discipline.** No new hypothesis is proposed in this document. The
candidate pool is the same set v1 already reconstructed (`REFERENCE v2`'s
8-candidate shortlist, itself never persisted as a standalone file — see
`docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md` §D on that provenance gap) minus
the two candidates now tested and closed. No code is written, no AD is
opened, and no claim of alpha is made or implied anywhere below.

---

## Current Research State

Three hypothesis-candidate cycles from the REFERENCE v2 shortlist have
now run to closure. A fourth cycle (`reference_h4`) also completed, but
was never a candidate from that shortlist and is not read as evidence for
or against any of the remaining candidates — see the dedicated note at
the end of this section.

| Cycle | Candidate | Status | Outcome |
|---|---|---|---|
| `reference_v1` | MOMENTUM / VALUE | CLOSED | Archived — insufficient evidence (underpowered, not disproved) |
| `reference_v2_h1` | H1 — Low volatility | CLOSED | Archived — directionally opposite to hypothesis |
| `reference_h3` | H3 — Relative strength / segment rotation | CLOSED | **Evidence against** — H3-B's reversal is Holm-Bonferroni significant |
| `reference_h4` | Excess kurtosis (governance exercise) | CLOSED | Gate **PASS**, explicitly not an alpha search |

Of the original 8-candidate shortlist v1 reconstructed
(`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` §5), H1 and H3 — the two
top-ranked candidates at the time — are both now closed. **No validated
signal exists on this platform after three independent hypothesis
tests.** This is unchanged from what v1 already stated and Phase 4's own
completion review reiterates (`docs/PHASE4_COMPLETION_REVIEW_2026-07-27.md`
§5): governance and reproducibility infrastructure verify process, not
predictive validity, and `docs/BASELINE_STATUS.md` continues to record
the scoring-signal question as open.

**On `reference_h4`.** Its own registration document states its purpose
directly: "This cycle's explicit purpose is to exercise the Phase A–E
governance machinery end-to-end for the first time against the real
repository... It is **not** an alpha search"
(`research_archive/reference_h4/hypothesis.md`). Its hypothesis — ETF
daily returns exhibit excess kurtosis versus a Gaussian null — was chosen
specifically because it has "essentially no researcher degrees of
freedom," not because it was a candidate for capital allocation. Its
Decision-phase gate passing (median excess kurtosis 9.995, 95% bootstrap
CI [7.611, 15.268], both well clear of the zero threshold) confirms a
well-known stylized fact about return distributions; it says nothing
about any REFERENCE v2 candidate and is not used below to rank, select,
or bias any of them. What `reference_h4` *does* change is procedural: it
is the first cycle to run the governed lifecycle for real, and AD-072
(accepted 2026-07-25, after `reference_h4` closed) now imposes a Level 2
review floor on most of that lifecycle's transitions — a floor
`reference_h4`'s own five self-review transitions would not have
satisfied, per AD-072's own worked example. This matters for how the
next cycle should be run (see Phase 5 Recommendation), not for which
candidate to pick.

## Closed Hypotheses

Preserved from v1 without alteration; restated here for a single-document
reference, not a re-litigation.

### `reference_v1` — MOMENTUM / VALUE

No statistic (MOMENTUM IC, VALUE IC, raw blend, normalized blend,
top-vs-bottom spread) survived Holm-Bonferroni-corrected permutation
testing combined with bootstrap robustness at all three block lengths.
Effective sample size ≈23 independent 20-day windows behind 463
overlapping ranking dates was the binding constraint. Single regime
(2024–2026), survivorship-biased 25-ETF universe, no transaction costs
modeled. Full detail: `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`.

### `reference_v2_h1` — Low volatility

H1-A (raw returns) and H1-B (risk-adjusted returns) were both
permutation-significant, Holm-Bonferroni-corrected, and **directionally
opposite** to the hypothesis — lower realized volatility associated with
*lower*, not higher, subsequent returns. Neither statistic's bootstrap CI
excluded zero at any block length, so the reversed point estimate was not
confirmed robust either. Same effective-sample-size ceiling as v1 (a
property of the panel structure, not the specific hypothesis). Full
detail: `docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md`.

### `reference_h3` — Relative strength / segment rotation

**CLOSED — EVIDENCE AGAINST**, the strongest-evidence outcome of the
three. H3-A (score autocorrelation) was permutation-significant and
correctly signed but not bootstrap-robust at any block length. H3-B
(top-5/bottom-5 portfolio spread) was Holm-Bonferroni significant **and
reversed** (−0.00573): ETFs ranked in H3's bottom 5 by relative standing
outperformed the top 5 over the following 60 trading days. Under
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's Decision Framework, a
significant reversal on an implementable statistic is recorded as
evidence against the mechanism, not mere non-confirmation. Effective
sample size was ≈7–8 independent windows at the pre-registered
non-overlapping 60-day horizon — thinner than v1/H1's ≈20–23, because H3
used a non-overlapping horizon by design rather than an overlapping one.
Full detail: `docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md`.

## Remaining Candidates

The six candidates from v1's reconstructed shortlist not yet tested,
carried forward unchanged (`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` §5),
re-ranked below against the four factors this memo is scoped to:
economic rationale, overlap with the three now-closed tests, data
requirements, degrees-of-freedom risk, and expected research value.

### H2 — Long-term momentum (12–1 month)

- **Rationale.** Strong, independently replicated literature (12-month
  formation, 1-month skip to avoid short-term reversal contamination) —
  one of the most robust cross-sectional equity anomalies historically
  documented, distinct in construction from v1's own MOMENTUM indicator.
- **Strengths.** High economic justification; a well-specified,
  pre-existing literature to freeze a construction against; the
  skip-month convention gives it a concrete, citable degrees-of-freedom
  discipline (not a free parameter to be chosen post hoc).
- **Weaknesses.** v1's own table already flagged this candidate as
  "closest of all candidates to v1's own MOMENTUM" — Medium–Low
  independence, the weakest overlap profile of any remaining candidate.
  Entry requirement 2 (`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` §4,
  now checked against *three* priors, not two) requires a written
  argument for why 12-1 month momentum is not a disguised variant of
  whatever construction v1's MOMENTUM indicator used, before any code is
  written — this argument does not yet exist and is a hard gate, not a
  formality.
- **Data constraints.** v1 rated this "Fair — needs deeper history than
  currently backfilled." A 12-month formation window needs materially
  more calendar depth than the ~2-year window the platform currently
  holds to produce a usable count of non-overlapping (or block-corrected
  overlapping) formation periods.
- **Governance risks.** The overlap argument above must be frozen and
  reviewed at Level 2 (Research Proposal → Pre-validation, per AD-072) —
  the specific failure mode to avoid is a Level 2 reviewer accepting a
  weak overlap argument because the candidate is otherwise attractive.
  No new external data source is required, so no new dataset-provenance
  work is implied.

### H6 — Long-horizon reversal (3–6 month)

- **Rationale.** High — long-horizon mean reversion is a distinct,
  literature-grounded mechanism from both momentum-style persistence and
  volatility mispricing; high independence from all three closed cycles.
- **Strengths.** The strongest overlap profile of any remaining
  candidate (v1 rated independence "High"); no ambiguity about hypothesis
  direction, unlike H7 below.
- **Weaknesses.** v1 rated data availability "Poor — as few as 4-8
  non-overlapping windows in the current history." `reference_h3` has
  since produced a live demonstration of exactly this failure mode at a
  *60-day* horizon (≈7-8 windows, correctly-signed statistic that could
  not clear the bootstrap-CI-exclude-zero bar). A 3–6 month horizon is
  longer still, so this candidate is structurally more exposed to the
  same problem, not less.
- **Data constraints.** Poor today; improved by extending historical
  depth, but a non-overlapping 3–6 month horizon consumes calendar time
  fast — even a substantial history extension is likely to leave this
  candidate thin on independent windows relative to H2's overlapping
  12-month formation, which can use block-bootstrap correction instead
  of requiring strict non-overlap.
- **Governance risks.** Same Level 2 floor as any other candidate at
  Research Proposal → Pre-validation and Pre-validation → Methodology
  Freeze; the specific risk here is spending a full cycle's cost only to
  reproduce H3-A's exact failure shape (correctly signed, permutation
  significant, not bootstrap-robust) for structural sample-size reasons
  foreseeable in advance.

### H7 — Correlation-regime / idiosyncrasy

- **Rationale.** Medium–Low — v1's own table already flags "no clear a
  priori direction," which is a substantive weakness, not a data gap:
  Phase 1 (Hypothesis) and the entry requirements both call for a
  mechanism stated and frozen before any outcome data is seen, and a
  hypothesis without a predicted sign is difficult to freeze honestly.
- **Strengths.** High independence from all three closed cycles; data
  availability rated "Good" — the only remaining candidate that needs no
  historical-depth extension and no new external data source.
- **Weaknesses.** Sign-selection risk is the dominant concern: v1 rated
  this "Medium–High... sign-selection risk without a clear a priori
  direction." Absent a directional mechanism, the Methodology Freeze
  would either have to commit to an arbitrary sign (introducing exactly
  the kind of undisclosed researcher degree of freedom
  `docs/RESEARCH_GOVERNANCE_STANDARD.md`'s freeze standard exists to
  prevent) or run as a two-sided test with a correspondingly weaker
  claim.
- **Data constraints.** None beyond the current universe/window — the
  only candidate immediately runnable without an infrastructure
  milestone first.
- **Governance risks.** The sign-selection problem is a Pre-validation
  Gate (economic rationale / no unresolved specification degrees of
  freedom) risk specifically — the kind of issue H3's own Gate 4 was
  designed to catch, and the one most likely to produce a Level 2
  refusal or a forced rewrite at that gate for this candidate.

### H4 — Volume / flow acceleration

- **Rationale.** Medium — plausible mechanism (order-flow-driven
  short-term price pressure) but weaker literature grounding than H2 or
  H6.
- **Strengths.** High independence from the three closed cycles (none
  used volume/flow data).
- **Weaknesses.** v1 flagged the central problem precisely: "ETF-level
  volume is contaminated by creation/redemption mechanics" — this is a
  measurement-validity problem, not a statistical-power problem, and
  does not improve with more historical depth or a different horizon.
- **Data constraints.** Rated "Uncertain" — volume data reliability at
  the ETF level is unverified on this platform; resolving this would
  itself be a pre-validation research task (verifying what ETF-reported
  volume actually measures) before any hypothesis-specific work could
  begin.
- **Governance risks.** A Pre-validation Gate 2 (historical data
  adequacy) risk distinct from every other candidate here: the open
  question is not "is there enough data" but "does the data measure what
  the hypothesis needs it to measure," which the existing gate structure
  is not obviously suited to resolve quickly.

### H5 — Carry / yield

- **Rationale.** High — well-established mechanism (yield-seeking
  capital flow, especially cross-asset) with strong independence from
  all three closed cycles (High).
- **Strengths.** Low degrees-of-freedom / overfitting risk per v1's
  table — carry construction is comparatively mechanical once a yield
  source is fixed.
- **Weaknesses.** Requires a genuine new data source; universe fit
  (whether the current 25-ETF curated universe has meaningful,
  comparable yield dispersion) is unverified.
- **Data constraints.** Poor — the platform's current schema
  (`ETF`, `TradingSession`, `PriceBar`, indicators) has no yield field;
  acquiring and provenance-tracking a new source is a data-engineering
  project of its own, prior to any Phase 1–2 hypothesis work.
- **Governance risks.** A new external data source means new
  `dataset_manifest.json` entries and new hash/provenance obligations
  under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §6 (Data Provenance
  Requirements) before Methodology Freeze can even run
  `freeze_verifier.verify_freeze()` cleanly — a materially larger
  governance surface than any candidate above.

### H8 — Macro-conditional beta exposure

- **Rationale.** High economic justification but v1 already rates this
  candidate "most researcher degrees of freedom" of the full shortlist.
- **Strengths.** Highest independence from all three closed cycles of
  any candidate.
- **Weaknesses.** v1's own assessment: "needs new statistical
  infrastructure beyond a simple score" — this candidate cannot be
  evaluated with the existing `mean_ic` / `top_bottom_spread` /
  `permutation_null` / `holm_bonferroni` / `bootstrap_ci` machinery
  reused unmodified across all three closed cycles to date; it would
  require new, unaudited statistical code.
- **Data constraints.** Poor — new external (macro) data source
  required, same class of problem as H5 but compounded by the new
  statistical infrastructure requirement.
- **Governance risks.** Largest of any candidate: new data provenance
  obligations (as H5), new statistical code with no prior-cycle
  reuse-and-therefore-informal-validation history, and the highest
  sign/parameter-selection surface of the full shortlist. Not a near-term
  candidate for a single-developer platform.

### Ranking summary

| Rank | Candidate | Rationale | Overlap w/ closed | Data readiness | DoF risk | Expected value |
|---|---|---|---|---|---|---|
| 1 | H2 — Momentum (12-1mo) | High | **Weakest** (needs written overlap argument) | Needs depth extension | Low (literature-fixed) | High, conditional on clearing overlap gate |
| 2 | H6 — Long-horizon reversal | High | Strongest | Poor, worsened at longer horizons | Low in principle, undermined by sample size | Medium — real risk of repeating H3-A's exact failure shape |
| 3 | H7 — Correlation-regime | Medium-Low | Strong | **Best — no extension needed** | High (sign-selection) | Medium — fast to run, but Pre-validation Gate risk is real |
| 4 | H4 — Volume/flow | Medium | Strong | Uncertain (measurement validity, not fixable by more data) | Medium | Low near-term — needs a data-quality sub-investigation first |
| 5 | H5 — Carry/yield | High | Strong | Poor (new source) | Low | Medium long-term, low near-term (new provenance work) |
| 6 | H8 — Macro-conditional beta | High | Strongest | Poor (new source + new infra) | **Highest** | Low near-term — largest scope of any candidate |

## Historical Depth Decision

**Decision: extend historical depth first, before selecting and freezing
the next hypothesis.**

Reasoning:

1. **The pattern is no longer speculative.** v1 flagged the
   effective-sample-size ceiling as a "standing, unresolved question the
   research program has now encountered twice" after `reference_v1` and
   `reference_v2_h1`. `reference_h3` is now a third, independent
   confirmation — at a *different* horizon (60-day, non-overlapping)
   than the first two (20-day, overlapping) — and produced the platform's
   clearest example yet of the failure mode: a correctly-signed,
   permutation-significant statistic (H3-A) that could not clear the
   stricter bootstrap-CI-exclude-zero bar because only ≈7-8 independent
   windows existed. Treating this as a one-off footnote a third time
   would understate it further, not less.
2. **The two candidates with the best economic rationale are the two
   most data-constrained.** H2 (rank 1) and H6 (rank 2) above are both
   rated "Fair" and "Poor" on data availability *specifically and only*
   because of window depth — not because of any weakness in their
   economic mechanism. Choosing either one today, without extending
   history, means knowingly re-running v1/H1/H3's binding constraint a
   fourth time on a candidate that would not otherwise be data-limited.
3. **It is not itself research.** Extending backfilled price history is
   a data-engineering task with no hypothesis, no forecast direction, and
   no researcher degrees of freedom — it does not consume a "hypothesis
   cycle" against the no-tuning-against-prior-results discipline every
   closed cycle's entry requirements impose, and it does not require a
   new AD (no governed *behavior* changes, only the volume of history
   available to whatever is tested next).
4. **It does not benefit every candidate equally, which is informative,
   not disqualifying.** H2's constraint (12-month formation window) is
   directly calendar-depth-driven and should improve materially with
   more history. H6's constraint (short non-overlapping windows at a
   3–6 month horizon) improves more slowly, because a longer horizon
   consumes calendar time faster than a shorter one for the same amount
   of added history — worth knowing *before* committing to either
   candidate, not after a fourth inconclusive cycle. H7 needs no
   extension at all, which keeps it available as a fallback if the depth
   extension proves harder than expected (see recommendation below).
5. **Choosing a hypothesis first would not avoid this work — it would
   only defer discovering whether the chosen candidate's data constraint
   was addressable**, spending Pre-validation Gate 2 effort to reach the
   same conclusion this decision reaches directly.

This decision does not itself specify how much additional history to
backfill, from what provider, or over what target window — those are
implementation questions for whoever executes this milestone, outside
this memo's review-only scope.

## Phase 5 Recommendation

1. **Next hypothesis candidate: H2 — long-term momentum (12–1 month)**,
   conditional on two prerequisites completing first, in order:
   - the historical-depth extension (Historical Depth Decision, above),
     sized to give H2's 12-month formation window a defensible count of
     independent or block-correctable windows — not merely "more than
     today";
   - a written novelty argument, produced and frozen *before* any H2
     code is written, distinguishing 12-1 month momentum's construction
     from whatever indicator `reference_v1`'s own MOMENTUM statistic
     used — satisfying entry requirement 2
     (`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` §4) against a third
     prior, not a formality but the specific weakness the ranking above
     identifies as H2's worst factor.

   **Fallback: H7 — correlation-regime**, if either prerequisite above
   stalls or the novelty argument for H2 cannot be written convincingly.
   H7 needs no data extension and has strong independence, but its
   sign-selection weakness must be resolved in writing (a committed,
   pre-registered direction, or an explicitly two-sided test) at Phase 1,
   not deferred to Pre-validation.

2. **Required preparation, in sequence:**
   - Execute the historical-depth extension as a standalone
     data-engineering milestone (no hypothesis content, no AD).
   - Write and freeze H2's novelty argument against `reference_v1`'s
     MOMENTUM construction as a named artifact reviewed at Level 2
     before Phase 1 (Hypothesis) is opened for H2 — earlier than the
     Standard's normal Phase 1→2 gate, because this is the specific
     factor most likely to sink the candidate later if left unaddressed.
   - Confirm, before Phase 1 begins, that the extended history plus the
     existing 25-ETF universe gives H2 a materially larger effective
     window count than v1/H1's ≈20-23 or H3's ≈7-8 — a quantitative
     check, not an assumption.

3. **Governance phases to execute, and at what review level (AD-072,
   accepted 2026-07-25):**

   | Transition | Required floor |
   |---|---|
   | Hypothesis → Research Proposal | (not floored by AD-072's evaluated set; Level 1 minimum applies) |
   | Research Proposal → Pre-validation | **Level 2** |
   | Pre-validation → Methodology Freeze | **Level 2** |
   | Methodology Freeze → Implementation | **Level 2** |
   | Implementation → Validation | Level 1 (no elevated floor) |
   | Validation → Decision | **Level 2** |
   | Decision → Archive | **Level 2** |

   Unlike `reference_h4` — whose five self-review transitions would not
   have satisfied this floor had AD-072 existed at the time, per AD-072's
   own worked example — this cycle should obtain genuine Level 2
   (AI-assisted adversarial, procedurally independent per
   `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4) review at each floored
   transition as it happens, not reconstruct compliance after the fact.
   This is the live-review-workflow test the Phase 5 direction review
   identified as the actual gap AD-072 has not yet been exercised
   against.

No implementation plan, timeline, dataset-extension sizing, or commitment
to any specific outcome is made by this document. Nothing here claims H2,
H6, or H7 will validate; the ranking above reflects relative readiness
and risk given three prior closures, not a prediction.
