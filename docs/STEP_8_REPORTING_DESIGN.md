# Step 8 Reporting v0.1 — Implementation Design Specification

**Status:** design specification, ready for implementation approval. No
code is introduced by this document. It translates
`docs/ARCHITECTURE_DECISIONS.md` AD-046 (input boundary: `GateResult`,
not `project_id`/`report_type`) and
`docs/REPORTING_ARCHITECTURE_PROPOSAL.md` (purpose, layers, declined
scope) into the exact module layout, types, and contracts Step 8
implements against. Where this document's account of `GateResult`
disagrees with an earlier summary, `core/validation/gate_result.py` (read
directly for this review) is authoritative.

**Scope discipline.** This is the smallest architecture that satisfies
AD-046 and the Migration Plan's Step 8 line item ("minimal `ReportBuilder`
+ a single Markdown renderer," JSON built first as the lower-risk shape
check). Every module, type, and test below is justified against that
line, not against what a general-purpose reporting library would
eventually want.

---

## 1. Module/package layout

```
core/reporting/
    __init__.py          # existing; docstring updated at implementation time
    report_model.py       # ReportModel (new)
    report_builder.py     # build_report() (new)
    json_renderer.py       # render_json() (new)
    markdown_renderer.py   # render_markdown() (new)
```

No subpackages (`renderers/`, `builders/`). Justification for each file:

- **`report_model.py`** — the one type both renderers depend on. Isolated
  in its own module so `json_renderer.py` and `markdown_renderer.py` can
  import it without also importing `report_builder.py` (and, transitively,
  `core.validation`) — see §6.
- **`report_builder.py`** — the single seam that touches
  `core.validation.gate_result.GateResult`. Deliberately the *only* file
  in this package permitted that import (§6).
- **`json_renderer.py` / `markdown_renderer.py`** — one file per format,
  flat at package level. Two files does not justify a `renderers/`
  subpackage; that structure would be paid for before there is a second
  file *per format* to organize, which AD-046 explicitly rules out
  (no `ReportRegistry`, no dispatch). Compare `core/validation/gates/`,
  which is a real subpackage — but only because it holds multiple
  interchangeable implementations of the *same* role (comparing a
  statistic against a frozen criterion) that a future `Gate` Protocol
  could dispatch over. Two fixed, non-interchangeable output formats are
  not that shape.

**No `Renderer` Protocol/ABC.** `core/validation/gates/__init__.py` is the
controlling precedent here, not an aspiration: it already has *two*
concrete gate implementations today and still declines to formalize the
`Gate` Protocol PLATFORM_ARCHITECTURE_V1.md §4.2 sketches, deferring it to
AD-044 until `GateRunner`/`ValidationRegistry` give it an actual
consumer. Reporting v0.1 has the identical shape — two concrete renderers,
no dispatcher — so it follows the identical discipline: `render_json` and
`render_markdown` are plain functions with a matching signature
(`ReportModel -> str`) by convention, not by an enforced interface. A
`Renderer` Protocol is the first thing to add if and when a second
consumer (a registry, a third format) needs to hold renderers
polymorphically — not before.

**Naming note.** AD-046 and the migration plan write "`ReportBuilder`"
and "`Renderer`" as the conceptual role names from
`docs/PLATFORM_ARCHITECTURE_V1.md` §4.5, not a mandated class shape.
Precedent for resolving a role name to a plain function when there is no
state to hold: `FreezeVerifier` (§4.4's sketch) resolved to the plain
function `verify_freeze`, not a class. `ReportBuilder` has no
configuration, no injected dependency, and no state across calls — it is
`GateResult -> ReportModel`, nothing else — so it resolves to
`build_report()`, a plain function, for the same reason.

## 2. `ReportModel`

**Responsibility.** The one type both renderers render from. Exists so
neither renderer imports `core.validation.gate_result` directly (§6) —
without it, two renderers would each independently couple to Validation's
schema, and a future Validation-side change to `GateResult` would have to
be reasoned about against two call sites instead of one (`report_builder.py`).
`ReportModel` is Reporting's own type; it is not a Validation type wearing
a different name.

**Ownership.** `core/reporting/report_model.py`. Reporting owns this
type outright — it is the one piece of schema this domain is allowed to
design, precisely because it holds no information `GateResult` didn't
already supply.

**Fields** (frozen, `slots=True`, mirroring `GateResult`/`DecisionMetadata`/
`VerificationResult`'s existing convention):

```python
@dataclass(frozen=True, slots=True)
class ReportModel:
    gate_name: str
    status: str            # GateStatus.value, verbatim — "pass" | "fail" | "ambiguous"
    summary: str            # GateResult.summary, verbatim, unparsed
    evidence_refs: tuple[str, ...]  # verbatim, unresolved
    reviewer: str
    review_level: str
    decided_at: str
```

Two structural choices, both flagged explicitly so they aren't mistaken
for interpretation:

- `status` is stored as `GateStatus.value` (a plain string), not the enum
  itself. This is a type-boundary choice, not a semantic one — `.value`
  is definitional (`GateStatus.PASS.value == "pass"`), not derived from
  the status by any judgment. Keeping `ReportModel` enum-free also means
  neither renderer needs to import `core.validation.gate_result.GateStatus`.
- `DecisionMetadata`'s three fields (`reviewer`, `review_level`,
  `decided_at`) are flattened to the top level rather than nested as a
  sub-object. This changes field *depth*, not field *values* — every
  string is copied unchanged. Flattening is chosen because both renderers
  want scalar field access (a JSON `dict` key, a Markdown template slot)
  and nesting would just move that flattening into two call sites instead
  of one.

No field exists in `ReportModel` that isn't a direct, unmodified copy of
a `GateResult`/`DecisionMetadata` field. If a future renderer needs
something `GateResult` doesn't carry (raw statistics, `VerificationResult`
detail — both flagged as open gaps in
`docs/REPORTING_ARCHITECTURE_PROPOSAL.md` §3), that is a `GateResult`
schema change for Validation to decide, not a field for `ReportModel` to
grow independently.

## 3. `ReportBuilder`

**Responsibility.** One pure function:

```python
def build_report(gate_result: GateResult) -> ReportModel: ...
```

Constructs a `ReportModel` whose every field is a direct copy of the
corresponding `GateResult`/`DecisionMetadata` field (with the two
structural changes in §2 — enum-to-`.value`, decision-flattening — and
no others).

**Transformation allowed:**
- Reading `GateResult`'s own fields and `GateResult.decision`'s fields.
- `status.value` (enum member → its string value).
- Flattening `decision.{reviewer,review_level,decided_at}` to top-level
  `ReportModel` fields.

**Transformation forbidden:**
- Any change to `summary`'s text — no truncation, reformatting,
  re-casing, or re-punctuating.
- Any parsing of `summary` to extract, reformat, or validate numbers
  embedded in it.
- Any reordering, deduplication, filtering, or resolution of
  `evidence_refs`.
- Deriving, overriding, or re-checking `status` — `GateResult.status` is
  taken as given; `build_report` never inspects `summary` (or anything
  else) to decide whether the given status "looks right."
- Any default-filling, validation, or exception-raising beyond what
  constructing a `dataclass` already does. `gate_result` arrives already
  validated by Validation; `build_report` does not re-validate it — doing
  so would mean Reporting silently taking on a second opinion about
  Validation's own output.
- Any file, network, or `evidence_refs` I/O. `build_report` never opens,
  reads, or checks existence of anything `evidence_refs` names.

## 4. JSON renderer

```python
def render_json(model: ReportModel) -> str: ...
```

**Exact responsibility.** Serialize a `ReportModel` to a JSON string and
nothing else. Implementation is `json.dumps(dataclasses.asdict(model), ...)`
plus a fixed key order — the "closest to `dataclasses.asdict()`" shape
`docs/REPORTING_ARCHITECTURE_PROPOSAL.md` §2 specifies as the lowest-risk
validation of `ReportBuilder`'s output shape.

**Serialization rules:**
- Output key set is exactly `ReportModel`'s seven field names — no added,
  renamed, or computed keys (no `"generated_at"`, no `"report_id"`, no
  derived summary fields).
- Key order is stable and deterministic across calls (`sort_keys=True` or
  an explicit key list) — two calls on equal input produce byte-identical
  output, so output can be diffed and regression-tested directly.
- `evidence_refs` serializes as a JSON array of strings, preserving input
  order.
- No file is written by this function. It returns a string; if or where
  that string is persisted to disk is a caller decision, out of this
  function's scope (§8).
- Takes only a `ReportModel`. Never imports `core.validation`,
  `core.governance`, `core.statistics`, `core.analytics`, or
  `core.research` (§6).

## 5. Markdown renderer

```python
def render_markdown(model: ReportModel) -> str: ...
```

**Exact responsibility.** Format a `ReportModel`'s fields into a
Markdown document — the "templated portions of documents like
`gate1_final_determination.md`" `docs/REPORTING_ARCHITECTURE_PROPOSAL.md`
§2 names: frozen commit / evidence refs / status / reviewer / date. It
does not attempt the narrative portions (economic rationale prose, "known
limitations" free text) those hand-written documents also contain — per
AD-038's reasoning cited in the proposal, a generated paragraph "would
look like recorded evidence... while containing nothing" of the human
judgment that content requires. Step 8 v0.1 replaces only what is already
mechanical.

**Presentation rules:**
- `status` is displayed as given (`"pass"`/`"fail"`/`"ambiguous"`, or a
  fixed 1:1 label mapping such as `pass → "PASS"`) — a case/casing change
  is presentation; inventing a *fourth* label, or collapsing the
  three-way status into a boolean-flavored "✅/❌" that drops the
  `ambiguous` case, is not.
- `summary` is reprinted verbatim as running text or inside a single
  block — never re-tokenized, re-sentenced, or partially quoted.
- `evidence_refs` are listed as a literal list of strings (e.g. one per
  bullet) — displayed as citations only.
- `reviewer`, `review_level`, `decided_at` are printed as given, in a
  fixed template layout (e.g. a small attribution line or table) — no
  computed "days since decision," no re-formatting of `decided_at` into a
  different date representation.

**Forbidden interpretation logic** (the concrete failure modes this
renderer must not grow into):
- Parsing `summary` to pull out a number and re-render it in a table,
  a chart, or a different rounding.
- Turning `status` into non-given language — "APPROVED FOR PRODUCTION,"
  "strong pass," a checkmark that implies more confidence than the
  status itself carries.
- Dereferencing an `evidence_refs` entry to read, embed, or summarize its
  contents (that is `ArchiveVerifier`/`ReproducibilityChecker` territory,
  neither of which exists — AD-042).
- Adding narrative sentences not present in any input field ("this result
  suggests...", "the operator should consider...") — that is exactly the
  hand-authored judgment AD-038 requires stay human-written.
- Any file write. Same rule as §4: returns a string only.

## 6. Input/output contracts

| Function | Signature | Purity | Allowed imports from this repo |
|---|---|---|---|
| `build_report` | `GateResult -> ReportModel` | Pure, no I/O | `core.validation.gate_result` (`GateResult`, `GateStatus`, `DecisionMetadata`), `core.reporting.report_model` |
| `render_json` | `ReportModel -> str` | Pure, no I/O | `core.reporting.report_model` only |
| `render_markdown` | `ReportModel -> str` | Pure, no I/O | `core.reporting.report_model` only |

Mechanical consequence: `json_renderer.py` and `markdown_renderer.py`
contain zero references to `core.validation`, `core.governance`,
`core.statistics`, `core.analytics`, or `core.research` — and zero
references to `pathlib`, `open`, `os`, or any HTTP/network client.
`report_builder.py` is the only file in the package permitted to import
`core.validation`, and permitted nothing beyond that one import from
outside `core.reporting`.

**Where files get written.** Out of scope for these three functions by
design — they are pure string producers, matching the "renders; never
validates" and "displays; never interprets" rules by construction (a
function with no I/O access cannot resolve `evidence_refs` or write a
decision log as a side effect). Persisting `render_markdown`'s or
`render_json`'s output to disk is a caller concern — e.g. a thin script
under `experiments/` today, a future CLI later — never logic inside
`core/reporting/`.

**Exceptions.** None of the three functions define new exception types
or catch anything. `build_report(gate_result)` raises only what
constructing a `dataclass` naturally raises on a malformed input (a
`TypeError` from a caller passing the wrong type) — there is no
`try`/`except`, no validation branch, and no recovery path, because a
malformed `GateResult` is a Validation-domain bug, not a condition
Reporting is responsible for handling gracefully.

## 7. Test strategy

**Unit tests** (`tests/test_report_model.py`, `tests/test_report_builder.py`,
`tests/test_json_renderer.py`, `tests/test_markdown_renderer.py`),
mirroring `tests/test_gate_result.py`'s existing style:

- `ReportModel` is frozen (`FrozenInstanceError` on mutation), same
  pattern as `test_decision_metadata_is_frozen`/`test_gate_result_is_frozen`.
- `build_report`: for a `GateResult` fixture covering all three
  `GateStatus` values, assert every `ReportModel` field equals the source
  field verbatim (`model.summary == gate_result.summary`, not just
  "truthy" or "non-empty") — this is the test that would catch an
  accidental reformat or truncation creeping into `build_report`.
  Explicitly assert `model.evidence_refs == gate_result.evidence_refs`
  (tuple equality, order preserved) and
  `model.status == gate_result.status.value` for each enum member.
- `render_json`: output round-trips through `json.loads` back to the
  original field values; two calls on an equal `ReportModel` produce
  byte-identical strings (stable key order); the parsed key set equals
  exactly `{"gate_name","status","summary","evidence_refs","reviewer","review_level","decided_at"}` —
  a test that fails the moment a computed key is added.
- `render_markdown`: output contains the exact `summary` string as a
  substring (verbatim-reprint check); contains every `evidence_refs`
  entry as a substring; does not contain any of a fixed denylist of
  words a compliant renderer should never introduce on its own
  (`"approved"`, `"recommend"`, `"should"`) — a cheap regression guard
  against narrative language creeping into the template.

**Boundary tests** (`tests/test_reporting_import_boundary.py`) — the
direct enforcement of §6 and the adversarial risks in §8, so a future
edit that adds a convenience import doesn't silently widen the domain's
dependencies:
- Parse (via `ast`, not `importlib`, to avoid needing the imports to
  actually succeed) the source of `json_renderer.py` and
  `markdown_renderer.py` and assert no `import`/`from` statement
  references `core.validation`, `core.governance`, `core.statistics`,
  `core.analytics`, `core.research`, `pathlib`, or `os`.
- Same check on `report_builder.py`, asserting its only same-repo import
  outside `core.reporting` is `core.validation.gate_result`.

**Regression expectations.** All four unit-test files plus the boundary
test run in the existing `pytest` suite alongside `test_gate_result.py`;
no new test infrastructure, fixtures directory, or golden-file mechanism
is introduced — `GateResult`/`ReportModel` instances are cheap to
construct inline, same as `tests/test_gate_result.py`'s `_decision()`
helper. No test depends on `research_archive/` content (Step 8 is
forward-only, per §8 and the Migration Plan).

## 8. Explicit non-goals

Carried forward from AD-046 and `docs/REPORTING_ARCHITECTURE_PROPOSAL.md`
§6, plus two added by this design pass (`Renderer` Protocol, format
dispatch):

- `ReportRegistry` / any format-keyed dispatch table — one caller, two
  known functions, called directly; no lookup layer.
- A `Renderer` Protocol/ABC — no second consumer needs renderers held
  polymorphically yet (§1).
- PDF, HTML, dashboard, or API renderers/endpoints.
- Any "investor-facing" report tier or differentiated-product framing.
- Retroactive rendering of `research_archive/reference_v1`,
  `reference_v2_h1`, or `reference_h3` — Step 8 applies only to
  `GateResult`s produced going forward.
- Rendering `core.analytics.ranked_report`'s `RankedETFReportEntry`/
  `ETFAnalysisReport` — product-logic output outside the six domains;
  reusing this pipeline for it is a separate, separately-justified
  decision, not a byproduct of this one existing.
- Any speculative expansion of `GateResult`'s schema (a `project_id`
  field, structured statistics fields) — those are Validation-domain
  decisions to make against a real second need, not something Reporting
  requests preemptively.
- `DecisionLogEntry` rendering — the type does not exist (AD-045 closed
  without it); `build_report` takes `GateResult` only.
- File/disk persistence of rendered output from inside `core/reporting/`
  — renderers return strings; writing them out is a caller's job (§6).
- A `project_id → GateResult` lookup of any kind, anywhere in this
  package — the exact gap AD-046 documents as *why* the narrower
  signature was chosen; building it here would silently reopen the
  question AD-046 closed.

## 9. Adversarial review — where Reporting could absorb another domain's responsibility

| Domain | Absorption risk | What it would look like | Guard specified above |
|---|---|---|---|
| **Validation** | Re-deriving or second-guessing a gate outcome | A renderer greps `summary` for words like "meets"/"exceeds" and prints its own "✅ APPROVED" independent of `status` | §3 forbids `build_report` inspecting `summary` to influence `status`; §5 forbids renderers inventing status language beyond a fixed 1:1 label mapping; boundary test denylist (§7) catches introduced narrative/approval words |
| **Governance** | Resolving or verifying evidence | A Markdown renderer opens the file an `evidence_refs` entry names to "show a preview," or calls `verify_freeze` to annotate freshness | §4/§5 list dereferencing evidence as explicitly forbidden; §6's import contract makes `core.governance` and filesystem access unimportable from either renderer; boundary test enforces this mechanically |
| **Statistics** | Reformatting numbers | A future "nicer table" renderer parses `measured_overlap=0.42` out of `summary` text to round or re-tabulate it | §3 and §5 both explicitly forbid parsing `summary`; `core.statistics` is on the forbidden-import list in §6/§7 |
| **Research** | Becoming the Research↔Validation join point | `build_report` grows a `project_id` parameter and looks up that project's `GateResult`s itself | This is the exact scenario AD-046 exists to foreclose; §1/§3 fix `build_report`'s only parameter as one already-resolved `GateResult`; `core.research` is on the forbidden-import list |
| **Analytics** | Becoming a general "any report" renderer | `render_markdown`/`render_json` get reused (or generalized) to also render `core.analytics.ranked_report` output, since "we already have a Markdown renderer" | §6 types both renderers against `core.reporting.report_model.ReportModel` only; `core.analytics` is on the forbidden-import list; §8 states reuse for ranked-report output is a separate decision |
| **Governance (DecisionLogger, AD-045)** | Writing, not just reading, decision data | Since `reviewer`/`review_level`/`decided_at` are already on hand, a renderer "helpfully" also appends a decision-log entry as a side effect of rendering | §4/§5/§6 fix all three functions as pure, I/O-free; only `DecisionLogger` writes decision-log entries, and Reporting never calls it |

None of these are hypothetical in the sense of requiring new
functionality to trigger — each is a small, locally-reasonable-looking
addition to a single function (`build_report`, `render_json`, or
`render_markdown`) that this design's per-function transformation rules
(§3–§5), import contract (§6), and boundary tests (§7) are built to
reject or catch in review.
