"""`core.governance.dataset_integrity` -- the branch AD-073 Decision part 8
delegated and AD-074 SS9 item 6 / AD-075 SS4 item 3 recorded as absent.

The first test below is the regression this module exists for: before it,
appending a line to a sealed archive's `dataset_hashes/*.jsonl` left
`verify_archive()` reporting `OverallStatus.SOUND`, because the Seal
excludes those paths (AD-074 SS5.1) and handed them to a checker that did
not exist. Everything else here defends the two properties that make the
check worth having: the expected value comes from the *sealing commit*,
and "could not check" is never reported as "checked".
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from core.governance.archive_verifier import OverallStatus, SealStatus, verify_archive
from core.governance.dataset_integrity import (
    DatasetIntegrityStatus,
    verify_dataset_integrity,
)

_SNAPSHOT_BYTES = b'{"row": 1}\n'
_SNAPSHOT_HASH = "sha256:" + hashlib.sha256(_SNAPSHOT_BYTES).hexdigest()
_SOURCE_TABLES = ("ETF", "PriceBar", "TradingSession")


def _git(args: list[str], *, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    _git(["init", "-q"], cwd=tmp_path)
    _git(["config", "user.email", "test@example.com"], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=tmp_path)
    # See tests/test_governance_archive_verifier.py's own fixture: the
    # committed bytes of a governance artifact must survive verbatim.
    _git(["config", "core.autocrlf", "false"], cwd=tmp_path)
    return tmp_path


def _dataset_manifest(project_id: str, *, row_count: int = 1, content_hash: str = _SNAPSHOT_HASH) -> dict:
    return {
        "schema_version": 3,
        "project_id": project_id,
        "generated_at": "2026-07-26T00:00:00+00:00",
        "datasets": [
            {
                "dataset_id": table.lower(),
                "type": "snapshot",
                "source_table": table,
                "row_count": row_count,
                "snapshot_path": f"dataset_hashes/{table}.jsonl",
                "content_hash": content_hash,
                "schema_version": 1,
            }
            for table in _SOURCE_TABLES
        ],
    }


def _sealed_archive(repo: Path, project_id: str, *, manifest: dict | None = None) -> tuple[Path, str]:
    """A closed, complete, committed archive with a Register record naming
    the commit that holds it. Mirrors the seal tests' own helper; kept
    local so that this module's fixtures never depend on another test
    module's internals."""
    archive_dir = repo / project_id
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "archive_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_id": project_id,
                "created_at": "2026-07-26T00:00:00+00:00",
                "lifecycle_version": "v1",
            }
        ),
        encoding="utf-8",
    )
    for name in ("hypothesis.md", "methodology.md", "decision_log.md"):
        (archive_dir / name).write_bytes(f"{name}\n".encode("utf-8"))
    for name in ("experiment_results", "reviewer_reports"):
        (archive_dir / name).mkdir(exist_ok=True)
    dataset_hashes = archive_dir / "dataset_hashes"
    dataset_hashes.mkdir(exist_ok=True)
    for table in _SOURCE_TABLES:
        (dataset_hashes / f"{table}.jsonl").write_bytes(_SNAPSHOT_BYTES)
    (archive_dir / "dataset_manifest.json").write_text(
        json.dumps(manifest if manifest is not None else _dataset_manifest(project_id)),
        encoding="utf-8",
    )
    (archive_dir / "transition_records.jsonl").write_bytes(
        json.dumps(
            {
                "authorization": {
                    "authorizer": "Test",
                    "reviewer_level": "Level 1 (self-review)",
                    "ambiguity_acknowledged": False,
                    "override_acknowledged": False,
                },
                "commit_hash": "0" * 40,
                "evidence_refs": [],
                "freeze_commit_ref": "",
                "freeze_covered_paths": [],
                "freeze_verification_status": "not_applicable",
                "from_phase": "Decision",
                "gate_outcomes": [],
                "predecessor_hash": None,
                "project_id": project_id,
                "recorded_at": "2026-07-26T00:00:00Z",
                "reproduction_record_ref": None,
                "sequence_number": 1,
                "to_phase": "Archive",
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )

    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-q", "-m", f"seal {project_id}"], cwd=repo)
    sealed_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    docs = repo / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "archive_seal_register.jsonl").write_bytes(
        json.dumps(
            {
                "schema_version": 1,
                "project_id": project_id,
                "sealed_commit": sealed_commit,
                "sealed_at": "2026-07-26T00:00:00Z",
                "sealed_by": "Test",
                "supersedes": None,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    _git(["add", "--", "docs/archive_seal_register.jsonl"], cwd=repo)
    _git(["commit", "-q", "-m", "register", "--", "docs/archive_seal_register.jsonl"], cwd=repo)
    return archive_dir, sealed_commit


def test_intact_sealed_archive_verifies(git_repo: Path) -> None:
    archive_dir, sealed_commit = _sealed_archive(git_repo, "dataset_ok_project")

    report = verify_dataset_integrity(archive_dir, repo_root=git_repo)

    assert report.status is DatasetIntegrityStatus.VERIFIED
    assert report.findings == ()
    assert report.sealed_commit == sealed_commit
    assert set(report.verified_datasets) == {table.lower() for table in _SOURCE_TABLES}


def test_dataset_corruption_makes_the_archive_not_sound(git_repo: Path) -> None:
    """The regression this module exists for. The Seal *excludes* these
    bytes by design (AD-074 SS5.1), so before the dataset branch existed
    this exact mutation left the archive `SOUND`."""
    archive_dir, _ = _sealed_archive(git_repo, "dataset_corrupt_project")

    before = verify_archive(archive_dir, repo_root=git_repo)
    assert before.overall_status is OverallStatus.SOUND

    snapshot = archive_dir / "dataset_hashes" / "ETF.jsonl"
    snapshot.write_bytes(snapshot.read_bytes() + b'{"row": 2}\n')

    after = verify_archive(archive_dir, repo_root=git_repo)

    # The Seal still says MATCHED, correctly and by design -- these bytes
    # are not its coverage. The overall verdict is no longer SOUND anyway.
    assert after.seal.status is SealStatus.MATCHED
    assert after.dataset.status is DatasetIntegrityStatus.DRIFTED
    assert after.overall_status is OverallStatus.UNSOUND
    assert [finding.kind for finding in after.dataset.findings] == ["content_hash_mismatch"]
    assert after.dataset.findings[0].snapshot_path == "dataset_hashes/ETF.jsonl"


def test_row_count_mismatch_is_reported_when_the_manifest_disagrees_with_itself(git_repo: Path) -> None:
    """`row_count` can only ever fire on its own when the sealed manifest's
    two records of the same file disagree -- a manifest defect, reported
    in the terms a reader can act on rather than as a bare hash mismatch."""
    project_id = "dataset_rowcount_project"
    archive_dir, _ = _sealed_archive(
        git_repo, project_id, manifest=_dataset_manifest(project_id, row_count=99)
    )

    report = verify_dataset_integrity(archive_dir, repo_root=git_repo)

    assert report.status is DatasetIntegrityStatus.DRIFTED
    assert {finding.kind for finding in report.findings} == {"row_count_mismatch"}
    assert "row_count=99" in report.findings[0].detail


def test_deleted_snapshot_is_a_missing_finding(git_repo: Path) -> None:
    archive_dir, _ = _sealed_archive(git_repo, "dataset_deleted_project")
    (archive_dir / "dataset_hashes" / "PriceBar.jsonl").unlink()

    report = verify_dataset_integrity(archive_dir, repo_root=git_repo)

    assert report.status is DatasetIntegrityStatus.DRIFTED
    assert [finding.kind for finding in report.findings] == ["missing"]
    assert set(report.verified_datasets) == {"etf", "tradingsession"}


def test_working_tree_manifest_cannot_launder_a_corrupted_snapshot(git_repo: Path) -> None:
    """The property that makes this a control rather than a checksum. The
    manifest *states* the expected hash, so an attacker who can rewrite
    both the snapshot and the working-tree manifest could otherwise make
    them agree. The expected value is read at the sealing commit
    (AD-074 SS7B D2's rule, applied to the same file for the same
    reason), so restating it changes nothing."""
    archive_dir, _ = _sealed_archive(git_repo, "dataset_launder_project")

    snapshot = archive_dir / "dataset_hashes" / "ETF.jsonl"
    tampered = b'{"row": 999}\n'
    snapshot.write_bytes(tampered)

    # Rewrite the working-tree manifest so it "expects" the tampered bytes.
    manifest_path = archive_dir / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["datasets"]:
        if entry["source_table"] == "ETF":
            entry["content_hash"] = "sha256:" + hashlib.sha256(tampered).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = verify_dataset_integrity(archive_dir, repo_root=git_repo)

    assert report.status is DatasetIntegrityStatus.DRIFTED
    assert [finding.kind for finding in report.findings] == ["content_hash_mismatch"]


def test_unsealed_archive_is_failed_never_verified(git_repo: Path) -> None:
    """No seal means no trustworthy expected value. That is "could not
    check", never "checked and fine" -- and it aggregates to
    UNVERIFIABLE, not to SOUND."""
    project_id = "dataset_unsealed_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)
    # Drop the Register from history entirely.
    _git(["rm", "-q", "--", "docs/archive_seal_register.jsonl"], cwd=git_repo)
    _git(["commit", "-q", "-m", "remove register"], cwd=git_repo)

    report = verify_dataset_integrity(archive_dir, repo_root=git_repo)

    assert report.status is DatasetIntegrityStatus.FAILED
    assert report.status is not DatasetIntegrityStatus.VERIFIED
    assert report.sealed_commit is None
    assert verify_archive(archive_dir, repo_root=git_repo).overall_status is OverallStatus.UNVERIFIABLE


def test_non_git_repo_root_is_failed_not_raised(tmp_path: Path) -> None:
    """Mirrors the Seal and freeze branches: an environmental failure is
    translated by `verify_archive`, never propagated out of it."""
    archive_dir = tmp_path / "dataset_no_git_project"
    archive_dir.mkdir()
    (archive_dir / "archive_manifest.json").write_text(
        json.dumps({"schema_version": 1, "project_id": "dataset_no_git_project", "lifecycle_version": "v1"}),
        encoding="utf-8",
    )

    report = verify_archive(archive_dir, repo_root=tmp_path)

    assert report.dataset.status is DatasetIntegrityStatus.FAILED
    assert report.dataset.reason is not None
