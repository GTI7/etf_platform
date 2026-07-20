# Research Lineage Register

**Status: append-only**, same discipline as any cycle's `decision_log.md`
under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5: new entries and new
fields within an entry's arrays are appended; nothing already recorded
is edited or removed. A correction to a recorded fact is added as a new,
dated sub-entry cross-referencing the one it corrects.

**Scope.** This is a **platform-level** governance artifact, not scoped
to any single research cycle. It exists to track, across cycles, every
mechanism/target-space that has been made subject to a Phase 3
construction-attempt cap (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2
Phase 3), so that a cap cannot be reset by the simple expedient of
starting a nominally new cycle that touches the same mechanism under a
different name or framing. It lives in `docs/` alongside
`RESEARCH_GOVERNANCE_STANDARD.md` and
`REFERENCE_RESEARCH_ROADMAP_NEXT.md` because, like those, it is a
living, cross-cutting document that outlives any one cycle's
`research_archive/<cycle_name>/` package (Standard §5) — it is never
filed inside a single cycle's archive folder.

**Who writes to this file.** Any research cycle that opens a Phase 3
attempt cap on a mechanism/target space must register a `lineage_id`
here before that cycle's first *correction* attempt (as distinct from
its baseline construction) is logged. Updates thereafter — new attempts,
status changes, certifications — are made by whichever governance
document (execution plan, decision log, remediation decision) records
the underlying event, cross-referenced into the relevant entry below.

---

## Schema

Each lineage entry is a level-2 heading `## <lineage_id>` containing the
following fields. Fields are written as a definition list; array fields
(`attempts`, `certifications`) are written as sub-lists, one item per
event, each individually dated.

- **`lineage_id`** — stable identifier for the mechanism/target-function
  space this entry tracks (e.g. `gate2_score_acf_target_fn`). Chosen to
  identify the *mechanism being corrected*, not the cycle or document
  that first defined it, so a later cycle touching the same mechanism
  under a different name still maps to the same `lineage_id`.
- **`lineage_status`** — one of:
  - `active` — the cap has remaining budget and the mechanism is under
    live consideration in an open cycle.
  - `exhausted` — the cap was reached with no attempt clearing the gate
    it governs; Standard §7's FAIL terminal-failure discipline applies
    to this mechanism going forward. Does not by itself mean the owning
    cycle is archived.
  - `superseded` — a later cycle's Phase 2 proposal and Level 2 sign-off
    have certified (see `certifications`) that a new construction for
    this mechanism is genuinely distinct, opening a fresh attempt count
    under a **new** `lineage_id`. This entry is retained, unedited, as
    the historical record; it is not deleted or merged into the new
    entry.
  - `archived` — the owning cycle has reached Phase 8 (Archive) and this
    lineage's status is terminal for that cycle, regardless of whether
    the outcome was PASS, FAIL, or INCONCLUSIVE. An `archived` entry may
    still be cited by a later cycle's certification requirement; it is
    never removed.
  - A status change is itself a dated, appended fact (see `status_log`)
    — never an in-place edit of the field's prior value.
- **`governing_cap`** — the cap value in effect (number of theory-based
  correction attempts permitted) and a citation to the document/gate
  that set it.
- **`status_log`** — ordered list of `{date, status, reason, ref}` —
  every value `lineage_status` has held, in order, each with the
  document/decision-log entry that changed it. The field above always
  reflects the last entry here; the two must never disagree.
- **`attempts`** — ordered list. Each item:
  - `attempt_number`
  - `cycle_name`
  - `date`
  - `candidate_mechanism` — one line identifying the construction (not
    a re-derivation of it; the derivation lives in the cycle's own
    documents)
  - `decision_log_ref` — file + entry number recording this attempt's
    execution and outcome
  - `outcome` — PASS / FAIL / PARTIAL / ANOMALY / not-yet-executed
  - `counted_against_cap` — boolean, with a one-line reason if `false`
    (e.g. a candidate rejected at pre-registration review for being fit
    to an observed residual rather than independently motivated does
    not consume a slot, per that cycle's own governing plan)
- **`certifications`** — ordered list, populated only when a later cycle
  claims a fresh attempt count for a construction touching this
  mechanism. Each item: `date`, `new_cycle_name`, `new_lineage_id`,
  `reviewer` + independence level (Standard §4), `mechanistic_basis`
  (the stated, non-restated-scope justification for why the new
  construction is not a continuation, renaming, or reformulation of any
  attempt already in this lineage), `cross_reference` to the prior
  cycle's archived evidence. Filing a certification here is what moves
  this entry's `lineage_status` to `superseded` and opens the new
  `lineage_id` entry with its own fresh `governing_cap`.

---

## Lineage entries

### `gate2_score_acf_target_fn`

- **lineage_status:** `active`
- **governing_cap:** at most one further theory-based correction attempt
  (Attempt 3) beyond Attempt 2, per
  [`docs/POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md`](POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md)
  G0.
- **status_log:**
  - `2026-07-20` — `active` — lineage entry opened at G1 commit
    readiness review, seeded with Attempts 1–2 below — ref: this
    register's initial commit.
- **attempts:**
  1. `attempt_number: 1` — `cycle_name: positive_control_phase3` —
     `date: 2026-07-20` — `candidate_mechanism: naive Bartlett(k)
     (V2 §1.3's pre-correction claim — score inherits the raw
     forward_return/sma kernel unmodified)` —
     `decision_log_ref: research_archive/positive_control_phase3/decision_log.md
     Entry 3` — `outcome: FAIL (16 of 20 lags outside tolerance)` —
     `counted_against_cap: false — baseline construction this Plan
     responds to, not itself logged as a "correction" attempt (G0)`.
  2. `attempt_number: 2` — `cycle_name: positive_control_phase3` —
     `date: derived 2026-07-20; not yet gate-executed` —
     `candidate_mechanism: G(k), the Addendum's grade-correlation
     target (docs/POSITIVE_CONTROL_PHASE3_ANALYTICAL_CORRECTION_ADDENDUM.md
     §6)` — `decision_log_ref: not yet logged — pending Track A's A1
     diagnostic per the Controlled Execution Plan` —
     `outcome: not-yet-executed (a post-hoc arithmetic comparison
     against already-recorded data exists in the Addendum §9 but is
     explicitly not a gate execution — Decision §4)` —
     `counted_against_cap: true (pending A1's execution)`.
- **certifications:** none.

---

*This register has no other entries as of its initial commit. Future
research cycles adding a Phase 3 attempt cap on any other mechanism —
within the Positive Control program or elsewhere on the platform —
append a new `## <lineage_id>` section here following the schema above.*
