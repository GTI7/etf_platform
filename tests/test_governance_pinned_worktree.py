from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.governance.pinned_worktree import WorktreeError, pinned_worktree


def _git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway git repository, isolated under pytest's tmp_path --
    never the real etf_platform repository (mirrors
    test_governance_freeze_verifier.py's fixture)."""
    _git(["init", "-q"], cwd=tmp_path)
    _git(["config", "user.email", "test@example.com"], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=tmp_path)
    return tmp_path


def _commit(repo: Path, filename: str, content: str, message: str) -> str:
    (repo / filename).write_text(content, encoding="utf-8")
    _git(["add", filename], cwd=repo)
    _git(["commit", "-q", "-m", message], cwd=repo)
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_pinned_worktree_checks_out_the_exact_commit_content(repo: Path) -> None:
    pinned_hash = _commit(repo, "experiment.py", "PINNED_VALUE = 1\n", "pin this")
    _commit(repo, "experiment.py", "PINNED_VALUE = 2\n", "HEAD moved on after the pin")

    with pinned_worktree(pinned_hash, repo_root=repo) as worktree_path:
        assert (worktree_path / "experiment.py").read_text(encoding="utf-8") == "PINNED_VALUE = 1\n"

    # The operator's own working tree must be completely untouched.
    assert (repo / "experiment.py").read_text(encoding="utf-8") == "PINNED_VALUE = 2\n"


def test_worktree_is_removed_after_the_context_exits(repo: Path) -> None:
    pinned_hash = _commit(repo, "a.py", "x = 1\n", "commit")

    with pinned_worktree(pinned_hash, repo_root=repo) as worktree_path:
        pass

    assert not worktree_path.exists()

    listing = _git(["worktree", "list"], cwd=repo).stdout
    assert str(worktree_path) not in listing


def test_worktree_is_kept_when_keep_is_true(repo: Path) -> None:
    pinned_hash = _commit(repo, "a.py", "x = 1\n", "commit")

    with pinned_worktree(pinned_hash, repo_root=repo, keep=True) as worktree_path:
        pass

    assert worktree_path.exists()

    # Clean it up manually since the fixture won't.
    _git(["worktree", "remove", "--force", str(worktree_path)], cwd=repo)


def test_unresolvable_commit_raises_worktree_error(repo: Path) -> None:
    _commit(repo, "a.py", "x = 1\n", "commit")

    with pytest.raises(WorktreeError):
        with pinned_worktree("not-a-real-commit-hash", repo_root=repo):
            pass


def test_never_leaves_head_or_branch_moved(repo: Path) -> None:
    pinned_hash = _commit(repo, "a.py", "x = 1\n", "first")
    head_hash = _commit(repo, "a.py", "x = 2\n", "second")

    with pinned_worktree(pinned_hash, repo_root=repo):
        current_head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
        ).stdout.strip()
        assert current_head == head_hash  # operator's own HEAD never moves
