# H3 Governance Remediation Addendum

**Status: governance transparency record, not a research document.** This
addendum documents the limitations discovered while hardening
[`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`](REFERENCE_H3_PREVALIDATION_PLAN.md)
for use as a formal pre-validation gate. It does not modify any code, any
H3 methodology, construction, or scoring logic, and it does not reopen or
re-decide any Gate 2 or Gate 3 determination already recorded in
`research_archive/reference_h3/`. Its sole purpose is to state plainly
what governance controls existed at each point in the H3 program, which
of them were introduced after the fact, and what a genuinely independent,
institutional-grade process would still require before a future research
cycle should be trusted on the strength of its own paperwork.

This document does not claim institutional independence for any review
performed to date, does not rewrite or soften any prior finding, and does
not remove any inconvenient fact recorded elsewhere in this program's
evidence. Where a prior document already states something plainly (e.g.
a self-disclosed non-independence, an unresolved root cause), this
addendum cites it rather than restates it more favorably.

---

## 1. Governance timeline

All times below are drawn directly from `git log` commit timestamps and
filesystem modification times of the untracked documents still awaiting
commit, both queried directly rather than taken from any document's own
self-reported date. All times are local (`+02:00`) as recorded by the
originating machine.

| Date/time | Event | Source |
|---|---|---|
| 2026-07-18 20:25 | `REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` written — H3 first appears as a ranked candidate (second, behind H1) in the original 8-hypothesis REFERENCE v2 strategy evaluation | file mtime; referenced secondhand in later docs |
| 2026-07-18 20:05–23:32 | REFERENCE v1 and REFERENCE v2 H1 closed out (both FAIL/insufficient-evidence outcomes) | commits `a1e8604`, `ff70d38` |
| 2026-07-18 23:37 | `REFERENCE_RESEARCH_ROADMAP_NEXT.md` committed — re-ranks 7 remaining candidates, promotes H3 to rank 1 | commit `1091a01` |
| 2026-07-19 00:16 | `REFERENCE_H3_PREVALIDATION_PLAN.md` frozen and committed — the governance document this whole program claims to operate under | commit `e909959` |
| 2026-07-19 00:25 | Gate 2 Phase 1: data sufficiency report produced, Option B (extend history) recommended | file mtime |
| 2026-07-19 (same session) | Data extension executed against the live database (49,300 rows inserted) | `REFERENCE_H3_DATA_SUFFICIENCY_REPORT.md` §4 |
| 2026-07-19 00:44 | Gate 2 discrepancy discovered and root-caused (50 invalid `PriceBar` rows) — investigation only, no fix | file mtime |
| 2026-07-19 00:48 | Database remediation plan written (not yet executed) | file mtime |
| 2026-07-19 00:56 | Backfill-gap-fill origin forensic report produced — origin **not** conclusively identified | file mtime |
| 2026-07-19 01:27 | Remediation executed (50 rows deleted, exported, re-verified) and recorded | file mtime |
| 2026-07-19 01:28 | Remediation script committed | commit `af239c2` |
| 2026-07-19 01:43 | Gate 2 **post-remediation** independent review recorded — PASS | file mtime |
| 2026-07-19 01:48 | Gate 3 economic rationale written | file mtime |
| 2026-07-19 02:00 | Gate 3 independent review recorded — PASS | file mtime |
| 2026-07-19 10:51 | H3 Construction Attempt 1 frozen (score formula, peer-segment grouping, 60-day lookback) | file mtime |
| 2026-07-19 12:03 | Gate 1 governance-readiness review recorded — PASS; quantitative Gate 1 testing declared eligible to begin | file mtime |
| 2026-07-19 (later, this program) | `REFERENCE_H3_PREVALIDATION_PLAN.md` hardened with six governance additions (rejected-candidates disclosure, methodology-freeze summary, reviewer-independence definition, reproducibility standard, terminal-failure restatement, final-determination template) | this session's prior turn |
| 2026-07-19 (this task) | This addendum produced | this session |

**Observations that follow directly from the timeline, not from
interpretation:**

- The entire pre-validation cycle — data extension, discrepancy
  discovery, remediation, two independent reviews, economic rationale, a
  frozen construction, and a Gate 1 readiness review — was completed
  within approximately 12 hours of a single calendar day
  (2026-07-19 00:16 to 12:03), following a prior evening in which two
  full prior research cycles (REFERENCE v1, REFERENCE v2 H1) were also
  closed out and a next-cycle roadmap memo written. No institutional
  quantitative research process this document is aware of would treat a
  same-day, single-operator sequence of this shape as equivalent in
  reliability to a multi-week process involving a standing research
  committee, scheduled review cadence, and cooling-off periods between
  stages. This is stated as a structural fact about the timeline, not as
  a claim that any individual step within it was performed carelessly.
- The original 8-hypothesis REFERENCE v2 strategy document that first
  ranked H3 is **not present in this repository** as its own committed
  artifact — it is known only through secondhand description in
  `REFERENCE_RESEARCH_ROADMAP_NEXT.md` and
  `REFERENCE_H3_PREVALIDATION_PLAN.md`. This means the earliest claimed
  point of H3's candidacy (and the claim that its original ranking
  predates any outcome data) cannot be independently verified from a
  primary source inside this repository — only from later documents'
  characterizations of it.

### Retrospective versus prospective controls

Of the six governance-hardening additions made to
`REFERENCE_H3_PREVALIDATION_PLAN.md` in the prior turn of this program:

| Control | Nature | Why |
|---|---|---|
| Rejected-candidates disclosure | **Retrospective** | The underlying roadmap ranking predates H3 pre-validation work, but its documentation inside the governance plan itself was added after Gates 2 and 3 had already passed. |
| Frozen-methodology summary | **Retrospective for Gates 2–3, prospective for Gate 1** | Gates 2 and 3 already ran under the plan's pre-existing (less consolidated) methodology language before this summary existed. Gate 1's own quantitative testing has not yet run, so this control is prospective with respect to the step it most directly governs. |
| Reviewer-independence definition | **Retrospective** | Added after three reviews (Gate 2 post-remediation, Gate 3, Gate 1 readiness) had already been recorded as "independent" under the plan's prior, looser language. |
| Reproducibility standard (no verbal explanation) | **Retrospective** | Same reason — added after the same three reviews. |
| Terminal-failure-rule restatement | **Prospective** | No FAIL determination has occurred in this cycle; the restatement governs a future event only. |
| Final-determination archive template | **Prospective** | No final determination (PASS/FAIL/INCONCLUSIVE) has been recorded for this cycle; the template awaits that event. |

A retrospective control can improve how future work in the same program
is judged. It cannot certify that earlier work already met a standard
that did not yet exist when that work was done. Where a retrospective
control and an already-completed step overlap (reviewer independence and
reproducibility, against the three reviews already recorded), this
addendum treats the earlier reviews as governed by whatever standard was
actually in effect when they were performed — the weaker, pre-hardening
standard — not by the standard introduced afterward.

---

## 2. Independence assessment

Every review recorded in this program to date is classified below using
three tiers: **independent** (a genuinely separate reviewing party, with
no shared authorship, incentive, or continuity with the work being
reviewed), **partially independent** (some real separation exists —
typically a fresh working session with no conversational memory of the
work — but without organizational, personnel, or incentive separation),
and **self-review assisted by AI** (the same session, or a session
directed by the same single operator with no procedural separation at
all, characterizes its own work as reviewed).

| Review | Classification | Basis |
|---|---|---|
| `gate2_independent_review_2026-07-19.md` (original, pre-remediation) | **Self-review** | The document itself discloses it was performed by the same session that did the underlying work, and explicitly states this does not satisfy the plan's independence requirement. Included here for completeness, not as a disputed classification. |
| `gate2_independent_review_2026-07-19_post_remediation.md` | **Partially independent** | Performed in a session with no conversational continuity to the remediation work, using an independently-written verification script rather than the remediation script's own output. This is real procedural separation. It is not organizational independence: same AI system, same class of operator direction, no distinct human or team, no compensation or incentive difference between "the work" and "the review of the work." |
| `gate3_independent_review_2026-07-19.md` | **Partially independent** | Same basis as above, applied to the economic-rationale document. |
| `gate1_governance_readiness_review_2026-07-19.md` | **Partially independent** | Same basis, applied to the frozen construction attempt. |
| Governance hardening of `REFERENCE_H3_PREVALIDATION_PLAN.md` (prior turn of this program) | **Not a review of prior work; self-directed governance authoring** | This work was explicitly framed as an adversarial governance review, but it modified the plan document itself rather than confirming or disputing any specific gate decision. It was performed by the same category of actor (a single AI session, directed by the same operator) as every review above. It should not be read as an independent audit of Gates 2, 3, or the Gate 1 readiness determination — it flagged the same independence limitation documented here, but flagging a limitation is not the same as correcting it. |
| This addendum | **Not independent; self-disclosed** | Produced by the same category of actor as every item above, in direct continuation of the same governance-hardening request. It documents limitations rather than resolving them, and should not be cited as an independent confirmation of anything it describes. |

### Limitations common to every "independent" review in this program

1. **No distinct reviewing party has ever been involved.** Every review
   to date has been an AI session, prompted by the same single human
   operator, with "independence" resting entirely on a self-report of
   absent conversational memory. There is no cryptographic, procedural,
   or organizational mechanism verifying that self-report from outside
   the session itself — a future reader has only the reviewing
   document's own word that it began "cold."
2. **No incentive separation exists.** An institutional independent
   review derives part of its value from the reviewer having no stake in
   the reviewed work passing. Nothing in this program's structure gives
   any reviewing session a distinct incentive from the working session it
   reviews — both are directed toward the same operator's same overall
   goal of completing the H3 pre-validation cycle.
3. **No standing reviewer role exists.** Institutional governance
   typically assigns review duties to a designated role (a risk
   committee, a second desk, a named individual) that persists across
   research cycles and can be held accountable across time. This program
   has no such role — each review is a one-off session with no identity
   that carries forward, which is itself the reason the plan's own
   "reviewer identity" archival requirement (Section 4, Section 6) has
   so far been satisfied only by "AI research assistant (Claude)," not by
   a named, accountable party.
4. **The one genuinely self-disclosed non-independent review
   (`gate2_independent_review_2026-07-19.md`) demonstrates the earlier
   process was capable of producing a review that failed the plan's own
   bar** — which is reassuring evidence that the process did not simply
   rubber-stamp itself indiscriminately, but does not establish that
   later "partially independent" reviews cleared a materially higher
   bar, only a procedurally different one (fresh session vs. same
   session).

**Conclusion.** No review in the H3 program to date should be described,
in any future document, as "independently confirmed" without also
disclosing the partial/session-only nature of that independence, per the
disclosure requirement added to `REFERENCE_H3_PREVALIDATION_PLAN.md`
Section 4 in this program's prior turn. This addendum extends that
disclosure requirement retroactively, in substance, to every review
performed before that requirement existed.

---

## 3. Data provenance assessment

### Known provenance gaps

- **Origin of the 50 `backfill-gap-fill` `PriceBar` rows: unresolved.**
  `REFERENCE_H3_BACKFILL_GAP_FILL_ORIGIN_REPORT.md` concludes "UNKNOWN,
  leaning NO, not provably closed" on whether the anomaly can recur. No
  script, commit, stash, or log entry was ever recovered; the most
  likely mechanism (a manual, un-versioned REPL action) was reconstructed
  from a data fingerprint, not confirmed. This gap was never closed — it
  was accepted as a residual risk under the remediation plan's own
  Section 5 mitigation (proceed on the strength of a recurrence check,
  since the rows are unambiguously invalid regardless of origin).
- **No structural write-time guard exists.** The invariant "a `PriceBar`
  row implies a matching `is_trading_day=1` `TradingSession` row" is
  enforced today only by the shape of the two current ingestion code
  paths, not by a database constraint, trigger, or application-level
  check. Both the origin report (§8) and the Gate 2 post-remediation
  review (§7, SHOULD FIX #2) recommend a durable guard; neither
  recommendation has been implemented.
- **The two-directional (missing + surplus) coverage check is not
  durable.** It was implemented once, inside the one-off remediation
  script, and has not been landed as a permanent part of this platform's
  regular data-verification tooling. The original discrepancy analysis
  (§9) and the Gate 2 post-remediation review (§7, SHOULD FIX #3) both
  flag this as outstanding.
- **No pre-delete database snapshot exists independent of the row-level
  export.** The Gate 2 post-remediation review (§3.1) explicitly
  discloses it had no direct byte-level "before" comparison available,
  relying on export-file arithmetic instead. The remediation plan's own
  recommended safeguard (a version-controlled or otherwise durable
  database snapshot at meaningful checkpoints) was never implemented
  (Gate 2 post-remediation review §7, OPTIONAL #2).
- **The runtime behavior of the append-only trigger
  (`trg_pricebar_no_delete`) was never independently tested.** Its
  presence and exact SQL text were confirmed by schema inspection only;
  no independent session has attempted (even inside a rolled-back
  transaction, against a disposable copy) to confirm it actually raises
  `ABORT` at runtime. The remediation record's claim that this was
  "manually re-verified after commit" is self-reported by the same work
  being verified and was explicitly not independently reproduced (Gate 2
  post-remediation review §3.6, §7 SHOULD FIX #1).

### Unresolved root causes

- The `backfill-gap-fill` insertion mechanism, above, is the program's
  only unresolved root cause. Every other data-quality question raised
  during Gate 2 (the +2 bar discrepancy itself, the one-directional
  verification gap that masked it, the trigger's schema state) was
  root-caused to a specific, confirmed mechanism.

### Accepted residual risks

- Proceeding with remediation despite an unconfirmed origin, per the
  remediation plan's own Section 5 precondition (mitigated by the
  recurrence check, not by closing the origin question).
- Relying on export-file arithmetic rather than a byte-level pre-delete
  snapshot as the reversal/audit mechanism for the deleted rows.
- Relying on schema-text inspection rather than runtime testing to
  confirm the append-only trigger's actual enforcement behavior.
- Operating without a durable, always-on two-directional coverage check,
  such that a similar surplus defect elsewhere in the platform would not
  currently be caught by routine tooling — only by a repeat of the kind
  of ad hoc forensic investigation this incident required.

### Required future controls (data layer)

1. A structural write-time guard (schema constraint, trigger, or
   application-level check) tying every `PriceBar` insert to a matching
   `TradingSession` row, closing the gap a purely code-shape-dependent
   invariant currently leaves open.
2. The two-directional (missing + surplus) coverage check promoted from
   a one-off script into permanent, regularly-run verification tooling.
3. A durable, version-controlled or otherwise tamper-evident database
   snapshot policy at defined checkpoints (e.g., before and after any
   remediation), so future reviews have a direct comparison available
   rather than reconstructing state from export-file arithmetic.
4. An independent, runtime (not schema-text-only) test of any database
   invariant a future remediation depends on, performed against a
   disposable copy rather than the live file.

---

## 4. Future mandatory controls

The following are proposed as entry requirements for any future
REFERENCE research cycle (H3's own construction and Gate 1 testing
included, if it proceeds from here) — not as retroactive requirements on
work already completed, consistent with Section 1's retrospective/
prospective distinction above.

1. **Methodology freeze before implementation, verified by an artifact
   independent of memory.** A frozen methodology summary (of the kind
   added to `REFERENCE_H3_PREVALIDATION_PLAN.md` in this program's prior
   turn) must exist and be committed to version control *before* the
   first construction attempt or the first evaluation run — not
   reconstructed afterward from what the methodology happened to be. A
   commit hash, not a document's own prose claim, is the freeze
   evidence.
2. **Immutable research snapshot.** Both the code/methodology state and
   the underlying data state must be captured at each meaningful
   checkpoint (freeze, pre-remediation, post-remediation, final
   determination) in a form that cannot be altered after the fact —
   version control for documents and scripts, and a durable, checksummed
   data snapshot for anything a live, mutable database currently leaves
   unprotected. This program's own Gate 2 review (§3.1, §7 OPTIONAL #2)
   already identifies this as a gap it had to work around rather than
   rely on.
3. **Reviewer separation that is organizational, not only
   procedural.** A "fresh session with no conversational memory" is not,
   by itself, sufficient independence for a determination this program
   treats as gating. Future cycles should either (a) involve a distinct
   human reviewer with no role in the work being reviewed, or (b), where
   an AI-assisted review is used, explicitly and permanently label it as
   procedurally rather than organizationally independent in every
   document that cites it — never simply "independent," unqualified, per
   the disclosure requirement already added to the plan's Section 4.
4. **Evidence archive with immutable provenance.** Every archived
   artifact should carry a commit pointer (or equivalent tamper-evident
   reference) from the moment it is produced, not added later as a
   SHOULD-FIX recommendation. This program's own archive currently
   contains five documents that were, at the time of this addendum,
   uncommitted and therefore without a verifiable timestamp independent
   of filesystem metadata — a gap the Gate 1 governance-readiness review
   itself already flagged (§3, §4 SHOULD FIX) but did not close.
5. **Decision log, separate from individual gate records.** A single,
   append-only log recording every decision point (which option was
   chosen among A/B/C, which construction attempt was frozen, which
   review classification applies, and why) should exist as its own
   artifact, distinct from the gate-by-gate documents, so that a future
   reader does not have to reconstruct the decision sequence by reading
   every underlying document's prose, as this addendum's Section 1 had
   to do.

---

## 5. Governance status

**Current governance status.** The H3 pre-validation cycle has completed
Gate 2 (data adequacy) and Gate 3 (economic rationale), both recorded as
PASS, and has frozen one construction attempt (Attempt 1 of a maximum of
three). A governance-readiness review has certified Gate 1's quantitative
independence testing may begin. No Gate 1 quantitative result has yet
been produced, and Gate 4 (no unresolved degrees of freedom) has not been
assessed. This status is unchanged by this addendum; this addendum
documents the process by which the above was reached, and its
limitations, without altering any determination.

**Accepted limitations, stated without qualification:**

- Every review performed to date is, at most, procedurally independent
  (a fresh session with no conversational memory), never organizationally
  independent (a distinct accountable party with separate incentives).
  This applies to Gate 2's post-remediation review, Gate 3's review, and
  the Gate 1 governance-readiness review alike.
- The origin of the 50 invalid `PriceBar` rows discovered during Gate 2
  was never conclusively identified; Gate 2 was passed on the strength
  of a recurrence check, not a closed root cause.
- No structural (as opposed to code-shape-dependent) guard exists against
  a repeat of the same data-integrity defect.
- The entire pre-validation cycle to date was completed within a single
  operator's single extended working day, a cadence this addendum does
  not treat as equivalent in reliability to a multi-stage institutional
  process with standing personnel and scheduled review intervals.
- Five archive artifacts central to Gate 2, Gate 3, and the frozen
  construction remain uncommitted as of this addendum, leaving their
  provenance dependent on filesystem metadata rather than a
  tamper-evident record.
- The governance-hardening controls added to
  `REFERENCE_H3_PREVALIDATION_PLAN.md` in this program's prior turn are
  retrospective with respect to Gates 2 and 3 and the reviews that
  cleared them; they improve how the remainder of this cycle (and any
  future cycle) will be judged, but they do not and cannot certify that
  the already-completed portions of this cycle met a standard that did
  not yet exist when that work was performed.

**Required improvements before the next research cycle** (whether that
is H3's own Gate 1/Gate 4 continuation or a future hypothesis entirely):

1. Commit the five currently-uncommitted archive artifacts, establishing
   a tamper-evident provenance record for work already done.
2. Implement the structural data-integrity guard and the durable
   two-directional coverage check identified in Section 3, before
   further data extension or remediation work is undertaken on this
   database.
3. Establish, and disclose in every future gate document, whether a
   given "independent" review is procedurally or organizationally
   independent — never leave "independent" unqualified.
4. Adopt the immutable-snapshot and decision-log controls in Section 4
   before Gate 1's quantitative testing is run, so that Gate 1's own
   result — the first point in this program where an actual number
   (a correlation figure) will exist — is produced under a genuinely
   frozen, tamper-evident methodology rather than one whose freeze point
   is established only by this program's own prose.
5. Before any future PASS/FAIL/INCONCLUSIVE determination is recorded
   using `REFERENCE_H3_PREVALIDATION_PLAN.md` Section 7's template,
   confirm the recording reviewer's independence classification using
   the three-tier scheme in Section 2 of this addendum, and record that
   classification explicitly rather than the word "independent" alone.

---

**This addendum makes no determination about whether H3 should proceed,
pass, or fail.** It is a transparency record about how the process
reached its current state, produced under the same limitation it
describes — a single AI session, directed by a single operator, with no
organizational independence from the work it documents. A future reader
should weigh this addendum's own credibility accordingly.
