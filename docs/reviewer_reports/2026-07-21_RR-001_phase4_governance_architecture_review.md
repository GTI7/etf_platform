# RR-2026-07-21-001 — Phase 4 Governance Subsystem, Adversarial Architecture Review

**Filed:** 2026-07-21
**Review event window:** 2026-07-21T16:49:31Z – 2026-07-21T16:56:23Z (UTC)
**Reviewer identity:** AI review session titled `Phase 4 governance architecture review`, session id `local_16f5a96c-e28e-4304-b9da-63b648ee72f1`, model `claude-opus-4-8`, reasoning effort `high`, operator-directed, working directory `D:\Claude`.
**Independence level:** **Level 2** (`RESEARCH_GOVERNANCE_STANDARD.md` §4) — procedurally independent (fresh session, no conversational continuity with the authoring of `core/governance/*`), **not organizationally independent**.
**Review posture:** adversarial, hostile-by-instruction.
**Status of this document:** *review record only.* It is not an approval, not a gate determination, and not a decision. No code was written, executed against production data, or modified to produce it. It has no governance effect until committed (§7 below).

---

## Filing note — provenance and one label correction

> **This section is written by the filing archivist on 2026-07-21, not by the
> reviewer.** It is separated from the review record proper so that no
> statement below is mistaken for a reviewer observation.

**Provenance of this record.** The review event occurred in a session
transcript and was not written to the repository at the time it was
performed. This document transcribes that session's review output into
the archive on the same calendar day (2026-07-21). The source transcript
remains available at the session id given above and is the authority
against which this transcription can be checked. **No finding, severity,
recommendation, or conclusion has been added, removed, softened, or
re-sequenced in transcription.**

Two labelling conventions are used below and are load-bearing:

- **`[TRANSCRIBED]`** — content originating in the review event itself.
- **`[ARCHIVIST]`** — structure or context added at filing time to satisfy
  the report format required of a `reviewer_reports/` artifact. Archivist
  content never states a finding and never changes a severity.

**Label correction — the review self-titled as "Level-3".** The review
event's own heading reads *"Hostile Level-3 Review — Phase 4 Governance"*.
Filed unchanged, that title would assert an independence tier this
platform does not possess. `RESEARCH_GOVERNANCE_STANDARD.md` §4 states
that **no Level 3 review has ever been performed on this platform**, that
AI session separation "is not, and must never be represented as,
organizational independence," and that "no document may describe a Level 2
review using the unqualified word 'independent'."

This record is therefore filed at **Level 2**, which is what the review
event actually was. The reviewer's own words are preserved verbatim in the
findings below; only the *filing* independence declaration is set to its
correct tier. The archivist reads the original "Level-3" as a designation
of review *depth/aggressiveness* as instructed by the operator, colliding
with §4's *independence tier* namespace. **The collision is a real
governance defect in the naming convention, not merely a typo**, and it is
raised as an implementation requirement in §6 (RR-001-R9) because a
downstream document has already inherited it.

---

## 1. Review scope

`[TRANSCRIBED]` The reviewer was directed to conduct an adversarial
architecture review of the Phase 4 governance subsystem: the
`core/governance/*` modules implementing reproducibility controls, the
persistence layer they depend on, the governing Phase 4 amendment
document, and the governance test suite.

`[ARCHIVIST]` Explicitly **out of scope** for this review event, as
evidenced by the material examined and not examined:

- The statistical/quantitative content of any research cycle (H3,
  reference_v1, reference_v2_h1, positive_control_phase3). No gate result,
  significance figure, or effect size was re-derived.
- The correctness of `core/analytics/*` scoring, indicator, or ranking
  logic. It is discussed only where the reproduction path fails to execute
  the pinned copy of it (finding A2).
- Any judgement on whether Phase 4 may open. That is a gate determination
  and is not a reviewer function.

## 2. Artifacts reviewed

`[TRANSCRIBED]` The reviewer states having read every governance module,
the persistence layer they depend on, the Phase 4 amendment document, and
all eight governance test files. Artifacts cited by file and line in the
review output:

| Artifact | Cited locations |
|---|---|
| `core/governance/reproduction_runner.py` | :11-15, :24-32, :47-68, :74-85, :95-103, :106-121, :116-120, :124-149, :132-142, :163-176, :181-183, :197-201, :211, :212-215, :223-232, :285, :292-295, :304, :312 |
| `core/governance/reproduction_record.py` | :23, :29-38 |
| `core/governance/reconstruction_loader.py` | :117, :123-135, :151, :174-179, :187, :189-196, :217, :249-267, :262, :263-265 |
| `core/governance/dataset_manifest.py` | :70-78, :100-102 |
| `core/governance/dataset_snapshots.py` | :79, :86, :135, :139, :204, :208 |
| `core/governance/identity_verification.py` | :53-56, :56 |
| `core/governance/canonical_jsonl.py` | :36-51 |
| `core/governance/network_guard.py` | :20-24, :42-64 |
| `core/governance/pinned_worktree.py` | :46-52, :52, :59-60 |
| `core/governance/calendar_definitions.py` | :38 |
| `core/governance/freeze_verifier.py` | :103, :103-120 |
| `core/market_data/persistence/migrations.py` | :21, :39 |
| `core/market_data/persistence/database.py` | :22 |
| `tools/archive_manifest.py` | :64-69 |
| `experiments/daily_etf_universe_update.py` | :43, :45-66, :217-221 |
| `tests/test_governance_*.py` (8 files) | incl. `test_governance_reproduction_runner.py:36`, :335-336, :373-374 |
| `docs/PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md` | :473, :517 |
| `docs/PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md` | :728 |
| `research_archive/` | directory-level search |

## 3. Assumptions

`[ARCHIVIST-EXTRACTED]` The review event did not contain a section headed
"assumptions." The following are the assumptions the review demonstrably
operated under, extracted from its reasoning at filing time. They are
recorded because a later reader must be able to test them; they are **not**
reviewer statements.

1. **The subsystem is pre-first-use.** Severity is argued at the point of
   use. Finding C7 establishes that no archive can currently be
   reproduced, and the review nonetheless scores A1–A3 as live Critical
   defects. `[ARCHIVIST]` This tension is internal to the review record and
   is preserved here unresolved; it is not the archivist's to adjudicate.
2. **The reproduction target is `experiments/daily_etf_universe_update.py`.**
   The review reasons about the runner exec'ing "the universe module."
3. **The reader of a `VERIFIED` verdict is an external auditor** with no
   developer context, who will treat the verdict at face value.
4. **The adversary model for A3/C1 is an actor with write access to the
   cycle directory** but without the ability to rewrite git history.
5. **Static reading plus targeted interpreter checks are sufficient** to
   establish the findings. The subsystem was not run end-to-end against a
   real archive during this review — because, per C7, it cannot be.
6. **`CALENDAR_DEFINITIONS` will eventually hold more than one entry** (C2
   is a latent, not live, defect and is scored as such).

## 4. Findings

`[TRANSCRIBED]` Twenty findings across four severity bands, plus a band of
subsystems named architecturally sound. Severities are the reviewer's own
as recorded at the review event.

### Band A — Critical architecture flaws

**A1 — `VERIFIED` never verifies the output; the reproduction contract is unwired.**
`reproduction_record.py:29-38`, `reproduction_runner.py:211`, `:230-232`.
`ReproductionRecord` is a dead dataclass — repo-wide it is never
constructed, never parsed, never compared. A repo-wide grep for
`result_report_hash|ReproductionRecord|dataset_content_hashes` returns only
the definition itself and two test fixtures. The runner reads exactly one
field from `reproduction_record.json` — `commit_hash` (`:292`) — and ignores
`dataset_content_hashes` and `result_report_hash` entirely. At `:211` the
seam where the output would arrive is present and discarded:
`run_experiment(module, scratch_db_path)` — return value dropped.
Consequently `ReproductionStatus.VERIFIED = "inputs matched, output matched"`
(`reproduction_record.py:23`) actually means: *the experiment's `run()` did
not raise, and four tables it never touched are unchanged.*
`REPRODUCTION_FAILED` — documented as "all inputs matched; output did not" —
is unreachable for its stated cause; it fires only on an exception or the
offline guard. **Failure scenario:** a scoring bug is introduced in
`core/analytics` between freeze and audit; reproduction runs; the experiment
completes, writes a materially different significance report, changes no
frozen-identity row, and the runner prints `verified`, exit 0. A published
result is certified as reproduced by machinery that never looked at it.
**Tests detect it?** No — `test_full_reproduction_verifies` asserts
`VERIFIED` with `"dataset_content_hashes": {}` in the fixture; the tests
encode the gap as correct behaviour.

**A2 — Pinned-commit execution is an illusion; everything except the top-level file comes from HEAD.**
`reproduction_runner.py:106-121`. By the time `exec_module` runs, the process
has already imported `core.governance.*` and
`core.market_data.persistence.database` **from HEAD**. `core` is therefore in
`sys.modules` and its `__path__` points at HEAD's `core/`. When the pinned
experiment executes `from core.analytics.write_pipeline import ...`, Python
resolves `core` from the cache and walks HEAD's `__path__`. The worktree's
`core/` is never loaded; `sys.path.insert` cannot override an
already-imported package. The reviewer confirmed the real experiment
scripts do import `core.*`. The module docstring's central claim — that the
experiment script comes from the pinned commit's own worktree — is true
only of the ~200-line entrypoint. The same defect affects
`_load_expected_tickers_from_worktree` (`:124-149`). **Failure scenario:** an
auditor reproduces `reference_h3` against commit `abc123`;
`core/analytics/domain/calculations.py` has since changed its z-score
normalization; the audit reports `verified`; the published number is now
attributed to code that never produced it. **Tests detect it?** No, and
`test_experiment_code_runs_from_the_pinned_commit_not_head` actively
conceals it: its fixture experiment imports only `sqlite3`. *The one test
named for this invariant is the one test that cannot exercise it.*

**A3 — Dataset artifacts are not pinned by `commit_hash`; the manifest is self-attesting.**
`reproduction_runner.py:285`, `:304`, `reconstruction_loader.py:117`,
`tools/archive_manifest.py:64-69`. The docstring asserts dataset snapshots
come from the pinned worktree and that "`commit_hash` pins code and data
together." The implementation does the opposite: `cycle_dir` is
`args.cycle`, a **live working-tree path**, and `dataset_manifest_path` is
resolved from it. Nothing routes dataset artifacts through `worktree_path`.
The remaining integrity chain is a closed loop: snapshot bytes are checked
against the manifest's `content_hash`; the manifest is checked against
**nothing**; `archive_manifest.json` contains no file hashes at all; and
`reproduction_record.json.dataset_content_hashes`, which exists precisely to
anchor the loop, is unread (A1). **Failure scenario:** editing
`pricebar.jsonl` to drop three bars that break a significance threshold and
recomputing one `content_hash` string — a two-line edit — passes every check
in `preflight_validate` and yields `VERIFIED`. **Tests detect it?** No —
every fixture builds manifest and snapshots together in `tmp_path`, so the
self-attestation is never probed.

### Band B — Serious reproducibility weaknesses

**B1 — TOCTOU: the bytes hashed are not the bytes loaded.** Each snapshot
file is opened from disk four separate times (hash, row-count, preflight,
load). The verification result is never carried forward — only the `Path`.
Between hash and load the file may change; nothing re-verifies post-load.

**B2 — `commit_hash` is never validated as a commit hash.**
`record_raw.get("commit_hash")` is checked only for truthiness, then handed
to `git worktree add --detach`, which accepts any commit-ish: `main`,
`HEAD`, `v2^`, a tag, an abbreviation. A record containing
`"commit_hash": "main"` resolves to a moving target while reporting
`verified`. `freeze_verifier._resolve_commit` already performs the correct
resolution and can be reused.

**B3 — Exception masking makes the four-state outcome unreliable as evidence.**
Two bare `except Exception` backstops collapse categorically different
failures into verdicts that assign blame. The reconstruction backstop maps
loader bugs, `ScratchDatabaseExistsError`, `MemoryError`, disk-full
`OSError` and `PermissionError` to `DRIFTED` ("an input doesn't match its
claimed hash"). The execution backstop maps `ModuleNotFoundError`,
`sqlite3.OperationalError` and `ReproductionRunnerError` to
`REPRODUCTION_FAILED` — *the single most damaging verdict the system can
emit, assigned to an environment problem.* The backstops undo the
separation the four-state enum exists to create, in the direction that
produces false accusations rather than false clears.

**B4 — A raw exception escapes `run_reproduction` entirely.**
`_load_expected_tickers_from_worktree` catches only `OSError` around
`exec_module`; the call site catches only `ReproductionRunnerError`. Any
`ImportError`, `SyntaxError` or `ValueError` raised during the real module's
import chain propagates out of `run_reproduction` as a traceback,
contradicting the docstring's guarantee that no raw exception escapes.

**B5 — No audit record is produced or persisted.** `ReproductionOutcome`
carries `status` plus a `str(exc)` detail; the CLI prints one line to
stdout; nothing is written. There is no record of when the attempt ran, the
resolved commit SHA, the observed manifest hashes, the Python/SQLite
versions, the platform, or the migrations applied. *For a subsystem whose
output is meant to be audit evidence, the evidence is a terminal line that
vanishes.* `detail=str(exc)` is additionally lossy — `str()` of an
argument-less exception is `""`, and no traceback is retained.

### Band C — Governance weaknesses

| # | Finding | Location |
|---|---|---|
| **C1** | `snapshot_path` is unvalidated and can escape the cycle directory. Verified: `Path('cycle') / '/etc/passwd'` → `Path('/etc/passwd')` (base discarded); `Path('cycle') / '../../../secret.jsonl'` retains the traversal. `_parse_entry` validates the `sha256:` prefix but performs no validation on `snapshot_path` and no type checks. Breaks the invariant that an archive is self-contained. | `reconstruction_loader.py:117`, `dataset_manifest.py:70-78` |
| **C2** | Calendar preflight validates against a set the loader does not load. Preflight validates `calendar_id` against **all** of `CALENDAR_DEFINITIONS`; the loader inserts exactly **one**. Invisible today (one entry); on the day a second literal is added, a snapshot passes preflight then dies at load with a raw `sqlite3.IntegrityError` — which the B3 backstop reports as `DRIFTED`. Degrades the exact error-quality guarantee the module is built around. | `reconstruction_loader.py:174-179`, `:189-196`, `:262` |
| **C3** | Frozen-identity hash has an unescaped `\|` delimiter. Verified collision: rows `[('A\|B','C')]` and `[('A','B\|C')]` produce an identical sha256. `name` and `source` are free-text columns, so `\|` is reachable. The check exists precisely to catch same-row-count in-place edits. | `identity_verification.py:56` |
| **C4** | `read_canonical_jsonl` does not enforce the canonical form it documents. The docstring lists five rules; the reader checks two. Unenforced: alphabetical key order, "one JSON *object* per line", duplicate keys. Verified: `json.loads('{"a":1,"a":2}')` → `{'a': 2}` silently. A trailing `\n\n` yields a `""` element whose `JSONDecodeError` is not a `ReconstructionValidationError`. | `canonical_jsonl.py:36-51` |
| **C5** | Failed reconstruction leaves a scratch DB that poisons retries with a wrong verdict. `run_migrations` commits internally, so a later failure rolls back rows but the file survives. A retry with the same `--scratch-db` raises `ScratchDatabaseExistsError`, hits the B3 backstop, and prints `drifted` — *a `DRIFTED` verdict on corrected data.* | `reconstruction_loader.py:249-267` |
| **C6** | The offline guard does not cover subprocesses. The module honestly names its narrow gaps but not the wide one: it patches this interpreter's `socket` module only. The reproduction path itself spawns subprocesses, so this is not hypothetical. Presented as a "process-level offline guarantee"; it is an in-interpreter guarantee. | `network_guard.py:42-64` |
| **C7** | **No archive in the repository can be reproduced by this machinery.** A search for `dataset_manifest.json` / `reproduction_record.json` across `research_archive/` returns nothing. All four archives lack both files; the subsystem has never executed against a real cycle; every test fixture is synthetic. Consistent with the hardening proposal listing this as outstanding work — *a known gap rather than a hidden one* — but it means A1–A3 have never had a chance to surface operationally. | `research_archive/` |

### Band D — Minor robustness

| # | Finding |
|---|---|
| **D1** | `mkdtemp()` → `rmtree()` → `git worktree add` opens a window on a shared `/tmp` where a symlink can be placed at the freed path. |
| **D2** | `git worktree remove` return code discarded; failed removals silently accumulate worktrees and stale `.git/worktrees` entries. |
| **D3** | `sys.path.remove` removes the first occurrence only; insert/remove is not re-entrant. Modules pulled in by the exec stay in `sys.modules` and contaminate a second `run_reproduction` call with a different commit. |
| **D4** | `ReproductionOutcome` is mutable while every peer result type is `@dataclass(frozen=True, slots=True)`. |
| **D5** | `SELECT *` makes the digest depend on physical column order; `row.keys()` requires `conn.row_factory = sqlite3.Row`. |

### Band E — Subsystems named architecturally sound

`[TRANSCRIBED]` The reviewer explicitly named the following as correct
"rather than pad the findings list": the `identity_verification` scope
boundary (called "the hardest thing in the subsystem to get right"), the
`network_guard` depth counter, `dataset_manifest` coverage validation
(including closing the reviewer's own initial hypothesis that duplicate
entries could silently collapse), load ordering and the fail-fast preflight
discipline, the `canonical_jsonl` write path, `freeze_verifier`, and
`calendar_definitions`.

## 5. Blocking issues

`[TRANSCRIBED]` The review's own priority ordering:

1. **A1** — wire `ReproductionRecord`. *Until then no `VERIFIED` result is
   citable, and the manifest forgery in A3 has no counterweight.*
2. **A2** — out-of-process execution, or a hard refusal when `core.*` is
   already imported. *A silent HEAD substitution is worse than a crash.*
3. **A3 / B2** — bind the record to the commit; validate the commit is a
   commit.
4. **B1, B3, B4** — one read per file; narrow the backstops; stop the
   escaping exception.
5. **C and D as capacity allows.** *C2 and C3 are the two that will bite
   without warning* — C2 the day a second calendar is added, C3 whenever a
   free-text field contains a pipe.

`[ARCHIVIST]` Recorded as stated. Note for the downstream reader: this
priority list and finding C7 are in tension (see §3 assumption 1). The
review asserts a `VERIFIED` result today is not citable while its own C7
establishes that no such result can currently be produced. **This record
does not resolve that tension**; it is the reviewer's position as stated at
the review event.

## 6. Required remediation

`[TRANSCRIBED]` The fixes proposed by the reviewer, stated as the
reviewer stated them. `[ARCHIVIST]` These are *reviewer recommendations*,
not committee decisions and not adopted requirements. Nothing in this
section has been ratified by any decision-making body as of this filing.

| ID | Finding | Reviewer-proposed remediation |
|---|---|---|
| RR-001-R1 | A1 | Parse `reproduction_record.json` into `ReproductionRecord`; (a) assert each manifest entry's `content_hash` equals `record.dataset_content_hashes[source_table]` → `DRIFTED` on mismatch; (b) hash the experiment's output report and compare to `result_report_hash` → `REPRODUCTION_FAILED` on mismatch. Reviewer asserts: *"No new architecture; both seams already exist."* |
| RR-001-R2 | A2 | Execute the pinned entrypoint out-of-process via `subprocess.run([sys.executable, ...], cwd=worktree_path, env={PYTHONPATH: worktree_path})`. Reviewer asserts this "stays in-architecture." Fallback if in-process execution is retained: assert no `core.*`/`adapters.*` key is present in `sys.modules` before `exec_module` and raise → `UNVERIFIABLE`. |
| RR-001-R3 | A3 | Add the record and manifest paths to `freeze_verifier`'s covered-paths list for the cycle; alternatively resolve `cycle_dir` inside `worktree_path` so the git object store is the anchor. |
| RR-001-R4 | B1 | Read each snapshot's bytes once, hash that buffer, thread parsed rows (not paths) through preflight and load. |
| RR-001-R5 | B2 | Reject `commit_hash` not matching `^[0-9a-f]{40}$`; resolve via `freeze_verifier._resolve_commit` and assert the resolved SHA equals the input. |
| RR-001-R6 | B3, C5 | Route `ReproductionRunnerError`, `ImportError`, `ScratchDatabaseExistsError`, `OSError` to `UNVERIFIABLE`; keep the `Exception` backstop but tag its detail explicitly. Unlink the scratch DB in a `finally` when reconstruction fails. |
| RR-001-R7 | B4 | Broaden `except OSError` in `_load_expected_tickers_from_worktree` to `except Exception`, wrapping as `ReproductionRunnerError` → `UNVERIFIABLE`. |
| RR-001-R8 | B5 | Carry `resolved_commit`, `observed_dataset_hashes`, `started_at`/`finished_at`, and platform/Python/SQLite versions on the outcome; have `_cli_main` write `reproduction_attempt_<timestamp>.json` next to the cycle. |
| RR-001-R9 | C1–C6, D1–D5 | C1: reject non-relative and `..`-containing `snapshot_path`, assert types. C2: derive calendars from data, or validate preflight against `{calendar_id}`. C3: length-prefixed or `repr`-escaped fields; include `row.keys()` in the digest. C4: reject duplicate keys, assert `isinstance(obj, dict)`, assert recursive key order. C5: see R6. C6: document the subprocess gap, or install the guard in the child if execution moves out-of-process. D1: `mkdtemp` a parent. D2: check the return code and warn. D3–D5: as tabulated. |
| RR-001-R10 | C7 | `[ARCHIVIST]` No remediation was proposed by the reviewer for C7; it is stated as a status observation. Recorded here so the gap is not lost. |

## 7. Acceptance criteria

`[ARCHIVIST-DERIVED]` The review event did not contain a section headed
"acceptance criteria." The criteria below are derived at filing time from
the review's own "Tests detect it?" assessments — every Band A and B
finding was recorded as *not* detected by the existing suite, and two were
recorded as actively concealed by it. They are stated so that a future
implementer and a future auditor can agree on what "fixed" means. **They
are not reviewer statements and carry no ratified authority.**

A remediation of a finding in this record is acceptable when all of the
following hold:

1. **A test exists that fails against the pre-fix code and passes after.**
   For A2 this specifically requires a fixture experiment that imports a
   `core.*` symbol — the current fixture imports only `sqlite3` and
   therefore cannot exercise the invariant it is named for.
2. **No test encodes the defect as correct behaviour.** For A1 this
   requires amending `test_full_reproduction_verifies`, whose fixture
   asserts `VERIFIED` with `"dataset_content_hashes": {}`.
3. **The docstring guarantee and the implementation agree.** Findings A2,
   A3, B4, C4 and C6 are each a divergence between a documented promise
   and the code; closing the code without closing the doc, or vice versa,
   does not discharge the finding.
4. **Verdict semantics are preserved.** No remediation may widen the set of
   conditions that produce `VERIFIED`, or route an environment failure to
   `DRIFTED` or `REPRODUCTION_FAILED`.
5. **C7 is discharged only by an end-to-end run against a real archive**,
   not by any unit test. `[ARCHIVIST]` This follows from the finding's own
   terms: every fixture is synthetic, so no synthetic test can close it.

## 8. Verification status

`[TRANSCRIBED]` Verifications the reviewer performed during the review
event:

| Claim | Method | Result |
|---|---|---|
| A1 — `ReproductionRecord` unreferenced | repo-wide grep for `result_report_hash\|ReproductionRecord\|dataset_content_hashes` | Confirmed — definition + two test fixtures only |
| A2 — real experiments import `core.*` | `grep -l "^from core\|^import core" experiments/*.py` | Confirmed — includes `daily_etf_universe_update.py` |
| C1 — path traversal semantics | interpreter check of `Path('cycle') / '/etc/passwd'` and `'../../../secret.jsonl'` | Confirmed |
| C3 — delimiter collision | computed digest of `[('A\|B','C')]` vs `[('A','B\|C')]` | Confirmed identical |
| C4 — duplicate-key silent overwrite | `json.loads('{"a":1,"a":2}')` | Confirmed → `{'a': 2}` |
| C7 — no reproducible archive | `find research_archive -name dataset_manifest.json -o -name reproduction_record.json` | Confirmed — no results |

**Not verified by execution at the review event:** A3's forgery scenario
(argued from code reading, not performed); B1's TOCTOU window (no test
mutates a file mid-run); B3/B4/B5 (argued from control-flow reading); D1's
symlink race (argued, and platform-dependent).

**Subsystem-level verification status: NOT VERIFIED END-TO-END.** Per C7,
the subsystem has never been executed against a real cycle. Every claim in
this record about runtime behaviour is derived from source reading plus the
targeted interpreter checks tabulated above.

`[ARCHIVIST]` **Filing-time re-verification (2026-07-21).** Two of the
load-bearing claims were re-checked at filing against the working tree, by
a party other than the reviewer:

- The `core.governance.*` and `core.market_data.persistence.database`
  imports at `reproduction_runner.py:47-68` are present, so `core` is in
  `sys.modules` before any `exec_module` call — **A2's premise holds.**
- `run_experiment(module, scratch_db_path)` at `reproduction_runner.py:211`
  discards its return value — **A1's seam holds.**
- The C7 search was re-run and still returns no results — **C7 holds as of
  filing.**

**Governance effect of this document: NONE until committed.** Per this
platform's own repeated standard, a document's claim to be reviewed is not
evidence until committed and its commit hash recorded. The subject matter
of this review (`core/governance/*`, the eight governance test files, and
three Phase 4 docs) is **itself uncommitted** as of filing — it appears as
untracked content on branch `arb/phase4-determination`. **A review of
uncommitted code is a review of a moving target**, and this record's
findings are anchored to the working-tree state at the review event window,
not to any commit.

---

## Cross-references

- **Reviewed subject:** `core/governance/*`, `tests/test_governance_*.py`,
  `docs/PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md`.
- **Peer review of this review:** filed separately as
  [RR-2026-07-21-002](2026-07-21_RR-002_phase4_governance_peer_review.md).
  `[ARCHIVIST]` That review event began at 16:58:21Z, after this one closed
  at 16:56:23Z. **It is not part of this record and did not inform it.**
- **Downstream adjudication:** `docs/PHASE_4_ARB_DETERMINATION_2026-07-21.md`
  rules on the findings in this record. `[ARCHIVIST]` That determination is
  **downstream of and later than** this review event (17:21:39Z) and its
  rulings are deliberately **not** reflected in this document. Where the
  determination accepts, modifies, or rejects a finding above, the record
  above stands unedited as what the reviewer found at the time.
