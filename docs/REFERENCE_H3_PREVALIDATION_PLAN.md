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

### Candidate selection and rejected alternatives

H3 was not chosen in isolation. `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`
(Section 5) ranked seven remaining candidate hypotheses — carried over,
untested, from the original REFERENCE v2 eight-hypothesis strategy
document — against four fixed criteria: economic justification,
independence from REFERENCE v1 and REFERENCE v2 H1, data availability,
and overfitting risk. That ranking was produced, and frozen, before any
H3-specific pre-validation work began and before any H3 construction,
benchmark, or data extension existed to observe. It could not have been
shaped by an H3 result that did not yet exist.

The six candidates ranked below H3, and why each was not selected as
the next hypothesis:

- **H2 — Long-term momentum (12-1 month).** Rejected primarily on
  independence: ranked "Medium–Low" independence from REFERENCE v1's
  own MOMENTUM, the closest of any candidate to a disguised variant of
  an already-tested construct. Also data-constrained — requires deeper
  history than was backfilled at ranking time.
- **H6 — Long-horizon reversal (3–6 month).** Strong economic
  justification and independence, but rejected on data availability:
  as few as 4–8 non-overlapping windows in the pre-extension history,
  an effective-sample-size problem worse than the one both prior
  cycles already failed to clear.
- **H5 — Carry / yield.** Strong economic justification and
  independence, but rejected because it requires a genuinely new data
  source not yet integrated into the platform, with universe fit
  unverified.
- **H4 — Volume / flow acceleration.** Rejected on data reliability:
  ETF-level volume is contaminated by creation/redemption mechanics
  specific to the ETF wrapper, an uncertainty no other candidate
  carries.
- **H7 — Correlation-regime / idiosyncrasy.** Rejected primarily on
  economic grounds: no clear a priori direction, which the roadmap
  memo flags as a sign-selection risk — a researcher-degrees-of-freedom
  problem this plan's own Gate 3 discipline is designed to prevent.
- **H8 — Macro-conditional beta exposure.** Rejected as the weakest
  candidate on every criterion simultaneously: requires new external
  data and new statistical infrastructure beyond a simple score, and
  carries the highest researcher-degrees-of-freedom risk of the set.

H3 was ranked first because it was the only candidate scoring well on
all four criteria simultaneously — not because it was the only
candidate considered, and not because any candidate's construction was
tried and observed to fail before H3 was chosen. No candidate in this
list, including H3, was evaluated against any forward return, IC, or
other outcome variable before or during this ranking; the ranking
criteria are all determinable without touching outcome data, and the
roadmap memo's own scope statement confirms none was computed. This is
recorded here, in the document where H3's construction is actually
chosen and frozen, for the same reason Section 2 restates the roadmap's
prior-result-independence constraint at this level: so the constraint
binds at the point decisions are made, not only where it is first
stated.

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
  - **General ambiguity-resolution principle, restated.** The rule
    above is a specific instance of a single standing principle that
    governs every ambiguous reading this phase can produce, not only
    the near-1.0 boundary: where measurement uncertainty, a small
    number of underlying dates, or any other source of imprecision
    leaves a reviewer unable to confidently place a result on one side
    of a boundary or the other, the ambiguous case is treated as the
    stricter of the two possible readings by default. This applies
    symmetrically to the moderate-correlation/low-correlation boundary
    as well — a result that could plausibly be read as either should be
    treated as moderate (requiring a written economic explanation)
    until that explanation is provided, not defaulted to low
    (requiring nothing further). No new numerical threshold is
    introduced by this restatement; it only makes explicit that
    ambiguity is never resolved in the direction of less scrutiny,
    anywhere in this phase.
  - **Scope boundary — not a promotion or acceptance threshold.** This
    section resolves ambiguity only in Gate 1's score-to-score
    correlation reading. It does not, and cannot, define how
    near-threshold ambiguity in H3's eventual significance test
    (forward return, IC, p-value, or any promotion criterion) should be
    resolved, because Section 2's own standalone principle prohibits
    this phase from touching that kind of data at all. That question
    belongs to the frozen H3 specification a PASS outcome here would
    authorize (Section 6), and must be resolved there using the same
    pre-registered, no-post-hoc-adjustment discipline REFERENCE v1 and
    REFERENCE v2 H1 already established (Holm-Bonferroni correction,
    bootstrap robustness, and a promotion table fixed before any result
    is seen) — not invented ad hoc if a result later turns out to be
    close to whatever bar that future document sets.

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

### Frozen methodology summary (binding once Gate 1 begins)

Restating in one place what Sections 2 and 3 above already define
piecemeal — this summary adds no new rule; it only collects the frozen
elements so a reviewer does not have to reconstruct them from separate
sections:

| Element | Frozen definition | Source |
|---|---|---|
| Datasets | The current 25-ticker ETF universe, at whatever historical depth Gate 2's A/B/C decision and any resulting extension establish — not a forward-return dataset, since none is used in this phase | Section 3 |
| Evaluation basis | Same-date score-to-score comparison, restricted to ranking dates already covered by REFERENCE v1's own analysis — not a forward-looking evaluation period, since this phase never evaluates against a future outcome | Section 2 |
| Metrics | Daily cross-sectional Spearman rank correlation (distribution across dates) and score-overlap at the ranking extremes | Section 2 |
| Benchmark | REFERENCE v1's frozen MOMENTUM score, unchanged | Section 2 |
| Decision rules | The degenerate-case boundary, the moderate-correlation explanation requirement, and the ambiguity-resolution principle; the four research decision gates | Section 2, Section 4 |

**Freeze point.** All five elements above are fixed as of the version
of this document in effect when the first construction attempt
(Section 2) is logged against Gate 1 — that logging event is what
"Gate 1 begins" means for the purpose of this freeze. From that point
through the end of this pre-validation cycle (a PASS, PARTIAL, or FAIL
determination, Section 6), no element in this table may be changed for
any reason, including a reason discovered while reviewing an attempt's
results. A change to any row — a different date-sampling rule, a
different aggregation statistic, a different degenerate-case boundary,
a different benchmark — is a methodology change, not a construction
change, and Section 2 already states what a methodology change does:
it invalidates the pre-validation cycle to date and requires this
document to be revised and re-approved before any further attempt is
logged.

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
who did not perform the work being confirmed. "Someone" here means a
distinct reviewing party in substance, not merely a technically
separate work session — a fresh session initiated by, or under the
direction of, the same individual or process that performed the work
being reviewed does not, by itself, establish independence; it
establishes only that the review and the work happened at different
times. Where the work and its review are both carried out by the same
underlying researcher or process (human or AI) with no organizational
separation between them, that fact must be disclosed alongside the
confirmation record (Section 6), not left for a reader to assume from
the review's own "independent" framing. The confirming reviewer must,
before the gate counts as satisfied:

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

**Reproducibility standard (applies to all five duties above).** Every
input dataset, calculation, selection criterion, and the final
conclusion for each gate must be reproducible by the confirming
reviewer from the written record alone — the frozen documents, the
archived evidence (Section 6), and the raw data itself — without
requiring any verbal explanation, clarification, or supplementary
context from whoever performed the original work. If a reviewer can
only reach or understand a result after the original author explains
it in conversation, the record is incomplete and the gate is not
satisfied, regardless of whether the reviewer is ultimately persuaded.
A satisfied gate must leave enough in writing that a reviewer with no
access to the original author at all — not merely one who chooses not
to ask — could still complete the confirmation.

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

**Terminal failure discipline (explicit restatement).** The moment a
FAIL determination is reached, four things follow immediately and are
non-negotiable, not matters of researcher judgment:

1. **Research on this H3 attempt stops.** No further construction
   attempts, data work, or analysis proceeds under the H3 name once
   FAIL is recorded, other than the archive-discipline steps above.
2. **No tuning to force a different outcome.** No parameter, benchmark,
   peer-grouping, universe, or lookback adjustment may be made to any
   already-failed attempt, or proposed as a quick fix, in order to
   convert a FAIL into a PASS. Any construction change of any kind is a
   new attempt under Section 2's cap, not a correction to an old one —
   and if the cap (case (a) above) is what triggered FAIL, no further
   attempt is permitted regardless of how the change is characterized.
3. **No alternative evaluation period may be substituted after the
   fact.** The dataset and evaluation basis fixed by this document's
   frozen methodology summary (Section 3) may not be swapped for a
   different historical window, a different subset of dates, or a
   different universe once a FAIL determination is reached, in an
   attempt to find a period where the same construction would have
   passed. Section 3's Option C (universe change) remains available
   only as a pre-attempt research-direction decision (PARTIAL outcome,
   above) — not as a post-FAIL do-over.
4. **No parameter adjustment introduced after seeing results.** This
   restates, for the specific moment of a FAIL determination, the
   standing rule already implicit throughout this document: nothing
   about a candidate's construction may be selected or adjusted with
   knowledge of how it, or any close variant of it, performed against
   the independence check or any outcome data. A FAIL determination is
   the single moment in this process where the temptation to violate
   this rule is highest, which is exactly why it is restated explicitly
   here rather than left to be inferred from the general principle
   alone.

These four points restate rules already established elsewhere in this
document (Section 2's attempt cap and methodology freeze, Section 2's
prior-result-independence principle, Section 3's frozen dataset);
nothing above introduces a new decision rule. They are collected here
because a terminal FAIL is the point in the process where the pressure
to quietly bend an existing rule is greatest, and a governance document
that only states its rules once, far from the moment they are tested,
invites exactly that kind of drift.

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

## 7. H3 Final Determination (Archive Template)

A fillable record, separate from and in addition to the archive
discipline already required by Section 6. Section 6 requires that a
final determination be preserved in `research_archive/`; this template
is the structured form that determination should take, so that every
H3 pre-validation cycle — this one, or any future one permitted under
the Terminal rule (Section 6) — produces a determination record in a
consistent, comparable shape rather than free-form prose scattered
across whichever documents happened to be produced along the way.

This section is a template only. It contains no determination as of
this document's own freeze; it is completed once, at the point a final
PASS, FAIL, or INCONCLUSIVE determination is actually reached, by
whoever is authorized to close the pre-validation cycle — not filled in
speculatively before that point, and not filled in by the same
reviewer who performed the work being determined, consistent with
Section 4's independent-confirmation duties.

---

**Determination:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

*(PASS and FAIL correspond exactly to Section 6's PASS and FAIL
outcomes. INCONCLUSIVE is used only if the cycle is closed — by
deliberate decision, not by neglect — without reaching a Section 6
PASS or FAIL determination and without an open PARTIAL redirection
still in progress; a stalled or abandoned cycle, per Section 6's
"incremental preservation" clause, should be recorded as INCONCLUSIVE
rather than left with no determination at all. A PARTIAL outcome that
is still an active, in-progress redirection is not itself a final
determination and should not be recorded here until it resolves to one
of the three options above.)*

**Determination date:** _______________

**Reviewer(s) recording this determination:** _______________
*(must satisfy Section 4's independent-confirmation duties relative to
whoever performed the work being determined; state explicitly whether
that independence was organizational or session-based only, per
Section 4's disclosure requirement)*

**Version of this plan in effect:** _______________
*(commit hash or equivalent immutable pointer, per Section 6's commit-
pointer convention)*

**Evidence references:**
- Construction attempt log (Section 2), all attempts: _______________
- Independence analysis (Gate 1): _______________
- Data inventory and A/B/C decision (Gate 2): _______________
- Economic rationale (Gate 3): _______________
- Gate confirmation records (Section 4, all gates confirmed): _______________

**Synthesis rationale:**
_______________
*(a short, written account of how the evidence above led to the
determination above — not left to be inferred from the individual gate
records alone, per Section 6)*

---
