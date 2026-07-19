# Research Platform Retrospective

**Role: Institutional Quant Research Platform Architect. Scope: the
platform, not H3.** This document evaluates the research framework
itself — governance, automation, reproducibility, statistical
infrastructure, archive structure, validation workflow, developer
workflow — using the completed H3 cycle as a case study. It does not
evaluate whether H3's EVIDENCE AGAINST determination was correct, does
not revisit, modify, or re-interpret any H3 artifact, and does not
propose H4 or any future hypothesis. H3 is treated as closed, historical
input: a data point about how the platform behaves under a real,
full-lifecycle research cycle, not a subject for further review.

**Sources.** `docs/RESEARCH_GOVERNANCE_STANDARD.md`,
`docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md`,
`docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md`,
`research_archive/reference_h3/decision_log.md` (all 18 entries),
`research_archive/reference_h3/h3_final_closure.md`,
`research_archive/reference_h3/README.md`,
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`, the REFERENCE v1 and
REFERENCE v2 H1 close-outs, `docs/ARCHITECTURE_DECISIONS.md`, and the
`experiments/` validation scripts, cross-checked against `git log`
(45 commits, 2026-07-16 through 2026-07-19).

---

## 1. Platform strengths

**The outcome-data firewall held across every cycle, verified rather
than assumed.** Phases 1–5 of every cycle to date (REFERENCE v1,
REFERENCE v2 H1, H3) touched zero outcome data — no IC, p-value, or
forward return existed anywhere in the repository until Validation. This
wasn't just a rule; it was independently re-checked at each gate by grep
and by database query (`docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md` §3
confirms this three separate times for H3 alone). A platform that states
this discipline and then actually verifies it, repeatedly, by re-derived
evidence rather than self-report, is rare.

**The terminal-failure discipline was tested by a real result and held.**
H3-B came back significant in the wrong direction — the platform's own
Acceptance Criteria correctly classified this as a *stronger* negative
finding ("significant reversal") than a bare non-result, not a softer
one, and no parameter was adjusted afterward to look for a friendlier
window (`decision_log.md` Entry 17). REFERENCE v2 H1 hit the same
wrong-direction pattern earlier. Two consecutive cycles resolving to
"the data pointed the other way" and being recorded as such, without
retrying under a different label, is the single strongest piece of
evidence that the governance framework is not just aspirational.

**The archive discipline (supersession, never silent edit) was followed
consistently, including during an active incident.** The H3
backfill-gap-fill anomaly — 50 invalid rows discovered mid-cycle — was
handled by leaving every prior artifact (`gate2_independent_review_...md`,
both pre-remediation `data_inventory_*.json` files) unedited and adding
new, dated files on top. The `README.md`'s "pointer added without
editing the above" pattern, used three times as H3's status changed, is
the same discipline applied to narrative prose, not just data files.

**The platform corrected its own governance model mid-flight, using the
same cycle as the evidence.** `docs/RESEARCH_GOVERNANCE_STANDARD.md` was
authored *during* H3's pre-validation phase, explicitly built from where
H3's own process fell short (uncommitted freeze artifacts, unqualified
"independent" labeling). The `H3_GOVERNANCE_COMPLIANCE_AUDIT.md` and its
own remediation are a closed loop: gap found → generalized into a
standard → applied prospectively to the rest of the same cycle. Few
processes produce their own audit and fix real, checkable violations it
raises before the cycle that triggered it even finishes.

**Reviewer independence is classified honestly, at real cost to the
platform's own credibility claims.** The explicit refusal to call any AI
session review "independent" without the Level 2 qualifier — including
retroactively correcting three of its own documents' titles — is the
kind of admission most processes bury. `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§4 states plainly that no Level 3 review has ever occurred on this
platform. That's a weakness in absolute terms (Section 2, below) but a
strength in how the platform represents itself.

**Statistical infrastructure is genuinely reused, not re-derived per
cycle.** `build_statistic_view()`, written for REFERENCE v2 H1, was
reused unmodified for H3's own outcome separation
(`h3_final_closure.md` §7); the permutation/Holm-Bonferroni/block-bootstrap
machinery has now generalized across three economically unrelated
hypotheses (momentum/value, volatility, relative strength) without
modification. This is the platform's actual reusable asset — arguably
more valuable than any single hypothesis's result.

**The data-provenance incident response is the template the platform's
own Standard now cites for itself.** The backfill-gap-fill investigation
(discovery → forensic origin report → remediation plan weighing seven
rejected alternatives → export-then-delete execution → independent
re-verification) is thorough enough that `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§6 uses it as the worked example for anomaly handling generally. That a
mid-cycle data incident produced the platform's best-documented process,
rather than an embarrassment to paper over, says something real about
the culture in effect.

---

## 2. Platform weaknesses

**Documentation volume is now badly out of proportion to research
signal.** H3 produced two numbers (H3-A, H3-B) and one determination.
Getting there generated roughly 7,000+ lines across 19
`docs/*H3*` files plus 19 files in `research_archive/reference_h3/` —
against REFERENCE v1's 3-file archive and REFERENCE v2 H1's 3-file
archive for comparable prior cycles. Some of that growth is real
governance maturation (the Standard itself, written once, benefits every
future cycle). But a meaningful fraction is narrative re-derivation of
the same facts at multiple altitudes: the `reference_h3/README.md`
status section, `decision_log.md`'s 18 entries, and
`h3_final_closure.md` each restate H3's trajectory in overlapping prose.
A future reader has to cross-reference three documents to get the
current status of one gate.

**Freeze provenance was enforced by a later audit, not by the process in
real time.** `attempt_001_specification.md` called itself "frozen" in
its own §6 while sitting untracked in git for hours before
`docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md` caught it. The Standard's own
words — "a document's own prose claim to be frozen is not freeze
evidence" — existed *because* this happened, but nothing in the
day-to-day workflow would have caught it without a dedicated audit pass.
The same gap hit `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` (modified but
uncommitted relative to the commit hash cited as its freeze evidence).

**The decision log — the platform's own answer to fragmented history —
was itself reconstructed after the fact.** `decision_log.md` Entry 15
records the acceptance-criteria freeze commit *retroactively*, admitting
"this entry was written retroactively... this log was briefly incomplete
against [the Standard's] requirement." The tool built specifically to
prevent scattered, hard-to-reconstruct history was, for one of its own
Phase 4 elements, itself scattered and reconstructed.

**No structural recurrence guard exists for the one data-integrity
defect the platform has actually found.** The `backfill-gap-fill`
incident's root cause was never conclusively closed ("UNKNOWN, leaning
NO, not provably closed"), and three separate documents
(`H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` §3, the discrepancy analysis,
the Gate 2 post-remediation review) recommend the same fix — a
structural write-time guard tying `PriceBar` to `TradingSession` — and
none of them implement it. A recommendation repeated three times without
being acted on is a process gap, independent of how well the incident
itself was documented.

**The idealized archive layout the Standard defines was never actually
used by the cycle that motivated it.** `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§5 specifies `hypothesis.md`, `methodology.md`, `dataset_manifest.json`,
`dataset_hashes/`, `experiment_results/`, `reviewer_reports/`,
`decision_log.md`. H3's actual archive (`research_archive/reference_h3/`)
uses none of those names except `decision_log.md` — `decision_log.md`
Entry 17 discloses this directly ("does not follow the idealized...
layout... judged out of scope for this closure"). The founding case
study for the standard doesn't conform to it.

**Dataset immutability remains entirely aspirational.** The live SQLite
database is gitignored and mutable; despite being Phase 4 element #2 and
Data Provenance control #1, no `dataset_manifest.json` with content
hashes has ever existed for any cycle. Three differently-shaped
`data_inventory_*.json` files stand in for it in H3's archive, each with
its own schema, none hash-based.

**Same-day, single-operator compression is structural, not incidental.**
The entire H3 pre-validation-through-closure sequence — hypothesis
ranking, plan freeze, data extension, incident discovery and
remediation, two gate reviews, construction freeze, Gate 1/4, acceptance
criteria freeze, Phase 6 validation, and Phase 7/8 closure — ran inside
roughly seventeen hours on 2026-07-19, following two prior cycles closed
the previous evening. `H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` §1 flags
this explicitly as not equivalent in reliability to a multi-stage
process with cooling-off periods, but nothing in the workflow enforces
elapsed time, a session break, or a cross-session handoff between
phases — the disclosure exists; the control does not.

**No automated check catches the platform's own known failure modes
before a human (or a dedicated audit pass) finds them.** Every gap in
this section — uncommitted freeze artifacts, unqualified "independent"
labeling, a retroactively-built decision log, a missing structural
guard — was caught by a dedicated compliance-audit *task*, not by
routine tooling. That means detecting these gaps costs a full research
session each time, rather than a few seconds of CI.

---

## 3. Automation opportunities

Ranked by how directly each maps to a gap H3 actually hit (Section 2),
not by general appeal.

1. **Freeze-commit verifier.** A script that scans every document
   claiming to be "frozen" (grep for the word, or a required frontmatter
   field) and confirms it corresponds to a real, resolvable git commit
   hash — not merely present in the file, but matching the file's
   current content. Would have caught `attempt_001_specification.md`'s
   uncommitted state and `REFERENCE_H3_PREVALIDATION_PLAN.md`'s
   modified-but-uncommitted drift at write time, not audit time.

2. **Independence-label linter.** A single regex/CI check for the
   literal word "independent" appearing without an adjacent Level 2/3
   qualifier anywhere under `docs/` or `research_archive/`. This is the
   cheapest possible automation on this list and would have caught every
   one of the three mislabeled H3 review documents before they were
   written, not after.

3. **Decision-log entry scaffolding.** A git pre-commit or post-commit
   hook, scoped to commits touching a methodology/acceptance-criteria
   document, that appends a stub `decision_log.md` entry (date, commit
   hash, filename) automatically. Removes the exact failure mode Entry
   15 discloses — a freeze commit made without a same-session log entry.

4. **Archive-completeness checker.** A script that validates a
   `research_archive/<cycle_name>/` directory against a defined manifest
   (whatever set the platform actually commits to — see Section 4) and
   reports missing items. Converts what `H3_GOVERNANCE_COMPLIANCE_AUDIT.md`
   did manually, section by section, into a checklist that runs in
   seconds.

5. **Dataset snapshot/hash utility.** A small stdlib-only function
   (consistent with `docs/ARCHITECTURE_DECISIONS.md` AD-005's
   no-frameworks constraint) that computes a content hash over an
   ordered dump of a table/date-range and writes it to a
   `dataset_hashes/` file at defined checkpoints. This is the one item
   on this list that requires new code, not just a script — see Section
   5, item 1.

6. **Two-directional coverage check as standing tooling.** The
   remediation script's verification logic (missing + surplus, per-ETF,
   per-date) is currently a one-off. Promoting it to a callable
   `maintenance/verify_price_coverage.py` (or a `tests/test_db_invariants.py`
   addition) that any future ingestion or remediation step can invoke
   turns a forensic-investigation capability into routine tooling.

7. **Report generation from JSON evidence.** Every validation script
   already emits a machine-readable JSON artifact
   (`phase6_economic_validation_2026-07-19.json`, etc.); the markdown
   reports that summarize them are currently written by hand, which is
   exactly the kind of transcription step that introduces the risk the
   platform otherwise works hard to eliminate. A template renderer that
   populates the standard report tables directly from the JSON would
   remove that risk without touching the statistical methodology itself.

---

## 4. Standardization opportunities

The instruction here is documentation shape, not research methodology —
none of the below changes what a hypothesis test measures or how it's
scored.

- **Decision log template.** The append-only entry shape used
  consistently across all 18 H3 entries (Date / Decision / Evidence
  references / Governance status / Reviewer level / Known limitations)
  is well-designed and already validated by repeated real use. It should
  become a literal starter file created at Phase 1, not reconstructed at
  Phase 8 the way `docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md` had to note it
  was missing entirely partway through H3.

- **Gate/final-determination record template.** `gate1_final_determination.md`,
  `gate4_final_determination.md`, and `h3_final_closure.md` independently
  converged on the same shape: identifier, frozen commit(s), evidence
  references, determination, governance status, disclosed limitations,
  terminal status. Extracting this into a fill-in template removes the
  need to reinvent structure each time and makes gaps (a missing
  "reviewer level" line, say) visible by omission rather than by audit.

- **Acceptance-criteria freeze template.** The eight-element checklist
  in `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3 (universe, dataset
  version, evaluation period, benchmark, metrics, scoring rules,
  parameters, acceptance criteria) is already the de facto structure of
  `docs/H3_ACCEPTANCE_CRITERIA.md`. A literal template with those eight
  headers, each requiring an explicit entry or an explicit "UNRESOLVED"
  (as H3's own §7 correctly did for three items rather than inventing
  numbers), would make an incomplete freeze visually obvious before
  Phase 5 begins rather than discoverable only by careful reading.

- **Research close-out template.** REFERENCE v1, REFERENCE v2 H1, and
  H3's close-out documents independently arrived at the same shape
  (hypothesis, experiments performed, results table, audit conclusions,
  lessons learned, entry bar for the next cycle) across three separate
  authoring passes. Three independent reinventions of the same structure
  is itself the signal that it should be a template, not a pattern
  re-derived from memory each time.

- **Compliance-audit checklist.** `docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md`'s
  own structure (Lifecycle Audit table, Freeze Audit, Review Independence
  Audit, Evidence Package Audit, Data Provenance Audit, Governance Gaps,
  Final Determination) is a reusable audit shape independent of H3's
  substance. Standardizing it as a template — and, per Section 3 item 4,
  automating the parts of it that don't require judgment — would let a
  future cycle run the same audit at lower cost each time.

---

## 5. Technical debt

Repository-level items, not documentation items — things that require
code or schema changes to close, and that benefit every future
hypothesis cycle equally.

1. **No dataset-hashing infrastructure exists anywhere in the
   codebase.** This is the most consequential single gap: every
   Phase 4/6 freeze claims a "dataset version" but none is
   content-addressed. Closing it needs a real utility (a small module
   under `core/shared/` or a new `experiments/` helper, consistent with
   the platform's stdlib-only constraint per AD-005), not another
   document.

2. **No structural guard against the one data-integrity defect already
   found.** A migration adding a trigger or constraint tying `PriceBar`
   inserts to a matching `TradingSession` row (extending the pattern
   AD-009 already established for insert-only immutability) would close
   a gap that's been recommended in writing three times and acted on
   zero times.

3. **The two-directional coverage check lives inside a one-off
   remediation script** (`maintenance/remediate_h3_invalid_pricebar_rows.py`)
   instead of reusable tooling — debt in the sense that the exact
   capability that caught a real defect once is not available to catch
   the same class of defect again without rewriting it.

4. **`research_archive/` has no shared scaffold.** Three cycles, three
   different directory shapes (REFERENCE v1: 3 flat files; REFERENCE v2
   H1: 3 flat files; H3: 19 files, gate-review subfolder absent, its own
   ad hoc naming). Nothing generates the directory structure a cycle
   should start with, so each cycle's archive shape is whatever its
   author happened to invent that day.

5. **A known gitignore-hygiene gap was fixed reactively twice, not
   once.** `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` §2 records that
   REFERENCE v2 H1's generated report wasn't gitignored at
   implementation time — the same class of issue REFERENCE v1 had
   already surfaced. A shared `experiments/` output-path convention
   (even just a documented default directory pattern new scripts inherit
   from) would prevent a third recurrence rather than relying on each
   new script's author to remember.

6. **Governance framework documents and per-cycle research documents
   are not separated on disk.** `docs/RESEARCH_GOVERNANCE_STANDARD.md`
   (permanent, applies to every cycle) sits in the same flat `docs/`
   directory as `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`
   (H3-specific, historical). A `docs/governance/` split would make "what
   rule applies to every cycle" trivially distinguishable from "what one
   cycle happened to produce," which currently requires reading each
   filename's prefix.

---

## 6. Roadmap

Prioritized by ratio of effort to how directly each item closes a gap
this retrospective actually found — not a generic maturity checklist.

**Tier 1 — cheap, closes known gaps, no new infrastructure (do before
any future hypothesis cycle opens).**
- Independence-label linter (Section 3.2).
- Freeze-commit verifier (Section 3.1).
- Decision-log and gate-determination templates (Section 4), including
  scaffolding a cycle's `decision_log.md` at Phase 1 instead of Phase 8.
- `docs/governance/` split (Section 5.6) — pure file move, zero risk.

**Tier 2 — moderate effort, converts one-off capability into standing
tooling.**
- Promote the two-directional coverage check into reusable tooling
  (Section 3.6 / Section 5.3).
- Archive-completeness checker script (Section 3.4), run against
  whichever manifest shape the platform actually commits to.
- Research close-out and acceptance-criteria templates (Section 4).
- A documented `experiments/` output-path convention closing the
  gitignore-hygiene recurrence (Section 5.5).

**Tier 3 — real infrastructure investment, needed before the next
cycle's Phase 4 freeze can honestly claim "dataset version" the way the
Standard already requires.**
- Dataset-hashing utility and `dataset_hashes/` convention (Section 5.1).
- Structural write-time guard for the `PriceBar`/`TradingSession`
  invariant (Section 5.2).
- Report-generation-from-JSON to remove hand-transcription risk
  (Section 3.7).

**Tier 4 — structural/organizational, not solvable by code or
documents.**
- Level 3 (organizationally independent) review capacity. The Standard
  already states this doesn't exist and can't be manufactured by tooling
  — it requires a distinct, differently-incentivized reviewing party.
  Not actionable within this repository; recorded here only so the
  roadmap doesn't imply it's a near-term engineering task.
- A minimum-elapsed-time or cross-session-gap control between lifecycle
  phases, addressing the same-day compression risk (Section 2). This is
  a process policy decision for whoever operates the platform, not a
  script — noted as open, not solved.

**Sequencing note.** Tier 1 items are all things H3 already proved are
needed — each maps to a specific, named incident in this document, not
a hypothetical. They should land before Tier 2 or 3 work, and certainly
before any future hypothesis's Phase 1 opens, since every one of them
makes the *next* cycle's evidence trail more trustworthy at effectively
zero marginal research cost.
