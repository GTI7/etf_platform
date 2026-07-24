# Phase F — Pre-Implementation Amendment Plan

**Date:** 2026-07-24
**Author role:** principal architect.
**Repository state:** canonical `D:\Claude\etf_platform`, `master`, HEAD
**`67b42bd`**, `origin/master == master`, working tree carrying two
untracked files: `docs/PHASE_F_IMPLEMENTATION_READINESS_REVIEW.md` and
this plan itself, `docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md`.
**Disposes of:** findings **R-16 … R-23** of
`docs/PHASE_F_IMPLEMENTATION_READINESS_REVIEW.md`.
**Reads and is bound by:** `PHASE_F_ARCHITECTURE_ACCEPTANCE.md`
(conditions C-1 … C-12), `PHASE_F_ACCEPTANCE_CONDITIONS.md`
(F-C1 … F-C4), `PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` (R-1 … R-7,
§5 required AD content), `ARCHITECTURE_DECISIONS.md` at HEAD.

**Review level: Level 1 — self-review** (`RESEARCH_GOVERNANCE_STANDARD.md`
§4). This document is **not a review**: it produces no findings of its
own and re-derives only the four facts its own rulings turn on (§7). It
is a **disposition plan** — it decides, for each of R-16 … R-23, the
instrument by which the finding is discharged. It must never be cited as
a review of any level, and never using the unqualified word
*independent*.

**Nothing is executed by this document. No production code. No tests. No
ADR text. `ARCHITECTURE_DECISIONS.md` is untouched.** AD-061 … AD-067
remain reserved and unaccepted; the accepted ceiling remains **AD-069**.

---

## 0. The ruling that orders everything below

**You cannot amend an AD that has never been written.**

AD-061 … AD-067 are *reserved and unaccepted*. Every instruction in the
readiness review of the form "AD-064 gains a clause" is therefore **not
an amendment**. It is **required content of an unwritten AD** — a forward
obligation discharged by the authoring act, F-0, exactly as
`PHASE_F_ACCEPTANCE_CONDITIONS.md` §0 already states for F-C1 … F-C4.

This distinction is not pedantry; it decides the instrument:

| Target | Status at HEAD | Correct instrument |
|---|---|---|
| AD-061 … AD-067 | reserved, **unwritten** | **required content at F-0.** No amendment block — there is no prior text to preserve |
| AD-047 … AD-060, AD-068, AD-069 | **accepted** | **dated amendment block only**, appended, prior text preserved by quotation. Not touched by this plan |
| The AD numbering reservation block | **accepted text**, non-numbered | **dated amendment block**, quoting and superseding its one stale status sentence (the next-free-number claim) only |
| AD-070, AD-071 | **free** | **not reserved by this plan.** Numbered and drafted, if still required, at Track C's own head commit (C0) |

So the four-way decision the task asks for resolves, for R-16 … R-23,
into exactly three live buckets. **The "ADR amendment" bucket is empty
for all eight findings**, and that is the correct outcome: no accepted AD
is amended, no accepted AD is weakened, and no historical AD text is
rewritten.

---

## 1. Disposition table — R-16 … R-23

| # | Decision | Affected AD | Instrument | Lands in |
|---|---|---|---|---|
| **R-16** | **F-0 acceptance text** | **AD-061** (primary). AD-068 **cited, not amended** | Required content — one scoping sentence beside C-5's | **A1** |
| **R-17** | **New AD required — but not Phase F's, and not F-0's.** Numbered and drafted at Track C's own head (C0), not reserved before it; the writer itself waits until implementation | **AD-070** *(new)* | Numbered/drafted (C0) → code (C1) | **C0 / C1** |
| **R-18** | **F-0 acceptance text — non-bridge, non-claim only.** No composition-root placement is stated by F-0 | **AD-064** (non-bridge, non-claim). Proposal §7.1 reading in A2 | Required content | **A1 + A2** |
| **R-19** | **New AD required** — a mechanism-demonstration cycle is not a research cycle | **AD-071** *(new)* | Numbered/drafted (C0) → the cycle (C3) | **C0 / C3** |
| **R-20** | **Wait until implementation.** Real, and carries **no new decision** — it is a consequence of accepted AD-047 part 2 and AD-051 | **None amended.** Restated as an operating precondition inside **AD-071** | Operator obligation + `decision_log.md` | **C0 / C3** |
| **R-21** | **Split.** Non-claim → F-0. Positive semantics → AD-070. Enforcement → acceptance criterion | **AD-064** (non-claim) + **AD-070** (what a valid reference *is*) | Required content + criterion | **A1 / C0 / C4** |
| **R-22** | **The stale next-free-number claim is resolved before F-0, in its own commit** — the reservation block's own same-commit rule forces this. The "independent review" sentence is a separate matter and moves to A1 (see §4) | The **reservation block** (dated amendment) | Dated amendment block, prior text quoted | **A0 (numbering only) / A1 (review-basis sentence)** |
| **R-23** | **F-0 acceptance text.** The two documents that overclaim are **not edited** | **AD-064** (primary) | Required content — a dated census | **A1** |

**Not a real issue: none of the eight.** Every one was re-derived from
the repository by the readiness review, and I re-derived the four that my
own rulings depend on (§7). R-20 and R-21 are real findings that
nonetheless generate **no new decision** — R-20 because accepted ADs
already decide it, R-21 because AD-042 already decided that
`dataset_refs` is opaque *on purpose*. Both are disposed of as
disclosure and criterion, never as mechanism.

---

## 2. The four findings the task singles out for architectural statement

### 2.1 R-16 — Research → ETF: the correct architectural statement

**The statement is a prohibition on placement, and it is a consequence,
not a decision.**

> **No `Experiment` implementation that reads ETF data may live under
> `core/research/`.** `core.analytics` is the `etf` domain
> (`check_import_boundaries.py`, `DOMAIN_OF_TOPLEVEL`); `research`'s
> allowed set is `{data, statistics, governance, validation}` and holds
> **no `etf` grant**; and AD-068 decision 2 makes that grant
> **unavailable rather than merely absent** — `etf` appears in no other
> domain's value set *by construction*, because an asset class is a
> plug-in above the platform. AD-068 decision 3 closes the remaining
> route: `ETF_SYMBOLS_BY_MODULE` attributes `ETFId`, `ETF`, and the
> `insert_etf` / `get_etf` / `get_etf_by_ticker` repository functions to
> `etf` **by the name bound, not by the module that hosts it**, so
> reaching ETF data through the *granted* `research → data` edge is a
> violation too. An ETF `Experiment` therefore lives **outside `core/`**.

**Why AD-061 and not AD-068.** Three reasons, in order of weight.

1. **Symmetry with C-5.** AD-061 is already required to carry a sentence
   scoping Phase F's *no-`core.store`* property to Phase F's own modules
   rather than to an `Experiment` an author might write later. R-16 is
   the identical sentence for a second domain, with a stronger ending:
   `store` is *addable by recorded decision* under AD-069's demand-driven
   rule; `etf` is **not addable**. The two belong side by side, in the AD
   that governs what the runner and its inputs may know.
2. **Direction of repair.** Amending AD-068 to restate its own
   consequence would set the precedent that every downstream consumer
   edits the upstream decision it consumes. AD-068's text is sufficient
   as accepted; what is new is the *derivation*, and the derivation is
   Phase F's.
3. **The mechanism already refuses correctly.** No grant is added, no
   file moves, no checker changes, no test changes. The repair is one
   sentence because the boundary works.

**AD-068 is cited by decision number (2 and 3) and is not amended.
AD-069 is untouched.** F-9's AST test is unaffected — its predicate is
AD-063's authority enumerations, and `core.analytics` carries no Decision
Chain authority.

### 2.2 R-18 — Experiment object vs. reproduction runner: what F-0 may say now

**F-0's text is limited to three negative/structural statements — nothing
more:**

> **Phase F builds no bridge** between an `Experiment` implementation and
> `core.governance.reproduction_runner.run_reproduction`. **Phase F makes
> no reproduction claim**: `experiment_name` is a caller-chosen label, not
> an identity, and nothing in Phase F asserts that code reproduced under
> `reproduction_runner` is the same code that ran under `ResearchRunner`.
> The two models remain **structurally separate** — neither references
> the other, and Phase F is not authorized to connect them.

This is deliberately silent on *how*, or *whether*, an operator might
later achieve identity between the two — **no adapter, no
composition-root inhabitant, no `run()`-entrypoint convention, and no
placement decision is stated here.** Any such route is an implementation
choice for **Track C**, made — if at all — when C2 is actually written; it
is not a claim F-0 gets to make about code that does not yet exist.

Three things this non-claim is **not**, restated because each is
individually forbidden and a later reader will otherwise re-derive one as
novel: it is not a `ReproducibilityChecker` or any bridge object
(Proposal §7.1 forbidden list, restated in force by F-C2 §2.3 item 4); it
is not `ResearchRunner` wired into `reproduction_runner` (R-11 defers
that to a later increment explicitly); and it authorizes **no
`ReproductionRecord` producer** — writing the
`(commit_hash, dataset_content_hashes, result_report_hash)` triple for
Golden Run 001 is a **human act against the existing frozen dataclass**,
not a component.

**Divergence from the readiness review, recorded so it is not later read
as an inconsistency.** R-18's ruling item 1 places the whole ruling in
AD-064. That placement is **kept as a single home, not split.** AD-063
enumerates authority the composition root *holds*; F-0 states no
composition-root inhabitant at all (above), so AD-063 gains nothing from
this finding and is not amended by it. Everything R-18 discharges lands
in **AD-064** alone, as the non-bridge, non-claim disclosure.

**§7.1's `experiments/validate_h4_*.py` prohibition is unrelaxed.** Its
reading is written down rather than assumed: the prohibition is on **H4
research content** written as a shortcut around the runner. Whether a
**non-H4** experiment module the runner itself invokes is or is not that
shortcut is a question for whoever writes it — not one F-0 answers in
advance, since F-0 states no invocation route. Primary home: the Proposal
§7.1 amendment in **A2**. Mirrored as one clause in AD-064's non-bridge
paragraph, so the reading survives independently of the Proposal.

### 2.3 R-19 — the first official research archive

**Golden Run 001 runs against a dedicated cycle, `golden_run_001`. Not
`reference_h4`. Not any existing cycle.**

Scaffolded by the existing `tools/archive_manifest.scaffold_project_archive()`,
which creates `dataset_hashes/`, `experiment_results/`, and
`reviewer_reports/` with `.gitkeep`. This **sidesteps C-11 entirely**
rather than depending on it: no `ArchiveWriter` precondition is relaxed,
`reference_h4` is not touched, and C-11 stays open on its own timetable
by the additive `tools/` route (X2, off the critical path).

**Why this needs a number rather than a `decision_log.md` entry.** The
decision is not "which cycle" — that is operational. The decision is
that **a mechanism-demonstration cycle is a legitimate inhabitant of
`research_archive/`**, producing a real, permanent, hash-chained
`transition_records.jsonl` that **asserts nothing about any hypothesis**.
No accepted AD contemplates such an entity: AD-050 defines research cycle
identity, derived phase state, and human-authorized transitions, and
every record it governs is a research record. A first real chain entry
that is *not* a research record is a new kind of thing in the archive,
and the misreading it invites — a later reader treating
`golden_run_001`'s transition as evidence — is the highest-consequence
misreading on the entire Golden Run path.

That is claim-sensitive disclosure, which is precisely the granularity
test the Resolution's Q3 ruling applied when it kept AD-064 … AD-067
separate. It gets **AD-071**.

**What AD-071 must record** (drafted at C0, not here):

1. `golden_run_001` is a **mechanism cycle**: it demonstrates the
   mechanism and nothing more. Its ranking is not a research result; its
   frozen criteria are **demonstration criteria frozen for this run
   only**; `reference_h4` has not advanced in any way.
2. The marking obligation: the cycle's own `README.md` **and**
   `decision_log.md` carry that statement, in §7.1's words.
3. **R-20's minimum freeze contract** (§2.4) as the cycle's operating
   precondition.
4. The **non-claims** of §7.5 of the readiness review, carried in full —
   including that a `VERIFIED` reproduction proves the same inputs
   produced the same output and **not** that the measurement was correct,
   and that the repository still has **no reproducibility contract**
   (F-C1).
5. That AD-071 authorizes **one** such cycle. A second mechanism cycle is
   a new decision. This is what keeps a demonstration from becoming a
   category.

### 2.4 R-20 — the minimum freeze contract

**No mechanism, no guard, and — this is the ruling — no new decision.**
Every fact R-20 states is already decided by **accepted** ADs: `GateContext`
refuses an empty `freeze_covered_paths` in `__post_init__` (AD-047
part 2), `verify_freeze` returns `UNVERIFIABLE` for an empty set
(AD-051), and `compose_transition()` refuses with `FreezeNotVerified` /
`BracketInvalidated` when the bracket does not project to `verified`.
Restating a consequence of an accepted AD inside an amendment block to
that AD would be rewriting decided text to say what it already says.
**AD-047 and AD-051 are not touched.**

The contract is therefore stated **once**, as an operator obligation,
inside AD-071 and repeated in `golden_run_001/decision_log.md`:

> **Minimum freeze contract for any real run.**
> 1. `freeze_covered_paths` is **non-empty** and names real paths.
> 2. `freeze_commit_ref` is a commit that **already contains** the
>    methodology and criteria files it covers.
> 3. The working tree is **clean** at execution time — no committed and
>    no uncommitted drift since `freeze_commit_ref` on the covered paths.
> 4. Therefore the sequence is, and can only be:
>    **freeze commit → clean tree → run.** Freezing a methodology and
>    running the experiment inside one uncommitted edit yields `DRIFTED`
>    and a refused transition.

Discharged by **sequencing**, which is why C3 (freeze) and C4 (run) are
two commits and not one.

---

## 3. Dataset identity — R-17 and R-21 together

The two findings are one subject read from opposite ends, so they are
decided together and land in one AD.

**R-17: does the writer belong before Golden Run, or in F-1?**
**Neither, as posed. It is Track C, and it is not F-1.**

- **Not F-1.** F-1 is `core/research/execution/` measurement types, and
  its exit criterion is F-C2's closed, test-pinned field set. The
  manifest writer is a `tools/` module at a different altitude, in no
  domain, consumed by no Phase F component. Folding it into F-1 would
  corrupt F-1's exit criterion — the one gate F-C2 §6 says F-1 must not
  land without — by adding an obligation F-C2 never placed there.
- **Before Golden Run, necessarily.** The database is not a repository
  artifact (`.gitignore` excludes `*.db`), so dataset identity for a real
  run can come **only** from committed snapshots plus a manifest that
  hashes them. There is no alternative route. Zero `dataset_manifest.json`
  files exist repository-wide (re-derived, §7): the manifest class has a
  parser, a verifier, a consumer, and **no producer and no instance**.
- **Therefore: Track C, commit C1**, immediately after its authorizing AD
  and immediately before its only consumer.

**R-21: what a valid dataset reference means.** The task asks for the
positive definition. It cannot come from Phase F, and Phase F must not be
made to supply it:

> **A `dataset_ref` is valid for a cycle if and only if it resolves to a
> declared `snapshot_path` in that cycle's `dataset_manifest.json`.**
> `MeasurementBundle.dataset_refs` is `tuple[str, ...]` of **opaque**
> refs by accepted decision (AD-042). Nothing in Phase F resolves them
> and **nothing should** — a runner-side resolver would be the
> duplicated rule at the wrong altitude that R-5 refuses. Opaque refs are
> **evidence retention**; dataset identity lives in the manifest; the two
> are connected **only by the operator**, and the connection is checked
> as a **milestone acceptance criterion**, never by a runtime guard.

**Split of homes, and why:**

| Element | Home | Timing |
|---|---|---|
| Phase F **non-claim** — *Phase F does not validate that a `dataset_ref` identifies a dataset* | **AD-064** | **F-0 (A1)** |
| The **positive semantics** above, and the writer's authority | **AD-070** | **C0** |
| The **check** — every entry in `dataset_refs` resolves to a declared `snapshot_path` in `golden_run_001`'s manifest | Golden Run 001 acceptance criterion 5 | **C4** |

**What AD-070 must record** (drafted at C0, not here):

1. **The manifest schema has exactly one authority**, and it is the
   existing reader — `core.governance.dataset_manifest.parse_dataset_manifest`
   and `reconstruction_loader._verify_dataset_integrity`. The writer is
   verified **by round-trip through that reader** (build → parse →
   preflight → reconstruct), **never** by assertions against its own idea
   of schema v3. A writer verified only against itself **is a second
   schema**, and a second schema is the defect this clause exists to
   prevent.
2. **It hashes with `canonical_jsonl.sha256_of_file`** — the same
   function `_verify_dataset_integrity` checks with. Not an equivalent
   one.
3. **It lives in `tools/`, beside `archive_manifest.py`**, by direct
   analogy to **AD-039** (archive manifest tooling stays in `tools/`
   until a concrete governance consumer exists) and to Q1's ruling on
   `experiment_results/` creation. It touches no `core/` module and is
   not a domain abstraction. **AD-039 is cited, not amended.**
4. **It is one function, not a framework.** No dataset registry, no
   snapshot scheduler, no refresh policy, no incremental hashing. This
   clause is the load-bearing half: the prohibition is what keeps a
   milestone helper from becoming infrastructure.
5. **R-21's positive semantics**, above.
6. **Re-affirmation of AD-064's census, re-dated to C0 — not a second,
   independent finding.** AD-064 (landed at A1) already establishes, as of
   its own commit, that no `dataset_manifest.json` and no dataset
   snapshot for any real cycle exists in the repository. AD-070 does not
   re-derive this fact from scratch; it **re-checks and re-dates** the
   same fact to C0's later commit, the way AD-067 already requires for
   its own censuses (C-4). One authority for the fact — AD-064 — and two
   dated readings of it, at A1 and again at C0.

**Why AD-070 is not written in F-0.** Two independent reasons, either
sufficient. First, **it is not a Phase F decision** — F-0's own scope is
AD-061 … AD-067, and the readiness review's §2 finding that Phase F needs
"no eighth number" is a statement about *Phase F*, which AD-070 is not.
Second, and decisive, **its census would be stale on arrival**: clause 6
is a count at a commit, and accepting it at A1 would leave it eleven
commits behind by C1 — reproducing exactly the H-7 / R-13 staleness
defect that condition C-4 exists to correct. **C0 lands immediately
before C1**, and its censuses are true and freshly dated when written.

---

## 4. R-22 — numbering, resolved before F-0

**The correction owed at A0 is narrower than the readiness review's own
framing.** The reservation block's general rule reads:

> *A number is reserved from the moment any governance document claims
> it, and `docs/ARCHITECTURE_DECISIONS.md` is the single place a
> reservation is discoverable. Any document that claims a range must have
> that claim mirrored here, in a block like this one, **in the same
> commit that makes the claim**.*

**This plan claims no range.** AD-070 and AD-071 are named here only as
findings' likely eventual home *if Track C still needs them* — not as
numbers this document reserves. That reservation, if any, is Track C's
own act, at C0, in the same commit that drafts and accepts whichever of
the two survive re-derivation against Track B's actual output. The
mirroring rule therefore has nothing to mirror yet, and A0 makes no entry
for AD-070 or AD-071.

**What *is* stale, and owed now regardless.** The block's other status
sentence — *"New ADRs therefore number from **AD-068**"* — is a factual
claim about the file's own state, and it is false today: AD-068 and
AD-069 are both accepted, so the true next free number is **AD-070**.
This is owed at A0 because it is already false, independent of anything
Track C does later, and leaving it stale is the identical hazard the
block exists to prevent.

**Divergence from the readiness review**, recorded: R-22's ruling pairs
this fix in A1 with F-C4 §4.3 item 4's replacement sentence. That pairing
is **not followed here**. F-C4 §4.3 item 4's sentence — *"…blocked for
want of an independent review…"* — is a claim about whether F-0's blocker
is **discharged**, and F-C4 itself ties that supersession to "when F-0 is
performed." F-0 is **not** performed at A0; AD-061 … AD-067 are still
unwritten at that commit. Superseding that sentence at A0 would have A0
assert an acceptance that has not happened — exactly what this document's
own header forbids ("Nothing is executed by this document"). **That
supersession moves to A1**, the commit that actually performs F-0. A0
performs **only** the stale-numbering correction.

**Form of the correction — and the discipline it preserves.** The block
is accepted text. Its **decisions** (the reservation itself for AD-061 …
AD-067; the release condition; the general rule) are **never rewritten**.
Its one stale **status sentence** — the next-free-number claim — is
superseded **in place by a dated amendment note that quotes the prior
text**, in the same form AD-069's dated 2026-07-24 note already uses.
Nothing is silently overwritten and nothing is deleted.

**A0's amendment note to the reservation block records:**

1. **Superseded:** *"New ADRs therefore number from **AD-068**."* True
   when written; **stale at HEAD** — AD-068 (`:3139`) and AD-069
   (`:3274`) are both accepted. **The next free number is AD-070.**
2. **Unchanged and restated as unchanged:** AD-061 … AD-067 remain
   reserved to Phase F and unaccepted; the general rule; the release
   condition; the AD-052 … AD-055 precedent; and the *"blocked for want
   of an independent review…"* sentence, which A0 does **not** touch —
   see above, it moves to A1.

**Not performed at A0.** AD-070 and AD-071 are **not reserved by this
commit** and no new reservation range is opened. They remain forward
obligations on **Track C** only: numbered, drafted, and accepted together
at C0 if still needed, never pre-reserved ahead of it. After A0, the next
free number is **AD-070**, full stop, until C0 — if it writes into it —
says otherwise.

**Not updated in A0, and recorded as an open item rather than silently
left stale.** The free-number row in
`docs/PHASE_4_STORE_EXTRACTION_GOVERNANCE_RESOLUTION_2026-07-24.md`,
which reads `AD-070+ | Free`, becomes stale the moment this block's own
amendment note lands, for the identical reason. That document is a
closed governance ruling under its own author's authority, out of scope
for this plan to edit; its correction is a separate, later act by whoever
owns it. Flagging the staleness here is what keeps it from being
rediscovered as novel — it is not a license to edit that file from this
plan.

---

## 5. R-23 — the fixture-only disclosure, and what is *not* edited

**The census lands in AD-064, dated to F-0's own commit:**

> The reproduction model Phase F does not connect to has itself **never
> been run against a real cycle**. Its stack — `reproduction_runner`,
> `reconstruction_loader`, `dataset_snapshots`, `dataset_manifest`,
> `identity_verification`, `pinned_worktree`, `network_guard` — is fully
> built and **tested against fixtures only**. **No `dataset_manifest.json`
> and no dataset snapshot for any real cycle exists in the repository at
> the commit at which this AD is accepted.** It is a mechanism with no
> production instance — the same status as `compose_transition()`, which
> H-6 discloses.

Symmetry with H-6, at no new mechanism, in one sentence, and it prevents
a later reader from treating Golden Run 001's reproduction leg as a
**reuse** when it is a **first**.

**Documentation changes decided — including three refusals.**

| Artifact | Decision |
|---|---|
| **AD-064** | **Gains the census.** Primary and sufficient home: it is where the disconnect clause already goes, and it is dated |
| `PHASE_F_ARCHITECTURE_ACCEPTANCE.md` **R-11** | **Not edited.** A review is a record of what a reviewer said at a commit. Editing a dated finding after the fact destroys the artifact's value as evidence and is the one thing a governance register must never do |
| `PHASE_F_ACCEPTANCE_CONDITIONS.md` **F-C1 §1.1 item 2** | **Not edited**, same reason. It is a dated, committed amendment |
| `reproduction_runner.py` module docstring | **Not edited.** It would be a code change in a pre-implementation pass, and it goes stale the day Golden Run 001 runs — a docstring that must be maintained to stay true is worse than one that never claimed it |
| Proposal / Resolution | **A2 checks and corrects** any statement implying a working reproduction path; the standing correction record is R-23 itself |

The overclaim was by **implication**, and the repair is forward: the AD a
later reader consults is where the correction is placed. **R-23 is
discharged by AD-064's census, and the two documents that carry the
implication stand as written and dated.**

---

## 6. Recommended commit sequence

Four tracks. **Track A0 and A1 are the only commits authorized today.**

### Track A — governance closure and F-0 (3 commits, **documentation only**)

| # | Commit | Contents | Code? |
|---|---|---|---|
| **A0** | `phase4: record Phase F readiness review and disposition plan; correct stale next-free-number claim` | Commit `docs/PHASE_F_IMPLEMENTATION_READINESS_REVIEW.md` (untracked at HEAD) and this plan. Append the dated amendment note to the reservation block: **only** the stale numbering sentence ("New ADRs therefore number from AD-068" → "AD-070"). The "independent review" sentence is **not** superseded here (deferred to A1). AD-070 / AD-071 are **not reserved** here (deferred to Track C's C0, if still needed). **Does not** touch `docs/PHASE_4_STORE_EXTRACTION_GOVERNANCE_RESOLUTION_2026-07-24.md` — its own stale `AD-070+ \| Free` row is flagged in §4 as an open item for that document's owner, not corrected here. **No AD is written; no AD is amended.** | **none** |
| **A1** | `phase4: accept AD-061…AD-067 (Phase F, F-0)` | Write all seven into `ARCHITECTURE_DECISIONS.md`. Discharge **F-C1 … F-C4** and **C-1 … C-5** in its own text. **R-16** → AD-061. **R-18** → AD-064 (non-bridge, non-claim; no composition-root placement stated). **R-21** non-claim → AD-064. **R-23** census → AD-064. Re-date every AD-063 / AD-067 census to this commit (C-4). Each of the seven carries F-C4's **leveled review-basis line**. **Also supersedes** the reservation block's *"blocked for want of an independent review…"* sentence, in leveled terms (F-C4 §4.3 item 4) — the supersession A0 does not perform, because only here has F-0 actually been performed. | **none** |
| **A2** | `docs: fold Phase F acceptance conditions into the proposal and resolution` | Proposal §3.4's amended sentence; §8's non-claims; §5.2's collision bullet (C-10); **R-18**'s §7.1 reading written down; Resolution `lifecycle.py:48` → `:46` (C-4); F-0's exit criterion and Resolution §7 item 1 restated in leveled terms; **R-23**'s implication check. **Every change is a dated amendment block** appended to the Proposal and the Resolution — the same form the reservation block and AD-069 already use — **never a rewrite of either document's existing dated text.** A2 is **not** a precondition of B1: Track B unblocks the instant A1 lands (§7 precondition 1); A2 is independent documentation cleanup that no Track B or Track C precondition references. | **none** |

### Track B — the Phase F engine (10 commits, **code**, fixture-only)

Unblocks the instant **A1** lands. Carried from the readiness review
unchanged — this plan adds nothing to Track B and removes nothing.
Real ordering constraints: **F-1 → F-2**; **F-5 → F-6 → F-7 → F-10**;
and **F-9 before F-7** (C-8 — the composition root must not land before
the test that covers it).

| # | Step | Gate |
|---|---|---|
| B1 | **F-1** measurement types | **F-C2's closed field set, pinned by test.** F-1 must not land without it |
| B2 | **F-2** context assembly | F-C3's end-to-end pin clause; `provenance_ref=None` passes through |
| B3 | **F-3** run-record serialization | Field-set test; no aggregate introducible |
| B4 | **F-4** archive writer | Five preconditions refuse, **precondition 0 first**; creates no directory; `canonical_jsonl` import asserted permitted under AD-063 (b) |
| B5 | **F-5** result and port types | Exactly-one invariant; no aggregate/phase/boolean |
| B6 | **F-6** `ResearchRunner`, fake composer | Call-order assertion; naive clock refuses at step 1 |
| B7 | **F-9** boundary AST test | **Before B8** (C-8). Scoped by name to `core/research/execution/` **and** `adapters/research/` |
| B8 | **F-7** composition root | Sole `TransitionComposer` implementation; sole non-test caller of `compose_transition()` |
| B9 | **F-8** failure-mode suite | Chain byte-identical asserted **on bytes**; F-C1's `provenance_ref=None` case |
| B10 | **F-10** fixture end-to-end traversal | Fixture cycle, temp archive root, registries populated in fixture code only. F-C3's pin lands here |

### Track C — Golden Run 001 (6 commits, mixed). Starts after **B10**

| # | Commit | Contents | Code? |
|---|---|---|---|
| **C0** | `phase4: number, draft, and accept AD-070 and AD-071 (Golden Run 001)` | If still required at this point (re-derived against Track B's actual output, not assumed from this plan): number **AD-070** and **AD-071** for the first time and write them (§3; §2.3, §2.4) into `ARCHITECTURE_DECISIONS.md` in the same commit — no prior reservation to release, since none was made at A0. Censuses dated to **this** commit. | **none** |
| **C1** | `tools: emit dataset_manifest.json for a cycle` | **R-17.** Additive, `tools/`, verified by round-trip through the **existing** reader. | **code** |
| **C2** | `experiments: golden_run_001 ETF ranking experiment + composition-root adapter` | **R-16, R-18.** Module under `experiments/` with `run()`; `Experiment` adapter at the composition root. **Both outside `core/`.** Reuses `rank_scores` / `generate_ranked_etf_report` **unchanged**; **not one line under `core/analytics/`**. | **code** |
| **C3** | `golden_run_001: scaffold cycle, freeze methodology and criteria` | **Human act.** `scaffold_project_archive()`; `methodology.md`; frozen criteria; `README.md` marking it a mechanism cycle; `decision_log.md` with the named human, the AD-066 + F-C3 gate-registration **propagation attestation**, and the **R-20 freeze contract**. **This is the freeze commit.** | none *(artifacts)* |
| **C4** | `golden_run_001: execute Golden Run 001` | **Human act**, clean tree at C3. Commits dataset snapshots, `dataset_manifest.json`, both `experiment_results/` artifacts, the ranking artifact, and the **first real `transition_records.jsonl`**. | none *(evidence)* |
| **C5** | `golden_run_001: reproduction attempt and negative controls` | `run_reproduction` → **`VERIFIED`**, plus the three negative controls (`DRIFTED`, `UNVERIFIABLE`, `REPRODUCTION_FAILED`). Commits `reproduction_record.json` — **hand-written against the frozen dataclass**, not produced by a new component. | none *(evidence)* |

### Track X — optional, parallel, off the critical path

| # | Commit | Code? |
|---|---|---|
| **X1** | `ci: run pytest on push` (C-9). Gates on **pytest only** — `check_import_boundaries.py` exits 1 at HEAD by design | **code** *(config)* |
| **X2** | `tools: ensure evidence subdirectories for reference_h4` (C-11, additive route). **Not** on the Golden Run path (R-19) and must not be conflated with it | **code** |

### Documentation-only vs. code, at a glance

| Documentation only | Introduces code |
|---|---|
| **A0, A1, A2** — the entire governance closure and F-0 | **B1 … B10** — the Phase F engine, fixture-only |
| **C0** — AD-070, AD-071 | **C1** — the manifest writer |
| **C3, C4, C5** — human acts producing archive artifacts and evidence, **not modules** | **C2** — the experiment module and its adapter |
| | **X1, X2** — optional, off the critical path |

Seven commits touch no executable file (A0, A1, A2, C0, C3, C4, C5).
**Every commit before B1 is documentation only** — which is the shape a
pre-implementation closure pass is supposed to have.

---

## 7. The exact point where Golden Run 001 becomes allowed

**Golden Run 001 is authorized at the first clean-tree moment after
commit C3 has landed — and not one commit earlier.** The run itself is
**C4**.

Stated as a conjunction, because every element is load-bearing and each
one fails differently:

| # | Precondition | Fails how, if skipped |
|---|---|---|
| 1 | **A1 landed** — AD-061 … AD-067 accepted | No authority exists for any Phase F module. The field set would be written before the decision authorizing it |
| 2 | **B1 … B10 landed and green** | No `ResearchRunner`, no `ArchiveWriter`, no composition root. Nothing to run |
| 3 | **C0 landed** — AD-070 and AD-071 accepted | The writer would exist before its schema-authority decision; the cycle would exist before the decision that a mechanism cycle may exist |
| 4 | **C1 and C2 landed** | No manifest producer; no experiment. Dataset identity would be uncapturable, since the database is not a repository artifact |
| 5 | **C3 landed** — cycle scaffolded, methodology and criteria **committed**, `README.md` and `decision_log.md` written, gate registration attested by a **named human** | `verify_freeze` has nothing to resolve against |
| 6 | **Working tree clean, and `freeze_commit_ref` = C3** | `verify_freeze` → `DRIFTED`; `compose_transition()` refuses with `BracketInvalidated`. **The run does not fail late — it is refused** |
| 7 | **`freeze_covered_paths` non-empty** | `GateContext.__post_init__` refuses before the runner is reached (AD-047 part 2); `verify_freeze` → `UNVERIFIABLE` in any case (AD-051) |

**Where it is *not* allowed, stated because both are tempting:**

- **Not at the end of Track B.** F-10 is a fixture experiment against a
  fixture cycle. Everything Golden Run 001 needs that F-10 does not is
  precisely R-16 … R-19 — and none of it is visible from inside F-1 … F-10.
- **Not after C2.** The code would all exist and run. There would be no
  freeze commit, so the transition would be **refused**, correctly, by a
  mechanism that is working as designed.

**And one constraint no sequencing discharges:** Golden Run 001 **cannot
be executed by a machine alone**. The `Authorization` is a required,
undefaulted human input; the phase → gate registration is a governance act
needing a named human and a `decision_log.md` entry (AD-066, as
strengthened by F-C3's attestation). The code can be written and reviewed
by anyone. **The run is a human act.**

---

## 8. What this plan does not do

- **It amends no accepted AD.** AD-047 … AD-060, AD-068, AD-069 are
  untouched, cited only. Not one accepted decision is weakened, narrowed,
  or reinterpreted.
- **It rewrites no historical ADR text.** The reservation block's one
  stale **status** sentence (the next-free-number claim) is superseded at
  A0 by a dated note that quotes it; the block's other stale sentence
  (the "independent review" wording) is superseded at A1, not here; its
  **decision** sentences are unchanged throughout.
- **It reserves no new AD number today, and Track C creates at most two,
  later.** AD-070 and AD-071 are not reserved by A0 — they are named here
  only as candidates, each forced (if still needed at C0) by a claim no
  accepted AD makes. R-16, R-18, R-20, R-21, R-22, R-23 require **none**
  of their own, and R-20 requires none *specifically* because accepted
  ADs already decide it.
- **A2 rewrites no historical Proposal or Resolution text either.** Its
  corrections are dated amendment blocks appended to each document,
  quoting what they supersede — the identical discipline applied to the
  reservation block above.
- **It adds no mechanism.** No guard, no validator, no detector, no
  registry, no framework. §7.1's forbidden list is carried forward
  **unrelaxed and in full**, extended by the readiness review's additions:
  nothing for `reference_h4`; no dataset framework; no CLI verb; no
  report renderer; **no second experiment**.
- **It does not discharge C-1 … C-12 or F-C1 … F-C4.** Those are
  discharged by A1's own text and by B1's and B2's exit criteria, and
  they remain open until then by their own terms.
- **A2 does not block B1.** Track B unblocks the instant A1 lands (§7
  precondition 1); A2 is documentation cleanup on the Proposal and the
  Resolution, gated on nothing in Track B or Track C, and gating nothing
  in return.
- **It is not a review**, of any level, of anything.

---

## 9. Claim-to-mechanism ledger for this plan

| Claim this document makes | Mechanism | Where it fails if unbuilt |
|---|---|---|
| No accepted AD is amended | Every finding lands either as **required content of an unwritten AD** (§0), as a **new AD**, or as an **implementation-time criterion** | If an "AD-064 gains a clause" instruction were executed as an edit, it would edit nothing — AD-064 does not exist — and the obligation would be discharged by memory |
| AD-070 and AD-071, if still needed at C0, are justified | Each would name a claim no accepted AD makes: schema-writer authority (AD-039 is precedent, not coverage) and a non-research chain record (AD-050 governs research records only) | If either were folded into AD-061 … AD-067, F-0 would accept a non-Phase-F decision under a number reserved to Phase F |
| The stale next-free-number sentence is corrected before F-0 | The reservation block's own same-commit mirroring rule, applied to **this document's own claim that AD-070 and AD-071 remain undecided** — a claim, not a reservation, since this plan reserves neither | If A1 held the fix, this plan would sit uncommitted-or-unmirrored — the exact condition that produced the "AD-061" collision the block was written to prevent |
| AD-070's censuses will be true when accepted | C0 lands **immediately before C1**; every count is dated to C0 | If C0 rode along with A1, clause 6's census would be eleven commits stale on arrival — H-7 / R-13 reproduced inside a brand-new AD |
| Golden Run 001 is refused, not broken, if run early | `verify_freeze` → `DRIFTED`; `GateContext.__post_init__` refuses an empty covered-path set; `compose_transition()` refuses the bracket | If any of the three were absent, premature execution would append a real record to a real chain — permanently |
| An ETF `Experiment` cannot live under `core/research/` | Re-derived at HEAD: `ALLOWED_DEPENDENCIES["research"] = {data, statistics, governance, validation}`, no `etf`; AD-068 decisions 2 and 3 | If read off the Proposal, the `ETF_SYMBOLS_BY_MODULE` half — which defeats the *granted* `data` edge — would be missed |
| Zero dataset manifests exist | `find . -name dataset_manifest.json` → empty, re-derived at HEAD `67b42bd` | A grep for the *type* finds seven files and suggests the capability exists |

**Facts re-derived for this plan** (not carried from the reviews), at
HEAD `67b42bd`: `ALLOWED_DEPENDENCIES["research"]` holds no `etf`;
`find . -name dataset_manifest.json` returns nothing; `ARCHITECTURE_DECISIONS.md`
contains **no occurrence of AD-070 or AD-071** and its accepted ceiling
is **AD-069** (AD-068 at `:3139`, AD-069 at `:3274`); the reservation
block's stale sentence sits at `:3107`; the only other free-number claim
in the repository is
`PHASE_4_STORE_EXTRACTION_GOVERNANCE_RESOLUTION_2026-07-24.md:743`.

**What this document does not claim:** that any AD is accepted (none is —
A1 and C0 are the acceptance acts); that Phase F's architecture is sound
(that judgment belongs to `PHASE_F_ARCHITECTURE_ACCEPTANCE.md`, at Level
2, and this plan does not re-litigate it); that R-16 … R-23 are correct
as findings (they were re-derived by their own review; this plan
re-derived only the four its rulings turn on, listed above); that Golden
Run 001 will succeed on first attempt; that any census here holds after
HEAD `67b42bd` — each is a count at that commit.
