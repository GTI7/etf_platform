"""Archive Seal primitive (AD-074 Increment 2 -- docs/ARCHITECTURE_DECISIONS.md
AD-073 as amended 2026-07-26, docs/AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md).

A sealed archive is one for which a **sealing commit** has been recorded
in the Archive Seal Register (``docs/archive_seal_register.jsonl``, C-1).
``verify_seal()`` confirms that every in-scope file under the archive's
working-tree directory is byte-identical (normalization-aware, D4) to
the same path at that commit, and that the two path sets agree.

**Comparison direction (governance hardening pass 2026-07-26), stated
here to disambiguate from ``core.governance.freeze_verifier``.** This
module always compares, in exactly this direction,

    **sealed commit tree -> archive filesystem**

-- "does the archive still match the bytes it was sealed at?" The left
side is the tree of the commit named by the Register record; the right
side is what is physically on disk under ``archive_dir`` right now.
``freeze_verifier`` instead compares a **frozen commit against the live
working tree/HEAD**: "has anything changed since the freeze claim was
made?" The fixed point differs -- a frozen sealing commit here, a
time-varying ``HEAD`` there -- which is why ``freeze_verifier``'s own
comparison helpers are named ``*_since_freeze`` rather than merely
``*_drift``: the two "has this drifted?" questions must never be
interchangeable at a call site, only in prose.

``HEAD`` is consulted here for exactly two things, both of them
*admissibility* questions about the seal's own inputs and neither of them
part of the comparison: whether the Register record is committed
(`_committed_register_text`) and whether the sealing commit is reachable
(`_unreachable_commit_error`). Both can only move a result toward
``UNVERIFIABLE``; neither can produce a ``MATCHED`` or a ``MISMATCH``
that would not otherwise have been reached, so the comparison itself
remains a function of the sealing commit and the archive bytes alone.

**What this module does not answer.** It answers archive tree integrity
against a fixed sealing commit, and nothing else. It makes no research
validity claim (AC-74-13), produces no ``GateResult`` and no
``DecisionRecord`` (AC-74-10), and -- as of the 2026-07-26 hardening
pass -- makes **no lifecycle-closure judgement**. AD-073 AC-15's
requirement that an unclosed cycle report ``UNVERIFIABLE`` is satisfied
at the report level by ``archive_verifier``'s completeness branch, which
owns that question; duplicating it here would have made the seal's
answer depend on the working-tree ``transition_records.jsonl``, which is
precisely the class of live input this module's other inputs were just
pinned to remove. See AD-074 SS7B D10 for the amendment that settles the
contradiction between AC-15's text and this module's scope.

**Neither side of that comparison is the git index** (integrity audit
item 1, 2026-07-26). The two sides are obtained as blob identities --
``git rev-parse <sealed_commit>:<path>`` for the sealed tree,
``git hash-object --path <path> -- <filesystem_path>`` for the archive
filesystem -- and compared directly. The superseded implementation used
``git diff --quiet <sealed_commit> -- <path>``, which routes the
working-tree side through the index and is therefore falsifiable in both
directions: ``git update-index --assume-unchanged`` makes ``diff``
report a tampered file clean, and ``git rm --cached`` makes ``diff``
report an untouched file modified. Neither is a fact about the archive's
bytes, and the seal must depend on nothing but those. ``hash-object
--path`` preserves the normalization safety ``diff`` was chosen for
(SS7B D4): ``--path`` applies exactly the attributes and clean filters
configured for that path, so a CRLF working-tree checkout of an LF blob
hashes back to that same blob under ``core.autocrlf=true``, and
``.gitattributes``'s ``*.jsonl -text`` exemption is honoured
identically. D4's actual bar -- never compare ``git cat-file blob``
output against raw working-tree bytes -- is unchanged and still binding:
``cat-file`` applies no filters, and nothing here uses it for content.

**The comparison has exactly three inputs, and all three are fixed at
the sealing commit** (governance hardening pass 2026-07-26). Those are
the sealed tree, the archive's on-disk bytes, and -- less obviously --
everything that decides *how* those bytes are hashed and *which* of them
are compared at all. Every input in the third category was live
working-tree or machine state before this pass, and each is now pinned:

- the **exclusion sets**. Both ``dataset_manifest.json`` (SS7B D2) and
  ``tests/fixtures/protected_file_hashes.json`` (SS7B D9) are read at
  the sealing commit. An exclusion is a file the Seal declines to check,
  so a working-tree-controlled exclusion source is an unreviewable
  exemption switch: appending one path to the fixture would have turned
  a tampered archive into ``MATCHED``. ``snapshot_path`` entries must
  additionally resolve strictly inside ``dataset_hashes/``, so an
  exclusion cannot reach a governance artifact.
- the **attribute stack** that governs ``hash-object --path``, the
  **attribute-source selection** (``attr.tree``/``GIT_ATTR_SOURCE``)
  that decides which tree that stack is even read from, and the
  **filter drivers** it can name -- see ``_ATTRIBUTE_TRUST_MODEL``
  below, which states the full model and what deliberately remains live.
  Verification explicitly neutralises all five influences: system
  attributes, global attributes, ``info/attributes``, working-tree
  ``.gitattributes``, and ``attr.tree``/``GIT_ATTR_SOURCE`` selection.
- the **sealing commit itself**, which must be a full object id. A
  Register record naming ``HEAD`` or a branch would make the seal
  re-derive its own expected value on every call -- the "compare against
  ``HEAD``" design SS6 records as considered and rejected, arrived at
  through data rather than through code.

**The fourth input is the Register record that names the sealing commit,
and it is the one input that cannot be pinned to that commit**
(governance hardening pass 2026-07-26, post-AD-075 implementation audit).
A record naming commit C is written after C exists, so reading the
Register at C is circular. It is instead read at ``HEAD``, and read as
**committed content**, never from the working tree -- see
`_committed_register_text` for why an uncommitted Register is the one
tamper AD-074 SS7B D5 admits no history review can reach. The commit it
names must additionally be *reachable* from ``HEAD``, not merely
*resolvable* -- see `_unreachable_commit_error` for the forged-commit
attack that distinction defeats, and for why SS7A B-1's contrary
reasoning does not survive contact with ``git commit-tree``.

**Trust boundary (AD-074 SS5.2), stated here as this module's own
contract, not only in the design review.** This module defeats:
accidental mutation, a deliberate edit committed normally, a file added
to a closed archive, and a file deleted from a closed archive -- all via
tree comparison against the recorded commit. It does **not** defeat
**history rewrite** (``git commit --amend``, ``filter-repo``, a
force-push that drops the sealing commit from every ref, or a squash/
rebase merge that makes it unreachable -- SS7B D3) or the loss of the
repository itself; no same-repo mechanism can (SS3 S-4). A previously
``MATCHED`` seal reporting ``UNVERIFIABLE`` after a legitimate squash
merge, rebase, branch deletion + gc, or a shallow clone is an accurate
report of "cannot currently verify", not a false ``MISMATCH`` -- this
module must never conflate "unreachable" with "modified".

**Never calls** ``freeze_verifier.verify_freeze()``,
``decision_recorder.verify_chain_intact()``, or
``decision_recorder.verify_chain_anchored()`` (AC-74-2). This module
does not import ``freeze_verifier`` or reuse any of its internals --
even ``NotAGitRepositoryError`` is redefined here, not imported --
because the Seal's responsibility (a fixed-commit, archive-local tree
comparison) must never be allowed to grow into FreezeVerifier's
(a live, time-varying freeze-claim verification), and a shared
exception type would be the first thread pulling the two together. All
git access here is read-only, confined to a commit named by the
Register, and of the same command class ``freeze_verifier`` already
uses (``rev-parse``, ``cat-file``, ``ls-tree``, ``show``, ``merge-base``,
plus ``hash-object``, which without ``-w`` computes an identity and
writes no object, and ``check-attr``, which only reports the attributes
already in force): nothing here ever writes, commits, checks out, or
resets anything, and the state of the index is never consulted.

**The Register is read-only** (AD-074 Increment 2 scope, SS9 item 3). No
function here writes a record; issuance is a recorded human act (AD-075
AC-75-4).
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core.governance.archive_identity import (
    ARCHIVE_MANIFEST_FILENAME,
    LEGACY_ARCHIVE_PROJECT_IDS,
)
from core.governance.dataset_manifest import (
    DATASET_MANIFEST_FILENAME,
    DatasetManifestError,
    parse_dataset_manifest_text,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ARCHIVE_SEAL_REGISTER_RELATIVE_PATH = "docs/archive_seal_register.jsonl"
PROTECTED_FILE_HASHES_RELATIVE_PATH = "tests/fixtures/protected_file_hashes.json"
GITATTRIBUTES_FILENAME = ".gitattributes"

# The directory every dataset_manifest.json `snapshot_path` must resolve
# inside (AD-074 SS5.1 as amended 2026-07-26, hardening item M-1).
_DATASET_SNAPSHOT_ROOT = "dataset_hashes"

# A sealed commit is a **fixed object id**, never a name that resolves to
# one (AD-074 SS5.3/C-1 as amended 2026-07-26, hardening item BLOCKER 3).
# Full-length, lowercase hexadecimal only: 40 for a SHA-1 repository, 64
# for SHA-256. Lowercase is required rather than merely accepted because
# `supersedes` chaining (C-1) compares `sealed_commit` strings for
# equality -- two spellings of one commit would silently break a chain
# this reader is otherwise obliged to verify.
_SEALED_COMMIT_PATTERN = re.compile(r"\A(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")

# git tree entry modes this module can compare. A regular file (blob) is
# the only shape `hash-object` computes a meaningful identity for; a
# symlink (120000) stores its target path as the blob, and a gitlink
# (160000) stores a commit id belonging to another repository entirely
# (hardening item M-5).
_REGULAR_FILE_MODES = frozenset({"100644", "100755"})

# The one Register record schema this implementation understands (AD-074
# SS5.5 C-1: "a closed integer, starting at 1"). A record declaring any
# other value -- higher, lower, or not an integer at all -- is a record
# written against a schema whose field meanings this code cannot vouch
# for, so it is UNVERIFIABLE rather than read optimistically. Bumping
# this constant is a schema migration, never a tolerance widening.
SUPPORTED_REGISTER_SCHEMA_VERSION = 1

# schema_version, project_id, sealed_commit, sealed_at, sealed_by are
# never absent from a well-formed record; supersedes is the one field
# allowed to be null, but the key itself must still be present (AD-074
# SS5.5 C-1/C-3).
_REQUIRED_RECORD_FIELDS = ("schema_version", "project_id", "sealed_commit", "sealed_at", "sealed_by", "supersedes")


class NotAGitRepositoryError(RuntimeError):
    """Raised for an environmental failure only (``repo_root`` is not
    inside a git working tree) -- not for a failed seal verification,
    which is a normal ``SealOutcome(status="unverifiable")`` result.
    Mirrors ``freeze_verifier.NotAGitRepositoryError``'s contract
    exactly but is a distinct class: see the module docstring for why
    this module never imports ``freeze_verifier``."""


@dataclass(frozen=True, slots=True)
class SealFinding:
    """One path's comparison outcome. ``kind`` is exactly one of
    ``"modified"``, ``"missing"`` (present at the sealing commit, absent
    from the working tree), or ``"unexpected"`` (present in the working
    tree, absent from the sealing commit) -- AC-74-3, never collapsed."""

    path: str
    kind: str


@dataclass(frozen=True, slots=True)
class SealOutcome:
    """The primitive's own result shape -- deliberately not
    ``core.governance.archive_verifier.SealReport``: this module has no
    dependency on ``archive_verifier`` (the dependency runs the other
    way). ``status`` is one of ``"matched"``, ``"mismatch"``,
    ``"unverifiable"``. ``excluded_paths`` is always populated on a
    reached comparison (bounded coverage must be auditable, AD-074
    SS5.6) and is empty when the outcome was decided before any
    exclusion set could be computed."""

    status: str
    findings: tuple[SealFinding, ...]
    reason: str | None
    excluded_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArchiveIdentity:
    """What the working-tree ``archive_manifest.json`` says this archive
    is. ``lifecycle_version`` is None when the field is absent or is not
    a string -- neither is "legacy", and neither is an error here: the
    completeness branch owns judgements about manifest shape."""

    project_id: str
    lifecycle_version: str | None


@dataclass(frozen=True, slots=True)
class SealRegisterRecord:
    schema_version: int
    project_id: str
    sealed_commit: str
    sealed_at: str
    sealed_by: str
    supersedes: str | None


def _unverifiable(reason: str, *, excluded_paths: tuple[str, ...] = ()) -> SealOutcome:
    return SealOutcome(status="unverifiable", findings=(), reason=reason, excluded_paths=excluded_paths)


# Applied to **every** git invocation this module makes, at the one
# place that builds the argument vector, so that no present or future
# call site can forget it (hardening item BLOCKER 2, extended by
# acceptance-audit finding RF-1). See `_ATTRIBUTE_TRUST_MODEL` below for
# what these neutralize and why neutralizing them is not enough on its
# own.
#
# `attr.tree=` pins the *source selection* knob git >=2.40 added, not an
# attributes file: it names a tree to read `.gitattributes` from instead
# of the working tree, so setting it to a tree with no rules strips every
# attribute the seal's comparison depends on. Empty resolves to "no
# alternate source", i.e. back to the working tree, which is the state
# the `.gitattributes` verification below actually checks. On git <2.40
# the key is simply unknown and ignored, so the pin is safe to pass
# unconditionally.
_ATTRIBUTE_PINNING_ARGS = (
    "-c",
    "core.attributesFile=",
    "-c",
    "attr.tree=",
)

_ATTRIBUTE_TRUST_MODEL = """\
There are **five possible attribute influences on `hash-object --path`,
including `attr.tree`/`GIT_ATTR_SOURCE` attribute-source selection** --
four stacked *files*, plus the knob that decides which tree the fourth
is read from at all. `hash-object --path` is one side of the seal
comparison, so every one of them is an *input to the seal result* -- a
third input beside the sealing commit and the archive bytes, and the
only one that was, before this hardening pass, entirely live
working-tree/machine state. Each is pinned here, by a different
mechanism, because git offers no single switch:

1. the **system** attributes file (`$(prefix)/etc/gitattributes`) --
   disabled via ``GIT_ATTR_NOSYSTEM=1`` in the environment of every
   invocation;
2. the **global/user** attributes file (``core.attributesFile``, whose
   default is ``~/.config/git/attributes``) -- disabled by passing
   ``-c core.attributesFile=`` ahead of every subcommand, which resolves
   the setting to a path that names no file. This is verified behaviour,
   not an assumption: a global file assigning ``*.dat filter=evil``
   reports ``filter: evil`` without the override and ``filter:
   unspecified`` with it;
3. ``$GIT_COMMON_DIR/info/attributes`` -- **not** overridable by any
   config or environment variable (verified: it still applies with both
   of the above in force), so its mere existence is reported
   ``UNVERIFIABLE``. It is a per-clone, never-committed file, so a seal
   whose result could depend on it is a seal whose result depends on a
   file no reviewer will ever see in a diff;
4. the ``.gitattributes`` files in the working tree, one per directory
   from the repository root down to each compared path -- verified,
   blob-for-blob, against the same paths at the sealing commit. A
   post-seal edit to any of them is a change to the seal's own
   comparison rules and is reported ``UNVERIFIABLE``, never absorbed
   silently;
5. the **attribute-source selection** itself -- ``attr.tree`` (config)
   and ``GIT_ATTR_SOURCE`` (environment), added in git 2.40. These do
   not add a rule; they decide *which tree source 4 is read from*, which
   makes source 4's verification vacuous when either is set. Pointing
   either at a tree with no ``.gitattributes`` in it strips every
   attribute the comparison depends on: a ``-text`` (byte-exact)
   artifact tampered to CRLF then normalizes straight back to its sealed
   blob, and a ``MISMATCH`` becomes ``MATCHED``. Verified end to end, in
   both directions, before and after this pin.

   They are neutralized by **two different mechanisms, and the ordering
   matters**: ``-c attr.tree=`` is passed ahead of every subcommand, and
   ``GIT_ATTR_SOURCE`` is *removed from the environment*, because the
   environment variable overrides the config setting -- verified, the
   config pin alone leaves the bypass fully open. Config pinning is
   therefore not sufficient on its own, and neither is the environment
   scrub: ``attr.tree`` can be set in repository, global, or system
   config, or injected via ``GIT_CONFIG_*``, none of which any artifact
   this module verifies would show.

Pinning the attribute *stack* still leaves one live input: a ``filter``
attribute names a driver, and the driver's ``filter.<name>.clean``
command lives in git **config**, not in any attributes file. That
command is arbitrary code run over the working-tree bytes before they
are hashed -- it can make a tampered file hash to anything at all,
including the sealed blob, without touching a single verified artifact.
This is not hypothetical: ``filter.lfs.clean`` is present in ordinary
developer global config. So a ``filter`` attribute applying to any
compared path is refused outright (``UNVERIFIABLE``) rather than
trusted; the repository's own ``.gitattributes`` assigns none today, so
the refusal costs nothing and closes the hole.

Two live inputs are deliberately **not** pinned: ``core.autocrlf`` and
``core.eol``. They are what makes the comparison normalization-aware at
all (SS7B D4) -- pinning them would reintroduce exactly the false
``MISMATCH`` on a CRLF checkout that D4 exists to prevent.

**The remaining guarantee is narrower than "cannot make differing
content hash alike," and is stated precisely here (acceptance-audit
finding W-1, corrected 2026-07-26).** Flipping ``core.autocrlf`` *can*
make two byte-sequences that differ **only** in line-ending style
(``\\n`` vs ``\\r\\n``) hash alike, for any path where line-ending
normalization applies at all -- that is what "normalization-aware"
means, and it is not a preimage attack, merely a config change. What it
cannot do is make content differing in anything else -- a single
changed byte that is not a line terminator -- hash alike; that would
still require a preimage attack. The two live inputs are sound to leave
unpinned only because every archive artifact whose exact bytes matter is
committed ``-text`` (``*.jsonl -text``, this repository's own
``.gitattributes``): ``-text`` disables line-ending normalization for
that path outright, so ``core.autocrlf``/``core.eol`` have no effect on
it at all, pinned or not, and the CRLF/LF collision above cannot reach
it. For a path that is *not* ``-text`` (a ``.md``, ``.py``, ``.json``),
flipping ``core.autocrlf`` remains live and can turn a true ``MATCHED``
into a false ``MISMATCH`` on a legitimate CRLF checkout (fail-loud, D4's
own point) -- or, symmetrically, collapse a line-ending-only tamper of
such a file into ``MATCHED``. That residual is accepted, not closed: it
is the cost of D4's normalization tolerance, bounded to line-ending
bytes only, and it is why byte-exactness for any Seal-relevant artifact
must be asserted with ``-text``, not assumed from file type.
"""


def _git_env() -> dict[str, str]:
    """The environment for every git invocation: the ambient one plus
    ``GIT_ATTR_NOSYSTEM=1``, minus ``GIT_ATTR_SOURCE``. See
    ``_ATTRIBUTE_TRUST_MODEL``.

    ``GIT_ATTR_SOURCE`` is **removed, not overwritten**, and the
    distinction is load-bearing (acceptance-audit finding RF-1): the
    environment variable takes precedence over the ``attr.tree`` config
    pin, so ``-c attr.tree=`` alone does not neutralize it. Verified
    directly -- with the variable set and the config pin in force, a
    CRLF-tampered ``-text`` artifact still hashes back to its sealed
    blob. Only an environment with no ``GIT_ATTR_SOURCE`` in it at all
    puts attribute lookup back on the working tree, which is the source
    ``_gitattributes_drift_error`` verifies against the sealing commit.
    An empty *value* would be a third state git may read as an attempt
    to name a tree, so the key is unset outright."""
    env = dict(os.environ)
    env["GIT_ATTR_NOSYSTEM"] = "1"
    env.pop("GIT_ATTR_SOURCE", None)
    return env


def _run_git(args: list[str], *, repo_root: Path) -> subprocess.CompletedProcess[str]:
    """Text-mode git invocation, decoded as **UTF-8 explicitly** -- never
    via the ambient locale encoding, which on Windows is a legacy code
    page and would silently mangle any non-ASCII byte git emits. Only
    output that is ASCII by construction is ever parsed from here (object
    ids, ``rev-parse --is-inside-work-tree``'s ``true``); anything
    path-shaped or content-shaped goes through ``_run_git_bytes`` and is
    decoded deliberately at the call site. ``errors="replace"`` therefore
    cannot corrupt a parsed value -- it only keeps a non-UTF-8 *message*
    on stderr from raising instead of being reported."""
    return subprocess.run(
        ["git", *_ATTRIBUTE_PINNING_ARGS, *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=_git_env(),
    )


def _run_git_bytes(
    args: list[str], *, repo_root: Path, stdin: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    """Byte-mode git invocation, for output that must not be decoded by
    anyone but the caller: NUL-delimited path lists and blob content.
    git emits paths as the raw bytes it stored, and file content as the
    bytes it holds -- neither is the platform's locale encoding, and
    neither may be guessed. ``stdin`` feeds NUL-delimited paths to
    ``check-attr --stdin``, whose input is a path list of unbounded size
    and therefore must never be passed on the command line."""
    return subprocess.run(
        ["git", *_ATTRIBUTE_PINNING_ARGS, *args],
        cwd=repo_root,
        capture_output=True,
        check=False,
        input=stdin,
        env=_git_env(),
    )


def _assert_git_repo(repo_root: Path) -> None:
    result = _run_git(["rev-parse", "--is-inside-work-tree"], repo_root=repo_root)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise NotAGitRepositoryError(f"{repo_root} is not inside a git working tree")


def _fixed_commit_id_error(commit: str) -> str | None:
    """None if `commit` is syntactically a **fixed object id**; an
    explicit reason otherwise (hardening item BLOCKER 3, 2026-07-26).

    AD-074's entire premise is that the sealed side of the comparison is
    a *fixed point* (SS5.2: "both sides fixed at archive close"). A
    Register record naming ``HEAD``, ``master``, a tag, or an abbreviated
    hash names no such thing:

    - ``HEAD`` and a branch name resolve to whatever that ref points at
      *now*. A seal recorded against ``master`` re-reads its own expected
      value on every call, so it reports ``MATCHED`` for whatever the
      branch currently says the archive should contain -- the seal would
      verify the archive against itself and could never detect a
      committed edit, which is threat 2 of SS5.2's table, the one that
      matters. It is also precisely the "compare against ``HEAD``" design
      SS6 records as considered and rejected, reachable through the
      Register rather than through the code.
    - A **tag** is a movable, deletable ref, and an annotated tag is an
      object that peels to a commit that can be re-pointed.
    - An **abbreviated hash** is a prefix, not an identity: it names one
      object today and can become ambiguous as the object database grows,
      at which point the same Register record resolves differently, or
      stops resolving, with no record having changed.

    Rejection is syntactic and happens *before* any resolution attempt,
    so a repository that happens to carry a branch literally named
    ``HEAD`` cannot make the check pass by accident."""
    if not _SEALED_COMMIT_PATTERN.match(commit):
        return (
            f"Register record names sealed_commit {commit!r}, which is not a full-length "
            f"lowercase hexadecimal object id (40 or 64 hex characters) -- a sealing commit "
            f"must be a fixed object id, never a symbolic ref (HEAD, a branch, a tag) or an "
            f"abbreviated hash, whose meaning is a time-varying repository fact (AD-074 SS5.2)"
        )
    return None


def _resolved_commit_id(commit: str, *, repo_root: Path) -> str | None:
    """The object id `commit` resolves to as a commit, or None if it does
    not resolve to a readable commit object at all.

    The caller compares the return value against the id it passed in.
    That round trip is what closes the residual gap
    ``_fixed_commit_id_error``'s syntactic check cannot: a recorded
    string can be a perfectly well-formed, full-length lowercase object
    id and still not name the object the comparison will run against.

    **The reachable case is an annotated tag** (corrected 2026-07-26,
    acceptance-audit finding RF-2). An annotated tag is a real object
    whose id is 40 (or 64) lowercase hex characters, so it passes the
    syntactic check untouched -- and then ``^{commit}`` *peels* it to a
    different object. A Register record naming the tag object would
    otherwise seal the archive against a commit the record does not
    name, via a ref that is itself re-pointable and deletable.

    The previously documented case -- a *ref* whose name is 40 hex
    characters masquerading as an object id -- is **not** reachable, and
    the claim that it was is withdrawn. git deliberately ignores refs
    whose names end in 40 hex characters when resolving a 40-hex
    revision (it warns about them precisely because they are created by
    mistake), so such a ref never resolves at all and the record fails
    earlier, as an unreadable commit. If what came back is not the same
    string that went in, the record did not name the object it appears
    to -- that remains the check; only the example justifying it was
    wrong."""
    result = _run_git(["rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"], repo_root=repo_root)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _unreachable_commit_error(commit: str, *, repo_root: Path) -> str | None:
    """None if `commit` is an ancestor of ``HEAD``; an explicit reason
    otherwise (governance hardening pass 2026-07-26, post-AD-075
    implementation audit).

    **This reverses SS7A B-1, and the reversal is deliberate.** B-1 removed
    the ancestry requirement on the argument that it was redundant --
    *"an unreachable sealing commit is already UNVERIFIABLE under D3 ...
    the commit-resolution step already fails first if the commit cannot be
    found at all."* That premise is false, and the falseness is
    demonstrable rather than theoretical: ``git commit-tree`` mints a
    commit object that no ref names and no ref reaches, and
    ``rev-parse --verify <id>^{commit}`` resolves it exactly like any
    other. Resolution proves an object is *present in the object
    database*, never that it is *part of this repository's history*.

    What that gap costs is the seal's entire threat model. An actor who
    can write the Register can stage a tampered archive, ``write-tree``/
    ``commit-tree`` it into an unreferenced commit, name that commit as
    ``sealed_commit``, and obtain ``MATCHED`` against a tree that no
    review, no ``git log``, and no branch has ever contained -- the
    forged commit is invisible to every history-based defense D5 relies
    on, because it is not in any history.

    B-1's *actual* concern survives and is respected: ancestry is a
    time-varying fact, so this check can only ever move a result toward
    ``UNVERIFIABLE`` -- never toward ``MISMATCH``, and never toward a
    ``MATCHED`` that would not otherwise have been reached. A legitimate
    squash merge, rebase, branch deletion plus ``gc``, or shallow clone
    lands here rather than at resolution, and reports "cannot currently
    verify" with the same two remedies D3 already names (restore the
    object, or issue a superseding Register record). That is the same
    class of answer B-1's own D3 paragraph already accepts as correct;
    what changes is that a forged commit now lands there too, instead of
    reporting ``MATCHED``.

    ``merge-base --is-ancestor`` exits 0 for "is an ancestor", 1 for "is
    not", and anything else for a failure to determine -- which is itself
    UNVERIFIABLE, never silently treated as reachable."""
    result = _run_git(["merge-base", "--is-ancestor", commit, "HEAD"], repo_root=repo_root)
    if result.returncode == 0:
        return None
    if result.returncode != 1:
        return (
            f"could not determine whether sealing commit {commit!r} is reachable from HEAD "
            f"(git merge-base --is-ancestor failed: {result.stderr.strip()!r}) -- an undetermined "
            f"reachability answer is UNVERIFIABLE, never assumed reachable"
        )
    return (
        f"sealing commit {commit!r} exists as an object but is **not reachable from HEAD**. "
        f"Resolving proves the object is in the object database, not that it is part of this "
        f"repository's history: an unreferenced commit minted by 'git commit-tree' resolves "
        f"identically to a real one, so a seal compared against it would attest to a tree no "
        f"branch has ever contained and no history review can reach. This is also how a sound "
        f"archive presents after a legitimate squash/rebase merge, a branch deletion plus 'gc', "
        f"or a shallow clone -- all of which are 'cannot currently verify', never evidence of "
        f"tampering (AD-074 SS7B D3). Remedies: restore the sealing commit to a reachable "
        f"history (deepen the clone, or restore the ref), or issue a superseding Register record"
    )


def _committed_register_text(repo_root: Path) -> tuple[str | None, str | None]:
    """(text, error) for the Archive Seal Register **as committed at
    ``HEAD``** -- never the working-tree copy (governance hardening pass
    2026-07-26, post-AD-075 implementation audit; closes the second of
    AD-074 SS7B D5's two cases).

    D5 states the gap precisely and this closes exactly it: a *committed*
    Register tamper "is visible in ``git log -p`` / ``git blame``", but an
    *uncommitted* working-tree rewrite "leaves **no commit to review at
    all**" -- a case history review "does not reach at all". Reading the
    blob rather than the file removes the unreviewable case outright: an
    edit that is never committed is never read, so the Register the seal
    obeys is always one a reviewer can diff. It does not, and does not
    claim to, close D5's *first* case; a committed forgery is still only
    as defended as the human review of that commit.

    **``HEAD`` is the only available fixed point, and this is the one
    input that cannot be pinned to the sealing commit.** Every other
    input to the comparison is read at ``sealed_commit`` (SS7B D2, D9,
    BLOCKER 1/2), but the Register record *names* that commit and is
    therefore written strictly after it exists -- reading the Register at
    the commit it points to is circular by construction. ``HEAD``
    reintroduces a bounded time-varying dependency, in the same direction
    as `_unreachable_commit_error`'s: a Register record that has not been
    committed, or that has been rewritten out of the current history,
    yields ``UNVERIFIABLE``, never a spurious ``MATCHED`` and never a
    spurious ``MISMATCH``.

    ``(None, None)`` means no Register is committed at ``HEAD`` at all --
    including an unborn ``HEAD`` in a repository with no commits -- which
    is exactly the "no record has been issued" case, not an error."""
    blob_id = _sealed_blob_id("HEAD", ARCHIVE_SEAL_REGISTER_RELATIVE_PATH, repo_root=repo_root)
    if blob_id is None:
        return None, None
    raw = _sealed_blob_bytes("HEAD", ARCHIVE_SEAL_REGISTER_RELATIVE_PATH, repo_root=repo_root)
    if raw is None:
        return None, (
            f"{ARCHIVE_SEAL_REGISTER_RELATIVE_PATH} resolves to object {blob_id} at HEAD but its "
            f"content could not be read -- the Register is UNVERIFIABLE rather than read from the "
            f"working tree, which is not a reviewable source"
        )
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError as exc:
        return None, f"{ARCHIVE_SEAL_REGISTER_RELATIVE_PATH} at HEAD is not valid UTF-8 ({exc})"


def _read_blob(commit: str, path: str, *, repo_root: Path) -> str | None:
    """`git show <commit>:<path>`'s stdout, decoded as UTF-8 text, or
    None if the path does not exist at that commit or is not valid
    UTF-8. Read-only, same command class as freeze_verifier's own git
    invocations.

    The read runs in byte mode and the UTF-8 decode is performed here,
    explicitly (integrity audit, secondary item 3). Text-mode capture
    would decode with the ambient locale encoding, which on Windows
    means a legacy code page: a governance artifact containing any
    non-ASCII byte would then either raise or -- worse -- decode to
    different characters than the ones committed, and be parsed as if
    that were what the file said. A blob that is not valid UTF-8 is not
    a manifest this module can read, and returning None routes it to the
    caller's UNVERIFIABLE, never to a silently mis-decoded parse."""
    result = _run_git_bytes(["show", f"{commit}:{path}"], repo_root=repo_root)
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _sealed_tree_entries(commit: str, subdir: str, *, repo_root: Path) -> dict[str, tuple[str, str]] | None:
    """Every tree entry under `subdir` at `commit`, as
    ``{repo-relative path: (mode, object_id)}``. Paths are forward-slash
    separated (git's own format). None if the ls-tree invocation itself
    fails, if its output is not the documented shape, or if git's stored
    path bytes are not valid UTF-8 (an un-comparable path set is never a
    comparable one, so the caller reports UNVERIFIABLE rather than
    guessing).

    **Modes are read, not discarded** (hardening item M-5, 2026-07-26).
    The superseded ``--name-only`` form could not distinguish a regular
    file from a symlink or a gitlink, so both were fed to a comparison
    defined only for regular files. Carrying the mode lets `verify_seal`
    refuse them explicitly instead.

    **Object ids come from this same call** rather than from a
    per-file ``rev-parse <commit>:<path>``. It is the identical value
    from the identical tree, obtained in one process instead of one per
    file, and it removes a whole class of question about how a path with
    unusual characters survives being spliced into an object name.

    **NUL-delimited, never line-delimited** (integrity audit item 2).
    Without ``-z``, git *quotes* any path outside a conservative ASCII
    set -- ``research_archive/p/"r\\303\\251sum\\303\\251.md"`` -- and a
    quoted name matches nothing in the working-tree walk, so a perfectly
    sound archive containing one non-ASCII filename would report that
    file as both ``missing`` (the quoted form, absent from disk) and
    ``unexpected`` (the real form, absent from the quoted set). A path
    containing a literal newline would additionally split into two
    fabricated entries. Splitting on NUL removes both failure modes at
    the source: with ``-z`` git emits the stored bytes verbatim, with no
    quoting and no escaping, whatever ``core.quotepath`` is set to."""
    result = _run_git_bytes(["ls-tree", "-r", "-z", commit, "--", subdir], repo_root=repo_root)
    if result.returncode != 0:
        return None
    entries: dict[str, tuple[str, str]] = {}
    for chunk in result.stdout.split(b"\0"):
        if not chunk:
            continue
        # `<mode> SP <type> SP <object> TAB <path>` -- the path is
        # separated by TAB precisely so that a path containing spaces
        # cannot be confused with the metadata fields.
        metadata, separator, raw_path = chunk.partition(b"\t")
        if not separator:
            return None
        fields = metadata.split(b" ")
        if len(fields) != 3:
            return None
        try:
            path = raw_path.decode("utf-8")
            mode = fields[0].decode("utf-8")
            object_id = fields[2].decode("utf-8")
        except UnicodeDecodeError:
            return None
        entries[path] = (mode, object_id)
    return entries


def _sealed_blob_id(commit: str, repo_path: str, *, repo_root: Path) -> str | None:
    """The blob identity git recorded for `repo_path` in the sealing
    commit's tree, or None if the path does not resolve to an object at
    that commit.

    Used for the two sealed-commit reads that fall **outside** the
    archive subtree, which `_sealed_tree_entries` therefore does not
    enumerate: the ``.gitattributes`` chain from the repository root
    down (BLOCKER 2), and ``protected_file_hashes.json``'s existence
    (BLOCKER 1). The archive's own files take their sealed-side identity
    from `_sealed_tree_entries` instead -- one process for the whole
    tree rather than one per file.

    ``rev-parse <commit>:<path>`` reads the commit's tree directly. It
    consults neither the index nor ``HEAD``, and ``<commit>:<path>`` is
    an object name, not a pathspec -- a path containing glob characters
    is taken literally, never expanded."""
    result = _run_git(["rev-parse", "--verify", "--quiet", f"{commit}:{repo_path}"], repo_root=repo_root)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _working_tree_blob_id(repo_path: str, *, repo_root: Path) -> str | None:
    """The **right** side of the seal comparison: the blob identity the
    archive's on-disk file at `repo_path` would have if git hashed it
    now. None if the file cannot be read or hashed at all.

    ``hash-object`` reads the named file from the filesystem and applies
    the attributes and clean filters configured for ``--path`` -- which
    is why ``--path`` is passed even though it is the same path: it is
    what makes ``core.autocrlf``'s CRLF->LF conversion and
    ``.gitattributes``'s ``*.jsonl -text`` exemption apply on this side
    exactly as they applied when the sealed blob was written (SS7B D4).
    Without ``-w`` nothing is written to the object database; this is a
    computation, not a store. The index is not consulted, so neither
    ``update-index --assume-unchanged`` nor a missing index entry can
    change the answer."""
    filesystem_path = repo_root / repo_path
    result = _run_git(["hash-object", "--path", repo_path, "--", str(filesystem_path)], repo_root=repo_root)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _working_tree_entries(archive_dir: Path, *, repo_root: Path) -> tuple[set[str], set[str]]:
    """``(regular_file_paths, symlink_paths)`` -- everything physically
    present under `archive_dir` right now, as repo-root-relative,
    forward-slash-separated paths. The archive directory "as a set of
    paths and bytes" (AD-074 SS5.1), not merely the tracked-by-git
    subset.

    **Symlinks are enumerated separately and never followed** (hardening
    item M-5, 2026-07-26). The superseded implementation used
    ``rglob("*")`` with ``Path.is_file()``, which resolves symlinks: a
    symlink to a file elsewhere counted as a regular file and would have
    been hashed as *its target's* content, and a symlinked directory was
    descended into as though its contents were the archive's own. Both
    report on bytes that are not at the path the seal claims to be
    comparing. ``os.walk(followlinks=False)`` plus an explicit
    `_is_link_or_reparse_point` test keeps the distinction, and the
    caller refuses rather than guessing. A broken symlink lands here too
    -- it appears among the walk's filenames and is a symlink regardless
    of whether it resolves.

    ``followlinks=False`` is necessary but **not sufficient on Windows**
    (acceptance-audit item F-3): it suppresses descent into *symlinked*
    directories only, and an NTFS junction is not a symlink by that
    test, so the walk descended into junctions and reported the target
    directory's files as the archive's own. `_is_link_or_reparse_point`
    is what closes that; ``subdirectories.remove(name)`` is what makes
    the refusal effective rather than merely reported."""
    regular: set[str] = set()
    symlinks: set[str] = set()
    for directory, subdirectories, filenames in os.walk(archive_dir, followlinks=False):
        base = Path(directory)
        for name in list(subdirectories):
            candidate = base / name
            if _is_link_or_reparse_point(candidate):
                symlinks.add(candidate.relative_to(repo_root).as_posix())
                subdirectories.remove(name)  # never descend into it
        for name in filenames:
            candidate = base / name
            relative = candidate.relative_to(repo_root).as_posix()
            if _is_link_or_reparse_point(candidate):
                symlinks.add(relative)
            elif candidate.is_file():
                regular.add(relative)
    return regular, symlinks


def _is_link_or_reparse_point(candidate: Path) -> bool:
    """True if `candidate` redirects to somewhere other than itself --
    a POSIX/Windows symlink, or a Windows NTFS junction or mount point
    (acceptance-audit item F-3).

    ``Path.is_symlink()`` alone is not enough on Windows. A **junction**
    is a reparse point that redirects a directory, and ``is_symlink()``
    reports it as False, so the walk in `_working_tree_entries` descended
    into one and reported another directory's files as though they were
    the archive's own -- the identical defect M-5 closed for symlinks,
    left open on the one platform where it is *easier* to reach:
    creating a junction needs no privilege, while creating a symlink
    needs Developer Mode or an elevated process.

    Existing symlink behaviour is preserved exactly -- the symlink test
    runs first and is unchanged -- and this only ever adds refusals, so
    it can turn a wrong ``MATCHED``/``MISMATCH`` into ``UNVERIFIABLE``
    and never the reverse."""
    if candidate.is_symlink():
        return True
    is_junction = getattr(os.path, "isjunction", None)
    if is_junction is not None:
        try:
            if is_junction(candidate):
                return True
        except OSError:
            return False
    # Fallback for interpreters without `os.path.isjunction` (added in
    # 3.12). `st_file_attributes` exists only on Windows; everywhere else
    # the symlink test above is already the whole answer.
    try:
        attributes = os.lstat(candidate).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _info_attributes_error(repo_root: Path) -> str | None:
    """An explicit reason if ``$GIT_COMMON_DIR/info/attributes`` exists,
    None otherwise (hardening item BLOCKER 2, source 3).

    This is the one attribute source git offers no way to disable --
    verified: it still applies with ``GIT_ATTR_NOSYSTEM=1`` and
    ``core.attributesFile=`` both in force. It is also per-clone and
    never committed, so nothing about it is visible to a reviewer
    reading the repository. A seal result that could depend on it is
    therefore reported ``UNVERIFIABLE`` rather than computed: refusing
    to answer is honest, and answering would be an answer about a file
    no audit trail contains."""
    result = _run_git(["rev-parse", "--git-common-dir"], repo_root=repo_root)
    if result.returncode != 0:
        return "could not locate the git common directory to check for an info/attributes override"
    common_dir = Path(result.stdout.strip())
    if not common_dir.is_absolute():
        common_dir = repo_root / common_dir
    info_attributes = common_dir / "info" / "attributes"
    if info_attributes.exists():
        return (
            f"{info_attributes} exists -- it overrides the attributes that govern how the archive's "
            f"bytes are hashed, it cannot be disabled by any git config or environment variable, and "
            f"it is never committed, so its effect on this comparison is invisible to review. The seal "
            f"is UNVERIFIABLE while it is present rather than computed against rules no audit can see"
        )
    return None


def _sealed_blob_bytes(commit: str, repo_path: str, *, repo_root: Path) -> bytes | None:
    """The raw stored bytes of `repo_path` at `commit`, or None if it
    does not exist there. Unlike `_read_blob` this performs no decode,
    and unlike `_working_tree_blob_id` it applies no filters -- which is
    the point at its one call site (`_gitattributes_drift_error`), where
    routing the comparison through the attribute machinery would let an
    attribute file vouch for itself. Never used for archive content:
    SS7B D4's bar on ``cat-file`` stands for everything else."""
    result = _run_git_bytes(["cat-file", "blob", f"{commit}:{repo_path}"], repo_root=repo_root)
    if result.returncode != 0:
        return None
    return result.stdout


def _normalized_line_endings(content: bytes | None) -> bytes | None:
    """`content` with CRLF collapsed to LF, or None unchanged. Applied to
    both sides of the ``.gitattributes`` comparison so that a checkout
    performed under ``core.autocrlf=true`` is not mistaken for an edit --
    the same tolerance `hash-object --path` provides for archive
    content, obtained here without depending on the attribute stack
    being trustworthy."""
    return None if content is None else content.replace(b"\r\n", b"\n")


def _attribute_source_directories(paths: set[str]) -> list[str]:
    """Every directory whose ``.gitattributes`` can govern any path in
    `paths`: each path's ancestor directories, up to and including the
    repository root (represented as ``""``). git consults one
    ``.gitattributes`` per directory along that chain, so this is
    exactly the set that must be verified against the sealing commit --
    no wider, and never narrower."""
    directories = {""}
    for path in paths:
        parts = path.split("/")[:-1]
        for depth in range(1, len(parts) + 1):
            directories.add("/".join(parts[:depth]))
    return sorted(directories)


def _gitattributes_drift_error(commit: str, paths: set[str], *, repo_root: Path) -> str | None:
    """An explicit reason if any ``.gitattributes`` governing `paths`
    differs between the working tree and `commit`, None otherwise
    (hardening item BLOCKER 2, source 4).

    A ``.gitattributes`` edit is an edit to the seal's own comparison
    rules -- ``text``, ``eol``, and ``working-tree-encoding`` all change
    what bytes `hash-object` sees. Verifying these files with the same
    blob-identity mechanism the archive's own files use means a
    line-ending-only difference (the thing SS7B D4 exists to tolerate) is
    tolerated here identically, while a content change is caught.

    Absent on both sides is agreement. Present on one side only is
    drift: a ``.gitattributes`` that has appeared since the seal is a new
    rule source, and one that has disappeared is a lost one. Both are
    reported rather than absorbed.

    **These files are compared as raw bytes, not via ``hash-object``,
    and that is deliberate.** Hashing them would route this check
    through the very attribute machinery it exists to validate: a
    working-tree ``.gitattributes`` containing a rule about *itself*
    (``.gitattributes filter=launder``) would be hashed through that
    filter, which is arbitrary code and can emit whatever the sealed
    blob contained -- the file would certify its own integrity. Reading
    both sides raw (``cat-file blob`` against the file's own bytes)
    breaks the circularity outright. This is not the case SS7B D4 bars:
    D4 forbids comparing ``cat-file`` output against working-tree bytes
    for *archive content*, because git's line-ending conversion would
    manufacture a false ``MISMATCH``. Here the normalization is applied
    explicitly, on both sides, by this function -- and it is sound to do
    so because ``.gitattributes`` is a line-oriented config file whose
    meaning is unchanged by line-ending style, which is exactly not true
    of the archive content D4 governs."""
    for directory in _attribute_source_directories(paths):
        relative = f"{directory}/{GITATTRIBUTES_FILENAME}" if directory else GITATTRIBUTES_FILENAME
        sealed = _sealed_blob_bytes(commit, relative, repo_root=repo_root)
        candidate = repo_root / relative
        if _is_link_or_reparse_point(candidate):
            return f"{relative!r} is a symlink -- the seal does not follow symlinked attribute sources"
        working: bytes | None = None
        if candidate.is_file():
            try:
                working = candidate.read_bytes()
            except OSError as exc:
                return f"{relative!r} governs how the archive's bytes are hashed and could not be read ({exc})"
        if _normalized_line_endings(sealed) == _normalized_line_endings(working):
            continue
        if sealed is None:
            detail = "it does not exist at the sealing commit but does in the working tree"
        elif working is None:
            detail = "it exists at the sealing commit but not in the working tree"
        else:
            detail = "its content differs between the sealing commit and the working tree"
        return (
            f"{relative!r} governs how the archive's bytes are hashed, and {detail} -- the attribute "
            f"stack that defines this comparison is not the one the archive was sealed under, so the "
            f"result is UNVERIFIABLE rather than computed under changed rules (AD-074 SS7B D7)"
        )
    return None


def _filter_attribute_error(paths: set[str], *, repo_root: Path) -> str | None:
    """An explicit reason if a ``filter`` attribute applies to any path
    in `paths`, None otherwise (hardening item BLOCKER 2, residual).

    Pinning the attribute *stack* does not pin the filter *driver*: the
    attribute names a driver, and ``filter.<name>.clean`` -- the command
    git runs over the working-tree bytes before hashing them -- is git
    config, not an attributes file. It is arbitrary code, changeable
    without touching any artifact this module verifies, and it can make
    a tampered file hash to the sealed blob. ``filter.lfs.clean`` is
    present in ordinary developer global config, so this is a live
    driver on a real machine rather than a hypothetical one.

    A ``filter`` attribute on a compared path is therefore refused
    outright. This repository's ``.gitattributes`` assigns none, so the
    refusal costs nothing today and closes the hole permanently."""
    if not paths:
        return None
    ordered = sorted(paths)
    stdin = b"\0".join(path.encode("utf-8") for path in ordered)
    result = _run_git_bytes(["check-attr", "-z", "--stdin", "filter"], repo_root=repo_root, stdin=stdin)
    if result.returncode != 0:
        return "could not determine whether a clean filter applies to the archive's paths"
    fields = result.stdout.split(b"\0")
    # `-z` emits a flat `<path> NUL <attribute> NUL <value> NUL` stream.
    for index in range(0, len(fields) - 2, 3):
        try:
            path = fields[index].decode("utf-8")
            value = fields[index + 2].decode("utf-8")
        except UnicodeDecodeError:
            return "check-attr emitted output that is not valid UTF-8 -- cannot rule out a clean filter"
        if value in ("unspecified", "unset"):
            continue
        return (
            f"a 'filter' attribute ({value!r}) applies to {path!r} -- a clean filter is arbitrary code, "
            f"configured in git config rather than in any attributes file this module can verify, and it "
            f"transforms the bytes before they are hashed. The seal refuses to compare through it rather "
            f"than trust it (AD-074 SS7B D7)"
        )
    return None


def _read_archive_identity(archive_dir: Path) -> tuple[ArchiveIdentity | None, str | None]:
    """(identity, error). Reads archive_manifest.json's own
    ``project_id`` and ``lifecycle_version`` fields from the working
    tree at `archive_dir` -- the only manifest copy available before a
    sealing commit is known. ``project_id`` is never taken from the
    archive directory's name (even though A8-C6 requires the two to be
    byte-identical at write time -- the seal does not lean on that
    invariant holding), from HEAD or any other live git state, or from
    any field of transition_records.jsonl (AD-074 SS7B D1). Both return
    values None only when no manifest exists at all (a legacy archive,
    or one that hasn't been scaffolded) -- the caller reports
    UNVERIFIABLE identically to every other failure to resolve a
    project_id.

    ``lifecycle_version`` is read here only so that `verify_seal` can
    refuse a legacy archive explicitly (AC-74-9, hardening item M-3); it
    takes no other part in the comparison, and it is never used to
    decide *what* is compared."""
    manifest_path = archive_dir / ARCHIVE_MANIFEST_FILENAME
    if not manifest_path.exists():
        return None, f"{manifest_path} does not exist -- cannot resolve a project_id to look up in the Register"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        return None, f"{manifest_path} could not be read as JSON ({exc.__class__.__name__}: {exc})"
    if not isinstance(manifest, dict):
        return None, f"{manifest_path} does not contain a JSON object"
    project_id = manifest.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        return None, f"{manifest_path} has no non-empty string 'project_id' field"
    lifecycle_version = manifest.get("lifecycle_version")
    return (
        ArchiveIdentity(
            project_id=project_id,
            lifecycle_version=lifecycle_version if isinstance(lifecycle_version, str) else None,
        ),
        None,
    )


def _legacy_archive_error(identity: ArchiveIdentity) -> str | None:
    """An explicit reason if this archive is a legacy archive, None
    otherwise (AC-74-9, hardening item M-3, 2026-07-26).

    AC-74-9 requires that the three legacy archives report
    ``UNVERIFIABLE``, never ``MATCHED`` and never ``MISMATCH``. Before
    this pass that held only by accident: the named three carry no
    ``archive_manifest.json``, so they failed at project_id resolution
    for an unrelated reason. Anything that gave one a manifest -- or any
    archive declaring ``lifecycle_version: "legacy"`` -- would have
    sailed straight through to a comparison, and a Register record for
    it would have produced ``MATCHED``. The criterion is now true by
    mechanism rather than by circumstance.

    A legacy archive's bytes belong to ``protected_file_hashes.json``
    (SS2 O-3), which is a different control with a different root of
    trust. "Exempt from a layout check" is not "sealed", and neither is
    "covered by the Phase-0 fixture" (SS5.6)."""
    if identity.project_id in LEGACY_ARCHIVE_PROJECT_IDS:
        return (
            f"{identity.project_id!r} is a named legacy archive (docs/RESEARCH_ARCHIVE_MANIFEST.md "
            f"Applicability) -- legacy archives are never sealed (AC-74-9); their bytes are "
            f"tests/fixtures/protected_file_hashes.json's claim, not the Seal's"
        )
    if identity.lifecycle_version == "legacy":
        return (
            f"{ARCHIVE_MANIFEST_FILENAME} declares lifecycle_version=legacy -- legacy archives are "
            f"never sealed (AC-74-9), and 'exempt from the v1 layout check' is not 'sealed'"
        )
    return None


def _latest_register_record(project_id: str, text: str | None) -> tuple[SealRegisterRecord | None, str | None]:
    """(record, error). `text` is the Register's **committed** content at
    ``HEAD`` (`_committed_register_text`), or None when no Register is
    committed there at all -- this reader never touches the filesystem,
    so an uncommitted working-tree Register cannot reach it.

    ``(None, None)`` -- no Register record exists for `project_id` at
    all (an empty or absent Register, or one with records for other
    projects only). AD-074 SS5.6 "No Register record for this archive".

    ``(None, <error>)`` -- either (a) a record for `project_id` exists,
    but the *latest* one by file order (C-2) is malformed, which fails
    closed and never falls back to an earlier valid record for the same
    `project_id` (SS5.5 C-3); (b) a line this reader cannot attribute to
    any project at all appears *after* that project's latest candidate
    (see below); or (c) the committed Register is not canonical JSONL,
    which is fatal for every archive checked against it in this run, not
    just this one (SS5.5 C-3 third bullet).

    **Positional fail-closed rule for unattributable lines (integrity
    audit item 5, 2026-07-26).** A line that is not valid JSON, is not a
    JSON object, or whose own `project_id` field is missing/empty/
    non-string cannot be positively matched to *any* project_id string.
    The superseded implementation skipped such lines outright, which
    made a valid record followed by a corrupt append resolve to the
    valid record -- a silent fallback to a stale sealing commit in
    exactly the situation ("something was appended and we cannot read
    it") where fail-closed is the entire point. It is also indefensible
    on the evidence: an unreadable append is *more* likely to be this
    project's re-seal than not, since a re-seal is the only reason
    anything is ever appended for a project that already has a record.

    The rule is positional, and per project:

    - unattributable lines *before* a project's latest candidate are
      ignored (C-3: a bad line is a self-contained parse failure, and a
      later valid record for that project supersedes whatever the bad
      line might have said);
    - an unattributable line *after* that project's latest candidate
      invalidates that project's lookup -- UNVERIFIABLE, never a
      fallback to the earlier record;
    - a project whose own latest candidate sits after every
      unattributable line is unaffected, and so is a project with a
      well-formed record of its own -- C-3's closing paragraph, "a
      single bad line is ... not a reason to refuse the whole file", is
      preserved for exactly the projects it was written to protect.

    A project with *no* candidate at all is invalidated by any
    unattributable line (its "latest candidate" is at position -1, so
    every such line is after it): nothing rules out that line having
    been this project's only seal, and reporting "no seal has been
    issued" would assert something this reader cannot know.

    **Why not ``canonical_jsonl.read_canonical_jsonl`` (integrity audit,
    secondary item 1).** It is not compatible with C-3, in kind rather
    than in detail: it raises on the first unparsable line and on any
    whole-file format violation (CRLF, missing trailing newline), so one
    bad line would refuse the Register for *every* project -- the
    whole-file refusal C-3's closing paragraph reserves for a file that
    cannot be read at all. Per-project attribution is a requirement of
    the contract, not an implementation preference, so this reader stays
    line-local.

    **The validation it would have brought is applied here instead**
    (hardening item M-6, 2026-07-26). Declining to reuse the canonical
    reader is not licence to be laxer than it: its two whole-file rules
    -- LF-only, and a required trailing newline -- are enforced below and
    fail for every project, which is the correct scope for them, since a
    file that is not canonical JSONL cannot be split into attributable
    records in the first place. Its per-line strictness stays
    positional, per C-3. The one place this reader was *silently* laxer
    than the canonical reader is also fixed below: it split on
    ``str.splitlines()``, which breaks on line separators JSON permits
    unescaped inside a string."""
    if text is None:
        return None, None
    # Named for the error messages only: this reader is handed committed
    # content and never opens a path.
    register_path = f"HEAD:{ARCHIVE_SEAL_REGISTER_RELATIVE_PATH}"

    # Whole-file canonical-JSONL validation (hardening item M-6,
    # 2026-07-26), applied here rather than delegated to
    # `canonical_jsonl.read_canonical_jsonl` for the reason given below.
    # These are that reader's own two whole-file rules, and a violation
    # of either is the C-3 third-bullet condition -- the file cannot be
    # read as the format it claims to be -- so it fails for every
    # project, not positionally.
    if "\r" in text:
        return None, (
            f"{register_path} is not canonical JSONL -- it contains CR line endings, and the Register "
            f"is LF-only. A CR-terminated file cannot be split into records this reader can attribute, "
            f"so the whole file is refused rather than parsed under a guess"
        )
    if text and not text.endswith("\n"):
        return None, (
            f"{register_path} is not canonical JSONL -- it is missing the required trailing newline, "
            f"which is how an append that was interrupted mid-record presents. The last line cannot be "
            f"assumed complete, so the whole file is refused"
        )

    # Split on LF alone, never `str.splitlines()` (same hardening item).
    # `splitlines()` also breaks on U+2028, U+2029, U+0085, VT and FF --
    # characters that are legal, unescaped content inside a JSON string
    # under `ensure_ascii=False`, which `canonical_jsonl` writes. One
    # such character inside a `sealed_by` field would have split one
    # valid record into two unparseable fragments, and the positional
    # rule below would then have reported a corrupt Register for a file
    # that was never corrupt. Splitting on LF matches exactly what the
    # writer joins on.
    lines = text[:-1].split("\n") if text else []

    candidates: list[tuple[int, dict[str, object]]] = []
    unattributable_lines: list[int] = []
    for index, line in enumerate(lines):
        if not line:
            # A blank line is a canonical-JSONL violation, not
            # whitespace to skip: it is unattributable to any project,
            # and is treated as such under the positional rule below.
            unattributable_lines.append(index)
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            unattributable_lines.append(index)
            continue
        if not isinstance(row, dict):
            unattributable_lines.append(index)
            continue
        row_project_id = row.get("project_id")
        if not isinstance(row_project_id, str) or not row_project_id:
            unattributable_lines.append(index)
            continue
        if row_project_id != project_id:
            continue
        candidates.append((index, row))  # file order: the last match for this project_id wins (C-2)

    latest_index = candidates[-1][0] if candidates else -1
    trailing_unattributable = [index + 1 for index in unattributable_lines if index > latest_index]
    if trailing_unattributable:
        return None, (
            f"Archive Seal Register line(s) {trailing_unattributable} could not be parsed as a JSON "
            f"object carrying a non-empty string 'project_id', and appear after the latest record for "
            f"{project_id!r} -- this project's lookup fails closed rather than falling back to an "
            f"earlier record (AD-074 SS5.5 C-3)"
        )

    if not candidates:
        return None, None

    latest_row = candidates[-1][1]

    missing = [field for field in _REQUIRED_RECORD_FIELDS if field not in latest_row]
    if missing:
        return None, f"latest Archive Seal Register record for {project_id!r} is missing required field(s): {missing}"

    schema_version = latest_row["schema_version"]
    # bool is an int subclass in Python; `"schema_version": true` is not a
    # schema version, and must not be admitted as the integer 1.
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        return None, (
            f"latest Archive Seal Register record for {project_id!r} has a non-integer "
            f"'schema_version' ({schema_version!r}) -- required, integer, currently {SUPPORTED_REGISTER_SCHEMA_VERSION}"
        )
    if schema_version != SUPPORTED_REGISTER_SCHEMA_VERSION:
        return None, (
            f"latest Archive Seal Register record for {project_id!r} declares unsupported "
            f"'schema_version' {schema_version} -- this implementation reads only "
            f"{SUPPORTED_REGISTER_SCHEMA_VERSION}, and cannot vouch for the field meanings of any other"
        )

    supersedes = latest_row["supersedes"]
    if supersedes is not None and not isinstance(supersedes, str):
        return None, f"latest Archive Seal Register record for {project_id!r} has a non-null, non-string 'supersedes'"

    # Supersession semantics (AD-074 SS5.5 C-1/C-2, integrity audit
    # secondary item 2). `supersedes` is null for a first-time seal and
    # names the superseded record's sealed_commit otherwise -- which is
    # what makes a re-seal attributable rather than merely inferable
    # from record order. A latest record that does not chain to the
    # previous record for its own project is a Register whose
    # supersession history this reader cannot reconstruct, so it is
    # UNVERIFIABLE rather than read as if the chain held.
    if len(candidates) >= 2:
        previous_row = candidates[-2][1]
        previous_commit = previous_row.get("sealed_commit")
        if not isinstance(previous_commit, str) or not previous_commit:
            return None, (
                f"the record preceding the latest one for {project_id!r} has no usable 'sealed_commit', "
                f"so the latest record's 'supersedes' cannot be checked against it"
            )
        if supersedes != previous_commit:
            return None, (
                f"latest Archive Seal Register record for {project_id!r} has 'supersedes' "
                f"{supersedes!r}, which does not name the previous record's 'sealed_commit' "
                f"({previous_commit!r}) -- a re-seal must name what it supersedes"
            )
    elif supersedes is not None:
        return None, (
            f"the only Archive Seal Register record for {project_id!r} has a non-null 'supersedes' "
            f"({supersedes!r}) but there is no earlier record for it to supersede"
        )

    sealed_commit = latest_row["sealed_commit"]
    if not isinstance(sealed_commit, str) or not sealed_commit:
        return None, f"latest Archive Seal Register record for {project_id!r} has an empty or non-string 'sealed_commit'"

    sealed_at = latest_row["sealed_at"]
    if not isinstance(sealed_at, str) or not sealed_at:
        return None, f"latest Archive Seal Register record for {project_id!r} has an empty or non-string 'sealed_at'"

    sealed_by = latest_row["sealed_by"]
    if not isinstance(sealed_by, str) or not sealed_by:
        return None, f"latest Archive Seal Register record for {project_id!r} has an empty or non-string 'sealed_by'"

    return (
        SealRegisterRecord(
            schema_version=schema_version,
            project_id=project_id,
            sealed_commit=sealed_commit,
            sealed_at=sealed_at,
            sealed_by=sealed_by,
            supersedes=supersedes,
        ),
        None,
    )


def _dataset_manifest_exclusion_set(
    sealed_commit: str, archive_relative_prefix: str, *, repo_root: Path
) -> tuple[set[str] | None, str | None]:
    """The archive-relative `snapshot_path` entries of
    dataset_manifest.json, **as it reads at the sealing commit** (AD-074
    SS7B D2) -- never the working tree's current copy, which would make
    the seal's own scope a time-varying fact. Excluded because AD-073
    Decision part 8 assigns those bytes to DatasetIntegrityChecker's
    domain, not because sealing them would duplicate a hash record (SS7A
    B-2): the seal asserts no hash of its own.

    An absent or unreadable dataset_manifest.json at the sealing commit
    makes the exclusion set underivable, which must never fall back to
    "exclude nothing" (AC-74-5) -- it is reported as (None, <reason>)."""
    manifest_repo_path = f"{archive_relative_prefix}/{DATASET_MANIFEST_FILENAME}"
    content = _read_blob(sealed_commit, manifest_repo_path, repo_root=repo_root)
    if content is None:
        return None, (
            f"dataset_manifest.json not found or unreadable at {manifest_repo_path!r} "
            f"as of sealing commit {sealed_commit!r} -- exclusion set underivable"
        )
    try:
        manifest = parse_dataset_manifest_text(content, source=f"{sealed_commit}:{manifest_repo_path}")
    except DatasetManifestError as exc:
        return None, f"dataset_manifest.json at {sealed_commit} could not be parsed: {exc}"

    exclusions: set[str] = set()
    for entry in manifest.datasets:
        if not is_contained_snapshot_path(entry.snapshot_path):
            return None, (
                f"dataset_manifest.json at sealing commit {sealed_commit!r} declares snapshot_path "
                f"{entry.snapshot_path!r} for dataset {entry.dataset_id!r}, which does not resolve to a "
                f"path strictly inside {_DATASET_SNAPSHOT_ROOT!r}. An exclusion names a file the Seal "
                f"will not check, so an exclusion that escapes the dataset directory removes an "
                f"arbitrary governance file from the comparison -- the exclusion set is refused rather "
                f"than applied (AD-074 SS5.1 as amended 2026-07-26)"
            )
        exclusions.add(f"{archive_relative_prefix}/{entry.snapshot_path}")
    return exclusions, None


def is_contained_snapshot_path(snapshot_path: str) -> bool:
    """True iff `snapshot_path` is an archive-relative path resolving
    strictly inside ``dataset_hashes/`` (hardening item M-1,
    2026-07-26).

    Every entry of the exclusion set is a file the Seal then declines to
    check, so the exclusion set is a *privilege*, and an unvalidated
    ``snapshot_path`` hands that privilege to whatever the manifest
    says. ``../../decision_log.md`` would silently drop a governance
    artifact out of the comparison; ``.`` or an absolute path would drop
    something stranger. Reading the manifest at the sealing commit (D2)
    means only a party who controls that commit can attempt this -- but
    a control whose integrity depends on the trustworthiness of the
    thing it is verifying is not a control, and this module is meant to
    be a trust anchor.

    Purely lexical, and deliberately so: no filesystem resolution is
    performed, because a rule that consults the live filesystem would
    reintroduce exactly the time-varying input D2 removed. Backslashes
    and colons are rejected outright rather than interpreted -- git
    stores paths forward-slash separated, so either character is a
    Windows path that has leaked into a manifest, not a path git will
    agree with."""
    if not snapshot_path or "\\" in snapshot_path or ":" in snapshot_path:
        return False
    if snapshot_path.startswith("/"):
        return False
    parts = snapshot_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return len(parts) >= 2 and parts[0] == _DATASET_SNAPSHOT_ROOT


def _protected_file_hashes_exclusion_set(
    sealed_commit: str, *, repo_root: Path
) -> tuple[set[str] | None, str | None]:
    """The full key set of tests/fixtures/protected_file_hashes.json,
    **as it reads at the sealing commit** (hardening item BLOCKER 1,
    2026-07-26) -- never the working tree's current copy. AC-74-4: no
    path this fixture names is ever compared by the Seal branch.

    **Why the source moved.** The superseded implementation read the
    working-tree copy, on the reasoning that the fixture is immutable
    Phase-0 data by convention and so has no "which copy" ambiguity. A
    convention is not a trust boundary. This file *controls what the
    Seal declines to check*, so whoever can write it can exempt any
    archive path from verification: appending
    ``{"research_archive/<project>/methodology.md": "..."}`` after the
    seal was issued turns a tampered file into a ``MATCHED`` archive,
    with no commit, no Register record, and nothing for a reviewer to
    see. That is the identical failure D2 already closed for
    ``dataset_manifest.json``, left open on the other exclusion source
    only because the fixture's immutability was believed to substitute
    for it. Both exclusion sources are now fixed at the sealing commit,
    so the seal's scope is a property of the commit and nothing else.

    **Fail-closed shape, and why it differs from D2's.** Absent at the
    sealing commit means the fixture named no paths then, which is a
    *derived* answer -- exclude nothing -- not an underivable one; the
    comparison that follows is strictly wider, never narrower, so
    nothing escapes the seal. Present but unreadable is genuinely
    underivable and is UNVERIFIABLE. D2's rule for
    ``dataset_manifest.json`` is UNVERIFIABLE in *both* cases because
    AC-74-5 fixes it that way and because that manifest is a required
    item of every v1 archive, so its absence at the sealing commit is
    itself evidence something is wrong; the Phase-0 fixture is a
    platform file with no such per-archive requirement."""
    sealed_object = _sealed_blob_id(sealed_commit, PROTECTED_FILE_HASHES_RELATIVE_PATH, repo_root=repo_root)
    if sealed_object is None:
        return set(), None
    content = _read_blob(sealed_commit, PROTECTED_FILE_HASHES_RELATIVE_PATH, repo_root=repo_root)
    if content is None:
        return None, (
            f"{PROTECTED_FILE_HASHES_RELATIVE_PATH} exists at sealing commit {sealed_commit!r} but "
            f"could not be read as UTF-8 text -- exclusion set underivable"
        )
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return None, (
            f"{PROTECTED_FILE_HASHES_RELATIVE_PATH} at sealing commit {sealed_commit!r} is not valid "
            f"JSON ({exc}) -- exclusion set underivable"
        )
    if not isinstance(data, dict):
        return None, (
            f"{PROTECTED_FILE_HASHES_RELATIVE_PATH} at sealing commit {sealed_commit!r} does not "
            f"contain a JSON object -- exclusion set underivable"
        )
    return set(data.keys()), None


@dataclass(frozen=True, slots=True)
class SealingCommit:
    """A resolved, reachable sealing commit and the archive it seals.
    The common prefix of every sealed-archive question -- the Seal's own
    comparison, and `core.governance.dataset_integrity`'s independent
    check of the dataset bytes the Seal excludes -- so that both read the
    *same* commit, established by the *same* rules, from the *same*
    Register. Two components deriving a sealing commit two ways is the
    duplicate-source-of-truth failure AD-073 Decision part 8 exists to
    prevent, one level up."""

    project_id: str
    sealed_commit: str
    archive_relative_prefix: str
    repo_root: Path


def resolve_sealing_commit(
    archive_dir: Path, *, repo_root: Path | None = None
) -> tuple[SealingCommit | None, str | None]:
    """(sealing_commit, reason). Resolves which commit `archive_dir` is
    sealed at, applying every trust rule in this module's docstring:
    identity from the archive's own manifest, the legacy refusal, the
    **committed** Register at ``HEAD``, the fixed-object-id syntax check,
    the resolution round trip, and reachability from ``HEAD``.

    ``(None, <reason>)`` for every case that cannot establish one; the
    caller reports it as its own branch's UNVERIFIABLE/FAILED. Raises
    only `NotAGitRepositoryError`, for an environmental problem.

    **Git repository status is now checked before the Register lookup**,
    where it previously came after. That ordering was justified by the
    Register being "a plain file read that needs no git at all" -- which
    ceased to be true when the Register moved to committed content
    (`_committed_register_text`). Identity resolution and the legacy
    refusal still precede it and still need no git, so the two outcomes
    that ordering protected (no manifest, a legacy archive) are decided
    exactly as before."""
    root = (repo_root if repo_root is not None else REPO_ROOT).resolve()
    archive_dir = archive_dir.resolve()

    identity, identity_error = _read_archive_identity(archive_dir)
    if identity is None:
        return None, identity_error or "project_id could not be resolved"

    # Before the Register is even consulted: a legacy archive is never
    # sealed, so a Register record naming one is an issuance error this
    # reader refuses to act on rather than a seal to verify (AC-74-9).
    legacy_error = _legacy_archive_error(identity)
    if legacy_error is not None:
        return None, legacy_error

    _assert_git_repo(root)  # raises NotAGitRepositoryError -- caller translates

    register_text, register_error = _committed_register_text(root)
    if register_error is not None:
        return None, register_error
    record, record_error = _latest_register_record(identity.project_id, register_text)
    if record is None:
        return None, (
            record_error
            or f"no committed Archive Seal Register record for project_id {identity.project_id!r}"
        )

    # The sealing commit must be a fixed object id, checked syntactically
    # before any resolution is attempted, then confirmed by round trip.
    fixed_id_error = _fixed_commit_id_error(record.sealed_commit)
    if fixed_id_error is not None:
        return None, fixed_id_error
    resolved_commit = _resolved_commit_id(record.sealed_commit, repo_root=root)
    if resolved_commit is None:
        return None, f"sealing commit {record.sealed_commit!r} does not exist or is not readable"
    if resolved_commit != record.sealed_commit:
        return None, (
            f"sealing commit {record.sealed_commit!r} resolves to {resolved_commit!r} -- it names a "
            f"reference rather than the object it appears to name, and a seal's fixed point may not be "
            f"a name that something else can re-point"
        )

    # Resolution proves presence in the object database, never membership
    # in this repository's history -- see `_unreachable_commit_error`.
    unreachable_error = _unreachable_commit_error(record.sealed_commit, repo_root=root)
    if unreachable_error is not None:
        return None, unreachable_error

    try:
        archive_relative_prefix = archive_dir.relative_to(root).as_posix()
    except ValueError:
        return None, f"{archive_dir} is not inside repo_root {root} -- cannot compare against git history"

    return (
        SealingCommit(
            project_id=identity.project_id,
            sealed_commit=record.sealed_commit,
            archive_relative_prefix=archive_relative_prefix,
            repo_root=root,
        ),
        None,
    )


def read_text_at_commit(commit: str, repo_path: str, *, repo_root: Path) -> str | None:
    """`repo_path`'s content at `commit`, as UTF-8 text, or None if it
    does not exist there or is not valid UTF-8. The public form of
    `_read_blob`, for sibling governance modules that must read a
    sealed-commit artifact through the same attribute-pinned, index-free
    git access this module already establishes rather than opening a
    second, laxer path to git of their own."""
    return _read_blob(commit, repo_path, repo_root=repo_root)


def verify_seal(archive_dir: Path, *, repo_root: Path | None = None) -> SealOutcome:
    """Verify `archive_dir` against the Archive Seal Register. Never
    raises for a failed verification -- only `NotAGitRepositoryError`,
    for an environmental problem, mirroring `freeze_verifier.verify_freeze`'s
    own contract.

    **`archive_dir` is resolved exactly once**, at `resolve_sealing_commit`'s
    public boundary (integrity audit item 3), and every function below
    receives the resolved path. A caller-supplied relative path
    (`Path("research_archive/reference_h4")`) previously reached
    `_working_tree_paths`, whose `Path.relative_to(repo_root)` -- with
    `repo_root` already absolute -- raised `ValueError` out of a
    verifier whose entire contract is to answer, never to raise, for a
    verification question. Resolving at the boundary rather than at each
    use also guarantees the path set, the repo-relative prefix, and the
    filesystem reads all describe the same directory."""
    sealing, sealing_error = resolve_sealing_commit(archive_dir, repo_root=repo_root)
    if sealing is None:
        return _unverifiable(sealing_error or "no sealing commit could be resolved")

    root = sealing.repo_root
    archive_dir = archive_dir.resolve()
    archive_relative_prefix = sealing.archive_relative_prefix

    # The attribute stack is a third input to the comparison alongside
    # the sealing commit and the archive bytes (see
    # `_ATTRIBUTE_TRUST_MODEL`). The one source no config can disable is
    # checked first, before any hashing happens under rules that source
    # could be silently governing.
    info_attributes_error = _info_attributes_error(root)
    if info_attributes_error is not None:
        return _unverifiable(info_attributes_error)

    dataset_exclusions, dataset_error = _dataset_manifest_exclusion_set(
        sealing.sealed_commit, archive_relative_prefix, repo_root=root
    )
    if dataset_exclusions is None:
        return _unverifiable(dataset_error or "dataset-manifest exclusion set underivable")

    protected_exclusions, protected_error = _protected_file_hashes_exclusion_set(
        sealing.sealed_commit, repo_root=root
    )
    if protected_exclusions is None:
        return _unverifiable(protected_error or "protected_file_hashes.json exclusion set underivable")

    # Only paths inside this archive's own comparison domain are
    # reported (integrity audit, secondary item 4). protected_file_hashes.json
    # names ~36 platform files, most of which have never been under
    # research_archive/ at all; listing them as this archive's
    # "excluded paths" described the fixture rather than the seal's
    # bounded coverage, which is the one thing SS5.6 asks the field to
    # make auditable. Behaviour is unchanged: both path sets below
    # contain only paths under this prefix, so out-of-domain entries
    # subtract nothing.
    domain_prefix = f"{archive_relative_prefix}/"
    excluded = {
        path for path in (dataset_exclusions | protected_exclusions) if path.startswith(domain_prefix)
    }
    excluded_paths = tuple(sorted(excluded))

    sealed_entries = _sealed_tree_entries(sealing.sealed_commit, archive_relative_prefix, repo_root=root)
    if sealed_entries is None:
        return _unverifiable(
            f"could not enumerate {archive_relative_prefix!r} at sealing commit {sealing.sealed_commit!r} "
            f"(ls-tree failed, its output was not the documented shape, or its stored path bytes are "
            f"not valid UTF-8)",
            excluded_paths=excluded_paths,
        )

    working_paths, working_symlinks = _working_tree_entries(archive_dir, repo_root=root)

    # Non-regular entries, on either side, are refused rather than
    # compared (hardening item M-5). `hash-object` computes a meaningful
    # identity only for a regular file: a symlink's blob is its target
    # path, and a gitlink is a commit id belonging to another repository
    # this module never reads. Comparing either would state a guarantee
    # the mechanism does not support, so the seal declines to state one.
    irregular = sorted(
        f"{path} (mode {mode})" for path, (mode, _) in sealed_entries.items() if mode not in _REGULAR_FILE_MODES
    )
    if irregular:
        return _unverifiable(
            f"sealing commit {sealing.sealed_commit!r} records non-regular tree entries under "
            f"{archive_relative_prefix!r}: {irregular}. The Seal compares regular files only -- a symlink "
            f"(120000) or a gitlink/submodule (160000) is outside what blob-identity comparison can "
            f"honestly answer, and is reported UNVERIFIABLE rather than compared (AD-074 SS7B D8)",
            excluded_paths=excluded_paths,
        )
    if working_symlinks:
        return _unverifiable(
            f"the archive directory contains symlink(s) or reparse point(s): {sorted(working_symlinks)}. "
            f"The Seal compares regular files only and never follows a symlink, an NTFS junction, or any "
            f"other reparse point -- hashing or descending into one would report on bytes that are not at "
            f"the path being compared (AD-074 SS7B D8)",
            excluded_paths=excluded_paths,
        )

    sealed_paths = set(sealed_entries)

    # Path-set comparison runs over the **full** sets; only the content
    # comparison below is narrowed by `excluded` (hardening item M-4).
    # An exclusion assigns a file's *bytes* to another control
    # (DatasetIntegrityChecker, or the Phase-0 fixture); neither of those
    # controls asserts that the file still exists, and SS5.2's threat
    # table promises that a file deleted from a closed archive is
    # detected. Deleting an excluded file outright previously produced no
    # finding from any mechanism at all.
    findings: list[SealFinding] = []
    for path in sorted(sealed_paths - working_paths):
        findings.append(SealFinding(path=path, kind="missing"))
    for path in sorted(working_paths - sealed_paths):
        findings.append(SealFinding(path=path, kind="unexpected"))

    compared = (sealed_paths & working_paths) - excluded

    # The attribute stack governs every hash computed below, so it is
    # verified before the first one is (see `_ATTRIBUTE_TRUST_MODEL`).
    attributes_error = _gitattributes_drift_error(sealing.sealed_commit, compared, repo_root=root)
    if attributes_error is not None:
        return _unverifiable(attributes_error, excluded_paths=excluded_paths)
    filter_error = _filter_attribute_error(compared, repo_root=root)
    if filter_error is not None:
        return _unverifiable(filter_error, excluded_paths=excluded_paths)

    for path in sorted(compared):
        # sealed commit tree -> archive filesystem, compared as blob
        # identities and never through the index (see the module
        # docstring for why `git diff` is not usable here).
        sealed_blob = sealed_entries[path][1]
        working_blob = _working_tree_blob_id(path, repo_root=root)
        if working_blob is None:
            # The archive-filesystem side could not be computed at all.
            # That is "cannot currently verify", not "modified" -- this
            # module must never conflate the two (SS7B D3) -- and an
            # incomplete comparison is never MATCHED.
            return _unverifiable(
                f"could not compute a blob identity for {path!r} on the archive filesystem side "
                f"at sealing commit {sealing.sealed_commit!r} -- the comparison is incomplete",
                excluded_paths=excluded_paths,
            )
        if sealed_blob != working_blob:
            findings.append(SealFinding(path=path, kind="modified"))
    findings.sort(key=lambda finding: (finding.path, finding.kind))

    if findings:
        return SealOutcome(
            status="mismatch",
            findings=tuple(findings),
            reason=f"{len(findings)} finding(s) against sealing commit {sealing.sealed_commit}",
            excluded_paths=excluded_paths,
        )
    return SealOutcome(status="matched", findings=(), reason=None, excluded_paths=excluded_paths)
