"""Git worktree execution model (Phase 4 Architecture Amendment v1.1 SS
F.2, SS D.2): reproduction runs the pinned commit's own code, never
HEAD's, by checking it out into an isolated, detached worktree -- never
disturbing the operator's actual working tree.

Mirrors ``core.governance.freeze_verifier``'s read-only git-plumbing
style; unlike that module, ``git worktree add``/``remove`` are not
read-only, so this is the one place in this codebase's governance
tooling that mutates git state -- deliberately scoped to a throwaway
path outside the operator's working tree, never HEAD, never a branch.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class WorktreeError(RuntimeError):
    """Raised when `git worktree add`/`remove` itself fails -- an
    environmental failure, not a normal reproduction outcome."""


def _run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


@contextmanager
def pinned_worktree(
    commit_hash: str,
    *,
    repo_root: Path | None = None,
    keep: bool = False,
) -> Iterator[Path]:
    """Check out `commit_hash` into a fresh, detached worktree and yield
    its path. Removed on exit unless `keep=True` (operator discretion
    for debugging, SS F.2) -- never disturbs the operator's actual
    working tree or HEAD."""
    root = repo_root if repo_root is not None else REPO_ROOT
    worktree_path = Path(tempfile.mkdtemp(prefix="reproduction_worktree_"))
    # `git worktree add` refuses a target directory it did not create
    # itself, even an empty one -- remove the mkdtemp placeholder first
    # so git creates the real thing.
    shutil.rmtree(worktree_path)

    result = _run_git(["worktree", "add", "--detach", str(worktree_path), commit_hash], cwd=root)
    if result.returncode != 0:
        raise WorktreeError(f"git worktree add failed for commit {commit_hash!r}: {result.stderr.strip()}")

    try:
        yield worktree_path
    finally:
        if not keep:
            _run_git(["worktree", "remove", "--force", str(worktree_path)], cwd=root)
