# Phase F Gate Review — Boundary-Hardening Completion Audit

**Date:** 2026-07-24
**Auditor role:** Lead architect, completion review
**Scope:** C0 … C7 (`bcae264` … `02b55d3`), against `origin/master` = `61d001a`
**Review level:** Level 1 (single pass, no independent reviewer) — see §A.2
**Method:** every claim below was established from the repository by
execution or by reading, and is cited to `file:line` or to a command
result. Nothing in this document is carried over from the commit
messages or from the resolution documents without independent check.

> **Governing principle inherited from `PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` §0:**
> *The repository must never record a claim stronger than the mechanism
> that enforces it.* This review is subject to it, and §A applies it to
> the review's own verdict.

---

## 1. Git integrity

### 1.1 Ancestry C0 → C7 — **VERIFIED**

`git log --oneline` and `git rev-list --left-right --count origin/master...HEAD`:

| # | SHA | Subject | Verified |
|---|---|---|---|
| C0 | `bcae264` | governance provenance (both resolutions committed) | ✅ |
| C1 | `6513573` | AD-061…AD-067 reservation block | ✅ |
| C2 | `4141231` | AD-068 ETF boundary governance + §5 | ✅ |
| C3 | `c7e85ba` | ETF dependency enforcement | ✅ |
| C4 | `ff9cea8` | AD-069 Store governance + §5 | ✅ |
| C5 | `6f81bf2` | `core.store` extraction | ✅ |
| C6 | `f92700f` | reproduction guards, tests, rename | ✅ |
| C7 | `02b55d3` | documentation pointer corrections | ✅ |

- **Linear, no merges.** `git log --merges 61d001a..HEAD` → empty.
  `git log --first-parent 61d001a..HEAD | wc -l` → `8`, equal to the
  total commit count. The history is a strict chain.
- **Ordering matches the ruling.** The resolution's ordering constraints
  (numbering first; each ADR + §5 amendment *before* the code it
  governs; step 1 fully before step 2) are satisfied by construction:
  C1 → C2 → C3 (ETF) → C4 → C5 (Store).

### 1.2 No unexpected files changed — **VERIFIED**

`git diff --name-status 61d001a..HEAD` returns **24 paths**, every one of
which appears in the resolution's §4 commit decomposition plan. No path
outside the plan was touched.

- Production code changed: `adapters/cli/main.py`,
  `core/governance/{reconstruction_loader,reproduction_runner}.py`,
  `core/market_data/persistence/{database,migrations}.py`,
  `maintenance/verify_price_coverage.py` — all import-site repointing —
  plus the three new `core/store/*.py` files. This is exactly the C5
  file list.
- **`tests/fixtures/protected_file_hashes.json` is untouched**
  (`git diff --stat 61d001a..HEAD --` on that path → empty), confirming
  the Phase-0 immutability convention was honoured and the 36
  parametrized hash cases pass unmodified.
- One deletion, `tests/test_database.py`, paired with the addition of
  `tests/test_store_connection.py` — the GR-15 rename, as planned.

### 1.3 No untracked implementation artifacts — **VERIFIED**

`git status --porcelain` returns exactly one line:

```
?? docs/PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md
```

No untracked code, no stray scratch files, no `.orig`/`.rej`. **See
§C-1: this file being untracked is itself an open item**, because C0
exists precisely to make review inputs tracked artifacts (GR-20).

### 1.4 Branch divergence — **VERIFIED, CLEAN**

`git rev-list --left-right --count origin/master...HEAD` → `0  8`.

Zero commits behind, eight ahead. **There is no divergence** — `master`
is a strict fast-forward of `origin/master`. Nothing has been rebased,
amended, or force-moved. The push is deferred by choice, not blocked by
a conflict. **See §C-2 on the durability risk of holding eight commits
unpushed.**

---

## 2. Governance closure matrix

### 2.1 GR-01 … GR-20

| Requirement | Evidence | Status |
|---|---|---|
| **GR-01** AD number collision | Reservation block `docs/ARCHITECTURE_DECISIONS.md:3098-3137`, incl. the general reservation rule; landed C1 | ✅ **CLOSED** |
| **GR-02** AD-061 denies its own permission change | AD-069 permission ledger, `ARCHITECTURE_DECISIONS.md:3274+`; landed C4 | ✅ **CLOSED** |
| **GR-03** Grant breadth | `ALLOWED_DEPENDENCIES` grants `store` to `data` and `governance` **only** — `tools/check_import_boundaries.py:171,174`; `statistics`/`etf`/`validation`/`research`/`reporting`/`kernel` all denied; enforced by T-5, T-6 | ✅ **CLOSED** |
| **GR-04** Bundling | Two independent commits: C3 `c7e85ba` (checker + tests, **no `store` reference**) and C5 `6f81bf2`. `ALLOWED_DEPENDENCIES` touched once per step | ✅ **CLOSED** |
| **GR-05** No ADR for ETF/Data split | AD-068 at `ARCHITECTURE_DECISIONS.md:3139`; landed C2, **before** C3's code | ✅ **CLOSED** |
| **GR-06** Shims load-bearing for reproduction | AD-069 records the `sys.modules` mechanism; executable guard T-2 at `tests/test_store_extraction.py:243` | ✅ **CLOSED** |
| **GR-07** Shrink condition instructs a destructive act | Corrected message in C5; retirement condition (b) made mechanical by T-3 at `tests/test_store_extraction.py:307`; AD-069 declares the shims **permanent** | ✅ **CLOSED** |
| **GR-08** §5 never amended | `docs/PLATFORM_ARCHITECTURE_V1.md` amended twice — C2 (+53/−9, ETF half) and C4 (+61/−13, Store half) | ✅ **CLOSED** |
| **GR-09** §5 Enforcement clause forbids AST attribution | Amended in C2 alongside AD-068's symbol-attribution departure and its termination condition | ✅ **CLOSED** |
| **GR-10** Stale documentation pointers | Blocking tier in C5 (`migrations/README.md`); non-blocking tier in C7 (`BASELINE_STATUS.md`, `PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md`). Dated records correctly **excluded** | ✅ **CLOSED** |
| **GR-11** Permanently red test as deliverable | `@pytest.mark.xfail(strict=True)` on `test_real_repository_has_no_boundary_violations`, `tests/test_import_boundaries.py:154-166`; convention documented at file head :6-24. Suite reports `1 xfailed` | ✅ **CLOSED** |
| **GR-12** Incomplete regression coverage | T-1 … T-8 all present and executing — see §2.2 | ✅ **CLOSED** |
| **GR-13** "Land step 2 before step 1" | **REJECTED** by ruling; C3 precedes C5 as ruled | ✅ **CLOSED (rejected)** |
| **GR-14** "Shorten duplicated docstring prose" | **REJECTED** by ruling; mechanical half addressed by T-8 | ✅ **CLOSED (rejected)** |
| **GR-15** Rename `tests/test_database.py` | `D tests/test_database.py` / `A tests/test_store_connection.py` in C6 | ✅ **CLOSED** |
| **GR-16** `_python_files()` lacks venv/vendor skip | Ruled **ACCEPT (deferred)**. Actual symbol is `_iter_python_files`, `tools/check_import_boundaries.py:237-241`; skips `__pycache__` only | ⚠️ **DEFERRED** — §3.1 |
| **GR-17** `check_repository` never scans `adapters/` | Ruled **ACCEPT as fact, out of scope**. Confirmed: `check_repository(core_root=DEFAULT_CORE_ROOT)` at :341; scan root is `core/` only | ⚠️ **OPEN BY DESIGN** — **but see §4.2(a), it becomes material at Phase F** |
| **GR-18** "`data` has no `core.store` importer" | **REJECTED**; `data` holds the two shims and is granted `store` at :171 | ✅ **CLOSED (rejected)** |
| **GR-19** `ImportError` escapes uncaught | Recorded in AD-069 as a disclosed consequence. **Record made; defect not repaired.** Audit finds the record over-broad — §3.3 | ⚠️ **DEFERRED (record inaccurate)** — §3.3 |
| **GR-20** Neither review is a repository artifact | C0 `bcae264` commits both resolution documents (+1943 lines) as tracked artifacts | ✅ **CLOSED** — *but the Phase F Proposal is still untracked, §C-1* |

**Tally:** 20 of 20 ruled. **16 CLOSED** (4 of them as rulings of
REJECT, which require no action). **3 DEFERRED** (GR-16, GR-17, GR-19).
**0 blocking items open.**

### 2.2 T-1 … T-8 — all present, all executing

Each test was located by name and its introducing commit traced with
`git log -S`. **Every test landed in exactly its planned commit.**

| Test | Implementation | Planned | Actual | Status |
|---|---|---|---|---|
| **T-1** ETF symbol existence | `test_every_etf_symbol_resolves_in_its_named_module`, `tests/test_import_boundaries.py:107` | C3 | `c7e85ba` | ✅ PASS |
| **T-2** Foreign-worktree shim binding | `test_legacy_import_from_a_foreign_worktree_still_binds_core_store`, `tests/test_store_extraction.py:243` | C6 | `f92700f` | ✅ PASS |
| **T-3** Archive-pin shrink guard | `test_pinned_commits_still_require_the_shims`, `tests/test_store_extraction.py:307` | C5 | `6f81bf2` | ✅ PASS |
| **T-4** `PRAGMA foreign_keys` ON | `test_foreign_keys_pragma_is_on`, `tests/test_store_connection.py:54` | C6 | `f92700f` | ✅ PASS |
| **T-5** Grant set matches importers | `test_store_grant_set_matches_demonstrated_importers` :439 + `test_statistics_may_not_depend_on_store` :477 | C5 | `6f81bf2` | ✅ PASS |
| **T-6** Real-tree purity | `test_real_tree_statistics_and_kernel_import_no_store`, `tests/test_import_boundaries.py:562` | C6 | `f92700f` | ✅ PASS |
| **T-7** `run_migrations` parity | `test_run_migrations_creates_the_ledger_and_is_idempotent` :88 + `..._applies_files_in_sorted_order` :117 | C6 | `f92700f` | ✅ PASS |
| **T-8** Shim surface is one name | `test_shim_public_surface_is_exactly_one_name`, `tests/test_store_extraction.py:198` | C6 | `f92700f` | ✅ PASS |

**T-3 executes for real — it is not silently skipped.** T-3 carries two
`pytest.skip` escape paths (non-git worktree; unresolvable pins). Both
were checked:

- All three archive pins resolve to real commit objects:
  `reference_h3` → `07f0da3`, `reference_v1` → `19771d4`,
  `reference_v2_h1` → `8831d54` (`git cat-file -t` → `commit` for each).
- Run in isolation: `1 passed in 0.57s`.

This mattered: a "Blocking"-tier guard that silently skips is worse than
no guard. It does not skip.

### 2.3 Test state — **INDEPENDENTLY REPRODUCED**

```
783 passed, 1 skipped, 1 xfailed in 43.05s
```

Matches the reported state exactly.

- **The 1 xfailed** is the intended AD-068 posture:
  `test_real_repository_has_no_boundary_violations`, strict.
- **The 1 skipped** is **not** a boundary-hardening test. It is
  `tests/test_domain_packages_import.py:55`, skipped with *"got empty
  parameter set for (module_name)"* — `STILL_EMPTY_DOMAIN_MODULES: list[str] = []`
  at :38. A pre-existing Phase-0 leftover; all domain packages are now
  populated, so the parametrize list is legitimately empty and the test
  is vacuous rather than wrong. Out of scope, noted at §C-6.

### 2.4 Milestone close items

| Item | Evidence | Status |
|---|---|---|
| AD-068 written and accepted | `ARCHITECTURE_DECISIONS.md:3139` | ✅ |
| AD-069 written and accepted | `ARCHITECTURE_DECISIONS.md:3274` | ✅ |
| AD-061…067 reserved and discoverable | `:3098-3137` | ✅ |
| §5 amended for both steps | `PLATFORM_ARCHITECTURE_V1.md`, C2 + C4 | ✅ |
| `core.store` is Layer −1, depends on nothing | `ALLOWED_DEPENDENCIES[STORE_DOMAIN] = frozenset()` :178; `test_store_imports_nothing_from_core` | ✅ |
| Every commit independently revertable | Linear chain, no merges; per-commit file sets disjoint by concern | ✅ |
| Protected-hash fixture untouched | §1.2 | ✅ |
| Suite green at HEAD | §2.3 | ✅ |
| Review inputs are tracked artifacts | C0 — **partial**, Proposal still untracked | ⚠️ §C-1 |
| Checker exit status at HEAD | **Exits 1 by design** — 5 known ETF violations across `data -> etf` (3) and `governance -> etf` (2) | ⚠️ §C-3 |

---

## 3. Deferred decisions review

### 3.1 GR-16 — `_iter_python_files()` virtual-environment exclusions

**What is actually there.** `tools/check_import_boundaries.py:237-241`:

```python
def _iter_python_files(core_root: Path):
    for path in sorted(core_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path
```

*(Note: the deferred item names this `_python_files()`; the symbol is
`_iter_python_files`. Recorded so the follow-up cites a real name.)*

**Findings.**

1. The scan root is **`core/` only** — `check_repository(core_root: Path = DEFAULT_CORE_ROOT)`
   at :341. It is not a repository-wide walk.
2. **No virtual environment exists in the repository.** `ls -d .venv venv env`
   → nothing; `find core -name site-packages -o -name pyvenv.cfg` → nothing.
3. The one reachable exposure is the CLI at :409,
   `core_root = Path(argv[0]).resolve() if argv else DEFAULT_CORE_ROOT`
   — an operator can point the checker at an arbitrary tree.
4. A vendored or virtualenv'd package placed under `core/` would be
   parsed, and would raise `UnmappedPackageError` at :250 rather than
   produce a wrong answer — it **fails loudly, not silently**.

**Severity: LOW.** The failure mode is a noisy crash or a slow scan, not
a false clean bill of health. The precondition (a venv inside `core/`)
does not hold and is not a normal state.

**Blocks Phase F: NO.** Phase F adds `core/research/execution/` — plain
first-party source under an already-mapped toplevel. It vendors nothing.

**Recommendation: KEEP DEFERRED.** No ADR — this is an implementation
detail of a tool, not an architectural decision, and creating an ADR for
it would dilute the register. Revisit only if the repository ever
vendors a dependency under `core/` or if the checker's CLI is wired into
an automated job that accepts an arbitrary root.

---

### 3.2 `reproduction_runner` docstring inaccuracy

**What is actually there.** `core/governance/reproduction_runner.py:1-15`
states that migrations, dataset snapshots and the experiment script come
from the pinned commit's own worktree, *"never from `repo_root`'s current
HEAD copy."*

That is **true for the experiment script**, which is loaded by file path
via `_load_module_from_worktree` (:106-121), and **false for the `core.*`
modules that script imports**: `sys.modules['core']` is already
populated, so a pinned script's `core.…` import resolves through HEAD's
`core.__path__` regardless of the `sys.path.insert` at :117.

**This is already disclosed, not hidden.** AD-069 records it verbatim
under *"Carried-forward inaccuracy, disclosed not repaired"*
(`ARCHITECTURE_DECISIONS.md` ~:3462), correctly classifies it as
**pre-existing**, and correctly observes that AD-069 *"converts a latent
inaccuracy into a load-bearing one."* T-2 pins the real behaviour.

**Severity: LOW operationally, MEDIUM as a record defect.** No behaviour
is wrong; the runtime does the right thing and a test proves it. The
defect is that the module's own docstring — the first thing a
reproduction operator reads — asserts an isolation property the module
does not have. Given that AD-069 now makes this mechanism load-bearing,
a reader who trusts the docstring will mis-reason about reproduction
isolation.

**Blocks Phase F: NO.** Phase F introduces no reproduction path and does
not import `reproduction_runner`.

**Recommendation: FIX NOW.** One docstring, zero behaviour change, zero
test impact. The correct text is already written — AD-069's disclosure
paragraph states the fact precisely; the fix is to carry that sentence
into the docstring and cite AD-069 and T-2. **No new ADR**: AD-069
already governs this and explicitly records it as an open item, so this
discharges an existing decision rather than creating one.

---

### 3.3 `ImportError` as an ungoverned reproduction status

**This is the sharpest of the three, and the existing record is wrong in
both directions.** GR-19 states, flatly, that `ImportError` from shim
deletion escapes uncaught. Tracing all three load paths in
`run_reproduction` shows that is true on **one** path and false on the
other two.

Exception-hierarchy premise, checked empirically:
`issubclass(ModuleNotFoundError, OSError)` → **False**.

| # | Path | Location | Behaviour on `ImportError` | Governed? |
|---|---|---|---|---|
| **A** | ETF-universe preload | :182-186 → `_load_expected_tickers_from_worktree` :133-142 | `except OSError` does **not** catch it → propagates → caller's `except ReproductionRunnerError` (:188) does **not** catch it → outer `except WorktreeError` (:236) does **not** catch it → **escapes `run_reproduction` entirely** | ❌ **NO — uncaught crash** |
| **B** | `reconstruct_database` | :194-210 | Caught by the governed backstop `except Exception` at :206 | ✅ Yes → `DRIFTED` |
| **C** | Experiment module load + run | :219-224 | Caught by `except Exception` at :221 | ✅ Yes → `REPRODUCTION_FAILED` |

**So the real exposure is Path A only**, and only when
`experiment_module_relative_path == UNIVERSE_MODULE_RELATIVE_PATH`
(:181) — i.e. the ETF universe cycles specifically.

**Two secondary findings the record does not contain:**

- On paths B and C the status is **governed but semantically wrong**. A
  deleted shim is not input drift and not an experiment failure; by the
  runner's own taxonomy (:17-23) an unloadable pinned artifact is
  **`UNVERIFIABLE`**. So even where nothing crashes, the reported status
  misattributes the fault to the archived data rather than to HEAD.
- The docstring at :25-32 claims the reconstruction phase lets *"no raw
  exception … ever escape this function."* That claim is accurate for
  the reconstruction phase proper (B), and the sweeping phrasing invites
  a reader to assume it covers the whole attempt. Path A precedes the
  reconstruction phase and is not covered. This compounds §3.2.

**Severity: MEDIUM.** Blast radius is high (an uncaught crash in the
governance runner, on the ETF cycles, with no recorded status) but
likelihood is **low and actively suppressed**: the trigger is shim
deletion, and **T-3 now mechanically refuses the deletion premise** while
any archived pin imports a legacy path — which, per AD-069, is
permanently the case for all three pins. T-3 is a genuine compensating
control, and it is the reason this is not rated HIGH.

**Blocks Phase F: NO.** Phase F adds no reproduction path, imports
nothing from `reproduction_runner`, and cannot reach Path A.

**Recommendation: FIX NOW (narrow), and amend the GR-19 record.**

- **Fix:** widen the `except OSError` at :134 to
  `except (OSError, ImportError)`, so Path A converts to
  `ReproductionRunnerError` and surfaces as `UNVERIFIABLE` through the
  existing handler at :188. Three-character change, one path, no new
  mechanism, aligns Path A with the documented taxonomy.
- **Amend, do not create:** AD-069's disclosure should be corrected to
  say *which* path is ungoverned and that B/C are governed-but-
  mislabelled. **No new ADR** — this is a factual correction inside an
  accepted decision's disclosure, and the gap is in the record's
  precision, not in the architecture. Creating an ADR here would record
  a decision that AD-069 already made.
- Optionally, map B and C's shim-absence case to `UNVERIFIABLE`. This is
  a **behaviour** change to governed statuses and is *not* recommended as
  part of the same fix; if pursued, it needs its own decision.

### 3.4 Deferred-items summary

| Item | Severity | Blocks Phase F | Recommendation |
|---|---|---|---|
| GR-16 venv exclusions | LOW | No | **KEEP DEFERRED** |
| `reproduction_runner` docstring | LOW / MED (record) | No | **FIX NOW** (docstring only; no ADR) |
| `ImportError` ungoverned | MEDIUM | No | **FIX NOW** (Path A only) + **amend AD-069 record**; no new ADR |

**None of the three blocks Phase F.**

---

## 4. Phase F readiness assessment

Sources read: `docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` (740
lines, tracked at C0) and
`docs/PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md` (untracked).

### 4.1 Does Phase F depend on Store extraction completion? — **NO**

The two tracks are **orthogonal**, and this was verified rather than
assumed:

- The Proposal explicitly forbids storage in the Phase F data path:
  `GateContext` is a values-only mapping — *"no callables, no lazy
  handles, no database connection, no path to recompute"* (§ line 88-89).
  Persistence is out of scope by design; `ArchiveWriter` (§3.5) writes
  filesystem artifacts and JSONL.
- Consistently, `ALLOWED_DEPENDENCIES["research"]` =
  `{data, statistics, governance, validation}` at
  `tools/check_import_boundaries.py:176` — **no `store` grant, and none
  needed.** Under the demand-driven growth rule (GR-03 / §5.3) this is
  the correct state: no importer, no grant.

**However, C0…C7 did benefit Phase F in one decisive way**: AD numbering
is now settled. AD-068/AD-069 are consumed, AD-061…AD-067 are reserved
*and discoverable in the AD file* (`:3098`), which is exactly the defect
GR-01 existed to repair. Phase F can cite its seven numbers without
collision risk.

**Store-extraction censuses in the Phase F documents still hold at
HEAD.** Both documents pin their evidence to HEAD `58908fe`, which is now
eight commits stale, and C5 modified two `core/governance/` files — so
this needed checking, not assuming:

| AD-067 / AD-063 census claim | At `58908fe` | At HEAD `02b55d3` | Verdict |
|---|---|---|---|
| Modules under `core/governance/` besides `__init__.py` | 13 | **13** | ✅ holds |
| `decision_recorder.py` export surface | 14 public names | **file unchanged** (`git diff` empty) | ✅ holds |
| `canonical_jsonl.py` | unchanged | **file unchanged** | ✅ holds |
| `core/governance/__init__.py` re-exports nothing | — | **file unchanged** | ✅ holds |

**None of AD-067's four amendment triggers fired during C0…C7.** C5
edited the *bodies* of `reconstruction_loader.py` and
`reproduction_runner.py` (import repointing only); it added no
governance module, relocated no chain-authority symbol, added no
re-export, and did not widen `canonical_jsonl`. **AD-063 and AD-067 may
be written as drafted, without re-derivation.**

### 4.2 Are any domain boundaries still ambiguous?

**Not ambiguous — but one is materially unenforced.**

**(a) `adapters/research/` is outside all mechanical governance — the one
that matters.** This is the intersection of two findings that were each
ruled non-blocking *in isolation* and are jointly significant:

- GR-17 established as fact that `check_repository` scans `core/` only
  (`:341`), and ruled it out of scope for the store work.
- Phase F places its **composition root** — `adapters/research/lifecycle_composer.py`,
  the module that holds Decision Chain authority by constructing
  `DecisionRecorder` and calling `compose_transition()` — precisely in
  that unscanned region (Resolution R-2).

Confirmed on disk: `adapters/research/` does not exist yet, and no
tooling would scan it if it did. The substitute is F-9's named-file AST
test. The Resolution discloses this honestly as *"a disclosure the
Proposal owes"* and states the substitute is weaker than the checker it
replaces. **The boundary is not ambiguous — it is defined and
deliberately unenforced by the general mechanism.** Phase F must not
land F-7 without F-9's scope covering `adapters/research/` by name.

**(b) `core/research/execution/` — not ambiguous.** `research` is already
mapped in `DOMAIN_OF_TOPLEVEL` at `:113`, and `_domain_of_file` keys off
the toplevel package only (`:244-255`). A new subpackage inherits the
`research` domain automatically; no mapping change is required and no
`UnmappedPackageError` will fire.

**(c) Authority vs. import boundaries — resolved in writing, unenforced
in code.** AD-067 exists specifically to record that *package boundaries
are not authority boundaries*. This is the correct resolution of a real
conceptual ambiguity, and it is explicit that Phase F ships **no**
mechanism to enforce it.

### 4.3 Are there missing ADRs before implementation? — **YES: all seven**

**AD-061 … AD-067 are drafted, resolved, and *unaccepted*.** F-0 —
*"Write AD-061 … AD-067 into `ARCHITECTURE_DECISIONS.md`… Docs only,
zero code"* — is **blocked**, and blocked on an artifact that does not
exist:

> **"The independent architecture review this resolution was
> commissioned against is not present in the repository, in this
> session's context, or anywhere on disk."** — Resolution §1.2

The Resolution refuses to self-certify, correctly: it states it *"does
not discharge the findings of an independent review… must not be cited
as evidence that Phase F has cleared independent review,"* and lists the
review as open item 1 of §7. Both Phase F documents are **Level 1
self-review only.**

This collides with a rule the repository has just finished enforcing on
itself. GR-05 and GR-08 established, and C2/C4 executed, the ordering
principle that **each ADR ships before the code it governs**. F-1 …
F-10 all cite AD-061 … AD-067. By the repository's own precedent, no
Phase F code may land while F-0 is blocked.

**No gap requiring a *new* ADR was discovered.** The seven drafted ADs
cover the architecture; §5 of the Resolution specifies their required
content clause by clause. The deficiency is **acceptance**, not
coverage.

### 4.4 Hidden risks from introducing the Research Execution Engine

| # | Risk | Basis | Severity |
|---|---|---|---|
| **H-1** | **F-0 rests on a review that does not exist.** Accepting seven ADs on a Level 1 self-review would violate the governing principle at the moment of its most consequential application | Resolution §1.2, §7.1 | **HIGH** |
| **H-2** | **Four amendment triggers, zero detection.** Any new `core/governance/` module, symbol relocation, `__init__.py` re-export, or widened `canonical_jsonl` silently invalidates F-9's containment evidence *while the test still passes* | AD-067 §4a; Resolution §7.5 — *"Nothing detects them"* | **HIGH** |
| **H-3** | **The repository has no CI.** No `.github/workflows`, no `.pre-commit-config.yaml`, no `.git/hooks/pre-commit`, no Makefile. Every governance guarantee — the 783-test suite, the strict xfail, T-1…T-8 — executes only when a human runs pytest | verified by `ls`/`find` | **HIGH** |
| **H-4** | **`reference_h4` would refuse.** Its directory holds `archive_manifest.json` **only** — no `experiment_results/`, confirmed on disk — so `ArchiveWriter`'s precondition refuses. Closing it is an additive `tools/` change or a dated human act, **never** a relaxation of F-4 | Proposal F-9; `ls research_archive/reference_h4/` | MEDIUM |
| **H-5** | **Two registries, no agreement check.** `ResearchRunner` reads both and populates neither; disagreement surfaces as a `run_sequence` preflight `KeyError`. Phase F ships no consistency check *by ruling* | AD-066; Resolution R-4 | MEDIUM |
| **H-6** | **`transition_records.jsonl` has never existed.** `find` → no such file anywhere. The Phase E chain machinery is built and unit-tested but **never exercised end-to-end**; F-10 is its first real run, and it is also the step that must produce the first genuine chain | verified | MEDIUM |
| **H-7** | **Both Phase F documents are pinned to a stale HEAD.** Their evidence is dated `58908fe`; HEAD is `02b55d3`. This audit re-verified the load-bearing censuses (§4.1) and they hold — but nothing *keeps* them true, and the obligation to re-derive recurs on every HEAD move | §4.1 | LOW–MED |
| **H-8** | **`ExperimentSpec`/`MeasurementBundle` closed field sets are pinned by test only.** A future field addition is a one-line change that no boundary mechanism would flag | Proposal F-1 | LOW |

---

## 5. Gate review

### A. Executive decision

> # ⛔ NOT READY
>
> **Blocked on exactly one item: F-0 acceptance of AD-061 … AD-067,
> which is blocked on an independent architecture review that does not
> exist in the repository or on disk.**

This verdict is **procedural, not technical.** It should be read
precisely:

**A.1 — The boundary-hardening milestone (C0…C7) is COMPLETE and of high
quality.** Ancestry is linear and unrewritten; the changed-file set
matches the plan exactly with no strays; the protected-hash fixture is
untouched; all 20 GR items are ruled with zero blocking items open; all
eight T-tests exist, execute, and landed in their planned commits; the
suite is green at 783/1/1 as reported. **On the merits of the work
under review, this is a pass.** Had the question been *"is C0…C7
complete?"*, the answer would be an unqualified yes.

**A.2 — The verdict is forced by the repository's own governing
principle.** *"The repository must never record a claim stronger than
the mechanism that enforces it."* Phase F's entry gate is F-0. F-0's
stated precondition is an independent review. That review does not
exist, and the Resolution — to its credit — refuses to pretend
otherwise. Declaring READY would record exactly the claim the principle
forbids, at the one gate where it matters most.

**A.3 — This document does not discharge that review either.** It is a
Level 1 completion audit of C0…C7 by a single pass. It must not be cited
as, or substituted for, the independent architecture review F-0
requires. Its findings on Phase F (§4) are readiness observations, not
review findings, and they do not continue the Resolution's R-numbering.

**A.4 — What would change the verdict.** Supplying the independent
review and completing F-0. Nothing in the repository state, the test
suite, the boundary posture, or the three deferred items stands in the
way. **On completion of C-3 through C-5 below, the verdict becomes
READY WITH CONDITIONS**, the conditions being H-2, H-3, and H-4.

### B. Remaining risks

**Blocking**

- **B-1 (H-1).** F-0 acceptance would rest on self-review. Both Phase F
  documents are Level 1.

**Non-blocking, live**

- **B-2 (H-2).** Four AD-067 amendment triggers are standing human
  obligations with no detection. The failure mode is a **green test
  falsely cited as containment**.
- **B-3 (H-3).** No CI. Every guarantee in §2 is enforced only by a
  human running pytest. This is the single highest-leverage unaddressed
  risk in the repository, and it is *cheap* to fix.
- **B-4 (H-4).** `reference_h4` lacks `experiment_results/`; F-10 cannot
  run against it until closed additively.
- **B-5 (H-6).** No `transition_records.jsonl` has ever been produced.
- **B-6 (§3.3).** `ImportError` ungoverned on the ETF-universe preload
  path. Compensated by T-3; not urgent, but real.
- **B-7 (§3.2).** `reproduction_runner`'s docstring asserts an isolation
  property the module does not have, now load-bearing per AD-069.
- **B-8 (§2.4 / C-2).** Eight commits, including the entire
  boundary-hardening milestone, exist only on one local disk.
- **B-9 (H-7).** Phase F evidence is dated to a stale HEAD; re-derivation
  is a recurring manual obligation.

### C. Required pre-Phase-F actions

**Must complete before any Phase F code lands**

- **C-1. Commit the Phase F Proposal.** It is the sole untracked file and
  it is the artifact the independent review must review. Leaving it
  untracked reproduces the exact defect GR-20 was raised to fix — C0
  tracked the two resolutions for precisely this reason and left the
  Proposal behind. *Docs only.*
- **C-2. Push `master` to `origin/master`.** Eight commits, fast-forward,
  zero divergence, zero conflict risk. Given this repository's history of
  total local loss, holding a completed milestone on one disk is an
  unnecessary and asymmetric risk. **Do this before anything else in
  this list.**
- **C-3. Commission and read the independent architecture review.** The
  hard blocker. Its findings continue the Resolution's numbering from
  **R-8** (the Resolution confirms R-1a did not consume R-8) and the
  header's review level is restated, never silently upgraded.
- **C-4. Re-derive AD-063/AD-067's censuses against the HEAD at which
  F-0 lands.** This audit verified they hold at `02b55d3` (§4.1); if HEAD
  moves again before F-0, repeat. Cheap: four `git` checks.
- **C-5. Execute F-0.** Write AD-061 … AD-067 with the Resolution §5
  clauses folded in. Docs only, zero code. AD-047 … AD-060 unedited.

**Should complete before Phase F code, cheap and independent**

- **C-6. Fix the `ImportError` Path A gap** (§3.3) and **amend AD-069's
  disclosure** to localize it. No new ADR.
- **C-7. Repair the `reproduction_runner` docstring** (§3.2). No new ADR.
- **C-8. Introduce CI** (B-3). Run pytest on push. Note that
  `tools/check_import_boundaries.py` **exits 1 at HEAD by design** — the
  5 known ETF violations under AD-068 — so CI must gate on **pytest**,
  where the posture is correctly encoded as a strict xfail, and must
  **not** gate on the checker's exit code. This distinction is easy to
  get wrong and would either break the build or silently disable the
  guard.

**May proceed in parallel with Phase F**

- **C-9.** Close `reference_h4`'s missing `experiment_results/`
  additively (a `tools/` change or a dated human act) — never by
  relaxing F-4's precondition.
- **C-10.** GR-16: no action. Deferred (§3.1).
- **C-11.** Optionally retire the vacuous
  `STILL_EMPTY_DOMAIN_MODULES` parametrization (§2.3) — cosmetic,
  pre-existing, out of milestone scope.

### D. Recommended next commit sequence

Docs and fixes first; **no Phase F code until C-5 lands.** Every commit
below leaves the suite green and is independently revertable, per the
property C0…C7 established.

| # | Commit | Files | Gate discharged |
|---|---|---|---|
| **—** | `git push origin master` (**do this first**) | — | C-2 / B-8 |
| **C8** | `docs: commit the Phase F Research Execution Engine proposal as the review basis` | `docs/PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md` | C-1, completes GR-20 |
| **C9** | `docs: localize the ungoverned ImportError path in AD-069's disclosure` | `docs/ARCHITECTURE_DECISIONS.md` | C-6 (record half), corrects GR-19 |
| **C10** | `governance: govern ImportError on the pinned-universe load path` | `core/governance/reproduction_runner.py` + a test asserting `UNVERIFIABLE` on Path A | C-6 (fix half) |
| **C11** | `governance: correct the reproduction_runner isolation docstring` | `core/governance/reproduction_runner.py` | C-7 / B-7 |
| **C12** | `ci: run the test suite on push` | `.github/workflows/*.yml` | C-8 / B-3 |
| **⛔** | **GATE — independent architecture review read; R-8+ folded in; review level restated** | `docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` | **C-3 / B-1** |
| **C13** | `docs: accept AD-061…AD-067 (Phase F Research Execution Engine)` | `docs/ARCHITECTURE_DECISIONS.md` — **docs only, zero code** | **C-5 = F-0** |
| **C14+** | Phase F implementation, F-1 → F-10 in roadmap order | per Proposal §7 | — |

**Ordering rationale, traceable to this repository's own rulings:** the
push precedes everything because it is free and the loss it prevents is
total. C8 precedes the review because a reviewer must review a tracked
artifact (GR-20). C9–C11 precede the gate because they are independent
of Phase F and would otherwise be forgotten behind it. C12 precedes F-1
because Phase F is the largest code addition since Phase E and is the
worst time to have no automated gate. **C13 precedes all Phase F code
because C2 and C4 established that an ADR ships before the code it
governs** — the milestone this review is auditing is the precedent, and
Phase F is bound by it.

---

## 6. Audit metadata

**Verified by execution:** full suite (783/1/1, twice, second run with
`-rs` to identify the skip); T-3 in isolation; `git log`, `git status
--porcelain`, `git rev-list --left-right --count`, `git log --merges`,
`git diff --name-status`, `git ls-tree` module censuses at both commits,
`git log -S` per T-test, `git cat-file -t` per archive pin;
`tools/check_import_boundaries.py`; `issubclass(ModuleNotFoundError,
OSError)`; filesystem checks for venvs, CI config, `reference_h4`,
`transition_records.jsonl`, and the Phase F target directories.

**Verified by reading:** `reproduction_runner.py:1-240` in full;
`check_import_boundaries.py` domain tables and file walk;
`test_store_extraction.py` T-2/T-3 bodies; the resolution's §3–§5 and
§7; the Phase F Resolution §0–§1.2, §5–§7; the Proposal's roadmap table
and §2.

**Not verified:** that the suite is green at each intermediate commit
C1…C6 individually (the plan asserts it; only HEAD was run). That
`core/store` behaviour is byte-identical to the pre-move originals
beyond what T-4/T-7 assert. Any claim about the content of the absent
independent review.

**Production code modified by this review: none.**
**Architecture decisions created by this review: none.** §3.3 recommends
amending AD-069's existing disclosure; §4.3 finds the seven drafted ADs
cover the architecture, with acceptance — not coverage — as the gap.
