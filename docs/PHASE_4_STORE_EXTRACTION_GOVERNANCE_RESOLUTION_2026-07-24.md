# Governance Resolution — `core.store` Extraction and ETF/Data Boundary Hardening

**Date:** 2026-07-24
**Author role:** Principal Governance Architect
**Subject:** the uncommitted working tree at `master` HEAD `61d001a` comprising
boundary-hardening step 1 (ETF/Data split) and step 2 (`core.store` extraction)
**Status:** RULING — binding on the working tree named above
**Review level:** **Level 1 (single reader, repository access).** This document
does **not** discharge the independent-review requirement recorded as absent at
[PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md:82](docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md)
and must never be cited as doing so.
**Scope limit:** governance decisions only. This document rules on findings,
numbering, decomposition, permissions, retirement, test policy, and merge
readiness. It proposes **no implementation detail** beyond what a governance
ruling requires, and **no code was modified** in producing it.

---

## 0. Provenance of the two reviews — and a defect in that provenance

The two reviews ruled on here are:

| Ref | Title | Origin | Retrieved from |
|---|---|---|---|
| **Review 1** | *Architecture Review: `core.store` Extraction (AD-061)* | session `local_6e408445` | session transcript |
| **Review 2** | *Architecture review evaluation* | session `local_119768f6` | session transcript |

**GR-20 (raised here). Neither review exists as a repository artifact.** Both
were searched for before this ruling: not in `docs/`, not untracked in the
working tree, not in any session scratchpad. They exist only as conversation
transcripts, which are not versioned, not hash-protected, and not citable by
`file:line`. Review 2 itself hit this wall — its §0 records that it could not
evaluate Review 1's F-1, F-2, and F-4 by label because it could not read
Review 1. It then evaluated a *paraphrase* supplied in-chat and correctly
flagged that its labels might not reconcile.

This is the same pattern project memory already records against Phase F:
thorough self-review, no durable review artifact. **Ruling: the reviews are
admitted as evidence for this resolution and their substance is preserved in
§2 below, but no future document may cite "the architecture review" for this
work without pointing at a committed file.** The finding register in §2 is
hereby the citable record.

**Label-space note.** Review 1's rendered text numbers its findings **F-3, F-4,
F-5** with no F-1 or F-2 present. Those two labels are unaccounted for. This
resolution therefore **discards both reviews' local labels** and re-registers
every finding under a single `GR-nn` space. Where a ruling below cites `F-3`,
`F-C`, `N-1` etc., it names the source review's label for traceability only.

---

## 1. Verification basis

Every ruling in §2 rests on evidence re-derived directly from the working tree
by this author, not on either review's assertion. Measurements taken
2026-07-24 against the tree described above:

| Fact | Result |
|---|---|
| Suite state | `1 failed, 768 passed, 1 skipped in 58.10s` |
| Failing test | `tests/test_import_boundaries.py::test_real_repository_has_no_boundary_violations` (5 ETF violations) |
| `ALLOWED_DEPENDENCIES` delta | `data: {} → {store}`; `statistics: {} → {store}`; `store` added to all seven non-kernel domains |
| Accepted AD ceiling | **AD-060** (`docs/ARCHITECTURE_DECISIONS.md`); AD-052…AD-055 retired at line ~2849 |
| Working tree writes | `### AD-061` |
| Phase F reservation | AD-061…AD-067, asserted non-colliding, at `PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` §5 close |
| `AD-061` citation sites | **9 sites in 6 files** outside `ARCHITECTURE_DECISIONS.md` |
| `AD-06[1-7]` in Phase F docs | **124 occurrences** across two documents |
| §5 dependency table | six domains; **no** ETF row/column, **no** Store row/column |
| §5 Enforcement clause | "…by top-level package name, **no AST-level cleverness required**" (line 554) |
| §5 forbidden entries | "**Statistics → anything.** The single hard rule (§4.3)"; "**Data → anything.** The foundation never calls upward" |
| `core.store` importers under `core/` | 4 sites in 3 files (2 governance, 2 shim) |
| Protected fixture | 36 entries; 9 `.py`, all importing a shim; **none** in `git status` |
| Archive commit pins | 3 (`07f0da3`, `19771d4`, `8831d54`), all `git cat-file -t` → `commit` |
| Pinned scripts' imports | all three pin `daily_etf_universe_update.py` importing **both** legacy paths (lines 58–59) |
| `xfail` precedent in repo | **none** |
| CI | **none** (`.github/` does not exist) |
| `PRAGMA foreign_keys=ON` | set at `core/store/connection.py:30`; **asserted in no test** |
| `check_repository()` default root | `core/` only — `adapters/` is never scanned |

Two experiments were run to settle claims the reviews disagreed on. Both were
executed in-memory against a loaded copy of the checker; **the repository was
not modified.**

**Experiment A — grant-set narrowing.** `ALLOWED_DEPENDENCIES` was narrowed
in memory and `check_repository()` re-run:

```
grant store to {governance}          -> 7 violations (2 new, both store-edge):
      core/market_data/persistence/database.py:19    data -> store
      core/market_data/persistence/migrations.py:12  data -> store
grant store to {governance, data}    -> 5 violations (0 store-edge)
grant store to {governance,data,etf} -> 5 violations (0 store-edge)
```

**Experiment B — `sys.modules` shadowing.** A synthetic worktree containing its
own `core/market_data/persistence/database.py` was placed at `sys.path[0]` and
a module performing the legacy import was `exec_module`'d, exactly as
`_load_module_from_worktree` does:

```
core.__path__  = ['D:\Claude\etf_platform\core']
resolved from  : D:\Claude\etf_platform\core\market_data\persistence\database.py
worktree marker: <absent — HEAD's shim was bound>
bound connect is core.store.connection.connect: True
```

---

## 2. Finding register and rulings

Twenty findings. **13 ACCEPT · 4 ACCEPT WITH MODIFICATION · 3 REJECT.**

| ID | Finding | Source | Ruling | Priority |
|---|---|---|---|---|
| GR-01 | AD-061 collides with Phase F's AD-061…067 reservation | R2 `N-1` | **ACCEPT WITH MODIFICATION** | Blocking |
| GR-02 | AD-061 denies the permission change it makes | R1 `F-3`, R2 `F-3` | **ACCEPT** | Blocking |
| GR-03 | `store` granted to all seven domains, ahead of demonstrated need | R1 `F-4`, R2 `F-C` | **ACCEPT WITH MODIFICATION** | Blocking |
| GR-04 | Step 1 and step 2 are one undifferentiated diff | R1, R2 `F-A` | **ACCEPT** | Blocking |
| GR-05 | The ETF/Data split has no ADR | R1, R2 `F-B` | **ACCEPT** | Blocking |
| GR-06 | Shims are load-bearing for pinned-commit reproduction | R1 `F-5`, R2 `F-5` | **ACCEPT** | Blocking |
| GR-07 | The documented shrink condition instructs a destructive act | R1 `F-5`, R2 `F-5` | **ACCEPT** | Blocking |
| GR-08 | §5 is never amended, though AD-061 claims it is | R2 `F-D` | **ACCEPT** | Blocking |
| GR-09 | §5's Enforcement clause forbids the AST attribution now used | R2 `F-D` | **ACCEPT** | Blocking |
| GR-10 | Stale documentation pointers to moved code | R1 §8, R2 `F-D` | **ACCEPT WITH MODIFICATION** | Split |
| GR-11 | A permanently red test ships as the deliverable | R2 `N-2` | **ACCEPT** | Blocking |
| GR-12 | Regression coverage is incomplete | R1 `T-1…T-6`, R2 `T-1…T-5` | **ACCEPT WITH MODIFICATION** | Split |
| GR-13 | Reverse the order: land step 2 before step 1 | R1 `S-1` | **REJECT** | — |
| GR-14 | Shorten duplicated docstring prose | R1 `S-3` | **REJECT** | — |
| GR-15 | Rename `tests/test_database.py` | R1 | **ACCEPT** | Non-blocking |
| GR-16 | `_python_files()` rglobs without venv/vendor skip | R2 | **ACCEPT** | Deferred |
| GR-17 | `check_repository` never scans `adapters/` | R2 | **ACCEPT** (as fact) | Out of scope |
| GR-18 | "`data` has no `core.store` importer" | R2 `F-C` premise | **REJECT** | — |
| GR-19 | `ImportError` from shim deletion escapes uncaught | R2 `F-5` | **ACCEPT** | Blocking |
| GR-20 | Neither review is a repository artifact | raised here | **ACCEPT** | Process |

---

### GR-01 — AD number collision · **ACCEPT WITH MODIFICATION**

**Why accepted.** Verified. `PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` §5
states as a re-confirmed fact that `ARCHITECTURE_DECISIONS.md` "contains **no
occurrence** of AD-061 … AD-067." Committing the working tree makes that
statement false and creates two distinct AD-061s cited from six files.

**Where I modify Review 2.** Review 2 ruled the reservation should be honored
on cost grounds and stopped there. The cost asymmetry is real and I confirm it
— **9 citation sites in 6 files** for this change versus **124 occurrences**
across the two Phase F documents — but cost is not the governing reason. The
governing reason is that a reservation, once recorded in a governance
document, binds until it is withdrawn by decision; whether Phase F's F-0 is
blocked bears on Phase F's *acceptance*, not on its *claim to the numbers*.

**The modification.** Review 2 treated the collision as a numbering accident.
It is a numbering **system** defect: the reservation lives only in an
unaccepted proposal document, invisible to anyone reading
`ARCHITECTURE_DECISIONS.md` — which is exactly how this collision happened.
The ruling therefore adds a requirement Review 2 did not raise: the
reservation must be written into `ARCHITECTURE_DECISIONS.md` itself.
**Precedent is direct** — the "AD-052 … AD-055 are retired, not available"
block at line ~2849 is that same instrument, already accepted in this
repository.

**Ruling.** ETF/Data split takes **AD-068**. `core.store` takes **AD-069**.
AD-061…AD-067 remain reserved to Phase F. A reservation block is added to
`ARCHITECTURE_DECISIONS.md` recording the reservation, its source document,
and that reserved numbers are released only by recorded decision.

- **Artifacts affected:** `docs/ARCHITECTURE_DECISIONS.md` (new reservation
  block + both new AD headings); `core/store/connection.py:2`,
  `core/store/migrations.py:2`, `core/market_data/persistence/database.py:2`,
  `core/market_data/persistence/migrations.py:2`,
  `tests/test_store_extraction.py:1,102,135`,
  `tools/check_import_boundaries.py:60,141`.
- **ADR impact:** creates the numbering for AD-068 and AD-069; amends no
  accepted AD; leaves Phase F's assertion true with **zero** edits to Phase F.
- **Section 5 impact:** none.
- **Reproduction impact:** none — comment and docstring text only.

---

### GR-02 — AD-061 denies its own permission change · **ACCEPT**

**Why accepted.** Verified against the diff. AD-061 closes: *"amends
docs/PLATFORM_ARCHITECTURE_V1.md Section 5's dependency table by addition
only; no existing edge changes direction or permission."* Both clauses are
false. `data` and `statistics` moved from `frozenset()` to
`frozenset({STORE_DOMAIN})` — two rows whose permission set was empty are now
non-empty, and they are precisely the two rows §5 names as absolute. "Addition
only" is true of the table's *shape* and false of its *permission content*: a
column every row is granted loosens six rows at once.

In a repository with no CI, where ADRs are the governing artifact and the
reader is a human auditor, an ADR that misstates its own effect on the
normative table is the highest-consequence defect available — it is the
artifact a future reader trusts *instead of* re-deriving the diff.

- **Artifacts affected:** `docs/ARCHITECTURE_DECISIONS.md` (AD-069's
  consequences section).
- **ADR impact:** the offending sentence is deleted and replaced by an
  explicit permission ledger. That ledger is only writable as a true statement
  **after GR-03 is applied** — GR-03 is a precondition of GR-02's fix, not an
  independent nicety.
- **Section 5 impact:** forces GR-08. The ADR may not claim an amendment that
  does not exist in the tree.
- **Reproduction impact:** none directly. Indirectly material: an ADR that
  understates permission changes is the mechanism by which an auditor loses
  confidence in the gate record generally.

---

### GR-03 — Grant breadth · **ACCEPT WITH MODIFICATION**

**Why accepted.** `store` was granted to all seven non-kernel domains. The
demonstrated demand under `core/` is four import sites in three files, in two
domains. `core/statistics/` imports nothing from `core` at all; `core/reporting`
is forbidden even `pathlib` and `os` by its own boundary test. Granting five
domains a storage edge no code uses is permission ahead of need. Worse, it is
**internally inconsistent within the same commit**: AD-061 clause 3 argues at
length that `store` must stay outside the kernel so `kernel -> store` remains
flaggable — "the kernel is a pure value vocabulary and must not acquire I/O" —
and then grants that exact I/O edge to `statistics`, which §4.3 defines by the
identical purity property. The change refutes its own reasoning and does not
disclose it.

**Where I modify Review 2 — its prescription is wrong and would break the
change.** Review 2 ruled the grant should go to **`governance` only**, with
`data` "added when and if a `core/market_data` module actually opens a
connection." Experiment A falsifies this. Under a governance-only grant the
checker reports **two new violations**, and they are the shims themselves:

```
core/market_data/persistence/database.py:19    data -> store
core/market_data/persistence/migrations.py:12  data -> store
```

A `core/market_data` module *already* imports `core.store` — the re-export
shim that Review 2 elsewhere (GR-06) correctly rules permanent. Review 2's
narrowing would therefore make the artifact it mandates a boundary violation.
Review 1's prescription — `data` **and** `governance` — is the correct one and
Experiment A confirms it produces exactly the 5 pre-existing ETF violations
and no store-edge violation.

**A second modification, raised by neither review.** Both reviews treat
"`data -> store`" and "`statistics -> store`" as the same kind of relaxation.
They are not, and the distinction must be recorded or the next reader will
re-litigate it:

- **`data -> store` is not upward.** §5 forbids "Data → anything" on the
  stated rationale that "the foundation never calls upward." `store` sits
  *below* Data — it is substrate, layer −1. The edge is consistent with the
  rule's rationale while violating its literal wording. §5's forbidden entry
  must be reworded to *"Data → anything above it"* and Store given its layer.
- **`statistics -> store` is denied on different grounds entirely** — not
  layering, but **purity**. §4.3 defines Statistics as a pure computational
  library. Statistics is refused I/O for the same reason the kernel is, and
  that is the reason to record, because it is the reason that survives future
  layer changes.

**Ruling.** `store` is granted to **`data` and `governance` only**.
`statistics`, `etf`, `validation`, `research`, `reporting`, and `kernel` keep
`frozenset()` with respect to `store`. The grant list is demand-driven and
grows only by recorded decision — the same shrink-inventory discipline the
change already applies to `ETF_SYMBOLS_BY_MODULE` and to the shims.

- **Artifacts affected:** `tools/check_import_boundaries.py`
  (`ALLOWED_DEPENDENCIES`); `tests/test_import_boundaries.py`
  (`test_every_domain_may_depend_on_store` is retired and replaced — see T-5,
  T-6); `docs/ARCHITECTURE_DECISIONS.md` (AD-069).
- **ADR impact:** AD-069 records the narrow grant, the demand-driven growth
  rule, and the two distinct denial grounds above. This is what makes GR-02's
  replacement sentence true.
- **Section 5 impact:** Store column added; only Data and Governance carry ✅.
  Statistics' forbidden entry is **preserved intact** — the single hard rule
  survives this change untouched, which is the whole point of the narrowing.
  Data's forbidden entry is reworded per above.
- **Reproduction impact:** none at runtime. Governance-material: under the
  broad grant a future `core/statistics` module opening a database is
  architecturally legal and silently passes the checker, which would
  contaminate the purity claim that reproducibility arguments rest on.

---

### GR-04 — Bundling · **ACCEPT**

**Why accepted.** The tree is one diff containing two independent
architectural decisions sharing exactly two files
(`tools/check_import_boundaries.py`, `tests/test_import_boundaries.py`).
Independence is verified: `core/store/*` references no ETF symbol, and the
symbol-attribution mechanism is invoked nowhere in the store path. The single
interaction, `test_store_is_not_a_route_from_a_domain_into_etf`, is a test, not
a dependency.

The cost is not stylistic. **Step 1 ships a failing test by design; step 2 is
green.** Bundled, the only rollback handle is a revert of the composite — so a
defect in the ETF attribution logic (the novel, unproven mechanism) forces
reverting the store extraction (a verbatim relocation guarded by an identity
assertion). The riskiest and safest parts of the change are welded to one
revert handle.

- **Artifacts affected:** all 16 paths in the working tree; the split is
  mechanical and confined to `ALLOWED_DEPENDENCIES` and two module docstrings.
- **ADR impact:** forces GR-05 — each step gets its own AD.
- **Section 5 impact:** each step's §5 amendment ships with its own ADR
  (ETF row/column with AD-068; Store row/column with AD-069).
- **Reproduction impact:** none directly; materially improves the blast radius
  of a revert touching `reproduction_runner.py`.

---

### GR-05 — No ADR for the ETF/Data split · **ACCEPT**

**Why accepted.** `docs/ARCHITECTURE_DECISIONS.md` contains no decision record
for step 1. The only occurrences of ETF-split vocabulary are inside AD-061's
prose, as passing context for a *different* decision. Five substantive
decisions are unrecorded and none is derivable from AD-061:

1. **ETF is a domain distinct from Data** — a change to §5's row/column set.
2. **No domain may depend on ETF** — verified: `ETF_DOMAIN` appears in no
   domain's allowed set. This is a novel rule with no §5 precedent; §5's
   forbidden list contains no "nothing may depend on X" entry.
3. **Domain attribution by imported symbol, not module path** — a change to
   the checker's *identification method* (see GR-09).
4. **The repository test stays red as a deliverable** (superseded in mechanism
   by GR-11, but the underlying decision still requires recording).
5. **`ETF_SYMBOLS_BY_MODULE` is a hand-maintained inventory** with a shrink
   condition and no mechanism guaranteeing its accuracy (see T-1).

- **Artifacts affected:** `docs/ARCHITECTURE_DECISIONS.md` (new AD-068);
  `docs/PLATFORM_ARCHITECTURE_V1.md` §5.
- **ADR impact:** AD-068 is created, numbered **below** AD-069, and lands
  before any step-1 code. AD-069's motivation section may then cite it as an
  accepted decision rather than as uncommitted work.
- **Section 5 impact:** ETF row and column added; the "nothing may depend on
  ETF" forbidden entry added.
- **Reproduction impact:** none.

---

### GR-06 — Shims are load-bearing for reproduction · **ACCEPT**

**Why accepted.** Both reviews raised this; Experiment B confirms it, and it is
the most consequential finding in the set. AD-061 gives exactly one reason for
the shims — hash-protected files cannot be edited. That reason is factually
correct (9 protected `.py` files, all importing a shim) but it is **not the
binding one.**

`_load_module_from_worktree` prepends the worktree to `sys.path` and
`exec_module`s the pinned script. But `sys.modules['core']` is already
populated with **HEAD's** package — the runner *is* `core.governance.
reproduction_runner`. Python resolves `core.market_data.persistence.database`
through `core.__path__`, so a pinned script's legacy import binds **HEAD's
shim**, never the worktree's copy. There is no isolation: `grep -rn
"sys.modules" core/` returns nothing.

This is live, not theoretical. All three archived cycles pin resolvable
commits, and all three pin `daily_etf_universe_update.py`, whose lines 58–59
import **both** legacy paths. The shims are runtime infrastructure for
reproduction, independent of hash protection — and they would remain so even
if every protected file were retired tomorrow.

- **Artifacts affected:** `core/market_data/persistence/database.py`,
  `core/market_data/persistence/migrations.py` (both permanent);
  `core/governance/reproduction_runner.py` (the mechanism, unmodified);
  `docs/ARCHITECTURE_DECISIONS.md` (AD-069).
- **ADR impact:** AD-069 must record the reproduction dependency as the
  **primary** shim rationale, naming the `sys.modules`/`core.__path__`
  mechanism explicitly, with hash protection demoted to the secondary reason.
- **Section 5 impact:** none. The shim's `data -> store` edge is the edge
  GR-03 grants; §5 needs no special case for it.
- **Reproduction impact:** **decisive.** Deleting the shims converts every
  archived cycle's reproduction from a verifiable result into a crash. This is
  the finding that sets the retirement policy in §6.

**Disclosure carried forward.** `reproduction_runner`'s own docstring claims
pinned code comes "never from `repo_root`'s current HEAD copy." That is
accurate for the experiment script loaded by file path and **inaccurate for
the `core.*` modules it imports.** This is a pre-existing defect, not
introduced by this change — but this change makes the repository *depend* on
it, which converts a latent inaccuracy into a load-bearing one. AD-069 must
disclose it. Repairing it is **out of scope** for this change and is recorded
here as an open item.

---

### GR-07 — The shrink condition instructs a destructive act · **ACCEPT**

**Why accepted.** `test_legacy_shim_importers_are_exactly_the_frozen_files`
asserts and instructs (`tests/test_store_extraction.py:140`):

> "no frozen file imports the shims any more -- delete
> `core/market_data/persistence/database.py` and `migrations.py` and this test
> with them"

That instruction is derived solely from the current tree. Reproduction targets
*historical* commits, and per GR-06 the pinned population is the only one that
matters. A maintainer who retires the frozen scripts, follows the message,
deletes both shims, and runs the suite gets **green** — while reproducibility
of `reference_v1`, `reference_v2_h1`, and `reference_h3` is silently
destroyed. A test that instructs a destructive act on a false premise is worse
than no test.

- **Artifacts affected:** `tests/test_store_extraction.py` (the assertion
  message and, per T-3, the predicate); `docs/ARCHITECTURE_DECISIONS.md`.
- **ADR impact:** AD-069 records the corrected retirement condition verbatim
  as ruled in §6.
- **Section 5 impact:** none.
- **Reproduction impact:** this finding *is* the reproduction impact. §6 is
  its discharge.

---

### GR-08 — §5 was never amended · **ACCEPT**

**Why accepted.** `docs/PLATFORM_ARCHITECTURE_V1.md` is not in `git status`.
Its §5 table still lists six domains; the checker now enforces nine. Every
violation message the checker emits ends *"forbidden per
docs/PLATFORM_ARCHITECTURE_V1.md Section 5"* — and §5 contains no ETF row, no
Store row, and nothing about symbol attribution. **The error message directs
the reader to a document that cannot explain the failure**, five times per run.
AD-049 part 2 already ruled that §5's table wins over contradicting prose;
leaving the table itself contradicted by the tool lets an auditor argue every
boundary claim in the repository is unenforced.

- **Artifacts affected:** `docs/PLATFORM_ARCHITECTURE_V1.md` §5 (table,
  forbidden-dependency list, Enforcement clause).
- **ADR impact:** the amendment ships **in the same commit as its ADR** —
  ETF row/column with AD-068, Store row/column with AD-069. Neither ADR may
  assert an amendment in a commit that does not contain it.
- **Section 5 impact:** this finding *is* the Section 5 impact; §5's final
  target shape is given in §5 of this document.
- **Reproduction impact:** none.

---

### GR-09 — §5's Enforcement clause contradicts the new checker · **ACCEPT**

**Why accepted.** §5 line 554 states the check is "a matter of scanning
`import` statements by top-level package name, **no AST-level cleverness
required**." The checker is now a per-alias AST symbol attributor with an
`ImportRef` dataclass. The normative document does not merely omit the new
mechanism — it **actively disclaims** it. This is sharper than GR-08: the
change contradicts a stated design constraint of the document it claims to
enforce, with no recorded decision.

- **Artifacts affected:** `docs/PLATFORM_ARCHITECTURE_V1.md` §5 Enforcement
  clause item 2; `tools/check_import_boundaries.py`.
- **ADR impact:** AD-068 records symbol-level attribution as a deliberate
  departure, with its justification: step 1 does not move files, so the ETF
  domain cannot be identified by path alone. The Enforcement clause is amended
  to permit symbol attribution **for domains not yet separated by package
  path**, and to state that the departure ends when the split is real.
- **Section 5 impact:** direct — the Enforcement clause is amended.
- **Reproduction impact:** none.

---

### GR-10 — Stale documentation pointers · **ACCEPT WITH MODIFICATION**

**Why accepted.** Verified. The two reviews produced **different, partly
disjoint** lists; the union is authoritative.

**The modification — the two lists are merged and re-tiered.** Review 2's list
omits `migrations/README.md`, which Review 1 found and which I rule
**blocking**, not cosmetic. It is the migration-policy document — the "frozen
once applied" rule that `core/store/migrations.py` cites in its own comment —
and its line 3 points `run_migrations` at a module that no longer contains it.
A policy document that misdirects the reader to the wrong mechanism is a
governance artifact in error, not a stale link.

| Pointer | Tier |
|---|---|
| `migrations/README.md:3` — `run_migrations` location | **Blocking** (ships in C5) |
| `docs/BASELINE_STATUS.md:234` — attributes `isolation_level=""` to the old path | Non-blocking (C7) |
| `docs/PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md:41,550-551` — line-anchored deep links into what is now shim docstring | Non-blocking (C7) |
| `docs/PHASE_4_ARCHITECTURE_AMENDMENT_V1.md:273`, `_V1_1.md:316` — name the old `run_migrations` path | **Not to be changed** |

**Ruling on the dated records.** Review 1 was right and Review 2 was wrong to
list `PHASE_4_ARCHITECTURE_AMENDMENT_V1.md:273` and `_V1_1.md:316` for repair.
These are **dated architecture records**; retrofitting them falsifies the
historical record. They are correct as of their date and stay untouched.
`BASELINE_STATUS.md` and the `_V1_1.md` deep links are borderline — they are
status/navigation aids rather than dated findings — and get a parenthetical
pointer, not a rewrite.

- **Artifacts affected:** as tabulated.
- **ADR impact:** none.
- **Section 5 impact:** none.
- **Reproduction impact:** none.

---

### GR-11 — A permanently red test ships as the deliverable · **ACCEPT**

**Why accepted.** Measured: `1 failed, 768 passed, 1 skipped`. The failure is
deliberate and the module docstring declares it. The **intent is correct** and
should be recorded as such: making pre-existing coupling fail loudly and
enumerably, rather than quietly re-blessing it, is the right call, and the
paired green inventory test is good design. The **mechanism is wrong.** A bare
failing assertion, in a repository with no CI where `pytest` is the only gate:

- destroys `pytest -q` as a pass/fail signal permanently, for everything
  unrelated to ETF;
- makes a second, real regression in that file indistinguishable from the
  intended failure at the summary line;
- has no forcing function — nothing announces when it should go green;
- and trains the only human gate to ignore red output.

- **Artifacts affected:**
  `tests/test_import_boundaries.py::test_real_repository_has_no_boundary_violations`
  and the module docstring.
- **ADR impact:** AD-068 records decision 4 (§GR-05) in its corrected form —
  the coupling is inventoried, not discharged, and the marker is the record of
  that posture.
- **Section 5 impact:** none.
- **Reproduction impact:** none.
- **Ruling detail:** see §7. Note there is **no `xfail` precedent anywhere in
  this repository**, so AD-068 introduces the convention and must say so.

---

### GR-12 — Incomplete regression coverage · **ACCEPT WITH MODIFICATION**

**Why accepted.** Both reviews found real gaps. Existing coverage is genuinely
good — store neutrality, the two-primitives scope fence, shim identity by `is`
rather than `==`, importer-set derivation from the hash fixture rather than
restatement, and nine checker tests. The gaps are nonetheless material, and
one of them (T-1) guards a **false-success** mode, which is strictly worse
than a false failure.

**The modification — the two reviews' `T-n` labels collide and are discarded.**
Review 1's `T-1` is the reproduction-path test; Review 2's `T-1` is the symbol
existence test and its `T-2` is the reproduction-path test. Anyone citing
"T-1" against these documents would be ambiguous. §7 issues a single
renumbered set of **eight** required tests, and rejects one.

- **Artifacts affected:** `tests/test_import_boundaries.py`,
  `tests/test_store_extraction.py`, `tests/test_database.py`.
- **ADR impact:** T-3's archive-pin predicate is named in AD-069 as the
  mechanical form of the retirement condition.
- **Section 5 impact:** T-5 and T-6 are the executable form of §5's Store
  column as narrowed by GR-03.
- **Reproduction impact:** T-2 and T-3 are the only executable guards on
  GR-06 and GR-07. Without them the retirement policy in §6 is prose only.

---

### GR-13 — "Land step 2 before step 1" · **REJECT**

Review 1 recommended reversing the order, on the grounds that step 2 does not
depend on step 1 and that step 1 ships red.

**Repository evidence.** The independence premise is **true** and I have
adopted it elsewhere (GR-04): `core/store/*` references no ETF symbol and the
attribution mechanism is absent from the store path. The *conclusion* does not
follow, on three grounds:

1. **The stated motive is discharged by GR-11.** Review 1's argument is that
   reversing "keeps the suite fully green through C1–C4" by deferring the red
   test. Under the accepted `xfail(strict=True)` ruling, step 1 **is** green
   when it lands. The reason to reorder no longer exists.
2. **AD-069's own rationale runs the other way.** Its context paragraph reads
   "Boundary-hardening step 1 (the ETF/Data split) made the cost visible… the
   checker reports three `data -> etf` violations inside it." Landing step 2
   first leaves an accepted ADR citing an unrecorded, undecided change as its
   context — the precise defect GR-05 exists to close. Review 1 anticipated
   this and proposed rewriting AD-069's motivation to stand alone; that is a
   real option, but it trades a true, verifiable causal record for a weaker
   one to buy an ordering benefit that GR-11 already delivers.
3. **Numbering.** GR-01 assigns AD-068 to the ETF split and AD-069 to store.
   Landing AD-069 before AD-068 puts the decision record out of order in the
   file for no remaining benefit.

**Ruling.** Step 1 fully precedes step 2, as Review 2 sequenced it.

---

### GR-14 — "Shorten duplicated docstring prose" · **REJECT**

Review 1 observed that `core/store/__init__.py`'s docstring, both relocation
preambles, and AD-061's shim section restate the same facts, and recommended
the module docstrings point at the ADR instead of paraphrasing it.

**Repository evidence.** The observation is accurate; the recommendation is
refused on governance grounds.

1. **The redundancy is the repository's established house style, not drift.**
   `core/governance/reconstruction_loader.py:8-17` carries an equivalent
   multi-line rationale preamble restating accepted ADR content, as do the
   Phase E modules. Singling out `core/store` for compression would make it
   the outlier.
2. **In a repository with no CI, prose at the call site is the enforcement
   surface a human actually reads.** The shim docstrings' "**No new code may
   import from here**" is the warning a maintainer sees when they open the
   file; an ADR cross-reference is one they must choose to follow.
3. **GR-06 and GR-07 require these docstrings to grow, not shrink.** The
   reproduction rationale and the corrected retirement condition must be
   legible at `core/market_data/persistence/database.py`, which is where
   someone contemplating deletion will be standing.

**Ruling.** No prose reduction. Review 1's underlying concern — that the same
fact stated in four places can drift — is real and is addressed instead by T-8
(shim surface) and T-3 (archive-pin predicate), which make the load-bearing
claims mechanical rather than merely repeated.

---

### GR-15 — Rename `tests/test_database.py` · **ACCEPT**

**Why accepted.** The file's subject moved to `core/store/connection.py`; the
name now points at a shim. It is not hash-protected. Verified that it already
exercises `core.store.connection` transitively through the repointed `conn`
fixture, so the rename records a coverage relationship that is already true.

- **Artifacts affected:** `tests/test_database.py` →
  `tests/test_store_connection.py`.
- **ADR impact:** none. · **Section 5 impact:** none. · **Reproduction
  impact:** none.
- **Sequencing:** lands in C6 with T-4, which adds the missing
  `foreign_keys` assertion to the same file. Non-blocking for merge.

---

### GR-16 — `_python_files()` lacks venv/vendor exclusions · **ACCEPT (deferred)**

**Why accepted.** Latent only — no `.venv`, `node_modules`, or `build`
directory exists under the scanned root today, which is why the checker runs
clean. The failure mode if one appears is an `UnmappedPackageError` crash or a
flood of spurious violations. Real, but not triggered by this change and not
caused by it.

- **Artifacts affected:** `tools/check_import_boundaries.py` (`skip_dirs`).
- **ADR impact / Section 5 impact / Reproduction impact:** none.
- **Ruling:** deferred past this milestone. Recorded here so it is not
  rediscovered as novel.

---

### GR-17 — `check_repository` never scans `adapters/` · **ACCEPT as fact, out of scope**

**Why accepted as fact.** Verified: `check_repository()` defaults to `core/`,
so `adapters/` — which contains `adapters/cli/main.py`, a repointed caller,
and `adapters/research/lifecycle_composer.py`, which Phase F R-2 identifies as
holding Decision Chain authority — is unchecked. Confirmed independently
during Experiment A, where passing the repository root as `core_root` raised
`UnmappedPackageError: core/adapters is not in DOMAIN_OF_TOPLEVEL`.

**Why out of scope.** Pre-existing, already disclosed by Phase F R-2, and
expanding the checker's root is a decision about the adapter layer's domain
membership — which no ADR has made and which this change is not authorized to
make. **Do not expand this change to cover it.**

---

### GR-18 — "`data` has no `core.store` importer" · **REJECT**

Review 2 tabulated `data` under "imports `core.store`? — no" and prescribed a
governance-only grant on that basis.

**Repository evidence.**

```
core/market_data/persistence/database.py:19    from core.store.connection import connect
core/market_data/persistence/migrations.py:12  from core.store.migrations import run_migrations
```

Both files are under `core/market_data`, which maps to the `data` domain.
Experiment A confirms the consequence: a governance-only grant yields seven
violations rather than five, the two additions being exactly these lines.

The premise fails because the review's own table counted *consumer* domains
and omitted the shims, which are consumers too. The shims are permanent per
GR-06 — the very finding Review 2 rules most strongly — so this is not a
transient state that a later grant could cover. Review 1's `data` +
`governance` set is adopted; see GR-03.

*(Recorded as a reject rather than folded silently into GR-03 because Review 2
carries the same premise into its C5 commit description, and anyone working
from that document needs the correction attached to it.)*

---

### GR-19 — `ImportError` escapes uncaught · **ACCEPT**

**Why accepted.** Verified by reading the call path.
`_load_expected_tickers_from_worktree` wraps `_load_module_from_worktree` in
`except OSError` only; its caller in `run_reproduction` catches
`ReproductionRunnerError` only. `ImportError` is neither, is not in
`_DRIFT_ERRORS`, and is raised *before* the `reconstruct_database` block whose
broad `except Exception` backstop maps failures to `DRIFTED`. A missing shim
therefore propagates out of `run_reproduction` as an uncaught exception.

This sharpens GR-06 materially: shim deletion does not degrade reproduction to
`UNVERIFIABLE` or `DRIFTED` — **it crashes the runner**, with no governed
status and no evidence record. A governed failure mode would at least be
auditable; this one is not.

- **Artifacts affected:** `core/governance/reproduction_runner.py:124-141,190`
  (analysis only — **not modified by this change**).
- **ADR impact:** AD-069 records the crash-not-degrade behavior as part of the
  GR-06 rationale, which is what makes the retirement condition in §6 a hard
  prohibition rather than a caution.
- **Section 5 impact:** none.
- **Reproduction impact:** direct and severe; the discharge is T-2 plus §6.
- **Boundary of the ruling:** widening the runner's exception mapping to
  govern `ImportError` is a change to `reproduction_runner`'s status semantics
  and is **out of scope** here. Recorded as an open item.

---

### GR-20 — Neither review is a repository artifact · **ACCEPT**

Ruled in §0. Recorded in the register for completeness.

- **Artifacts affected:** this document, which is the remedy.
- **ADR impact:** none. AD-068 and AD-069 cite **this** document, at a
  committed path, for their review basis — and cite it at its true level
  (Level 1), never as an independent review.
- **Section 5 impact / Reproduction impact:** none.

---

## 3. Deliverable 1 — Final ADR numbering plan

| Range | Status | Owner |
|---|---|---|
| AD-001 … AD-051 | Accepted | various |
| **AD-052 … AD-055** | **Retired** — never to be reissued | recorded at `ARCHITECTURE_DECISIONS.md` ~line 2849 |
| AD-056 … AD-060 | Accepted | Phase 4 Phase E |
| **AD-061 … AD-067** | **Reserved, unwritten** | Phase F Research Execution Engine — **not released by this ruling** |
| **AD-068** | **To be written** | ETF/Data domain split (boundary-hardening step 1) |
| **AD-069** | **To be written** | `core.store` storage substrate (boundary-hardening step 2) |
| AD-070+ | Free | — |

**Reservation instrument (GR-01 modification).** Before either new AD is
written, `ARCHITECTURE_DECISIONS.md` receives a reservation block, modeled on
the existing AD-052…AD-055 retirement block, recording that:

- AD-061 … AD-067 are reserved to the Phase F Research Execution Engine
  proposal, citing `PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` §5;
- the reservation is **live but unaccepted** — Phase F's F-0 remains blocked
  for want of an independent review;
- reserved numbers are released only by recorded decision, never by a later
  change finding them unoccupied;
- **the general rule:** a number is reserved from the moment a governance
  document claims it, and `ARCHITECTURE_DECISIONS.md` is the single place a
  reservation is discoverable.

That last clause is the actual repair. The collision occurred because the
reservation was invisible to a reader of the AD file, and nothing prevents the
next one otherwise.

**Required AD-068 content** (ETF/Data split):
the five decisions enumerated in GR-05; the symbol-attribution departure from
§5's Enforcement clause and its termination condition (GR-09); the
`xfail(strict=True)` convention and the fact that it is the repository's first
(GR-11); `ETF_SYMBOLS_BY_MODULE` as a hand-maintained shrink inventory whose
accuracy is guarded by T-1 and by nothing else.

**Required AD-069 content** (`core.store`):
clauses 1–4 of the current AD-061 draft, retained; **minus** the false
"no existing edge changes direction or permission" sentence, replaced by an
explicit permission ledger (GR-02); **plus** the narrow grant, the
demand-driven growth rule, and the two distinct denial grounds for
`statistics` versus `data` (GR-03); **plus** the reproduction dependency as
the *primary* shim rationale, naming the `sys.modules` mechanism, the
crash-not-degrade failure mode, and the carried-forward
`reproduction_runner` docstring inaccuracy (GR-06, GR-19); **plus** the
corrected retirement condition of §6 (GR-07).

**Citation sites to be written with the final numbers** — 9 sites in 6 files:
`core/store/connection.py:2`, `core/store/migrations.py:2`,
`core/market_data/persistence/database.py:2`,
`core/market_data/persistence/migrations.py:2`,
`tests/test_store_extraction.py:1,102,135`,
`tools/check_import_boundaries.py:60,141`.

---

## 4. Deliverable 2 — Final commit decomposition plan

Seven commits. **Every commit leaves the suite green and is independently
revertable.** That property is what the current single-diff bundle lacks and
is the primary thing this decomposition buys.

---

**C1 — `docs: record the AD-061…AD-067 reservation and the reservation rule`**

- Files: `docs/ARCHITECTURE_DECISIONS.md`
- Discharges: GR-01 (modification clause)
- Rationale: numbering must be settled before any artifact cites a number.
- Rollback: docs only, no dependents. · Test impact: none.

**C2 — `docs: record the ETF/Data domain split (AD-068) and amend Section 5`**

- Files: `docs/ARCHITECTURE_DECISIONS.md`, `docs/PLATFORM_ARCHITECTURE_V1.md`
- Discharges: GR-05, GR-08 (ETF half), GR-09
- Rationale: the ADR and its §5 amendment ship together and precede the code
  they govern, so AD-068's amendment claim is true by construction.
- Rollback: docs only. · Test impact: none.

**C3 — `phase4: split ETF out of the Data domain in the import checker (AD-068)`**

- Files: `tools/check_import_boundaries.py`, `tests/test_import_boundaries.py`
- Discharges: GR-04 (step 1 half), GR-11, T-1
- Contains **no** `store` reference — `ALLOWED_DEPENDENCIES` is touched
  exactly once per step.
- Rollback: self-contained; no production code imports the checker.
- **Test impact: `769 passed, 1 xfailed, 1 skipped`. Suite green.**

**C4 — `docs: record the storage substrate (AD-069) and amend Section 5`**

- Files: `docs/ARCHITECTURE_DECISIONS.md`, `docs/PLATFORM_ARCHITECTURE_V1.md`
- Discharges: GR-02, GR-03 (record), GR-06 (record), GR-07 (record),
  GR-08 (Store half), GR-19 (record)
- Rollback: docs only; C5 not yet landed. · Test impact: none.

**C5 — `phase4: extract storage primitives into core.store (AD-069)`**

- Files: `core/store/{__init__,connection,migrations}.py` (new);
  `core/market_data/persistence/{database,migrations}.py` (shims);
  `tools/check_import_boundaries.py`; `tests/test_import_boundaries.py`;
  `tests/test_store_extraction.py` (new); `adapters/cli/main.py`;
  `core/governance/reconstruction_loader.py`;
  `core/governance/reproduction_runner.py`;
  `maintenance/verify_price_coverage.py`; `tests/conftest.py`;
  `tests/test_cli.py`; `tests/test_governance_dataset_snapshots.py`;
  `tests/test_reproduction_contract.py`; **`migrations/README.md`**
- Discharges: GR-04 (step 2 half), GR-03 (enforce), GR-07 (message),
  GR-10 (blocking tier), T-3, T-5
- Deltas from the working tree: `store` granted to `data` and `governance`
  only; `test_every_domain_may_depend_on_store` retired and replaced;
  shrink-condition message corrected.
- Rollback: widest commit, safest content — a verbatim relocation behind
  re-export shims, guarded by an identity assertion.
  `maintenance/verify_price_coverage.py` is the sole non-test, non-`core`
  caller and warrants an eyeball on revert.
- Test impact: suite green. Zero protected-hash impact — verify by running the
  36 parametrized hash cases explicitly before pushing.

**C6 — `tests: close the boundary-hardening regression gaps`**

- Files: `tests/test_import_boundaries.py`, `tests/test_store_extraction.py`,
  `tests/test_database.py` → `tests/test_store_connection.py`
- Discharges: T-2, T-4, T-6, T-7, T-8; GR-15
- Rollback: tests only. · Test impact: suite green.

**C7 — `docs: repoint stale references to the moved storage primitives`**

- Files: `docs/BASELINE_STATUS.md`,
  `docs/PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md`
- Discharges: GR-10 (non-blocking tier)
- **Excludes** the dated-record pointers ruled untouchable in GR-10.
- Rollback: cosmetic. · Test impact: none.

**Ordering constraints, each traceable to a ruling:** numbering first (GR-01);
each ADR plus its §5 amendment before the code it governs (GR-05, GR-08);
step 1 fully before step 2 (GR-04, GR-13); the permission narrowing lands
*with* the store code and never after, since narrow-then-widen is additive and
broad-then-narrow is breaking (GR-03).

---

## 5. Deliverable 3 — Final dependency matrix for `STORE_DOMAIN`

**Layer assignment.** `store` is **Layer −1**, below Data and Statistics. It is
substrate: it holds `connect()` and `run_migrations()` and nothing else.

### 5.1 Who may depend on `store`

| Domain | Permitted → `store` | Basis |
|---|---|---|
| `data` | **✅ YES** | Demanded: `core/market_data/persistence/database.py:19`, `migrations.py:12` (the shims, permanent per §6). Verified by Experiment A. |
| `governance` | **✅ YES** | Demanded: `reconstruction_loader.py:36,37`, `reproduction_runner.py:68`. |
| `statistics` | **✕ NO** | **Purity**, not layering. §4.3 defines Statistics as a pure computational library; it is refused I/O on the same grounds as the kernel. §5's "single hard rule" is preserved intact by this change. |
| `etf` | **✕ NO** | No importer. Grant on demand. |
| `validation` | **✕ NO** | No importer. Grant on demand. |
| `research` | **✕ NO** | No importer. Grant on demand. |
| `reporting` | **✕ NO** | No importer, and `tests/test_reporting_import_boundary.py` forbids it even `pathlib` and `os`. A storage edge is directly at odds with its own design. |
| `kernel` | **✕ NO** | Structural. Keeping `store` outside the kernel is what makes `kernel -> store` flaggable at all — the single best decision in this change and the reason `store` is not folded in. |

### 5.2 What `store` may depend on

**Nothing.** `ALLOWED_DEPENDENCIES[STORE_DOMAIN] = frozenset()`, and
`test_store_imports_nothing_from_core` is **stricter than the checker**: it
forbids the kernel too, which the allowed-dependency table cannot express
because the kernel is an exempt target for every domain. Both are retained.

### 5.3 Growth rule

The grant list is **demand-driven**. A domain is added when a real importer
appears, by recorded decision, in the commit that introduces the importer.
Adding a grant later is a one-line reviewed change; a granted-but-unused edge
is invisible drift that a future module can occupy silently. Under a broad
grant, a future `core/statistics` module opening a database would be
architecturally legal and pass the checker — the exact failure the rule
exists to prevent.

### 5.4 Section 5 target shape

1. **Store column added** to the dependency table; ✅ for Data and Governance
   only, ✕ elsewhere.
2. **ETF row and column added** (AD-068), with the forbidden entry *"nothing
   may depend on ETF"* — a novel rule with no §5 precedent, which is why it
   needs its own ADR.
3. **"Data → anything" reworded to "Data → anything *above it*."** The
   rationale printed in §5 — "the foundation never calls upward" — is
   preserved exactly; Store is below Data, so the substrate edge does not
   offend it. Only the wording was over-broad.
4. **"Statistics → anything" left unchanged.** This change does not touch it,
   and AD-069 must say so explicitly, because the working tree did touch it.
5. **Enforcement clause amended** (GR-09) to permit symbol-level attribution
   for domains not yet separated by package path, with the termination
   condition: the departure ends when `ETF_SYMBOLS_BY_MODULE` empties.

---

## 6. Deliverable 4 — Final shim retirement policy

**Subjects:** `core/market_data/persistence/database.py`,
`core/market_data/persistence/migrations.py`.

**Status: PERMANENT until the condition below is satisfied in full. They are
not a transitional alias and must not be described as one.**

### 6.1 Why they exist — in priority order

1. **PRIMARY — pinned-commit module resolution.** `reproduction_runner`
   executes pinned code against **HEAD's** `core` package.
   `sys.modules['core']` is already populated before the pinned script is
   `exec_module`'d, so `core.*` submodules resolve through HEAD's
   `core.__path__` regardless of `sys.path`. A pinned script's legacy import
   binds **HEAD's shim**. Verified by Experiment B. All three archived cycles
   pin resolvable commits, and all three pin a script importing both legacy
   paths.
2. **SECONDARY — hash-protected evidence.** Nine `.py` files in
   `tests/fixtures/protected_file_hashes.json` import a legacy path and may
   not be edited, nor the fixture regenerated to permit an edit.

AD-061 as drafted gives **only** reason 2. That inversion is the defect: reason
2 could in principle expire (the protected files could be retired by decision);
**reason 1 cannot**, for as long as any archived cycle pins a pre-`core.store`
commit — and pinned history is immutable.

### 6.2 Retirement condition — binding

> **The shims may be deleted only when *both* hold:**
>
> **(a)** no file in the working tree imports either legacy path — the
> condition the current test checks; **and**
> **(b)** **no reproducible commit imports either legacy path** — that is, for
> every cycle under `research_archive/*/` with a `COMMIT.txt`, the pinned
> commit's own tree contains no import of
> `core.market_data.persistence.database` or
> `core.market_data.persistence.migrations`.
>
> Condition (b) is **strictly stronger** than (a) and is the binding one.
> Satisfying (a) alone and deleting the shims is a **prohibited act**: it
> converts every archived cycle's reproduction from a verifiable result into an
> **uncaught runner crash** (GR-19) — not a governed `UNVERIFIABLE`, not a
> `DRIFTED`, and with a fully green test suite.

**Currently:** (a) is satisfied for all non-frozen files; **(b) is not
satisfied and cannot be**, because `07f0da3`, `19771d4`, and `8831d54` are
immutable and all three import both paths. **The shims are therefore permanent
for the foreseeable life of the repository.**

### 6.3 How the condition is enforced

- **Prose:** stated in AD-069 and in both shim module docstrings — at the file
  a maintainer opens when contemplating deletion, per GR-14.
- **Mechanically:** **T-3** makes condition (b) executable by reading
  `research_archive/*/COMMIT.txt` and refusing the deletion premise while any
  pin resolves to a commit importing a legacy path.
- **The current assertion message is corrected** (GR-07): it may no longer
  instruct deletion on the current-tree condition alone.

### 6.4 If the condition is ever satisfiable

Retirement is a **governance act requiring a new ADR**, not a cleanup commit.
The ADR must record which archived cycles were re-verified after deletion and
by whom. A green suite is necessary and **not sufficient** evidence.

---

## 7. Deliverable 5 — Final test policy

### 7.1 The `xfail` decision — **ACCEPTED**

> `tests/test_import_boundaries.py::test_real_repository_has_no_boundary_violations`
> carries `@pytest.mark.xfail(strict=True, reason=...)`. It ships in **C3**,
> in the same commit as the mechanism that makes it fail.

**Why `xfail(strict=True)` and not the alternatives:**

| Option | Ruling |
|---|---|
| Leave it failing (as built) | **Rejected.** No CI exists; `pytest` is the only gate. A permanently red suite destroys that gate for all 768 unrelated tests, hides the next real regression at the summary line, and trains the human gate to ignore red. |
| `skip` / `skipif` | **Rejected.** Removes the assertion entirely. The coupling stops being checked, and nothing detects the day it is discharged. |
| Delete the test, keep only the inventory test | **Rejected.** The inventory test asserts the coupling *matches a documented list*; it cannot assert the list should be empty. The aspiration would go unrecorded. |
| **`xfail(strict=True)`** | **ACCEPTED.** Suite returns to green; the coupling stays asserted and enumerated; and `strict=True` makes an *unexpected pass* a **failure**, so the day the last coupling is discharged the suite forces the marker's removal — a stronger shrink signal than a red test, not a weaker one. |

**Conditions on the acceptance:**

1. **`strict=True` is mandatory.** A non-strict `xfail` silently absorbs the
   green state and destroys the forcing function that justifies the ruling.
2. **The `reason` must name the discharging step**, so the marker is
   self-documenting about when it is expected to go.
3. **The paired green inventory test
   (`test_known_etf_coupling_inventory_is_exactly_as_documented`) is
   retained.** The `xfail` records the aspiration; the inventory test records
   the current exact state. Neither substitutes for the other.
4. **AD-068 records the convention.** There is **no `xfail` anywhere in this
   repository today**; C3 introduces it, and an undocumented first use of a
   test-outcome marker in a governance-first repository is itself a gap.
5. **The marker is scoped to exactly one test.** It is not a pattern for
   deferring other failures and must not be cited as precedent for doing so.
6. **AD-005 compliance:** `pytest` is already the test runner; no framework is
   added.

### 7.2 Required tests — unified numbering

Both reviews' `T-n` labels are **discarded** (they collide — GR-12). This is
the authoritative set.

| # | Test | Guards | Commit | Tier |
|---|---|---|---|---|
| **T-1** | Every symbol in `ETF_SYMBOLS_BY_MODULE` actually resolves in its named module | **False success.** Rename or relocate any listed symbol and the inventory silently stops matching, violations drop toward 0, the `xfail` **passes unexpectedly**, and — under `strict=True` — the suite fails loudly instead of reporting the split complete while the coupling is untouched. The only existing test touching the constant asserts module *names appear in a string*. **Highest-value test in the set.** | C3 | **Blocking** |
| **T-2** | A module `exec_module`'d with a foreign `sys.path[0]` still resolves the legacy import to `core.store.connection.connect` | GR-06. The only executable guard on the reproduction path. Existing shim tests cover *static* importers; the dynamic exec path is the actual risk. | C6 | **Blocking** |
| **T-3** | Shrink guard reads `research_archive/*/COMMIT.txt` and refuses the deletion premise while any pin imports a legacy path | GR-07 / §6.2(b). Makes the binding retirement condition mechanical instead of advisory. | C5 | **Blocking** |
| **T-4** | `PRAGMA foreign_keys` is ON after `connect()` | Verified gap: the pragma is set at `core/store/connection.py:30` and asserted **nowhere**, while `reconstruction_loader.py:8` calls it load-bearing — "the load-order bug v1.0 had and v1.1 corrects." Relocation is the moment to pin it. | C6 | Required |
| **T-5** | `store` grant set matches demonstrated importers: `data` and `governance` permitted; `statistics -> store` is a **violation** | GR-03 / §5.1. Replaces `test_every_domain_may_depend_on_store`, which encodes the over-broad grant as a requirement. Positive and negative cases both required. | C5 | Required |
| **T-6** | Real-tree purity: `core/statistics/` and `core/shared/` import no `core.store` | GR-03. The existing kernel test builds a **synthetic** tree in `tmp_path`; nothing asserts the actual tree. Cheap and independent of T-5. | C6 | Required |
| **T-7** | `run_migrations` behavioral parity at the new home: ledger created, re-run idempotent, ordering is `sorted()` | A verbatim move deserves a direct assertion at its destination; today it is exercised only incidentally through the `conn` fixture. | C6 | Required |
| **T-8** | Each shim's public surface is exactly one name | Nothing stops a shim regrowing logic; `__all__` is declarative, not enforced. Also the mechanical half of GR-14's concern. | C6 | Required |

**Retained unchanged** — the seven existing store tests, all sound:
`test_store_imports_nothing_from_core` (stricter than the checker — keep),
`test_store_holds_only_the_two_primitives`,
`test_shims_re_export_the_moved_objects_themselves` (identity, not
equivalence — the correct choice),
`test_legacy_shim_importers_are_exactly_the_frozen_files` (message corrected
per GR-07, predicate strengthened per T-3),
`test_store_may_not_depend_on_any_domain`,
`test_shared_kernel_may_not_depend_on_store`,
`test_store_is_not_a_route_from_a_domain_into_etf`.

**Retired:** `test_every_domain_may_depend_on_store` — superseded by T-5.

**Rejected:** Review 1's doc-path drift guard (its `T-6`). **REJECT.** A test
that greps documentation for stale module paths guards a class of error whose
cost is a misdirected reader, at the price of a test that fails on every
legitimate documentation edit and that cannot distinguish a dated historical
record (which must *keep* the old path, per GR-10) from a live pointer. The
one-time fixes in C5 and C7 are the proportionate remedy.

### 7.3 Expected suite state per commit

| After | Expected |
|---|---|
| C1, C2 | `768 passed, 1 skipped` — unchanged |
| C3 | `~770 passed, 1 xfailed, 1 skipped` — **green** |
| C4 | unchanged — **green** |
| C5 | `~+7 passed, 1 xfailed, 1 skipped` — **green** |
| C6 | `~+5 passed, 1 xfailed, 1 skipped` — **green** |
| C7 | unchanged — **green** |

**T-1 may legitimately fail on first write** if a listed symbol has already
drifted. That is the test working. It must be investigated, never adjusted to
pass.

---

## 8. Deliverable 6 — Merge readiness verdict

# APPROVE WITH REQUIRED CHANGES — DO NOT MERGE AS IT STANDS

**On the architecture, recorded separately from the defect list.** The core
judgment is sound and I want that on the record. `core.store` as its own
domain rather than a kernel fold is right, for the right reason, and clause 3
of the draft ADR argues it correctly — `test_shared_kernel_may_not_depend_on_store`
is the concrete payoff and would have been permanently impossible under the
kernel fold. Scoping the substrate to exactly two primitives while leaving
repositories in their owning domains is the correct boundary. Symbol-level ETF
attribution is a genuinely good way to make a domain boundary visible without
moving a file. Deriving the shim's permitted-importer set from the
protected-hash fixture rather than restating it is exactly the discipline this
repository's governance standard asks for. Asserting shim identity with `is`
rather than `==` is the right choice and makes drift impossible by
construction. **None of the blocking items below is a design error.** Every
one is a claim defect, a sequencing defect, a permission over-grant, or a
missing guard.

**It cannot merge, on five independent grounds, each sufficient alone:**

1. **An accepted ADR would state a falsehood about its own effect** (GR-02),
   while the §5 amendment it claims to make does not exist (GR-08). In a
   repository with no CI, where ADRs are the governing artifact, this is the
   highest-consequence defect available.
2. **A live number collision** (GR-01) would falsify a verified statement in a
   second governance document and produce two AD-061s cited from six files.
3. **A documented instruction that destroys reproducibility** (GR-06, GR-07,
   GR-19). Following the repository's own guidance would crash reproduction of
   every archived cycle — silently, with a green suite, and with no governed
   status.
4. **A permanently red suite** (GR-11) where `pytest` is the only gate.
5. **A permission over-grant** (GR-03) that contradicts, inside the same
   commit, the purity argument the change itself makes for keeping `store`
   out of the kernel.

### 8.1 Discharge checklist — required before merge

| # | Item | Commit |
|---|---|---|
| 1 | AD-068 / AD-069 numbering + reservation block (GR-01) | C1 |
| 2 | AD-068 written; five decisions recorded (GR-05) | C2 |
| 3 | §5 amended — ETF row/column + forbidden entry + Enforcement clause (GR-08, GR-09) | C2 |
| 4 | `xfail(strict=True)` with all six §7.1 conditions (GR-11) | C3 |
| 5 | **T-1** — symbol existence (guards the false-success mode) | C3 |
| 6 | AD-069 written; false sentence replaced by permission ledger (GR-02) | C4 |
| 7 | Reproduction rationale recorded as **primary**, `sys.modules` mechanism and crash-not-degrade named (GR-06, GR-19) | C4 |
| 8 | §5 amended — Store row/column, "Data → anything above it", Statistics untouched (GR-03, GR-08) | C4 |
| 9 | Grant narrowed to `data` + `governance` (GR-03) | C5 |
| 10 | Shrink-condition message corrected (GR-07) | C5 |
| 11 | **T-3** — archive-pin guard | C5 |
| 12 | **T-5** — grant-set test replaces `test_every_domain_may_depend_on_store` | C5 |
| 13 | `migrations/README.md:3` repointed (GR-10, blocking tier) | C5 |
| 14 | **T-2** — reproduction-path shim test | C6 |
| 15 | Step 1 / step 2 landed as separate commits, step 1 first (GR-04, GR-13) | C2–C5 |

### 8.2 Required before the milestone closes — not before merge

T-4, T-6, T-7, T-8; the `tests/test_database.py` rename (GR-15); the
non-blocking stale-pointer sweep (GR-10, C7).

### 8.3 Deferred, recorded so they are not rediscovered as novel

- `_python_files()` venv/vendor exclusions (GR-16).
- **`reproduction_runner`'s docstring inaccuracy** — it claims pinned code
  never comes from HEAD, which is true of the script and false of the `core.*`
  modules it imports (GR-06). Pre-existing; this change makes the repository
  depend on it. Needs its own decision.
- **`ImportError` is not a governed reproduction status** (GR-19). Widening
  the runner's exception mapping changes status semantics and needs its own
  decision.

### 8.4 Explicitly out of scope — do not expand this change

- Discharging the five ETF violations. That is step 3; step 1's whole thesis
  is that **inventory is not repair**.
- Extending `check_repository` to `adapters/` (GR-17) — it presumes a domain
  ruling for the adapter layer that no ADR has made.
- Anything touching the Phase F AD-061…AD-067 reservation beyond leaving it
  intact and recording it.

### 8.5 Standing process finding

Of the blocking items, **GR-01 and GR-11 are mechanically detectable** and
neither was caught before the work reached a reviewable state; **GR-18** is a
factual error that survived into a review's own prescription and would have
broken the change had it been implemented as written. All three are the same
pattern project memory already records against Phase F: thorough self-review,
no independent review.

**This resolution is Level 1.** It is one reader with repository access. It
does not discharge the independent-review requirement for Phase F's F-0, for
AD-068, for AD-069, or for anything else, and must not be cited as though it
does.

---

## 9. Ruling ledger

| ID | Ruling | Blocking | Discharged by |
|---|---|---|---|
| GR-01 | ACCEPT WITH MODIFICATION | ✅ | C1 |
| GR-02 | ACCEPT | ✅ | C4 |
| GR-03 | ACCEPT WITH MODIFICATION | ✅ | C4, C5, T-5, T-6 |
| GR-04 | ACCEPT | ✅ | C2–C5 |
| GR-05 | ACCEPT | ✅ | C2 |
| GR-06 | ACCEPT | ✅ | C4, T-2, §6 |
| GR-07 | ACCEPT | ✅ | C5, T-3, §6 |
| GR-08 | ACCEPT | ✅ | C2, C4 |
| GR-09 | ACCEPT | ✅ | C2 |
| GR-10 | ACCEPT WITH MODIFICATION | partial | C5 (blocking), C7 (rest) |
| GR-11 | ACCEPT | ✅ | C3, §7.1 |
| GR-12 | ACCEPT WITH MODIFICATION | partial | C3, C5, C6, §7.2 |
| GR-13 | REJECT | — | — |
| GR-14 | REJECT | — | — |
| GR-15 | ACCEPT | ✕ | C6 |
| GR-16 | ACCEPT (deferred) | ✕ | §8.3 |
| GR-17 | ACCEPT as fact / out of scope | ✕ | §8.4 |
| GR-18 | REJECT | — | — |
| GR-19 | ACCEPT | ✅ | C4, §6.2, §8.3 |
| GR-20 | ACCEPT | ✕ | this document |

**Totals: 13 ACCEPT · 4 ACCEPT WITH MODIFICATION · 3 REJECT.**
**15 discharge items required before merge.**

---

*No code was modified in producing this resolution. The working tree is
exactly as found: `1 failed, 768 passed, 1 skipped`.*
