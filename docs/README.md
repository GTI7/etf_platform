# `docs/` — Governance and Research Documentation Index

**Last updated:** 2026-07-21
**Purpose of this file:** to make this directory navigable by someone who
has never spoken to its authors.

Before this index existed, `docs/` held 46 documents with no entry point
and no status markers. Reading order was inferable only from filename
conventions and prior context — which meant the lifecycle could not be
reconstructed by an external auditor. That gap is what this file closes.

---

## Start here — the four-document path

An auditor who reads nothing else should read these, in this order:

1. **[RESEARCH_GOVERNANCE_STANDARD.md](RESEARCH_GOVERNANCE_STANDARD.md)** —
   the platform's constitution. Defines the 8-phase lifecycle (§2), what
   "frozen" means and how it is proved (§3), the three reviewer
   independence levels (§4), the evidence-package structure every research
   cycle must produce (§5), and the PASS/FAIL/INCONCLUSIVE framework (§7).
   **Nothing else in this directory makes sense without §4 and §5.**
2. **[RESEARCH_PLATFORM_RETROSPECTIVE.md](RESEARCH_PLATFORM_RETROSPECTIVE.md)** —
   what was actually built and what went wrong, written against the
   platform rather than for it.
3. **[PHASE_4_ARB_DETERMINATION_2026-07-21.md](PHASE_4_ARB_DETERMINATION_2026-07-21.md)** —
   the current binding determination on the reproducibility subsystem.
   Its §10 ("Certification question") is the most direct statement of what
   would prevent an independent reproducibility audit from certifying this
   platform today.
4. **[§ Known open governance defects](#known-open-governance-defects)**
   below — what is still wrong, stated in this index rather than left for
   the auditor to discover.

**The single most important fact for an external reader** is in the ARB
determination §10, item 1, and it is unchanged as of this index's date:
**no archive in this repository can currently be reproduced.** No cycle
contains a `dataset_manifest.json` or a `reproduction_record.json`. The
reproducibility subsystem has never been executed against a real research
cycle. Every governance document below should be read in that light.

---

## How to read a document's status

Every document in this directory is one of:

| Status | Meaning |
|---|---|
| **Living** | Updated over time; the current version is the only version. Append-only where marked. |
| **Design of record** | The controlling specification for a subsystem. Read as specification, never as a description of the code. |
| **Superseded** | Replaced by a named successor. Retained unedited as historical record. Carries a banner. **Never implement from a superseded document.** |
| **Historical** | A record of a completed or abandoned cycle. Accurate as of its date; not maintained. |
| **Binding determination** | Adjudicates prior review events. Changes what may be implemented, not what the code does. |
| **Review record** | A reviewer's observations at a point in time. Not an approval. |

**Uncommitted documents are not evidence.** Standard §3: *"A commit hash is
freeze evidence; a document's own claim to be 'frozen' is not."* This rule
applies to every file listed below, including this one.

---

## Lifecycle map — Standard §2 phases to documents

| Phase | Artifacts in this repository |
|---|---|
| **1 — Hypothesis** | Cycle specifications: [REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md](REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md), `research_archive/reference_h3/attempt_001_specification.md` |
| **2 — Research Proposal** | [POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL.md](POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL.md) → [_V2](POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md) |
| **3 — Pre-validation** | [REFERENCE_H3_PREVALIDATION_PLAN.md](REFERENCE_H3_PREVALIDATION_PLAN.md), [H3_ACCEPTANCE_CRITERIA.md](H3_ACCEPTANCE_CRITERIA.md), the H3 gate reports, [POSITIVE_CONTROL_PHASE3_*](#positive-control-phase-3-open) |
| **4 — Methodology Freeze** | [The Phase 4 governance set](#phase-4-governance-subsystem-current-work). **Not open** — see the Phase 3 blockers in the Positive Control remediation decision §9. |
| **5 — Implementation** | `core/governance/*` (**uncommitted**), [V0_6_0_DESIGN_WRITE_PIPELINE_COMPOSITION.md](V0_6_0_DESIGN_WRITE_PIPELINE_COMPOSITION.md), [STEP_8_REPORTING_DESIGN.md](STEP_8_REPORTING_DESIGN.md) |
| **6 — Validation** | [H3_PHASE6_ECONOMIC_VALIDATION_REPORT.md](H3_PHASE6_ECONOMIC_VALIDATION_REPORT.md), [H3_ECONOMIC_EVIDENCE_VALIDATION_REPORT.md](H3_ECONOMIC_EVIDENCE_VALIDATION_REPORT.md) |
| **7 — Decision** | [POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md](POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md), `research_archive/reference_h3/gate4_final_determination.md` |
| **8 — Archive** | `research_archive/` — see [§ Research cycles](#research-cycles-and-their-archives). **No cycle currently satisfies §5's full evidence-package structure** ([H3_GOVERNANCE_COMPLIANCE_AUDIT.md](H3_GOVERNANCE_COMPLIANCE_AUDIT.md) row 8). |

---

## Platform governance — living documents

These outlive any single research cycle and are never filed inside a
cycle's archive folder.

| Document | Status | What it is |
|---|---|---|
| [RESEARCH_GOVERNANCE_STANDARD.md](RESEARCH_GOVERNANCE_STANDARD.md) | Living | The constitution. Lifecycle, freeze, independence levels, evidence package, decision framework, exceptions, standing corrective rules. |
| [RESEARCH_LINEAGE_REGISTER.md](RESEARCH_LINEAGE_REGISTER.md) | Living, **append-only** | Cross-cycle register of mechanisms under a Phase 3 construction-attempt cap, so a cap cannot be reset by renaming a cycle. |
| [RESEARCH_ARCHIVE_MANIFEST.md](RESEARCH_ARCHIVE_MANIFEST.md) | Living | Schema v1 for `archive_manifest.json`. Explains why the three legacy archives will never receive one retroactively. |
| [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) | Living, append-only | The AD register (AD-001…). The traceability spine for engineering decisions. |
| [PLATFORM_ARCHITECTURE_V1.md](PLATFORM_ARCHITECTURE_V1.md) | Design of record | Target platform architecture. §4.4 specifies the not-yet-built `ArchiveVerifier`. |
| [STATISTICS_DOMAIN.md](STATISTICS_DOMAIN.md) | Design of record | Statistical primitives and their boundaries. |
| [REFERENCE_RESEARCH_ROADMAP_NEXT.md](REFERENCE_RESEARCH_ROADMAP_NEXT.md) | Living | Forward research agenda and standing entry requirements. |
| [RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md](RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md) | Living | Phased migration toward the platform architecture. |
| [RESEARCH_PLATFORM_RETROSPECTIVE.md](RESEARCH_PLATFORM_RETROSPECTIVE.md) | Historical | Adversarial retrospective on the platform's own failures. |
| [templates/](templates/) | Living | Four templates: acceptance criteria, decision log, gate determination, research closeout. |

---

## Phase 4 governance subsystem — current work

The reproducibility and evidence-preservation layer. **Read in this order** —
the chain is base proposal → amendment → amendment → review → review →
determination → roadmap.

| # | Document | Status |
|---|---|---|
| 1 | [PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md](PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md) | **Base proposal**, amended twice, retained. §2.3 remains load-bearing for the ARB's A1(b) ruling. |
| 2 | [PHASE_4_ARCHITECTURE_AMENDMENT_V1.md](PHASE_4_ARCHITECTURE_AMENDMENT_V1.md) | ⛔ **SUPERSEDED** by v1.1. Received *C — RETURN FOR REDESIGN*. Do not implement from it. |
| 3 | [PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md](PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md) | ✅ **CURRENT DESIGN OF RECORD.** Partially implemented; implementation uncommitted and non-conformant. |
| 4 | [reviewer_reports/RR-001](reviewer_reports/2026-07-21_RR-001_phase4_governance_architecture_review.md) | **Review record**, Level 2. Adversarial architecture review; 20 findings in 4 bands, plus 7 subsystems named sound. |
| 5 | [reviewer_reports/RR-002](reviewer_reports/2026-07-21_RR-002_phase4_governance_peer_review.md) | **Review record**, Level 2. Peer review *of RR-001*; 5 claims independently re-executed. |
| 6 | [PHASE_4_ARB_DETERMINATION_2026-07-21.md](PHASE_4_ARB_DETERMINATION_2026-07-21.md) | **Binding determination.** Adjudicates RR-001 against RR-002. §6 is the MUST list; §10 is the certification assessment. |
| 7 | [PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md](PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md) | **Chartered, open.** Split out of A1(b) because naive file hashing can never match across runs (`generated_at`). |
| 8 | [PHASE_4_IMPLEMENTATION_ROADMAP.md](PHASE_4_IMPLEMENTATION_ROADMAP.md) | Sequencing proposal. Seven independent PRs; states the honest limit of what `VERIFIED` will mean after all of them. |
| 9 | [PHASE_4_GOVERNANCE_DOCS_FREEZE_RECORD.md](PHASE_4_GOVERNANCE_DOCS_FREEZE_RECORD.md) | **Freeze record** for documents 1–8. Supplies the commit hash that makes the freeze evidence rather than a claim. |

> **Freeze status.** Documents 1–8 above are frozen at commit `91acb2c`,
> tagged **`phase4-governance-docs-frozen-v1`**.
>
> **This is not the Phase 4 Methodology Freeze.** Standard §2's Phase 4
> gate is **not open** — the Positive Control cycle has Gate 2 and Gate 3
> both at FAIL. The tag freezes *documentation about the Phase 4 governance
> subsystem*, not a research methodology, and it is not an approval of
> anything. See the freeze record's "What this freeze is NOT" section
> before citing the tag.

**Reviewer reports.** `reviewer_reports/` holds one file per review event,
each with its own date, reviewer identity, and independence-level
declaration (Standard §5). It sits at platform level, not inside a cycle
archive, because these reviews examined shared infrastructure rather than
any one research cycle — the same rule
[RESEARCH_LINEAGE_REGISTER.md](RESEARCH_LINEAGE_REGISTER.md) states for
itself. Cycle-scoped reviews go in
`research_archive/<cycle>/reviewer_reports/` instead.

**These two reports discharge the provenance gap** the ARB determination
raised in its own header (*"Neither review exists as a repository
artifact… Both reviews should be written to `reviewer_reports/` before
this determination is acted on"*). That paragraph is now satisfied. It is
**not** edited in the determination, per supersession discipline — this
index records the discharge instead.

---

## Research cycles and their archives

| Cycle | Status | Docs | Archive |
|---|---|---|---|
| **reference_v1** | Closed | [REFERENCE_V1_RESEARCH_CLOSEOUT.md](REFERENCE_V1_RESEARCH_CLOSEOUT.md) | `research_archive/reference_v1/` — legacy shape, 3 flat files |
| **reference_v2_h1** | Closed | [Specification](REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md), [GO checkpoint](REFERENCE_V2_H1_GO_CHECKPOINT_REPORT.md), [Closeout](REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md) | `research_archive/reference_v2_h1/` — legacy shape |
| **reference_h3** | Closed | [Prevalidation plan](REFERENCE_H3_PREVALIDATION_PLAN.md), [Acceptance criteria](H3_ACCEPTANCE_CRITERIA.md), [Data sufficiency](REFERENCE_H3_DATA_SUFFICIENCY_REPORT.md), [Gate 2 discrepancy](REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md), [Gate 3 rationale](REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md), [DB remediation plan](REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md), [Backfill origin](REFERENCE_H3_BACKFILL_GAP_FILL_ORIGIN_REPORT.md), [Remediation record](REFERENCE_H3_REMEDIATION_RECORD.md), [Closeout](REFERENCE_H3_RESEARCH_CLOSEOUT.md), plus 6 `H3_*` gate/audit reports | `research_archive/reference_h3/` — 19 files incl. `FREEZE_RECORD.md` |
| **positive_control_phase3** | **OPEN** | See below | `research_archive/positive_control_phase3/` — v1 scaffold |

### Positive Control Phase 3 (open)

[Proposal](POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL.md) →
[Proposal V2](POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md) →
[Analytical Correction Addendum](POSITIVE_CONTROL_PHASE3_ANALYTICAL_CORRECTION_ADDENDUM.md) →
[Remediation Decision](POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md) →
[Controlled Execution Plan](POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md).

**Gate 2 and Gate 3 are both FAIL.** The Addendum is accepted as
diagnostic research only — explicitly **not** as a completed Gate 2
correction, and not as grounds to change any operative gate behaviour.
**Phase 4 (Methodology Freeze) is not open.** An auditor should not read
the Phase 4 governance work above as implying otherwise: that work is
infrastructure being built ahead of the gate, not evidence the gate has
passed.

---

## Engineering documents

[BASELINE_STATUS.md](BASELINE_STATUS.md) ·
[RELEASE_NOTES_v0.6.0.md](RELEASE_NOTES_v0.6.0.md) ·
[V0_6_0_DESIGN_WRITE_PIPELINE_COMPOSITION.md](V0_6_0_DESIGN_WRITE_PIPELINE_COMPOSITION.md) ·
[REPORTING_ARCHITECTURE_PROPOSAL.md](REPORTING_ARCHITECTURE_PROPOSAL.md) ·
[STEP_8_REPORTING_DESIGN.md](STEP_8_REPORTING_DESIGN.md)

---

## Known open governance defects

Recorded here rather than left for an auditor to find. None is closed by
the commit that introduced this index.

1. **No reproducible archive exists.** No cycle contains
   `dataset_manifest.json` or `reproduction_record.json`; the
   reproducibility subsystem has never run against a real cycle. ARB §10
   item 1 calls this *"disqualifying on its own."* Remedy: roadmap PR1–PR5.
2. **The Phase 4 implementation is uncommitted.** 10 of 13
   `core/governance/*.py` modules and 9 of 11 `tests/test_governance_*.py`
   files are untracked. RR-001 and RR-002 therefore reviewed a **working
   tree, not a commit** — both records say so explicitly. Their findings
   are anchored to a state that git cannot reproduce.
3. **Standard §5 is self-contradictory on supersession.** It requires a
   correction to be *"cross-referenced from the file it supersedes"* while
   requiring that file be *"retained, unedited."* Both cannot hold. The
   supersession banners added on 2026-07-21 were applied to files that had
   **never been committed**, so no history was rewritten — but the rule
   needs an explicit carve-out permitting a supersession banner on an
   otherwise-unedited document. **Unresolved.**
4. **The "Level-3" independence-tier collision.** Both Phase 4 review
   sessions were titled "Level-3," and
   [PHASE_4_ARB_DETERMINATION_2026-07-21.md](PHASE_4_ARB_DETERMINATION_2026-07-21.md)
   §1 inherited the phrase into **committed** history. Standard §4 records
   that **no Level 3 review has ever been performed on this platform** and
   forbids representing session separation as organizational independence.
   RR-001 and RR-002 are filed at their correct tier — **Level 2** — with
   the collision flagged in each. The committed determination is **not
   edited**; correcting it requires a new dated document, per §5. Tracked
   as RR-002-R7. **Unresolved.**
5. **No cycle satisfies Standard §5's evidence package.** Every archive is
   missing at least one of the seven required items
   ([H3_GOVERNANCE_COMPLIANCE_AUDIT.md](H3_GOVERNANCE_COMPLIANCE_AUDIT.md)
   row 8). The three legacy archives are exempt by design; the v1 cycle is
   incomplete.
6. **No Level 3 review capacity exists.** Standard §4. Every PASS, FAIL and
   ACCEPTED verdict on this platform — including those in the reviewer
   reports and the ARB determination — is **Level 2 at most**. An external
   auditor should weight all of it accordingly.
7. **The headline pipeline cannot be reproduced offline.**
   `daily_etf_universe_update.py` fetches through `YahooFinanceProvider`
   and trips `OfflineViolationError` under the guard regardless of every
   other fix. A reproduction target must be designated before roadmap PR2.
   Tracked as RR-002-R6.

---

## Conventions

- **Every document is dated**, in its filename or its own content
  (Standard §5).
- **Corrections are new dated files, never silent edits.** The superseded
  file is retained with a banner pointing forward.
- **`decision_log.md` in each cycle archive is literally append-only.**
- **"Independent" is never used unqualified.** Every review states its
  level (1, 2, or 3) per Standard §4.
- **A document's claim about itself is not evidence.** Freeze is proved by
  a commit hash, conformance by a passing test, reproduction by a
  reproduction record.
