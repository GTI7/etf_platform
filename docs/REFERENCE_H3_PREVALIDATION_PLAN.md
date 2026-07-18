# REFERENCE H3 Pre-Validation Plan

A governance/research-planning document, not an experiment design. It
defines a small verification phase that must complete **before** an H3
(Relative Strength / Rotation) specification is written, following the
critical findings in
[`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`](REFERENCE_RESEARCH_ROADMAP_NEXT.md)
and its adversarial review. No formula, lookback window, scoring
method, code, or implementation architecture is defined here.

## 1. Objective

REFERENCE v1 and REFERENCE v2 H1 were both closed with the same
diagnosis: the platform can detect non-random structure (permutation
significance was reached in both cycles), but the current dataset's
effective sample size (~20–23 independent windows after overlap
adjustment) was not enough to confirm robustness. Running a third
hypothesis cycle without addressing two specific, concrete open
questions would risk repeating that outcome for reasons that have
nothing to do with H3's own merit.

This phase exists because H3 carries a risk neither prior cycle had:
**H1's score (realized volatility) was structurally guaranteed to
differ from v1's MOMENTUM — dispersion and trend are different
statistical moments of the same price series, so no independence check
was needed.** H3 has no such guarantee. A naive relative-strength
construction (`ETF return − a single common benchmark return`) is
**mathematically rank-identical** to absolute-return ranking, since
subtracting the same value from every ETF cannot change relative
order. Absolute-return ranking, in turn, is plausibly close to
REFERENCE v1's SMA(20)-based MOMENTUM. This is a real, provable
degeneracy risk, not a hypothetical one — see Section 2.

**The goal of this phase is explicitly not to test whether H3 predicts
returns.** No forward return is touched anywhere in this plan. The
goal is narrower and prior to that question:

1. Is a candidate H3 construction sufficiently independent from
   REFERENCE v1's MOMENTUM to be a genuinely new economic signal,
   rather than a renamed one?
2. Is the available data — as currently scoped, or under some
   alternative — sufficient to make testing H3 worthwhile at all?

Only once both are answered does it make sense to invest in writing a
frozen H3 specification.

## 2. Research independence verification

**Standalone principle — no outcome data, ever, in this phase.** This
verification compares scores to scores only. At no point during
pre-validation may forward return, risk-adjusted return, Information
Coefficient, p-value, or any other outcome variable be read, computed,
or referenced. If a proposed check would require touching a forward
return in any form, it does not belong in this phase — it belongs in
the eventual H3 significance test, after a frozen specification exists.
This is stated here as its own principle, not left to be inferred from
the methodology bullets below, because it is the one rule this entire
document exists to enforce.

**Purpose:** answer "is this a new economic signal, or a renamed
momentum signal?" — without touching forward returns, without
computing a p-value, without a promotion decision, and without
comparing multiple candidate constructions against each other to pick
a winner.

**Prior-result independence.** H3's construction — including the
*first* proposed construction, not only later revisions — must not be
selected, shaped, or biased using REFERENCE v1's or REFERENCE v2 H1's
observed IC values, signs, p-values, or outcomes. `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`
states this constraint at the roadmap level; it is restated here
because this document is where the construction is actually chosen and
frozen, and that is the point where the constraint must bind.

**Required ordering (important, not optional):** the economic
rationale and construction logic for H3 (Gate 3, Section 4) must be
frozen *before* this check is run. This check is a confirmatory sanity
check on one, already-decided construction — not a tool for searching
across several candidate constructions for the one that happens to
correlate least with MOMENTUM. Running it the other way around would
be parameter mining wearing an independence check's clothing: it would
select for whichever construction looks different by chance, not for
whichever construction is different for a documented economic reason.
If the check fails on the frozen construction, the correct response is
to revisit the *economic* reasoning that produced it (why did
sound reasoning lead to a degenerate construction?) — not to iterate
mechanically through alternatives until one passes.

**Construction attempt log (mandatory).** Every candidate construction
that reaches Gate 1 — not only the one that ultimately passes, if any
do — must be recorded before Gate 1 is evaluated for it, capturing:

1. the construction description (in economic terms, not a formula);
2. the economic rationale offered for it;
3. its Gate 1 outcome (degenerate / moderate-with-explanation / low
   correlation).

**What counts as a new attempt.** Any change to construction logic
counts as a new attempt against the cap below — there is no category
of "refinement" that avoids being logged as one. This explicitly
includes: a changed benchmark choice, a changed peer-grouping scheme,
a changed universe definition, a changed ranking methodology, or any
other design choice that affects the construction. A construction
cannot be relabeled as a continuation of a prior attempt to sidestep
the cap.

**Verification methodology is frozen, independent of construction
attempts.** The methodology used to check each attempt — which dates
are sampled, the aggregation statistic used to summarize the daily
correlation distribution, how the degenerate case is identified, and
the interpretation rules that follow from it (Section 2's
"Acceptable interpretation boundaries," below) — is fixed by this
document before any attempt is logged, and does not change between
attempts. Only the candidate construction may vary from attempt to
attempt; the yardstick it is measured against may not. A change to the
methodology itself, for any reason, is not a "new attempt" in the
sense defined above — it invalidates the pre-validation cycle to date
and requires this document to be revised and re-approved before any
further attempt is logged against it.

**Pre-log attestation (mandatory).** Before any construction enters
the log, whoever is submitting it must attest, in writing, alongside
the log entry:

1. the construction was derived from economic reasoning alone;
2. no alternative candidate construction was evaluated against any
   outcome data (forward return, risk-adjusted return, IC, p-value, or
   any other outcome variable) before this one was submitted;
3. no alternative construction was selected or discarded based on its
   correlation with MOMENTUM, or on REFERENCE v1's or REFERENCE v2
   H1's observed results, before this one was submitted;
4. any alternative constructions that were informally considered —
   even without computing any number for them — are disclosed by name
   or brief description, together with why each was rejected, and
   confirmation that each rejection rested on economic reasoning only,
   never on an impression of how a construction might correlate with
   MOMENTUM or with any outcome variable.

Point 4 exists because points 2 and 3 only rule out *quantitative*
pre-screening — they do not, on their own, prevent someone from
privately weighing several candidates on purely qualitative economic
grounds and submitting only the one that "feels" most defensible.
Considering and setting aside alternatives is normal, healthy economic
reasoning and is not prohibited; what is required is that this
reasoning be visible to the reviewer, not silently discarded.

This cannot guarantee compliance by itself, but it converts "informal,
undisclosed exploration before logging" from an invisible gap into an
explicit, falsifiable claim — if it later emerges the attestation was
false, that is a clear, documented process violation rather than an
ambiguous gray area.

This makes a silent multi-attempt search visible after the fact even
though it cannot be prevented in the moment by process alone. A
**maximum of three** frozen-construction attempts are permitted within
a single pre-validation cycle. If a third attempt also fails to clear
Gate 1, the process must terminate as FAIL (Section 6) rather than
continue to a fourth — see Section 6 for what that requires and for the
terminal rule that follows from it.

**Methodology:**

- **Rank correlation comparison.** For each historical ranking date
  already covered by REFERENCE v1's own analysis, compute the
  cross-sectional Spearman rank correlation between the candidate H3
  score and REFERENCE v1's MOMENTUM score on that same date — one
  correlation per date, not pooled across dates, consistent with this
  project's existing discipline against pooling ETF-days into a single
  statistic. This produces a *distribution* of daily score-to-score
  correlations (median, spread) rather than a single number. No
  forward return, no null distribution, no p-value is computed at any
  point — this is a descriptive comparison of two already-computed
  scores against each other, not a hypothesis test.
- **Score overlap analysis.** Beyond the correlation coefficient,
  measure how much the *extremes* of the two rankings overlap on a
  given date — e.g., what fraction of the top-ranked ETFs under
  MOMENTUM also appear top-ranked under the candidate H3 score, and
  the same for the bottom. This is a more decision-relevant lens than
  a single correlation figure, since overlap at the extremes is what
  would matter most in practice, and a moderate overall correlation
  can still hide near-total overlap (or near-total divergence) at the
  tails. Reported as a distribution across dates, same as above.
- **Acceptable interpretation boundaries.** Per the instruction not to
  invent arbitrary thresholds, this plan proposes exactly one
  numerically justified boundary, not a full pass/fail scale:
  - The specific degenerate case already identified (a single, common
    benchmark subtracted from every ETF) is mathematically provable to
    produce a rank correlation of **exactly 1.0** with absolute-return
    ranking, and by extension a very high correlation with MOMENTUM is
    expected. A candidate construction whose measured median daily
    correlation sits at or near that value (allowing only a small
    tolerance for genuine construction differences within an otherwise
    near-degenerate design) should be treated as **not having escaped
    the degenerate case** and rejected outright — this is a
    consequence of the proven identity, not an arbitrary round number.
  - Below that boundary, the result is **interpretive, not a
    pass/fail gate**. A moderate correlation between H3 and MOMENTUM
    is not automatically disqualifying — relative-strength and
    absolute-momentum are documented "sibling" factor families in the
    literature and some positive correlation between them is expected
    even when both are genuinely, separately motivated. A moderate
    reading requires a written economic explanation for *why* the
    correlation exists (shared exposure to a common market factor,
    for instance) before Gate 1 can be considered satisfied — it
    cannot be waved through by the number alone, and it cannot be
    rejected by the number alone either.
  - A low or near-zero correlation is reassuring but not sufficient by
    itself: a construction could be trivially different (economically
    incoherent) rather than genuinely, meaningfully different. Low
    correlation is evidence *for* Gate 1, not a substitute for Gate 3's
    economic rationale.
  - **Resolving ambiguity at the boundary.** If reviewers cannot
    confidently determine that a measured correlation falls inside the
    mathematically obvious near-1.0 degenerate case, it must be
    treated as the stricter "moderate correlation" case — requiring a
    written economic explanation and independent confirmation — rather
    than being waved through as clearly non-degenerate. This document
    does not introduce a numerical tolerance figure to draw that line;
    instead, any case a reviewer is not confident about defaults to
    more scrutiny, never to less.

## 3. Historical data sufficiency verification

**Purpose:** determine whether the current dataset is adequate for
testing H3, without assuming in advance that more history is either
necessary or safe.

**Methodology:**

- **ETF inception-date inventory.** For all 25 tickers in the current
  universe, establish the real listing/inception date of each fund —
  not assumed, checked. Several tickers in the current universe are
  relatively young thematic funds (e.g. `ARKK`, `BOTZ`, `ICLN`, `HACK`,
  `SKYY`) and are the most likely to constrain how far back any
  extension can safely go without truncating the universe or
  reintroducing missing-data handling that the current window avoids
  entirely (both prior GO checkpoints measured 0% missing-data
  exclusion).
- **First usable price date, per ETF and for the full universe
  jointly.** Distinct from inception date — a fund can be listed
  before reliable daily price history is available from the existing
  data provider. Report both the per-ETF first usable date and the
  date at which *all* 25 ETFs simultaneously have usable data, since
  the latter is what actually bounds a full-universe panel.
- **Full-universe availability under candidate extension lengths.**
  For a small number of candidate extended windows (not chosen or
  justified here — that is an implementation-time decision), report
  how many of the 25 ETFs would have complete coverage, and how many
  would have to be dropped or gapped.
- **Effective sample size estimation.** Apply the same overlap
  adjustment already used in both prior close-outs (effective
  independent windows ≈ total ranking dates ÷ forward horizon) to
  estimate how much the effective sample size would actually improve
  under each candidate extension length. This is the number that
  determines whether an extension is worth its cost, not raw calendar
  span alone.
- **Regime coverage.** The most qualitative of the five checks, and
  should be reported as such, not dressed up as a precise figure. At
  minimum, document what distinct market conditions (e.g., periods of
  elevated vs. subdued volatility, sustained drawdowns vs. steady
  advances) are represented within the current window versus any
  candidate extended window, using realized volatility/drawdown
  dispersion across sub-periods as a documented proxy — not a claim
  that a fixed number of "regimes" can be objectively counted. This
  check is descriptive of the price history itself, not of any
  score-to-outcome relationship — it does not evaluate H3, MOMENTUM, or
  any candidate construction against a return, and is therefore
  consistent with Section 2's standalone no-outcome-data principle.

**Decision this output should support — not pre-decided here:**

- **A. Continue with current history** — indicated if the effective
  sample size gain from any safe extension is small relative to its
  cost, or if extension cannot be performed without compromising the
  survivorship/missing-data profile the current window already has
  cleanly.
- **B. Extend historical data** — indicated if the inception-date
  inventory shows the extension is safe for enough of the universe to
  matter, and the effective sample size estimation shows a material
  improvement, not a marginal one.
- **C. Change universe composition** — indicated if some ETFs
  (typically the younger thematic ones) are the specific obstacle to
  a safe extension, in which case testing on a smaller but
  longer-history subset of the universe may be preferable to either
  truncating the extension or accepting universe-wide gaps. This
  option carries its own risk — see Section 5.

This plan does not assume which of A/B/C is correct; that judgment
depends on the actual inventory results, not on this document.

**Universe change dependency (Option C only).** If Option C is chosen
and the resulting universe is not a strict subset of the original
25-ticker universe — i.e., it adds any ticker REFERENCE v1's MOMENTUM
was never computed against — Section 2's independence check no longer
has comparison data for those added tickers, and its coverage would
silently shrink if this is not addressed. In that case, Section 2 must
be explicitly re-scoped to the changed universe, including how a
MOMENTUM-equivalent comparison score would be obtained for every added
ticker, before Gate 1 can be approved. A universe change that stays a
strict subset of the original 25 does not trigger this requirement,
since existing MOMENTUM scores already cover it.

## 4. Research decision gates

Explicit gates, all of which must be satisfied before an H3
specification document is written. Note the ordering dependency
flagged in Section 2: although the gates are *checked* and *reported*
in the order below, the *work* behind Gate 3 (economic rationale)
must happen before the work behind Gate 1 (independence verification)
can be meaningfully performed, since Gate 1 requires a single, already
-frozen construction to test.

**Independent confirmation duties (apply to Gates 1, 2, and 3 alike).**
For each of these three gates, the confirming reviewer must be someone
who did not perform the work being confirmed, and must, before the
gate counts as satisfied:

1. review the complete construction attempt log (Section 2) — not only
   the final passing construction, if there is one;
2. explicitly confirm that no outcome data (forward return,
   risk-adjusted return, IC, p-value, or any other outcome variable)
   was read or computed at any point in the work being confirmed;
3. explicitly confirm that REFERENCE v1's or REFERENCE v2 H1's observed
   results did not influence construction selection, at any attempt,
   including the pre-log attestations (Section 2);
4. for Gate 1 specifically, **independently reproduce** — not merely
   inspect — the rank-correlation calculation, the score-overlap
   calculation, and the comparison against REFERENCE v1's frozen
   MOMENTUM scores, for the construction under review. The reviewer
   must arrive at their own figures using the frozen methodology
   (Section 2) and confirm they match what was submitted; reviewing
   the submitter's reported numbers without independently recomputing
   them does not satisfy this duty;
5. record this confirmation — reviewer identity, date, and the points
   above, including the independently reproduced figures for Gate 1 —
   as part of the archived evidence (Section 6), not only as an
   informal sign-off.

**Gate 1 — Candidate signal independence verified.**
The frozen H3 construction has been checked against REFERENCE v1's
MOMENTUM per Section 2's methodology, including the construction
attempt log (maximum three attempts) and, if applicable, the universe
change dependency re-scoping (Section 3). The degenerate-case boundary
was not triggered, and any moderate residual correlation has a
documented economic explanation, not merely a numeric excuse. This gate
requires independent confirmation per the duties above.

**Gate 2 — Historical data adequacy verified.**
Section 3's inventory has been completed and a decision among
A/B/C has been made and documented, including the specific reasoning
for that choice. If B or C was chosen, the resulting dataset/universe
change has itself been re-checked for missing data and survivorship
risk before this gate is considered satisfied. This gate requires
independent confirmation per the duties above — including, where
applicable, confirmation that an Option C universe change has been
correctly reflected in Section 2's re-scoping before Gate 1 is treated
as still valid.

**Gate 3 — Economic rationale frozen.**
A written, literature-grounded mechanism for H3 exists, documented
before the independence check was run (Section 2), not reverse
-engineered to justify a construction that happened to pass it. The
rationale must explicitly state why H3's proposed mechanism is
economically distinct from REFERENCE v1 MOMENTUM's underreaction /
diffusion mechanism — noting that a separate statistical check exists
(Gate 1) is not sufficient on its own; the economic case for
distinctness must be made on its own terms. This gate requires
independent confirmation per the duties above.

**Gate 4 — Specification can be written without unresolved degrees of
freedom.**
Every design choice a specification would need to state exactly once
— benchmark or peer-group definition, construction logic, universe —
has exactly one answer at this point. No "the exact benchmark will be
decided once we see the data" placeholders remain.

## 5. Research risks

- **Accidental momentum duplication.** The central, motivating risk of
  this whole plan — a naive construction collapsing into a
  rank-equivalent of MOMENTUM. Addressed by Gate 1, but only for the
  one construction actually tested; a different, later-proposed
  construction would need to be re-checked, not assumed to inherit an
  earlier construction's pass.
- **Universe selection bias, if Option C is chosen.** Deliberately
  narrowing the universe to ETFs with longer, cleaner histories could
  itself introduce a selection effect — funds that have survived long
  enough to have deep history may share characteristics (larger AUM,
  more established mandates) that correlate with return behavior,
  independent of anything H3 is trying to measure. This would need its
  own disclosure if Option C is selected, not a silent substitution.
- **Insufficient independent observations, regardless of A/B/C.** Even
  a successful extension is estimated, not guaranteed, to meaningfully
  raise the effective sample size (Section 3). Passing this
  pre-validation phase does not guarantee H3's eventual significance
  test will resolve cleanly — it only establishes that running the
  cycle is worth doing, not that it will avoid the same "insufficient
  evidence" outcome as v1 and H1.
- **Researcher degrees of freedom in the construction itself.**
  Benchmark definition, peer-grouping logic, and any other design
  choice must be fixed by economic reasoning (Gate 3) before Gate 1 is
  attempted — not discovered by trying several and keeping the one
  that "looks independent enough."
- **Gaming the independence check itself.** A subtler version of the
  above: choosing a construction specifically because it is
  superficially different from MOMENTUM (e.g., an unusual peer
  grouping with no real economic basis) purely to pass Gate 1, rather
  than because it is economically motivated. Gate 3's requirement that
  rationale precede the independence check is the primary defense
  against this, but it depends on that ordering actually being
  followed, not merely documented.
- **Regime-coverage judgment is inherently subjective.** Of the five
  Section 3 checks, this one is the least quantifiable and the most
  exposed to being rationalized toward whichever conclusion (extend or
  don't) is already preferred. Should be treated as supporting
  context for the A/B/C decision, not as a deciding factor on its own.

## 6. Decision outcomes

**Archive discipline (mandatory, applies to all three outcomes
below).** Regardless of whether the outcome is PASS, PARTIAL, or FAIL,
the pre-validation phase's own evidence must be preserved in
`research_archive/`, following the same convention already used for
REFERENCE v1 and REFERENCE v2 H1's significance results:

- the construction attempt log (Section 2), including every attempt,
  not only the last, together with each attempt's pre-log attestation;
- the independence analysis (rank correlation and score overlap
  results, Section 2);
- the data inventory (Section 3);
- the gate decisions, including which reviewer confirmed Gates 1, 2,
  and 3 and their recorded confirmation of the independent-review
  duties (Section 4), including the independently reproduced Gate 1
  figures;
- the **final determination** itself — PASS, PARTIAL, or FAIL — as its
  own explicit record, distinct from the individual gate decisions:
  the outcome, the decision date, and a short rationale synthesizing
  how the four gates led to it. This is not left to be inferred from
  the four gate records alone.

**Incremental preservation, not only a final bundle.** The attempt log
and its supporting evidence must be updated and preserved as each
attempt is logged, not assembled only once a final PASS/PARTIAL/FAIL
outcome is reached. A cycle that stalls or is quietly abandoned before
a formal outcome is declared must still leave a preserved record of
whatever attempts were logged up to that point — otherwise an
abandoned cycle could restart with no visible trace of prior attempts,
defeating both this archive requirement and the attempt cap at once.

**Commit pointer (recommended).** Where practical, the archived bundle
should include a pointer to the exact commit of this pre-validation
plan, and of any reviewer-confirmation records, that were in effect
when the evidence was produced — mirroring the `COMMIT.txt` convention
already used in `research_archive/reference_v1/` and
`research_archive/reference_v2_h1/`.

This applies to FAIL outcomes as much as PASS: nothing about this
document's own work should have to be silently redone by a future
researcher proposing a similar rotation-style idea later, with no
visibility that it was already attempted and why it did or didn't
proceed.

**PASS — proceed to H3 specification.**
All four gates satisfied: the frozen construction is not degenerate
with MOMENTUM (or its residual correlation is economically explained),
a data-sufficiency decision (A/B/C) has been made and documented, the
economic rationale is written and preceded the independence check, and
no design choice remains open. A formal, frozen H3 specification
document (mirroring `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md`'s
structure) can then be started as its own, separate task.

**PARTIAL — modify research direction with documented reason.**
Examples: the independence check repeatedly flags a near-degenerate
correlation for the initially proposed construction, requiring the
economic rationale itself to be revisited and a genuinely distinct
construction re-proposed (a return to Gate 3, not a search across
constructions at Gate 1); or the data sufficiency check indicates
Option C, requiring the `ETF_UNIVERSE` definition to be reconsidered
before H3 work can continue. A PARTIAL outcome is not a failure of the
pre-validation process — it is the process working as intended by
catching an issue before specification time rather than after a full
statistical run. Each construction revisit still counts as one attempt
against the Section 2 cap of three — a PARTIAL outcome does not reset
the count.

**FAIL — archive H3 idea before implementation.**
Indicated if either: (a) the construction attempt cap (Section 2,
maximum three attempts) is reached without a construction clearing
Gate 1 — this is a hard trigger, not a judgment call, once the log
shows three logged attempts have failed; or (b) the data sufficiency
analysis finds no viable path (extension unsafe, current history
judged inadequate, and no defensible universe change exists). Case (a)
suggests the relative-strength/rotation hypothesis family may not be
separable from momentum here regardless of construction, for this
specific platform's universe and data. In either case, H3 is archived
without ever having consumed implementation effort — with its
pre-validation evidence preserved per the archive discipline above —
and the project returns to `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`'s
ranked shortlist for the next candidate.

**Terminal rule.** Reaching the attempt cap closes H3, as currently
conceived, for this research program. It does not reset by opening a
new pre-validation cycle, relabeling the idea, or revising it under a
new name — any of those would defeat the cap in Section 2 as
effectively as an unlimited counter would. A future attempt to revisit
relative-strength or rotation-style ideas is only legitimate if it
rests on a materially different economic mechanism, independently
justified and subjected to its own fresh pre-validation plan from
Section 1 onward — not a continuation, reset, or rebranding of the
failed H3 attempts preserved in the archive.

Any such future proposal must, before its own Gate 3 can be
considered frozen: (1) consult the archived H3 pre-validation evidence
(Section 6) for every attempt previously logged; (2) explicitly state
how the new proposal's economic mechanism differs from each of those
attempts, not only from H3 in the abstract; and (3) demonstrate, in
writing, why it is a genuinely new hypothesis rather than a renamed or
restarted H3 attempt. A proposal that does not engage with the
archived evidence at all does not satisfy the terminal rule, regardless
of how it describes itself.
