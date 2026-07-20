# Positive Control Study — Phase 3 Remediation Decision

**Independent Quantitative Methodology Review Committee — Formal Decision Document**

**Subject of review:**
[`docs/POSITIVE_CONTROL_PHASE3_ANALYTICAL_CORRECTION_ADDENDUM.md`](POSITIVE_CONTROL_PHASE3_ANALYTICAL_CORRECTION_ADDENDUM.md)
(the "Addendum"), read together with
[`research_archive/positive_control_phase3/decision_log.md`](../research_archive/positive_control_phase3/decision_log.md)
Entries 1–4,
[`research_archive/positive_control_phase3/pilot_results.md`](../research_archive/positive_control_phase3/pilot_results.md),
and
[`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md`](POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md).

**Status of this document:** decision-only. No code was written, executed, or
modified to produce it. It does not itself constitute a `decision_log.md`
entry (see §6). It has no governance effect until committed (see §7).

**Reviewer-independence disclosure (read this before anything else below):**
This is a **Level 2** review — procedurally independent (no participation in
authoring the Addendum or V2), **not organizationally independent**. No Level
3 (organizationally independent) reviewer exists or is available on this
platform, per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4's standing
disclosure. An external auditor should weight this document accordingly: it
is a structured adversarial pass by the same party (same author, same
platform, same absence of a second implementation) that produced the
material under review, not an outside check. Where this document uses the
word "committee," that word describes a review *posture*, not a distinct
organizational body.

---

## 1. Standard applied

Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2, Phase 4 (Methodology Freeze)
may not open while a Phase 3 gate the freeze depends on is failing at the
dimension point the freeze would apply to. The Addendum does not dispute
this — its own §14 states Gate 2's status "remains FAIL... until §12 step 1
is actually run and separately logged." This committee's job is narrower
than re-deriving the mathematics (which is checked in §2 below) and broader
than rubber-stamping the Addendum's own stated limitations: it is to decide
what governance status the Addendum earns, what must happen before any of
its content changes operative gate behavior, and to actively look for ways
this correction cycle could drift into self-validating research — the
platform's own named failure mode (`docs/RESEARCH_GOVERNANCE_STANDARD.md`
§1, "protecting research integrity").

## 2. Mathematical spot-check

Lemma 1 (rank invariance under a common additive shift) is elementary and
correct as stated — no dependence on distributional assumptions, exact at
any finite N. Sheppard's 1899 grade-correlation identity,
`ρ_grade = (6/π)·arcsin(ρ/2)`, is standard literature, not derived or fit
for this study. The Bartlett(k) own-kernel and the cross-lag triangle
function in §7 of the Addendum follow directly from window-overlap counting
and are arithmetically consistent with the disjoint-window independence
property V2 already established as proven. **No error found in the closed-
form derivation itself.** This is the basis for the diagnostic-acceptance
decision in §3 — but see §8 item 2 for why a clean derivation does not by
itself close the validation question.

## 3. Decision: Is the Addendum accepted as diagnostic research?

**ACCEPTED as diagnostic/theoretical research. NOT accepted as a completed
Gate 2 correction, and NOT accepted as grounds to change any operative gate
behavior, target function, or governance status by itself.**

Reasoning: the Addendum earns acceptance at the diagnostic level because it
follows the discipline this platform requires of exploratory theory work —
no code touched, every empirical number traceable to an already-committed-
pending JSON file with no rerun, an explicit and specific non-claims section
(§13) that a reader cannot mistake for a passing result, and a bounded
follow-up plan (§12) with a stated stop condition. It does not earn anything
higher than diagnostic status because none of §12's three concrete tests
have been executed — the entire correction is, at present, an unexecuted
prediction checked once against the exact data that motivated it (see §8
item 2 for why that specific fact matters more than the Addendum's own
text acknowledges).

## 4. Decision: What must happen before Gate 2's methodology can change

Ranked. "Gate 2's methodology changes" means: any point at which
`target_fn` in the fidelity-gate code is changed from Bartlett(k) to G(k),
or at which any downstream document (pilot_results.md, a future
methodology.md, a status memo) describes Gate 2 as passing, closer to
passing, or resolved.

- **BLOCKER — Execute §12 step 1 as an actual gate rerun, not a post-hoc
  table.** The current §9 comparison is arithmetic against already-recorded
  output; it is not a gate execution and must not be cited as one.
- **BLOCKER — Use a fresh, independently-drawn seed set for that rerun**,
  not the original R=25/seed set the correction was derived in response to.
  This is a requirement this committee is adding beyond what §12 itself
  specifies — see §8 item 2 for why reusing the original seeds would leave
  the correction partially unvalidated even after a "rerun."
- **BLOCKER — Run §12 step 3's N-sensitivity diagnostic and obtain a clear
  verdict** on whether the lags 1–12 residual is closable finite-N bias or a
  missing structural term, before G(k) is adopted as Gate 2's operative
  target anywhere. Adopting G(k) now would only replace one unvalidated
  target with a different, still-unvalidated one. See §5 for why this must
  precede any empirical-curve alternative as well.
- **BLOCKER — Pre-register the N-sweep's stopping/interpretation rule before
  running it.** §12 step 3 as written says the sweep should show the
  residual "shrinks toward zero" without specifying a quantitative
  criterion (a threshold, a monotonic-trend test, a fitted decay-rate
  check). Left unspecified, "did it shrink enough" becomes exactly the kind
  of post-hoc judgment call this platform's own discipline exists to
  prevent. This criterion must be written down before the sweep is run, not
  chosen after looking at the four N-values' results.
- **REQUIRED — Independent Level 2 review of the derivation itself** (§2 of
  this document is a spot-check, not a full second derivation) by re-
  deriving §3–§8 from the model definition without reading the Addendum's
  own derivation first, then comparing.
- **REQUIRED — A second, independently written implementation of the
  fidelity-gate computation**, at minimum for the corrected-target rerun.
  Entry 3 of the decision log already flags this as a gap relative to H3's
  established practice (H3 Gate 1, decision_log Entry 13); this Addendum
  inherits that same gap and should not compound it by adopting a new
  target with the same single-implementation exposure.
- **REQUIRED — Execute §12 step 2 (w-blend cross-term test) before G(k)
  plus the cross term is used anywhere w > 0 matters**, including the full
  41-point calibration run. Currently 100% of the empirical validation is
  at w=0, where the cross term is structurally zero and untested.
- **OPTIONAL — Increase R above 25 for the corrected-target rerun** to
  tighten the already-narrow tolerance bands at short lags and produce a
  more decisive signal, independent of the N-sweep's own purposes.

## 5. Decision: finite-N correction vs. empirical reference curves — order of operations

**Pursue the finite-N diagnostic (§12 step 3) first. Do not adopt an
empirical reference curve as a substitute for, or shortcut around, that
diagnostic.**

Reasoning, stated adversarially: an empirical reference curve — measuring
the ACF at high R/high N and using *that measurement itself* as Gate 2's
target, rather than a closed-form prediction — would resolve the Gate 2
FAIL immediately and unconditionally, because the target would be
mechanically forced into agreement with what the generator produces. That
is precisely the governance failure mode this platform's own discipline is
built to prevent: a gate that cannot fail is not a gate. It would also
directly resemble the "calibration-leakage" pattern this study's own v1
design was rejected for and v2 was specifically redesigned to avoid
(`[[project_positive_control_study_proposal]]` memory record) — the
mechanism is different (target leakage into a fidelity gate rather than
effect-size leakage into a hypothesis threshold) but the shape of the
violation is the same: the thing being validated supplies its own
validation criterion.

The finite-N diagnostic is strictly preferable on every axis that matters
here: it is cheap (explicitly scoped by the Addendum as a small-R
diagnostic, not a fidelity determination), it is falsifiable in a specific,
pre-specifiable way (§4's pre-registration requirement above), and it
produces one of two informative outcomes — either it *confirms* the
existing closed-form target is correct (residual is pure finite-N
estimator bias, vanishing as N grows, meaning no empirical curve is ever
needed), or it *rules out* finite-N bias as sufficient, which is new
information pointing at a genuinely missing analytical term — an argument
for further closed-form derivation, not for switching strategies to
empirical curves.

Empirical reference curves should be treated as a **last resort**, only if
repeated theory-based attempts fail to close a persistent, N-independent
gap. If that point is ever reached, any such curve must be estimated from a
dedicated, high-R/high-N reference run whose sole purpose is defining the
target — pre-registered before being used as a gate, and structurally
walled off from the run(s) it is later used to validate, so the same
data never both motivates and confirms the same target. This firewall
requirement should be written down now, before it is needed, exactly as
the calibration-leakage firewall was written down for effect sizes before
Phase 3 began.

## 6. Decision: how Gate 3 must be handled

**Gate 3 remains FAIL, unexplained, and unresolved. The Addendum's §10
finding (true independence cutoff is `2h=40`, not `h=20`) is accepted only
as a correct, out-of-scope structural observation — it is explicitly NOT
accepted as an explanation for the lags 44–51 failure, and must not be
cited as one.**

- **BLOCKER — no change to Gate 3's target, cutoff, or pass/fail status**
  on the basis of this Addendum. §10 is explicitly self-labeled "plausible,
  not yet confirmed" and "out of primary scope"; this committee preserves
  that framing rather than upgrading it.
- **REQUIRED — Gate 3 correction, if pursued, must be a separate, later,
  independently-scoped addendum**, exactly as the Addendum's own §10
  states. A single document that quietly resolves two gates at once is
  harder for any reviewer — including this one — to evaluate cleanly, and
  creates a specific incentive risk: once two corrections are bundled, the
  temptation to declare an overall "PASS" once enough individually-weak
  arguments stack up becomes real. Keep Gate 2 and Gate 3 remediation on
  separate documents, separate decision-log entries, and separate votes.
- **REQUIRED — before treating the lags 44–51 failure as Monte Carlo noise,
  run a targeted diagnostic increasing R specifically across lags 40–60**
  (or globally) and check whether the excursion disappears. This is
  directly testable and should be pre-registered (what R, what pass
  criterion) before running, for the same reason as §4's N-sweep
  requirement.
- **OPTIONAL — literature check on whether the daily-IC series'
  autocorrelation has any known closed form** under this Gaussian
  latent-factor model before assuming none exists; low priority, does not
  block Gate 3's interim disposition.

## 7. Decision: governance artifacts requiring update

- **BLOCKER — commit status.** Everything under review — the Addendum, both
  V2 proposal drafts, `research_archive/positive_control_phase3/` in full —
  is uncommitted. Per this platform's own repeated standard ("a document's
  own claim to be frozen or reviewed is not evidence until committed," most
  recently applied in Addendum §14 and pilot_results.md §7/§8), **this
  decision document itself has no governance effect until it is committed
  and its commit hash is recorded** in a `decision_log.md` entry. This is
  stated as a blocker on the decision's *effectiveness*, not on its
  existence as a written record.
- **BLOCKER — a new `decision_log.md` Entry 5** recording: (a) this
  committee's diagnostic-only acceptance of the Addendum, (b) the full
  §4/§5/§6 requirement list above as conditions precedent to any operative
  change, (c) explicit non-adoption of the §10 Gate 3 reframing. Per the
  append-only discipline (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §5), this
  entry should be appended, not substituted for this standalone document —
  the two serve different audiences (the log is the terse audit trail; this
  document is the reasoned justification). **Not appended by this
  committee in this pass** — recommended as the immediate next action,
  pending explicit approval, consistent with this platform's established
  commit discipline (propose → approval → commit).
- **REQUIRED — promote a new standing rule into
  `docs/RESEARCH_GOVERNANCE_STANDARD.md`** (or the roadmap memo's standing
  entry-requirements list): *no more than one theory-based target
  correction may be applied to a gate without a fresh Level 2 review of
  that specific correction; any subsequent correction motivated by a
  residual observed after a prior correction must pre-register its
  candidate mechanism before being checked against data.* This is the
  concrete fix for the iterative-target-patching risk identified in §8
  item 1 — it does not yet exist anywhere on this platform, and this
  Addendum is the first case where the risk is live (a second correction,
  if the N-sweep fails to close the residual, is now a foreseeable next
  request).
- **REQUIRED — apply the previously-drafted calibration-leakage firewall
  promotion from V2 §11** to `RESEARCH_GOVERNANCE_STANDARD.md`, and extend
  its language to explicitly cover target-function tuning (not only
  effect-size tuning), per §5's reasoning above. The other two V2 §11
  drafted edits (synthetic-cycle manifest addendum, reduced-replication
  worked example) remain required but are not newly urgent from this
  Addendum specifically.
- **REQUIRED — file this document under
  `research_archive/positive_control_phase3/reviewer_reports/`** (currently
  an empty scaffold directory per the archive manifest) once committed,
  consistent with the archive structure already built for exactly this
  purpose.
- **OPTIONAL — add a one-line pointer in `pilot_results.md`** to this
  document and the eventual Entry 5, for discoverability. Not required
  because pilot_results.md makes no claim this document contradicts.

## 8. Adversarial audit — p-hacking, target-adjustment, circular-validation risk

Findings, ranked by materiality:

1. **Iterative target-patching risk (the central risk in this review).**
   The Addendum derives a corrected target, checks it, finds it still
   fails on 12 of 20 lags, and proposes (§11/§12) to investigate further.
   Nothing here is a violation *yet* — the derivation is closed-form and
   literature-based, not fit to the residual, and the Addendum is explicit
   that it does not yet close the gap. But the natural next step after this
   document — a further correction that specifically targets the observed
   "smooth, one-directional, peak near k=4–6" residual shape — is exactly
   how legitimate theory work slides into curve-fitting-dressed-as-theory
   if no rule stops it. §7's new standing-rule requirement is this
   committee's concrete answer: any second correction must be motivated by
   an independently named mechanism, pre-registered before being checked
   against the residual it is meant to explain.
2. **Same-data motivation-and-validation overlap.** G(k) was derived in
   response to observing Gate 2's failure, then checked (§9) against the
   *identical* R=25/seed-25 dataset that produced that failure. The
   derivation itself is data-independent (Sheppard's identity holds
   regardless of what this dataset shows), which is the mitigating fact —
   but the *validation* in §9 is not an independent test, it is confirming
   a prediction against the data that inspired making the prediction in the
   first place. This is a real, underweighted issue in the Addendum's own
   §13 non-claims list, which discusses statistical/scope limitations but
   not this specific look-then-leap structure. §4's fresh-seed-set
   requirement is the direct fix.
3. **Honest-framing check: passed.** The Addendum's §9 "reading this
   honestly" paragraph and §13's non-claims list correctly resist the
   temptation to summarize "8 of 20 lags now pass" as meaningful progress
   toward an overall PASS. This framing must be preserved verbatim in any
   downstream citation — any future document that shortens this to "Gate 2
   mostly passes under the corrected target" without the 12-lag-fail
   caveat should be treated as a governance violation in its own right.
4. **Scope-bundling check: passed, with a forward-looking condition.** The
   Addendum keeps Gate 3 explicitly out of scope (§10, §13) rather than
   quietly resolving it alongside Gate 2. §6 of this document makes that
   separation a formal requirement for any future work, not just a
   observation about this document.
5. **Independence/incentive check.** Both the Addendum and this review are
   produced without organizational independence (§0 disclosure). This is a
   pre-existing, disclosed platform limitation, not a new finding — but an
   external auditor should treat every "PASS," "FAIL," and "accepted"
   verdict in this entire research program, including this document's own
   verdicts, as Level 2 at most until a genuine Level 3 reviewer exists.
6. **Stopping-rule risk in future diagnostics.** Addressed as a BLOCKER in
   §4 and REQUIRED in §6 — both the N-sweep and the R-increase-for-Gate-3
   diagnostics need pre-registered interpretation criteria, or their
   results become exactly as gameable, after the fact, as an unfrozen
   effect-size threshold would be.

No finding above rises to "reject the Addendum" — the mathematics is sound
and the authoring discipline (no code touched, explicit non-claims,
bounded scope) is genuinely better than a bare curve-fit would look like.
The findings instead define the conditions under which this diagnostic
result is allowed to become an operative methodology change, which is the
purpose of this decision document.

## 9. Formal disposition

| Item | Verdict |
|---|---|
| Addendum accepted as diagnostic research | **YES** |
| Addendum accepted as a completed Gate 2 correction | **NO** |
| Gate 2 operative target may change now | **NO** — blocked on §4 |
| Finite-N diagnostic vs. empirical reference curve | **Finite-N diagnostic first; empirical curves last-resort with firewall** — §5 |
| Gate 3 status | **FAIL, unresolved; §10 not accepted as explanation** — §6 |
| Phase 4 (Methodology Freeze) | **Not open; unaffected by this document** |
| This document's own governance effect | **None until committed + logged (§7)** |

**Reviewer level:** Level 2 (AI-assisted adversarial, procedurally
independent; not organizationally independent — no Level 3 reviewer exists
on this platform).

**Next action, pending approval (not taken in this pass):** append
`decision_log.md` Entry 5 summarizing this document's verdicts, then commit
both together.
