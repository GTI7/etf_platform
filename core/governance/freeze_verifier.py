"""Freeze-commit verification (Governance Tier 1, item 1).

Automates ``docs/RESEARCH_PLATFORM_RETROSPECTIVE.md`` Section 3 item 1:
confirms a claimed freeze commit is real, resolvable, and that the files
it is claimed to cover have not drifted from that commit's content --
the check that would have caught ``attempt_001_specification.md``'s
uncommitted state and ``REFERENCE_H3_PREVALIDATION_PLAN.md``'s
modified-but-uncommitted drift at write time instead of at a later,
dedicated audit pass (see ``docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md``).

**Temporary pre-registry interface.** ``docs/PLATFORM_ARCHITECTURE_V1.md``
Section 4.4 sketches ``FreezeVerifier.verify_freeze(self, freeze_id:
FreezeId) -> VerificationResult``, where ``FreezeId`` is a Research-domain
concept backed by a project registry. No such registry exists yet --
``core/research/`` is still an empty stub (Migration Plan Step 5, not yet
built), and ``ProjectId``/``ArtifactRef`` are reserved names only (AD-031),
not a working registry. Building a ``FreezeId`` registry here, ahead of
Research existing, would be exactly the "abstraction ahead of a second
concrete need" this repository's governance rules rule out. This module
therefore takes a raw ``commit_ref: str`` plus an explicit list of
covered paths instead -- precisely what every existing frozen document
already states in prose today (see e.g.
``docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md``'s own freeze-commit
table). This is a deliberate, documented scope reduction, not a silent
divergence -- see ``docs/ARCHITECTURE_DECISIONS.md`` AD-033. When
``core/research/`` eventually exists, a ``FreezeId``-taking wrapper can
call this function; this function's own signature does not need to
change.

**What verification proves, and what it does not.** A ``VERIFIED``
result proves the covered files are byte-identical to their content at
the claimed commit, with no uncommitted drift on top -- i.e. the freeze
is *reproducible*. It proves nothing about whether the frozen
methodology was itself correct, adequate, or approved; it is not a
substitute for a Level 2/3 review and does not constitute approval of
any research decision. It answers exactly one question: "is this
document's own freeze claim, as stated, actually true of the current
repository state?"

Read-only. Every git invocation here is a read-only plumbing command
(``rev-parse``, ``cat-file -e``, ``diff``, ``status --porcelain``);
nothing in this module ever writes, commits, checks out, or resets
anything.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class FreezeStatus(str, Enum):
    """Three-way outcome -- deliberately not a boolean. A verification run
    can fail to complete (bad ref, path never existed at that commit) in a
    way that is categorically different from completing and finding drift."""

    VERIFIED = "verified"
    DRIFTED = "drifted"
    UNVERIFIABLE = "unverifiable"


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Plain, serializable outcome of one freeze-verification run."""

    commit_ref: str
    resolved_hash: str | None
    status: FreezeStatus
    drifted_files: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return self.status is FreezeStatus.VERIFIED


class NotAGitRepositoryError(RuntimeError):
    """Raised for environmental failures only -- not for a failed
    verification, which is a normal ``VerificationResult`` outcome."""


def _run_git(args: list[str], *, repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_git_repo(repo_root: Path) -> None:
    result = _run_git(["rev-parse", "--is-inside-work-tree"], repo_root=repo_root)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise NotAGitRepositoryError(f"{repo_root} is not inside a git working tree")


def _resolve_commit(commit_ref: str, *, repo_root: Path) -> str | None:
    result = _run_git(["rev-parse", "--verify", "--quiet", f"{commit_ref}^{{commit}}"], repo_root=repo_root)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _path_exists_at_commit(resolved_hash: str, path: str, *, repo_root: Path) -> bool:
    result = _run_git(["cat-file", "-e", f"{resolved_hash}:{path}"], repo_root=repo_root)
    return result.returncode == 0


def _has_committed_drift(resolved_hash: str, path: str, *, repo_root: Path) -> bool:
    """True if HEAD's content for `path` differs from its content at
    `resolved_hash` (a committed change since the freeze)."""
    result = _run_git(["diff", "--quiet", resolved_hash, "HEAD", "--", path], repo_root=repo_root)
    return result.returncode != 0


def _has_uncommitted_drift(path: str, *, repo_root: Path) -> bool:
    """True if the working tree has any uncommitted change to `path`
    relative to HEAD (staged or unstaged)."""
    result = _run_git(["status", "--porcelain", "--", path], repo_root=repo_root)
    return bool(result.stdout.strip())


def verify_freeze(
    commit_ref: str,
    covered_paths: Iterable[Path | str],
    *,
    repo_root: Path | None = None,
) -> VerificationResult:
    """Verify that `covered_paths` match their content at `commit_ref`,
    with no committed or uncommitted drift since. Never raises for a
    failed verification -- only for an environmental problem (not a git
    repository; see `_assert_git_repo`)."""
    root = repo_root if repo_root is not None else REPO_ROOT
    _assert_git_repo(root)

    paths = [str(p) for p in covered_paths]
    resolved_hash = _resolve_commit(commit_ref, repo_root=root)

    if resolved_hash is None:
        return VerificationResult(
            commit_ref=commit_ref,
            resolved_hash=None,
            status=FreezeStatus.UNVERIFIABLE,
            drifted_files=(),
            errors=(f"commit ref {commit_ref!r} does not resolve to a commit",),
        )

    errors: list[str] = []
    drifted: list[str] = []
    for path in paths:
        if not _path_exists_at_commit(resolved_hash, path, repo_root=root):
            errors.append(f"{path!r} does not exist at commit {resolved_hash}")
            continue
        if _has_committed_drift(resolved_hash, path, repo_root=root) or _has_uncommitted_drift(
            path, repo_root=root
        ):
            drifted.append(path)

    if errors:
        status = FreezeStatus.UNVERIFIABLE
    elif drifted:
        status = FreezeStatus.DRIFTED
    else:
        status = FreezeStatus.VERIFIED

    return VerificationResult(
        commit_ref=commit_ref,
        resolved_hash=resolved_hash,
        status=status,
        drifted_files=tuple(drifted),
        errors=tuple(errors),
    )
