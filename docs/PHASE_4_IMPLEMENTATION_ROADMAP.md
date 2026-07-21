# Phase 4 — MUST-List Implementation Roadmap

**Date:** 2026-07-21
**Status: roadmap — sequencing proposal. No code committed by this document. Not a gate determination and not an approval.**

**Terminal objective.** An external reviewer receives only
`research_archive/<cycle>/` — no repository access beyond the pinned
commit it names, no developer contact — and reproduces the published
result. Every PR below is justified by, and only by, its contribution to
that sentence.

**Inputs.** The MUST list of
[PHASE_4_ARB_DETERMINATION_2026-07-21.md](PHASE_4_ARB_DETERMINATION_2026-07-21.md) §6,
the findings recorded in
[RR-001](reviewer_reports/2026-07-21_RR-001_phase4_governance_architecture_review.md)
and [RR-002](reviewer_reports/2026-07-21_RR-002_phase4_governance_peer_review.md),
and the evidence-package structure of
[RESEARCH_GOVERNANCE_STANDARD.md](RESEARCH_GOVERNANCE_STANDARD.md) §5.

**No new architecture is proposed.** Every item traces to a finding
already raised and already adjudicated. Two structural deviations from the
requested five-PR shape are flagged in the next section; both are
consequences of the ARB's own binding rulings, not new design.

---

## 0. Two deviations from the requested PR sequence

The requested sequence was: dataset provenance → dataset reconstruction →
environment capture → reproduction record → archive verification. That
spine is correct and is preserved. Two insertions are required, and
suppressing either would produce a roadmap that cannot deliver the
terminal objective.

**Deviation 1 — the requested sequence omits A2, the highest-severity MUST
item.** ARB §6 item 1 is *out-of-process execution of the pinned entrypoint
with the offline guard installed in the child (A2 + C6, bundled)*. It maps
to none of the five requested PRs: it is neither dataset provenance,
reconstruction, environment capture, record-writing, nor verification. It
is *code execution integrity*.

This omission is material, not cosmetic. Without A2, a reproduction runs
**today's** `core/analytics` library against **frozen** data and reports
`VERIFIED`. Every artifact PR1–PR5 produces would be a correctly-hashed,
correctly-manifested, independently-verifiable record **of the wrong
computation**. An archive that is perfectly auditable and attests to a run
that did not execute the reproduced code is worse than no archive, because
it converts an absence of evidence into false evidence. Inserted below as
**PR2-A**, and it must land before PR4 writes any record a reviewer would
cite.

**Deviation 2 — verdict correctness must precede everything.** B2, B4, and
B3+C5 are four to six lines in total, but until they land, every failure
encountered while building PR1–PR5 is misreported: an `ImportError` reads
as `REPRODUCTION_FAILED` ("the science did not reproduce"), an operator's
stale scratch DB reads as `DRIFTED` ("your frozen data changed"), and a raw
traceback escapes the runner entirely. Building the provenance chain on top
of a verdict layer that assigns blame incorrectly means every integration
failure during PR1–PR5 costs debugging time and risks being recorded as a
governance event. Inserted as **PR0**.

**Resulting sequence.** PR0 → PR1 → PR2 → PR2-A → PR3 → PR4 → PR5.
PR0 has no dependencies and can start immediately. PR1 and PR0 are
independent of each other and may run in parallel.

**One item is explicitly not scheduled here.** RR-002-R6 — the headline
pipeline (`daily_etf_universe_update.py`) trips `OfflineViolationError`
under the guard and therefore cannot serve as the reproduction target at
all. The ARB records this as certification blocker 2 and notes it is *"not
on the critical path of any code change in §6 and can be resolved in
parallel."* It is a **target-designation decision, not an implementation
task**, and it gates PR2's choice of subject. Resolve it before PR2 opens.

---

## PR0 — Verdict correctness preconditions

**Objective.** Make the four-state outcome mean what it says, so that every
subsequent PR's failures are diagnosed rather than misattributed. Closes
ARB §6 items 3, 4, and 5 (B4, B2, B3+C5).

**Files/modules affected**
- `core/governance/reproduction_runner.py` — `_load_expected_tickers_from_worktree`
  exception width (:132-142); `commit_hash` validation in `_cli_main` (:292-295);
  the two `except Exception` backstops (:197-201, :212-215).
- `core/governance/freeze_verifier.py` — reuse `_resolve_commit` (:103); no
  behaviour change.
- `tests/test_governance_reproduction_runner.py`.

**Acceptance criteria**
1. `commit_hash` not matching `^[0-9a-f]{40}$` is rejected before any
   worktree is created; a 40-hex value is resolved through `_resolve_commit`
   and the resolved SHA must equal the input. `"main"`, `"HEAD"`, a tag, and
   an abbreviation are all refused.
2. `ReproductionRunnerError`, `ImportError`, `ScratchDatabaseExistsError`,
   and `OSError` route to `UNVERIFIABLE`, never to `DRIFTED` or
   `REPRODUCTION_FAILED`.
3. The `except Exception` backstop is **retained**, and its detail string is
   explicitly tagged as an ungoverned failure rather than asserted drift.
4. No raw exception escapes `run_reproduction` for any input, including a
   pinned entrypoint whose module-level imports raise.
5. **The scratch DB is not unlinked on failure.** Per ARB C5, deleting it
   destroys forensic state an auditor needs. Classification alone resolves
   the reported scenario.
6. `detail` is no longer `str(exc)` alone — an argument-less exception must
   not serialize to an empty string.

**Tests required**
- Parametrized rejection of `"main"`, `"HEAD"`, `"v2^"`, a 7-char
  abbreviation, `""`, and a 40-char non-hex string.
- A fixture entrypoint whose module-level import raises `ImportError` →
  asserts `UNVERIFIABLE`, **not** `REPRODUCTION_FAILED`. This is the
  regression test for the finding RR-002 called the best fix-value-per-line
  in the submission.
- A pre-existing `--scratch-db` path driven through `run_reproduction` →
  asserts `UNVERIFIABLE` and asserts **the file still exists afterwards**.
- A fixture entrypoint raising `SyntaxError` at import → asserts a status is
  returned rather than a traceback propagating.
- Assert the existing `test_malformed_dataset_manifest_..._as_drifted` still
  passes — the backstop is narrowed, not removed.

**Audit value.** An auditor who receives `UNVERIFIABLE` learns *"this
environment could not run the check"*; one who receives `DRIFTED` learns
*"the frozen data does not match."* Today those are the same output for an
environment fault. Until they separate, no verdict in any archive is
interpretable without developer context — which is the terminal objective
stated in the negative.

---

## PR1 — Dataset provenance: manifest, hashes, schema identity

**Objective.** Produce, for one real cycle, the `dataset_manifest.json` and
`dataset_hashes/` that Standard §5 requires and that no archive currently
has. This is the remedy for C7, which the ARB names the trigger condition
for the whole MUST list and *"disqualifying on its own."*

**Files/modules affected**
- `research_archive/<cycle>/dataset_manifest.json` — new.
- `research_archive/<cycle>/dataset_hashes/*.jsonl` — new snapshots
  (currently `.gitkeep` only).
- `core/governance/dataset_snapshots.py` — snapshot export path.
- `core/governance/canonical_jsonl.py` — write path is sound (RR-001 Band E);
  no change expected.
- `core/governance/identity_verification.py` — C3 length-prefixed digest.
- `tools/` — a snapshot-export entrypoint if none exists.

**Scope note.** C3 (length-prefixed field hashing, column names in the
digest) is ARB §7 SHOULD, deliberately pulled forward into this PR. ARB §2's
conditional flag on B5 states that once a digest format is written into
published evidence, changing it becomes a migration. This PR is the last
point at which the format is free. **Schema identity is in this PR's title
for exactly this reason** — `schema_version` per manifest entry and the
frozen-identity digest format are both identity claims that must be fixed
before first publication.

**Acceptance criteria**
1. One real cycle has a `dataset_manifest.json` whose entries cover exactly
   `REQUIRED_SOURCE_TABLES` — no missing, no unexpected, no duplicate
   `source_table`.
2. Every entry carries `sha256:`-prefixed `content_hash`, `row_count`,
   `schema_version`, and a `snapshot_path` that is **relative, POSIX, with
   no `..` component and no drive anchor** (C1's surviving half; the
   rejected type-validation add-on is *not* implemented).
3. Every `content_hash` is computed from the snapshot's own bytes on disk,
   never hand-written or back-filled to an expected value (Standard §5).
4. Snapshots are byte-reproducible: regenerating from the same database
   state yields identical bytes and identical hashes.
5. The frozen-identity digest uses length-prefixed fields and includes
   column names. A row set differing only by delimiter placement must
   produce different digests.
6. `archive_manifest.json` is **not** retroactively added to
   `reference_v1`, `reference_v2_h1`, or `reference_h3` — per
   `RESEARCH_ARCHIVE_MANIFEST.md`, that would itself be a silent edit to a
   closed archive.

**Tests required**
- Coverage: missing table, unexpected table, duplicate `source_table` each
  rejected with a distinct named error.
- `snapshot_path` rejection: absolute path, `..` traversal, Windows drive
  anchor, backslash separator.
- Byte-reproducibility: export twice, assert identical bytes.
- C3 regression: assert `[('A|B','C')]` and `[('A','B|C')]` now produce
  **different** digests — the collision RR-001 and RR-002 both reproduced.
- Assert a hand-edited `content_hash` fails verification against real bytes.

**Audit value.** This is the first PR after which the archive contains
anything an external party can independently check. Before it, an auditor
handed the archive has literally nothing to verify against; after it, they
can confirm that the bytes they hold are the bytes the manifest claims.
It does not yet establish that those bytes are the *right* bytes — that is
PR4's binding — but it converts an unfalsifiable archive into a falsifiable
one.

---

## PR2 — Dataset reconstruction

**Objective.** Prove the manifest from PR1 is sufficient: a database
adequate to run the experiment can be rebuilt from the archive alone, with
no network and no live database.

**Prerequisite.** RR-002-R6 must be resolved first — an offline-capable
reproduction target must be designated. PR2 cannot demonstrate
reconstruction for a target that cannot run offline.

**Files/modules affected**
- `core/governance/reconstruction_loader.py` — C2 preflight narrowing.
- `core/governance/dataset_snapshots.py` — read path.
- `core/governance/calendar_definitions.py` — unchanged (Band E, sound).
- `tests/test_governance_reconstruction_loader.py`.

**Scope note.** C2 is ARB §7 SHOULD, pulled forward in the **one-line form
the ARB explicitly preferred** — validate preflight against the calendar
actually loaded, not against all of `CALENDAR_DEFINITIONS`. The
derive-calendars-from-data variant is the better end-state and is
deliberately **not** taken here; ARB C2 defers it to the day a second
calendar arrives. B1 (single-read threading) is **not** in this PR — ARB §8
places it in hardening, explicitly *"not before v1.0."*

**Acceptance criteria**
1. Reconstruction from the archive alone, under `offline_guard`, yields a
   database that the designated experiment runs against successfully.
2. All validation completes before the scratch database is created or
   opened — the existing fail-fast property (RR-001 Band E) is preserved,
   not regressed.
3. Preflight validates `calendar_id` against the calendar actually loaded.
   A snapshot referencing an unloaded calendar fails with a **named,
   offline** error, never a raw `sqlite3.IntegrityError` reaching a backstop.
4. Load ordering `Calendar → ETF → TradingSession → PriceBar` holds and
   `PRAGMA foreign_keys=ON` remains a live second line of defense.
5. A tampered snapshot byte fails on `content_hash` before any row is
   written.

**Tests required**
- End-to-end reconstruct-then-run against a real (not `tmp_path`-synthetic)
  archive fixture — the first test in the suite that is not synthetic.
- Snapshot referencing a second, unloaded `calendar_id` → asserts a named
  `UnknownEtfCalendarError`-class failure, not `DRIFTED`. This is the
  regression test for C2's latent trap.
- Single-byte mutation of each snapshot → asserts `DRIFTED` with the
  offending `source_table` named.
- Row-count mismatch with a correct hash → asserts the distinct row-count
  error.
- Assert no network syscall occurs during reconstruction.

**Audit value.** Establishes that the archive is *sufficient*, not merely
*described*. A manifest that hashes files nobody can turn back into a
working dataset documents an archive without making it reproducible. This
PR is where "self-contained" stops being a docstring claim — the property
RR-001's C1 identified as the one at risk.

---

## PR2-A — Execution integrity: pinned-commit execution and the child-process guard

> **Inserted PR. Not in the requested sequence — see §0, Deviation 1.**
> ARB §6 item 1, and the ARB's binding integration ruling: *"A2's fix
> creates C6's severity… They ship in the same change or not at all."*
> This PR is that single change. **It must not be split.**

**Objective.** Ensure the code that runs during a reproduction is the code
at the pinned commit, and that the offline guarantee survives the move
out-of-process.

**Files/modules affected**
- `core/governance/reproduction_runner.py` — `_load_module_from_worktree`
  (:106-121), `_load_expected_tickers_from_worktree` (:124-149), and the
  `run_experiment: Callable[[ModuleType, Path], Any]` contract (:163-176),
  which this PR **deletes or replaces**.
- `core/governance/network_guard.py` — installation in the child.
- `core/governance/pinned_worktree.py` — D2 return-code check (free here).
- `tests/test_governance_reproduction_runner.py`, `..._network_guard.py`.

**Cost disclosure, per RR-002.** This is the one MUST item that is *not*
minimal and *not* in-architecture. It deletes a documented contract whose
stated reason for existing is that experiment signatures differ, and it
moves execution outside the in-process guard. RR-001's characterization
that it "stays in-architecture" was rejected by both RR-002 and the ARB.
Budget accordingly; this is the largest item on the MUST list.

**Acceptance criteria**
1. The pinned entrypoint executes in a child process with `cwd` set to the
   worktree and `PYTHONPATH` rooted there, such that `import core.*`
   resolves to the **worktree's** `core/`, never HEAD's.
2. The offline guard is active **in the child**. A child attempting network
   access fails as an `OfflineViolationError`-equivalent, not silently.
3. A non-zero child exit is classified per PR0's taxonomy — an import
   failure is `UNVERIFIABLE`, not `REPRODUCTION_FAILED`.
4. The scoped `sys.modules` denylist is implemented **only** as a
   time-boxed stopgap with a recorded expiry, if at all, and **never** in
   RR-001's blanket form, which RR-002 proved would refuse 100% of runs.
5. `network_guard`'s docstring no longer claims a "process-level"
   guarantee it does not provide; the subprocess gap is either closed or
   named.
6. `git worktree remove` return code is checked and warns (does not raise).

**Tests required**
- **The test that currently cannot exist:** a fixture experiment that
  imports a `core.*` symbol whose value differs between HEAD and the pinned
  commit; assert the *pinned* value is observed. RR-001 and RR-002 both
  identified `test_experiment_code_runs_from_the_pinned_commit_not_head` as
  named for this invariant while importing only `sqlite3`. That fixture must
  be replaced, and its replacement must fail against pre-PR2-A code.
- Child process attempting a socket connection → asserts a governed offline
  violation.
- Child exiting non-zero on `ImportError` → asserts `UNVERIFIABLE`.
- Two sequential `run_reproduction` calls in one process against different
  commits → asserts no cross-contamination (D3).

**Audit value.** This is the difference between "we re-ran the pipeline" and
"we re-ran *that* pipeline." Without it, every artifact PR1, PR3, PR4 and
PR5 produce is a rigorous, verifiable attestation about a computation the
auditor did not ask about. It is the single item on this roadmap whose
absence makes the other six actively misleading rather than merely
incomplete.

---

## PR3 — Environment capture

**Objective.** Record the execution environment in enough detail that an
auditor can tell whether a divergence is a genuine reproduction failure or
an environment difference — the distinction the four-state enum exists to
make and cannot currently support with evidence.

**Files/modules affected**
- `core/governance/reproduction_runner.py` — `ReproductionOutcome` (:95-103),
  made `frozen=True, slots=True` (D4, folded here per ARB §4, consistent
  with its peers).
- `core/governance/reproduction_record.py` — environment fields.
- `tests/test_governance_reproduction_runner.py`.

**Acceptance criteria**
1. Captured, at minimum: Python version and implementation, SQLite library
   version, platform/OS, the **resolved** 40-hex commit SHA, applied
   migration versions, `started_at`/`finished_at` as UTC ISO-8601.
2. Capture is passive — no value is asserted, compared, or gated on in this
   PR. Environment comparison policy is out of scope and is not smuggled in.
3. `ReproductionOutcome` is immutable, matching every peer result type.
4. No environment field can silently serialize to `""` or `null` — an
   uncapturable value is explicitly recorded as unavailable.

**Tests required**
- Assert every required field is present and non-empty for a successful run.
- Assert the captured commit is the **resolved** SHA, not the input string.
- Assert immutability (mutation raises).
- Assert environment capture still occurs on a failed run — evidence about
  failures matters more than evidence about successes.

**Audit value.** An auditor who reproduces and gets a different number must
distinguish "the science does not hold" from "I am on SQLite 3.45 and you
were on 3.40." Without captured environment, that question is unanswerable
from the archive and can only be resolved by contacting the developer —
which is precisely the dependency the terminal objective forbids.

---

## PR4 — Reproduction record

**Objective.** Write a durable, citable evidence artifact per attempt, and
close the integrity chain by binding the manifest to the record and both
to the pinned commit.

> **Indivisibility, per the ARB's binding bucketing ruling.** A1(a)
> (manifest `content_hash` ↔ `record.dataset_content_hashes`) and A3's
> covered-paths addition are **one change**. Binding the manifest to a
> record that is not itself covered by `freeze_verifier` at the pinned
> commit *"relocates the self-attestation one file over, and a forger edits
> three files instead of two."* **Neither ships alone.**

**Files/modules affected**
- `core/governance/reproduction_record.py` — `ReproductionRecord` becomes
  live; currently constructed nowhere.
- `core/governance/reproduction_runner.py` — parse and enforce the record;
  `_cli_main` writes `reproduction_attempt_<timestamp>.json`.
- `core/governance/freeze_verifier.py` — covered-paths list.
- `research_archive/<cycle>/reproduction_record.json` — new.
- `tests/test_governance_reproduction_runner.py`.

**Scope boundary — A1(b) is excluded.** Result-report hashing is chartered
separately as
[PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md](PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md).
RR-002 proved a naive `sha256_of_file` can **never** match across runs
because the report carries a `generated_at` timestamp. The ARB: *"Do not
attempt it as a patch."* **This PR must not introduce output-hash
comparison.** Consequently `VERIFIED` after PR4 still does not mean the
output matched, and §"Honest status" below states what it does mean.

**Acceptance criteria**
1. `reproduction_record.json` is parsed into `ReproductionRecord` — not
   read field-by-field.
2. Each manifest entry's `content_hash` is asserted equal to
   `record.dataset_content_hashes[source_table]`; mismatch → `DRIFTED`.
3. `reproduction_record.json` **and** `dataset_manifest.json` are in
   `freeze_verifier`'s covered paths at the pinned commit. Editing either
   in the working tree is detected as drift.
4. Every attempt writes a record — success, failure, and `UNVERIFIABLE`
   alike — carrying PR3's environment fields, observed hashes, and status.
5. Attempt records are append-only. A second attempt never overwrites a
   first (Standard §5).
6. The record is written even when the run fails before execution.

**Tests required**
- Manifest hash edited to disagree with the record → asserts `DRIFTED`.
- Record edited in the working tree → asserts `freeze_verifier` reports
  uncommitted drift. **This is the forgery test** RR-001's A3 said no
  fixture probes: the manifest must stop being self-attesting.
- Both manifest and record edited consistently → still detected, via the
  commit-coverage path. This is the test that distinguishes a real fix from
  relocating the self-attestation.
- Two attempts → two records, neither overwritten.
- Failed run → asserts a record exists.
- Assert `result_report_hash` is **not** consulted (guards the A1(b) scope
  boundary against silent scope creep).

**Audit value.** The first PR after which a reproduction produces something
citable. ARB certification blocker 6: *"Even a fully correct run today emits
one line to stdout… Certification rests on artifacts."* This closes
blockers 5 and 6 and converts the archive's integrity chain from a loop
that closes on itself into one anchored to the git object store.

---

## PR5 — Archive verification

**Objective.** One command, run against an archive directory alone, that
reports whether the package is complete, internally consistent, and
anchored — so the auditor does not have to know what to check.

**Files/modules affected**
- `core/governance/archive_verifier.py` — new; the `ArchiveVerifier`
  anticipated by `PLATFORM_ARCHITECTURE_V1.md` §4.4 and
  `RESEARCH_ARCHIVE_MANIFEST.md`.
- `tools/archive_manifest.py` — input contract, unchanged in behaviour.
- `research_archive/README.md` — auditor-facing entry point.
- `tests/test_governance_archive_verifier.py` — new.

**Acceptance criteria**
1. Verifies Standard §5 completeness: `hypothesis.md`, `methodology.md`,
   `dataset_manifest.json`, `dataset_hashes/`, `experiment_results/`,
   `reviewer_reports/`, `decision_log.md`.
2. Reads `lifecycle_version` and applies the `v1` structural check **only**
   to `v1` packages; `legacy` packages are reported as exempt, not as
   failing. `reference_v1`, `reference_v2_h1`, and `reference_h3` must not
   be reported as violations.
3. Recomputes every `content_hash` from bytes on disk and reports
   per-entry pass/fail.
4. Confirms `reproduction_record.json` and `dataset_manifest.json` are
   covered by the freeze at the named commit.
5. Reports **status, not a boolean** — complete / incomplete / exempt /
   unverifiable, matching the platform's established three-and-four-state
   discipline.
6. Runs offline, read-only, and **writes nothing into the archive**. Per
   `RESEARCH_ARCHIVE_MANIFEST.md`, tooling must be structurally incapable
   of writing into a closed archive.
7. Output is interpretable without developer context: each failure names
   the file, the expectation, and what was observed.

**Tests required**
- A complete `v1` archive → complete.
- Each of the seven items removed in turn → names the missing item.
- A `legacy` archive → exempt, not violation.
- Tampered snapshot byte → names the failing entry.
- Assert the verifier opens nothing for writing (read-only enforcement).
- Assert a non-zero exit code on failure, so it is usable as a gate.

**Audit value.** Collapses the entire chain into one executable question.
Every prior PR adds a property the archive must have; this PR is the only
one that lets an outsider *confirm* those properties without being told
what they are. It is the difference between an archive that is auditable in
principle and one that is auditable in practice.

---

## Honest status after all seven PRs

What a reviewer can then do unaided: verify the package is complete; verify
the bytes match their hashes; verify the manifest is anchored to a commit
rather than to itself; reconstruct the database offline; execute the
experiment at the pinned commit with the pinned library; and read a durable
record of what ran, where, when, and under which interpreter.

**What they still cannot do: confirm the output matches.** A1(b) is
chartered separately and deliberately excluded from PR4. After all seven
PRs, `VERIFIED` means *"inputs verified, frozen identities unchanged, and
the pinned code executed without error"* — **not** *"the published number
was reproduced."* That gap closes only when the canonicalization charter
lands.

This must be stated in `research_archive/README.md` in those terms. An
auditor who reads `VERIFIED` as "the number checks out" has been misled by
the archive, and no amount of provenance machinery elsewhere repairs that.
**Recording the boundary is part of the deliverable, not a caveat on it.**
