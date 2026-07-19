from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.governance.freeze_verifier import (
    FreezeStatus,
    NotAGitRepositoryError,
    verify_freeze,
)


def _git(args: list[str], *, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway git repository, isolated under pytest's tmp_path --
    never the real etf_platform repository. All verification here is
    read-only, but the repo itself is disposable so commits are free."""
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


def test_unmodified_frozen_file_verifies(repo: Path) -> None:
    freeze_hash = _commit(repo, "frozen.md", "frozen content\n", "freeze")

    result = verify_freeze(freeze_hash, ["frozen.md"], repo_root=repo)

    assert result.status is FreezeStatus.VERIFIED
    assert result.verified
    assert result.drifted_files == ()
    assert result.errors == ()
    assert result.resolved_hash == freeze_hash


def test_committed_change_after_freeze_is_drift(repo: Path) -> None:
    freeze_hash = _commit(repo, "frozen.md", "frozen content\n", "freeze")
    _commit(repo, "frozen.md", "changed content\n", "oops, edited after freeze")

    result = verify_freeze(freeze_hash, ["frozen.md"], repo_root=repo)

    assert result.status is FreezeStatus.DRIFTED
    assert not result.verified
    assert result.drifted_files == ("frozen.md",)


def test_uncommitted_change_after_freeze_is_drift(repo: Path) -> None:
    freeze_hash = _commit(repo, "frozen.md", "frozen content\n", "freeze")
    (repo / "frozen.md").write_text("dirty, uncommitted content\n", encoding="utf-8")

    result = verify_freeze(freeze_hash, ["frozen.md"], repo_root=repo)

    assert result.status is FreezeStatus.DRIFTED
    assert result.drifted_files == ("frozen.md",)


def test_unresolvable_commit_ref_is_unverifiable(repo: Path) -> None:
    _commit(repo, "frozen.md", "frozen content\n", "freeze")

    result = verify_freeze("not-a-real-commit-hash", ["frozen.md"], repo_root=repo)

    assert result.status is FreezeStatus.UNVERIFIABLE
    assert not result.verified
    assert result.resolved_hash is None
    assert result.errors


def test_path_absent_at_freeze_commit_is_unverifiable(repo: Path) -> None:
    freeze_hash = _commit(repo, "frozen.md", "frozen content\n", "freeze")
    _commit(repo, "later_file.md", "added after freeze\n", "second commit")

    result = verify_freeze(freeze_hash, ["later_file.md"], repo_root=repo)

    assert result.status is FreezeStatus.UNVERIFIABLE
    assert result.drifted_files == ()
    assert any("later_file.md" in error for error in result.errors)


def test_multiple_covered_paths_all_checked(repo: Path) -> None:
    _commit(repo, "a.md", "a content\n", "freeze a")
    freeze_hash = _commit(repo, "b.md", "b content\n", "freeze b")
    _commit(repo, "a.md", "a content changed\n", "drift a after freeze")

    result = verify_freeze(freeze_hash, ["a.md", "b.md"], repo_root=repo)

    assert result.status is FreezeStatus.DRIFTED
    assert result.drifted_files == ("a.md",)


def test_short_hash_prefix_resolves(repo: Path) -> None:
    freeze_hash = _commit(repo, "frozen.md", "frozen content\n", "freeze")

    result = verify_freeze(freeze_hash[:8], ["frozen.md"], repo_root=repo)

    assert result.status is FreezeStatus.VERIFIED
    assert result.resolved_hash == freeze_hash


def test_non_git_directory_raises(tmp_path: Path) -> None:
    not_a_repo = tmp_path / "plain_dir"
    not_a_repo.mkdir()

    with pytest.raises(NotAGitRepositoryError):
        verify_freeze("HEAD", ["anything.md"], repo_root=not_a_repo)


def test_never_mutates_the_repository(repo: Path) -> None:
    freeze_hash = _commit(repo, "frozen.md", "frozen content\n", "freeze")
    status_before = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout

    verify_freeze(freeze_hash, ["frozen.md"], repo_root=repo)

    status_after = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    assert status_before == status_after == ""
