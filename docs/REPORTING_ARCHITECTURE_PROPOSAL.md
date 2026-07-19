# Reporting Domain Architecture Proposal

**Status: proposal, not a decision record.** Nothing in the repository
changes as a result of this document, and no code is proposed here —
only the shape of the next increment (`docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md`
Step 8) ahead of designing `ReportBuilder`/`Renderer` themselves. Written
as an architecture checkpoint following Step 7's completion (`core/validation/`,
within its ADR-approved scope — AD-040 through AD-044) and the closure of
`DecisionLogger` (AD-045).

**Sources.** Direct inspection of `core/statistics/significance.py`,
`core/validation/gate_result.py`, `core/governance/freeze_verifier.py`,
`research_archive/reference_h3/`'s actual file listing,
`core/analytics/ranked_report.py`, plus
`docs/PLATFORM_ARCHITECTURE_V1.md` §4.5 (Reporting Domain, fixed target
design), `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Step 8, and
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` §3 item 7 (the gap this domain
exists to close). Every claim below is grounded in a specific file, not
inferred from naming or intent.

---

## 1. Reporting purpose

**Primary user:** the single research operator, acting in different
reviewer-level capacities (Level 1/2 per `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§4). Every artifact reviewed — `decision_log.md`, `gate1_final_determination.md`,
`h3_final_closure.md` — is authored and consumed by the same person
across all three completed cycles. No document anywhere in this
repository describes a second user role; this is the evidenced scope,
not an assumption.

**Decisions it should support:** whether a `GateResult` is trustworthy
enough to act on without re-deriving it from raw JSON (status + freeze
provenance + evidence refs, legible at a glance), and whether a cycle's
evidence is complete enough to advance a phase. It does **not** make
that determination itself — `PLATFORM_ARCHITECTURE_V1.md` §4.5: *"never
makes a determination — a report is a rendering, not a source of
truth."* Its concrete justification is Retrospective §3 item 7: today's
`phase6_economic_validation_2026-07-19.json` and today's hand-written
`H3_PHASE6_ECONOMIC_VALIDATION_REPORT.md` are the same numbers authored
twice — Reporting's job is to make the JSON the only authored copy.

## 2. Reporting layers

Two real layers, one declined.

- **Machine/API output (JSON).** Nearly free today — `GateResult` is
  already a frozen, serializable dataclass. A JSON `Renderer` is close
  to `dataclasses.asdict()` plus a stable key order. Build this first:
  it validates `ReportBuilder`'s shape against zero formatting risk.
- **Researcher report (Markdown).** What Step 8 actually names: "minimal
  `ReportBuilder` + a single Markdown `Renderer`." Replaces the
  *templated* portions of documents like `gate1_final_determination.md`
  (frozen commit, evidence refs, PASS/FAIL/AMBIGUOUS, reviewer/date) —
  not the narrative portions (economic rationale prose, "known
  limitations" free text), which AD-038's reasoning already establishes
  must stay human-authored: a generated paragraph would "look like
  recorded evidence... while containing nothing" of the judgment that
  content actually requires.
- **"Investor-facing report" — not proposed here.** See Section 5.

## 3. Required inputs — and one gap this surfaces

- **`GateResult`** (exists, frozen, tested): status, `summary`,
  `evidence_refs`, `DecisionMetadata`. The only structured
  Research/Validation output that exists today.
- **Raw statistics** (`mean_ic`, `bootstrap_ci`, `holm_bonferroni`,
  `empirical_p_value` in `core/statistics/significance.py`): **not
  currently reachable as structured data.** `GateResult` carries only a
  formatted string (`summary`) and opaque `evidence_refs` — e.g.
  `signal_independence.py` builds
  `f"measured_overlap={measured_overlap} {comparator} frozen_threshold={frozen_threshold}..."`
  as prose, not fields. A Markdown renderer can reprint that string
  as-is; anything wanting to reformat the numbers (a table, different
  rounding) would have to parse it back out of prose. This is a real
  open question for the `ReportBuilder` design, not something to
  silently assume away — to be resolved explicitly when that increment
  is scoped, not before.
- **Freeze/governance artifacts** (`VerificationResult` from
  `freeze_verifier.verify_freeze`): also not preserved structurally past
  `GateResult` — a failed verification collapses into an `AMBIGUOUS`
  status plus a summary string; the specific drifted path or resolved
  commit hash isn't carried forward. Same category of gap as above.
- **`evidence_refs`**: deliberately opaque per AD-042 ("references to
  immutable evidence locations... never validates what a reference
  points to"). A Markdown renderer displays them as citations; it must
  not resolve, dereference, or validate them — that crosses into
  `ArchiveVerifier`/`ReproducibilityChecker` territory, neither of which
  exists and neither of which is this domain's job.
- **Ranked/scored ETF output** (`core/analytics/ranked_report.py`'s
  `RankedETFReportEntry`/`ETFAnalysisReport`): reviewed per the request
  behind this proposal — this is explicitly **product logic, outside
  the six domains**, per the Migration Plan's own Current State Mapping.
  A different kind of report (ETF scoring) than a Research-domain
  `GateResult`. Nothing in Step 8's definition includes it; recommend it
  stay excluded — pulling it in would make Reporting depend on
  Data/product logic for a use case no cycle has ever needed a
  governance report for.
- **Research archive structure**: `research_archive/reference_h3/` is
  19 ad hoc files with no shared scaffold (confirmed by direct listing).
  This is why Step 8 explicitly does not regenerate any historical
  report — Reporting applies only going forward, to new `GateResult`s.

## 4. Output formats

- **JSON** — build first, lowest risk, closest to what already exists.
- **Markdown** — the one Step 8 commits to; the actual replacement for
  hand-authored `*_determination.md` files.
- **PDF** — named as a `Renderer.format` literal in §4.5's sketch but
  explicitly "later," with no reader or distribution need identified
  anywhere in any document. Not now.
- **Dashboard/API** — not proposed anywhere in this repository's
  architecture. The Migration Plan's opening paragraph explicitly
  excludes "any SaaS, multi-tenant, or UI feature," and §4.5 states
  Reporting is "a true leaf; no domain's correctness can ever depend on
  Reporting having run" — designed to produce files an operator reads,
  not a served endpoint. A JSON file on disk is not the same thing as an
  API; treating them as the same layer would smuggle in the excluded
  scope. Not now.

## 5. Differentiation from existing ETF screeners — declined

This question is not answered as design here, for two independent
reasons grounded in the repository rather than in style preference:

- **It contradicts every scoping document reviewed.** The Migration
  Plan states outright it "does not propose any SaaS, multi-tenant, or
  UI feature." §4.5 designs Reporting as an internal, leaf-node
  rendering of governance evidence for the one operator who already
  holds all the context — not a competitive product surface.
  Differentiation against ETF.com/Morningstar-style screeners is a
  product-positioning question; no ADR, no architecture-doc section, and
  no retrospective finding has ever framed this platform that way.
- **The evidence doesn't support it substantively.** All three
  completed research cycles closed `ARCHIVE` / `ARCHIVE` /
  `EVIDENCE AGAINST` — none validated an actionable ranking signal. A
  report designed to read as differentiated, screener-competitive output
  would present unvalidated (or negatively-validated) research as
  decision-useful ranking content to an audience outside the person who
  understands its caveats.

A genuine future need for external-facing output would be a separate
decision requiring its own justification (an actual second audience, a
validated signal to report on) — not something to design speculatively
alongside Step 8.

## 6. Explicitly not built yet

- `ReportRegistry` (multi-format dispatch) — one renderer today
  (Markdown, possibly JSON); same "no registry before a second
  consumer" discipline as AD-040's `GateRunner`.
- PDF, HTML, dashboard, API renderers.
- Any "investor-facing" tier or format.
- Retroactive rendering of `reference_v1`/`reference_v2_h1`/`reference_h3`
  archives — the Migration Plan is explicit that Step 8 applies only
  forward.
- Rendering `core.analytics.ranked_report` output through this domain.
- Any expansion of `GateResult`'s schema done speculatively — if the
  Markdown renderer genuinely needs structured numeric fields (Section
  3's gap), that is a narrow, real need to address when `ReportBuilder`
  is actually designed, not something to pre-solve here.
- `DecisionLogEntry` rendering — not a type that exists (AD-045);
  `ReportBuilder` builds from `GateResult` only, matching what has
  already been decided.
