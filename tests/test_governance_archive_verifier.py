from __future__ import annotations

import ast
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from core.governance import archive_seal, freeze_verifier
from core.governance.archive_verifier import (
    ARCHIVE_MANIFEST_FILENAME,
    CompletenessStatus,
    FreezeStatus,
    OverallStatus,
    SealStatus,
    TRANSITION_RECORDS_FILENAME,
    derive_overall_status,
    verify_archive,
)

_REQUIRED_FILES = ("hypothesis.md", "methodology.md", "dataset_manifest.json", "decision_log.md")
_REQUIRED_DIRS = ("dataset_hashes", "experiment_results", "reviewer_reports")


def _write_manifest(archive_dir: Path, *, lifecycle_version: str = "v1") -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "project_id": archive_dir.name,
        "created_at": "2026-07-25T00:00:00+00:00",
        "lifecycle_version": lifecycle_version,
    }
    (archive_dir / ARCHIVE_MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")


def _write_all_required_items(archive_dir: Path) -> None:
    for name in _REQUIRED_FILES:
        (archive_dir / name).write_text("content\n", encoding="utf-8")
    for name in _REQUIRED_DIRS:
        (archive_dir / name).mkdir(parents=True, exist_ok=True)


def _transition_record_dict(
    archive_dir: Path,
    *,
    to_phase: str,
    sequence_number: object = 1,
    freeze_commit_ref: str = "0" * 40,
    freeze_covered_paths: list[str] | None = None,
) -> dict[str, object]:
    # `sequence_number` is typed `object`, not `int`: some callers below
    # deliberately pass a malformed value (a string, or None) to prove
    # ArchiveVerifier doesn't raise on it (AD-073 Phase B audit F-1).
    return {
        "project_id": archive_dir.name,
        "sequence_number": sequence_number,
        "from_phase": "Decision",
        "to_phase": to_phase,
        "recorded_at": "2026-07-25T00:00:00Z",
        "commit_hash": "0" * 40,
        "freeze_commit_ref": freeze_commit_ref,
        "freeze_verification_status": "verified",
        "freeze_covered_paths": freeze_covered_paths if freeze_covered_paths is not None else [],
        "gate_outcomes": [],
        "authorization": {
            "authorizer": "Test",
            "reviewer_level": "Level 1 (self-review)",
            "ambiguity_acknowledged": False,
            "override_acknowledged": False,
        },
        "evidence_refs": [],
        "reproduction_record_ref": None,
        "predecessor_hash": None,
    }


def _write_transition_records_raw(archive_dir: Path, records: list[dict[str, object]]) -> None:
    # write_bytes, not write_text: canonical_jsonl.read_canonical_jsonl()
    # rejects CRLF, and Windows text-mode writes would introduce it.
    lines = "\n".join(json.dumps(record) for record in records) + "\n"
    (archive_dir / TRANSITION_RECORDS_FILENAME).write_bytes(lines.encode("utf-8"))


def _write_transition_record(
    archive_dir: Path,
    *,
    to_phase: str,
    sequence_number: int = 1,
    freeze_commit_ref: str = "0" * 40,
    freeze_covered_paths: list[str] | None = None,
) -> None:
    record = _transition_record_dict(
        archive_dir,
        to_phase=to_phase,
        sequence_number=sequence_number,
        freeze_commit_ref=freeze_commit_ref,
        freeze_covered_paths=freeze_covered_paths,
    )
    _write_transition_records_raw(archive_dir, [record])


def _closed_complete_archive(tmp_path: Path, name: str = "some_project") -> Path:
    archive_dir = tmp_path / name
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    _write_transition_record(archive_dir, to_phase="Archive")
    return archive_dir


def _archive_with_freeze_claim(
    root: Path,
    name: str,
    *,
    to_phase: str = "Archive",
    freeze_commit_ref: str = "0" * 40,
    freeze_covered_paths: list[str] | None = None,
) -> Path:
    """Like `_closed_complete_archive`, but with a caller-controlled
    freeze claim on the terminal record -- used only by the freeze-branch
    tests below."""
    archive_dir = root / name
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    _write_transition_record(
        archive_dir,
        to_phase=to_phase,
        freeze_commit_ref=freeze_commit_ref,
        freeze_covered_paths=freeze_covered_paths,
    )
    return archive_dir


def _git(args: list[str], *, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A throwaway git repository at `tmp_path`, used only by the freeze
    branch tests -- `verify_freeze()` is read-only, but the repo is
    disposable so commits are free. Archive directories created under
    this same `tmp_path` (via `_closed_complete_archive` /
    `_archive_with_freeze_claim`) are plain untracked directories;
    `git status --porcelain -- <path>` only reports on the exact path
    checked, so their presence never affects freeze verification of a
    separately committed file."""
    _git(["init", "-q"], cwd=tmp_path)
    _git(["config", "user.email", "test@example.com"], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=tmp_path)
    # Committed bytes must survive verbatim, because several tests below
    # assert on exactly which bytes a governance artifact holds *at a
    # commit*. The real repository gets this from `.gitattributes`'s
    # `*.jsonl -text`; a throwaway repo has no `.gitattributes`, so
    # without this it inherits the machine's global `core.autocrlf`,
    # which on Windows is `true` and rewrites CRLF to LF on the way into
    # the object database. A test that writes a CRLF Register to prove it
    # is refused would then silently commit an LF one and prove nothing.
    _git(["config", "core.autocrlf", "false"], cwd=tmp_path)
    return tmp_path


def _commit(repo: Path, filename: str, content: str, message: str) -> str:
    (repo / filename).write_text(content, encoding="utf-8")
    _git(["add", filename], cwd=repo)
    _git(["commit", "-q", "-m", message], cwd=repo)
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_complete_archive_reports_complete_completeness_and_unverifiable_overall(tmp_path: Path) -> None:
    archive_dir = _closed_complete_archive(tmp_path)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.COMPLETE
    assert all(finding.outcome == "present" for finding in report.completeness.findings)
    # No Archive Seal Register record exists for this project (the real
    # Register is empty as of AD-074 Increment 2), so the Seal branch is
    # UNVERIFIABLE and overall status cannot be SOUND -- a per-archive
    # fact now, not the platform-wide Phase-1 stub it used to be.
    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_missing_required_artifact_is_incomplete(tmp_path: Path) -> None:
    archive_dir = _closed_complete_archive(tmp_path)
    (archive_dir / "hypothesis.md").unlink()

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.INCOMPLETE
    hypothesis_finding = next(f for f in report.completeness.findings if f.item == "hypothesis.md")
    assert hypothesis_finding.outcome == "missing"
    assert report.overall_status is OverallStatus.UNSOUND


def test_wrong_artifact_type_is_incomplete(tmp_path: Path) -> None:
    archive_dir = _closed_complete_archive(tmp_path)
    # dataset_hashes/ must be a directory; replace it with a file.
    import shutil

    shutil.rmtree(archive_dir / "dataset_hashes")
    (archive_dir / "dataset_hashes").write_text("not a directory\n", encoding="utf-8")

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.INCOMPLETE
    finding = next(f for f in report.completeness.findings if f.item == "dataset_hashes")
    assert finding.outcome == "wrong_kind"
    assert report.overall_status is OverallStatus.UNSOUND


def test_legacy_archive_by_name_is_exempt(tmp_path: Path) -> None:
    # No archive_manifest.json, directory named after one of the three
    # named legacy archives (RESEARCH_ARCHIVE_MANIFEST.md Applicability).
    archive_dir = tmp_path / "reference_v1"
    archive_dir.mkdir()
    (archive_dir / "README.md").write_text("legacy\n", encoding="utf-8")

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.EXEMPT
    assert report.completeness.findings == ()
    assert report.completeness.reason is not None


def test_legacy_archive_by_manifest_declaration_is_exempt(tmp_path: Path) -> None:
    archive_dir = tmp_path / "some_other_project"
    _write_manifest(archive_dir, lifecycle_version="legacy")

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.EXEMPT


def test_non_legacy_missing_manifest_is_incomplete_not_exempt(tmp_path: Path) -> None:
    # A directory that is NOT one of the three named legacy archives and
    # has no archive_manifest.json is a missing-required-item failure,
    # never an exemption (AC-14 / AD-073 F-3 correction).
    archive_dir = tmp_path / "brand_new_project"
    archive_dir.mkdir()
    _write_all_required_items(archive_dir)
    # No archive_manifest.json written, and no transition_records.jsonl --
    # the closure gate never runs because there is no manifest to read a
    # lifecycle_version from.

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.INCOMPLETE
    manifest_finding = next(f for f in report.completeness.findings if f.item == ARCHIVE_MANIFEST_FILENAME)
    assert manifest_finding.outcome == "missing"
    assert report.overall_status is OverallStatus.UNSOUND


def test_open_cycle_is_unverifiable_not_incomplete(tmp_path: Path) -> None:
    # A v1 manifest but no transition_records.jsonl at all: the cycle
    # has never transitioned, so it cannot have closed.
    archive_dir = tmp_path / "in_progress_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_open_cycle_with_non_archive_terminal_phase_is_unverifiable(tmp_path: Path) -> None:
    archive_dir = tmp_path / "still_in_validation"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    _write_transition_record(archive_dir, to_phase="Validation")

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE


def test_seal_with_no_register_record_is_unverifiable(tmp_path: Path) -> None:
    # AD-074 Increment 2: the Register is empty (no issuance yet), so a
    # real, complete, closed archive with no matching Register record
    # still reports UNVERIFIABLE -- but per-archive ("no seal issued for
    # this project"), not platform-wide ("no format exists yet", the old
    # Phase-1 stub reason). repo_root=tmp_path (no docs/ subdirectory at
    # all) is deliberately not a git repository: project_id resolution
    # and the Register lookup are both plain file reads that need no
    # git, so this must not raise NotAGitRepositoryError.
    complete_archive = _closed_complete_archive(tmp_path, name="complete_one")
    empty_archive = tmp_path / "empty_one"
    empty_archive.mkdir()

    complete_report = verify_archive(complete_archive, repo_root=tmp_path)
    empty_report = verify_archive(empty_archive, repo_root=tmp_path)

    for report in (complete_report, empty_report):
        assert report.seal.status is SealStatus.UNVERIFIABLE
        assert report.seal.findings == ()
        assert report.seal.reason is not None
        assert report.seal.excluded_paths == ()


def test_corrupt_archive_manifest_is_unverifiable_not_raised(tmp_path: Path) -> None:
    archive_dir = tmp_path / "corrupt_manifest_project"
    archive_dir.mkdir()
    (archive_dir / ARCHIVE_MANIFEST_FILENAME).write_text("{not valid json", encoding="utf-8")
    _write_all_required_items(archive_dir)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.completeness.reason is not None
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_corrupt_transition_records_is_unverifiable_not_raised(tmp_path: Path) -> None:
    archive_dir = tmp_path / "corrupt_transitions_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    (archive_dir / TRANSITION_RECORDS_FILENAME).write_bytes(b"{not valid json\n")

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_transition_record_missing_required_field_is_unverifiable(tmp_path: Path) -> None:
    # Valid JSON, but the row is missing a required DecisionRecord field
    # (_row_to_record's row["to_phase"] would raise KeyError). This must
    # not propagate: closure cannot be established, so the branch reports
    # UNVERIFIABLE exactly like an unclosed cycle, not a crash.
    archive_dir = tmp_path / "missing_field_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    incomplete_record = {
        "project_id": archive_dir.name,
        "sequence_number": 1,
        "from_phase": "Decision",
        # "to_phase" deliberately omitted.
        "recorded_at": "2026-07-25T00:00:00Z",
        "commit_hash": "0" * 40,
        "freeze_commit_ref": "0" * 40,
        "freeze_verification_status": "verified",
        "freeze_covered_paths": [],
        "gate_outcomes": [],
        "authorization": {
            "authorizer": "Test",
            "reviewer_level": "Level 1 (self-review)",
            "ambiguity_acknowledged": False,
            "override_acknowledged": False,
        },
        "evidence_refs": [],
        "reproduction_record_ref": None,
        "predecessor_hash": None,
    }
    (archive_dir / TRANSITION_RECORDS_FILENAME).write_bytes(
        (json.dumps(incomplete_record) + "\n").encode("utf-8")
    )

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_manifest_json_array_instead_of_object_is_unverifiable(tmp_path: Path) -> None:
    # Valid JSON, but a top-level array rather than an object -- manifest
    # would be a list, and list.get() doesn't exist.
    archive_dir = tmp_path / "array_manifest_project"
    archive_dir.mkdir()
    (archive_dir / ARCHIVE_MANIFEST_FILENAME).write_text(
        json.dumps(["not", "an", "object"]), encoding="utf-8"
    )
    _write_all_required_items(archive_dir)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.completeness.reason is not None
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_manifest_missing_lifecycle_version_is_handled_not_raised(tmp_path: Path) -> None:
    # Manifest is a valid JSON object but has no lifecycle_version key at
    # all (an older/incompatible manifest shape). manifest.get(...)
    # tolerates the missing key (returns None, not "legacy"), so this
    # falls through to the v1 closure gate rather than crashing; with no
    # transition_records.jsonl the cycle cannot be closed.
    archive_dir = tmp_path / "no_lifecycle_version_project"
    archive_dir.mkdir()
    manifest = {
        "schema_version": 1,
        "project_id": archive_dir.name,
        "created_at": "2026-07-25T00:00:00+00:00",
    }
    (archive_dir / ARCHIVE_MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    _write_all_required_items(archive_dir)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.completeness.reason is not None
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_manifest_invalid_utf8_is_unverifiable_not_raised(tmp_path: Path) -> None:
    # Bytes that are not valid UTF-8 at all (not even malformed JSON --
    # manifest_path.read_text(encoding="utf-8") itself raises
    # UnicodeDecodeError before json.loads ever runs).
    archive_dir = tmp_path / "invalid_utf8_manifest_project"
    archive_dir.mkdir()
    (archive_dir / ARCHIVE_MANIFEST_FILENAME).write_bytes(b"\xff\xfe\x00invalid")
    _write_all_required_items(archive_dir)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.completeness.reason is not None
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_manifest_replaced_by_directory_is_unverifiable_not_raised(tmp_path: Path) -> None:
    # archive_manifest.json exists (as a path) but is a directory, not a
    # file -- _read_manifest's path.exists() guard does not rule this
    # out, so read_text() itself must fail without escaping verify_archive().
    archive_dir = tmp_path / "manifest_is_directory_project"
    archive_dir.mkdir()
    (archive_dir / ARCHIVE_MANIFEST_FILENAME).mkdir()
    _write_all_required_items(archive_dir)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.completeness.reason is not None
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_transition_records_invalid_utf8_is_unverifiable_not_raised(tmp_path: Path) -> None:
    # Bytes that are not valid UTF-8 -- read_canonical_jsonl's
    # raw.decode("utf-8") raises UnicodeDecodeError before any JSONL
    # parsing runs. Closure cannot be established, so this is treated
    # the same as an unclosed cycle, not a crash.
    archive_dir = tmp_path / "invalid_utf8_transitions_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    (archive_dir / TRANSITION_RECORDS_FILENAME).write_bytes(b"\xff\xfe\x00invalid\n")

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_transition_records_replaced_by_directory_is_unverifiable_not_raised(tmp_path: Path) -> None:
    # transition_records.jsonl exists (as a path) but is a directory --
    # read_chain()'s own path.exists() guard does not rule this out, so
    # the underlying read_bytes() must fail without escaping
    # verify_archive(). Cycle closure cannot be proven either way.
    archive_dir = tmp_path / "transitions_is_directory_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    (archive_dir / TRANSITION_RECORDS_FILENAME).mkdir()

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_overall_status_precedence() -> None:
    # UNSOUND: a confirmed problem in either branch wins outright,
    # including when both branches report a problem simultaneously.
    assert derive_overall_status(CompletenessStatus.INCOMPLETE, SealStatus.MATCHED) is OverallStatus.UNSOUND
    assert derive_overall_status(CompletenessStatus.COMPLETE, SealStatus.MISMATCH) is OverallStatus.UNSOUND
    assert derive_overall_status(CompletenessStatus.INCOMPLETE, SealStatus.MISMATCH) is OverallStatus.UNSOUND
    # UNSOUND outranks UNVERIFIABLE: a confirmed problem in one branch
    # beats an unresolved verdict in the other.
    assert derive_overall_status(CompletenessStatus.INCOMPLETE, SealStatus.UNVERIFIABLE) is OverallStatus.UNSOUND
    assert derive_overall_status(CompletenessStatus.UNVERIFIABLE, SealStatus.MISMATCH) is OverallStatus.UNSOUND
    # UNVERIFIABLE: no confirmed problem, but at least one branch
    # could not reach a verdict.
    assert derive_overall_status(CompletenessStatus.UNVERIFIABLE, SealStatus.MATCHED) is OverallStatus.UNVERIFIABLE
    assert derive_overall_status(CompletenessStatus.COMPLETE, SealStatus.UNVERIFIABLE) is OverallStatus.UNVERIFIABLE
    assert derive_overall_status(CompletenessStatus.EXEMPT, SealStatus.UNVERIFIABLE) is OverallStatus.UNVERIFIABLE
    # SOUND: every invoked branch reports its confirmed-good value.
    assert derive_overall_status(CompletenessStatus.COMPLETE, SealStatus.MATCHED) is OverallStatus.SOUND
    assert derive_overall_status(CompletenessStatus.EXEMPT, SealStatus.MATCHED) is OverallStatus.SOUND


# --- Phase B: FreezeVerifier integration -----------------------------------


def test_default_call_omits_freeze_branch_matching_phase_1_behaviour(tmp_path: Path) -> None:
    # verify_archive(archive_dir) with no verify_freeze kwarg must behave
    # exactly as Phase 1 did: no freeze branch, same completeness/seal/
    # overall results as before this AD-073 Phase B increment.
    archive_dir = _closed_complete_archive(tmp_path)

    report = verify_archive(archive_dir)

    assert report.freeze is None
    assert report.completeness.status is CompletenessStatus.COMPLETE
    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_freeze_not_requested_branch_is_absent(tmp_path: Path) -> None:
    archive_dir = _closed_complete_archive(tmp_path)

    report = verify_archive(archive_dir, verify_freeze=False)

    assert report.freeze is None


def test_valid_freeze_verification_reports_verified(git_repo: Path) -> None:
    freeze_hash = _commit(git_repo, "frozen.md", "frozen content\n", "freeze")
    archive_dir = _archive_with_freeze_claim(
        git_repo,
        "freeze_ok_project",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["frozen.md"],
    )

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.freeze is not None
    assert report.freeze.status is FreezeStatus.VERIFIED
    assert report.freeze.verified
    assert report.freeze.covered_paths == ("frozen.md",)
    assert report.freeze.resolved_hash == freeze_hash


def test_empty_freeze_commit_ref_is_unverifiable(git_repo: Path) -> None:
    # No freeze claim at all -- freeze_commit_ref is the empty string on
    # the terminal record. This must not be passed to verify_freeze();
    # it is recognized as "no claim" before that call.
    archive_dir = _archive_with_freeze_claim(git_repo, "no_freeze_claim_project", freeze_commit_ref="")

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.freeze is not None
    assert report.freeze.status is FreezeStatus.UNVERIFIABLE
    assert report.freeze.resolved_hash is None
    assert report.freeze.commit_ref == ""


def test_empty_freeze_covered_paths_is_unverifiable(git_repo: Path) -> None:
    # freeze_commit_ref is present and resolvable, but freeze_covered_paths
    # is empty -- passed to verify_freeze() exactly as read (AD-073), which
    # already reports UNVERIFIABLE for zero coverage (AD-051).
    freeze_hash = _commit(git_repo, "frozen.md", "frozen content\n", "freeze")
    archive_dir = _archive_with_freeze_claim(
        git_repo,
        "empty_covered_paths_project",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=[],
    )

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.freeze is not None
    assert report.freeze.status is FreezeStatus.UNVERIFIABLE
    assert report.freeze.resolved_hash == freeze_hash
    assert any("empty" in error for error in report.freeze.errors)


def test_invalid_freeze_commit_ref_is_unverifiable(git_repo: Path) -> None:
    _commit(git_repo, "frozen.md", "frozen content\n", "freeze")
    archive_dir = _archive_with_freeze_claim(
        git_repo,
        "bad_ref_project",
        freeze_commit_ref="not-a-real-commit-hash",
        freeze_covered_paths=["frozen.md"],
    )

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.freeze is not None
    assert report.freeze.status is FreezeStatus.UNVERIFIABLE
    assert report.freeze.resolved_hash is None


def test_freeze_drift_is_detected(git_repo: Path) -> None:
    freeze_hash = _commit(git_repo, "frozen.md", "frozen content\n", "freeze")
    _commit(git_repo, "frozen.md", "changed after freeze\n", "oops, edited after freeze")
    archive_dir = _archive_with_freeze_claim(
        git_repo,
        "drifted_project",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["frozen.md"],
    )

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.freeze is not None
    assert report.freeze.status is FreezeStatus.DRIFTED
    assert report.freeze.drifted_files == ("frozen.md",)
    # DRIFTED is Freeze's confirmed-problem value -- outranks Seal's
    # UNVERIFIABLE stub, same as Completeness INCOMPLETE already does.
    assert report.overall_status is OverallStatus.UNSOUND


def test_malformed_transition_records_with_freeze_requested_is_unverifiable(git_repo: Path) -> None:
    # Completeness's own malformed-input hardening (Phase 1.1) already
    # treats this as an unclosed cycle; the freeze branch must reach the
    # same "no terminal record" conclusion via the shared _terminal_record
    # helper, not crash.
    archive_dir = git_repo / "malformed_freeze_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    (archive_dir / TRANSITION_RECORDS_FILENAME).write_bytes(b"{not valid json\n")

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.freeze is not None
    assert report.freeze.status is FreezeStatus.UNVERIFIABLE
    assert report.freeze.resolved_hash is None
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_open_cycle_with_valid_freeze_claim_still_verifies_freeze(git_repo: Path) -> None:
    # A requested freeze branch always runs, independent of cycle closure
    # (AD-073: "a requested freeze branch always runs"). The cycle being
    # open makes Completeness UNVERIFIABLE; Freeze reaches its own,
    # independent VERIFIED result from the same terminal record.
    freeze_hash = _commit(git_repo, "frozen.md", "frozen content\n", "freeze")
    archive_dir = _archive_with_freeze_claim(
        git_repo,
        "open_cycle_with_freeze_project",
        to_phase="Validation",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["frozen.md"],
    )

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.freeze is not None
    assert report.freeze.status is FreezeStatus.VERIFIED
    # Completeness's own UNVERIFIABLE still wins overall precedence over
    # Freeze's confirmed-good result -- one branch's success never masks
    # another branch's unresolved verdict (AD-073 Decision part 4).
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_overall_status_precedence_with_freeze() -> None:
    # Freeze DRIFTED is a confirmed problem -- UNSOUND, even when both
    # other branches are confirmed-good.
    assert (
        derive_overall_status(CompletenessStatus.COMPLETE, SealStatus.MATCHED, FreezeStatus.DRIFTED)
        is OverallStatus.UNSOUND
    )
    # A confirmed problem elsewhere still wins even when freeze is VERIFIED.
    assert (
        derive_overall_status(CompletenessStatus.INCOMPLETE, SealStatus.MATCHED, FreezeStatus.VERIFIED)
        is OverallStatus.UNSOUND
    )
    # Freeze UNVERIFIABLE, no confirmed problem elsewhere -- UNVERIFIABLE.
    assert (
        derive_overall_status(CompletenessStatus.COMPLETE, SealStatus.MATCHED, FreezeStatus.UNVERIFIABLE)
        is OverallStatus.UNVERIFIABLE
    )
    # All three branches confirmed-good -- SOUND.
    assert (
        derive_overall_status(CompletenessStatus.COMPLETE, SealStatus.MATCHED, FreezeStatus.VERIFIED)
        is OverallStatus.SOUND
    )
    # freeze=None (branch not invoked) takes no part in the computation --
    # identical to the two-argument call, confirming an absent branch is
    # never conflated with an invoked branch reporting UNVERIFIABLE.
    assert derive_overall_status(
        CompletenessStatus.COMPLETE, SealStatus.MATCHED, None
    ) is derive_overall_status(CompletenessStatus.COMPLETE, SealStatus.MATCHED)


# --- Phase B audit: F-1, F-2, F-3 -------------------------------------------


def test_mixed_int_and_string_sequence_numbers_do_not_raise_and_are_unverifiable(tmp_path: Path) -> None:
    # A chain with inconsistent sequence_number types across records (a
    # hand-edited or corrupted chain) must not let max()'s cross-type
    # comparison raise out of verify_archive().
    archive_dir = tmp_path / "mixed_sequence_type_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    records = [
        _transition_record_dict(archive_dir, to_phase="Validation", sequence_number=1),
        _transition_record_dict(archive_dir, to_phase="Archive", sequence_number="2"),
    ]
    _write_transition_records_raw(archive_dir, records)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_null_sequence_number_does_not_raise_and_is_unverifiable(tmp_path: Path) -> None:
    # A record with sequence_number: null (e.g. a partially-written or
    # corrupted row) must not let max()'s None-vs-int comparison raise.
    archive_dir = tmp_path / "null_sequence_number_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    records = [
        _transition_record_dict(archive_dir, to_phase="Validation", sequence_number=None),
        _transition_record_dict(archive_dir, to_phase="Archive", sequence_number=1),
    ]
    _write_transition_records_raw(archive_dir, records)

    report = verify_archive(archive_dir)

    assert report.completeness.status is CompletenessStatus.UNVERIFIABLE
    assert report.completeness.findings == ()
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_freeze_verification_in_non_git_repo_root_is_unverifiable_not_raised(tmp_path: Path) -> None:
    # repo_root points at a directory that is not a git working tree at
    # all -- freeze_verifier.verify_freeze() raises NotAGitRepositoryError
    # for this (an environmental failure, per its own docstring, not a
    # failed verification). ArchiveVerifier must catch it and report
    # UNVERIFIABLE with a reason, not let it escape verify_archive().
    non_git_root = tmp_path / "not_a_repo"
    non_git_root.mkdir()
    archive_dir = _archive_with_freeze_claim(
        tmp_path,
        "freeze_claim_no_git_project",
        freeze_commit_ref="0" * 40,
        freeze_covered_paths=["frozen.md"],
    )

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=non_git_root)

    assert report.freeze is not None
    assert report.freeze.status is FreezeStatus.UNVERIFIABLE
    assert report.freeze.resolved_hash is None
    assert report.freeze.errors
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_terminal_record_not_first_record_is_used_for_freeze_verification(git_repo: Path) -> None:
    # A multi-record chain where the earlier (non-terminal) record has a
    # *different* freeze_commit_ref and freeze_covered_paths than the
    # terminal record. ArchiveVerifier must use the terminal record's
    # freeze claim, not the first record in the file -- kills a
    # `records[0]` mutation of the selection rule.
    early_hash = _commit(git_repo, "early.md", "early content\n", "early")
    terminal_hash = _commit(git_repo, "terminal.md", "terminal content\n", "terminal")
    archive_dir = git_repo / "terminal_selection_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    records = [
        _transition_record_dict(
            archive_dir,
            to_phase="Validation",
            sequence_number=1,
            freeze_commit_ref=early_hash,
            freeze_covered_paths=["early.md"],
        ),
        _transition_record_dict(
            archive_dir,
            to_phase="Archive",
            sequence_number=2,
            freeze_commit_ref=terminal_hash,
            freeze_covered_paths=["terminal.md"],
        ),
    ]
    _write_transition_records_raw(archive_dir, records)

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.freeze is not None
    assert report.freeze.commit_ref == terminal_hash
    assert report.freeze.resolved_hash == terminal_hash
    assert report.freeze.covered_paths == ("terminal.md",)
    assert report.freeze.status is FreezeStatus.VERIFIED
    assert report.completeness.status is CompletenessStatus.COMPLETE


def test_highest_sequence_number_wins_regardless_of_file_order(git_repo: Path) -> None:
    # The same two records as above, but written to the file in reverse
    # of sequence_number order (the terminal record first, the earlier
    # record last). Terminal-record selection must be driven by
    # sequence_number, never by file/line position -- kills a
    # `min(records, key=...)` mutation of the selection rule, which
    # (coincidentally, for two records) would otherwise be indistinguishable
    # from "last record in the file wins".
    early_hash = _commit(git_repo, "early.md", "early content\n", "early")
    terminal_hash = _commit(git_repo, "terminal.md", "terminal content\n", "terminal")
    archive_dir = git_repo / "out_of_order_selection_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    terminal_record = _transition_record_dict(
        archive_dir,
        to_phase="Archive",
        sequence_number=2,
        freeze_commit_ref=terminal_hash,
        freeze_covered_paths=["terminal.md"],
    )
    early_record = _transition_record_dict(
        archive_dir,
        to_phase="Validation",
        sequence_number=1,
        freeze_commit_ref=early_hash,
        freeze_covered_paths=["early.md"],
    )
    # Terminal (higher sequence_number) written first; early record last.
    _write_transition_records_raw(archive_dir, [terminal_record, early_record])

    report = verify_archive(archive_dir, verify_freeze=True, repo_root=git_repo)

    assert report.freeze is not None
    assert report.freeze.commit_ref == terminal_hash
    assert report.freeze.resolved_hash == terminal_hash
    assert report.freeze.covered_paths == ("terminal.md",)
    assert report.freeze.status is FreezeStatus.VERIFIED
    assert report.completeness.status is CompletenessStatus.COMPLETE


# --- AD-074 Increment 2: Archive Seal branch --------------------------------


def _dataset_manifest_dict(project_id: str) -> dict[str, object]:
    def entry(source_table: str) -> dict[str, object]:
        return {
            "dataset_id": source_table.lower(),
            "type": "snapshot",
            "source_table": source_table,
            "row_count": 1,
            "snapshot_path": f"dataset_hashes/{source_table}.jsonl",
            "content_hash": "sha256:" + "a" * 64,
            "schema_version": 1,
        }

    return {
        "schema_version": 3,
        "project_id": project_id,
        "generated_at": "2026-07-25T00:00:00+00:00",
        "datasets": [entry("ETF"), entry("PriceBar"), entry("TradingSession")],
    }


def _write_seal_test_archive(repo_root: Path, project_id: str) -> Path:
    """A closed, completeness-COMPLETE archive with a schema-valid
    dataset_manifest.json (needed for the Seal branch's exclusion-set
    derivation, AD-074 SS7B D2) and the dataset_hashes files its
    snapshot_path entries name."""
    archive_dir = repo_root / project_id
    _write_manifest(archive_dir)
    (archive_dir / "hypothesis.md").write_text("hypothesis\n", encoding="utf-8")
    (archive_dir / "methodology.md").write_text("methodology\n", encoding="utf-8")
    (archive_dir / "decision_log.md").write_text("decisions\n", encoding="utf-8")
    (archive_dir / "experiment_results").mkdir(exist_ok=True)
    (archive_dir / "reviewer_reports").mkdir(exist_ok=True)
    dataset_hashes_dir = archive_dir / "dataset_hashes"
    dataset_hashes_dir.mkdir(exist_ok=True)
    for table in ("ETF", "PriceBar", "TradingSession"):
        (dataset_hashes_dir / f"{table}.jsonl").write_text('{"row": 1}\n', encoding="utf-8")
    (archive_dir / "dataset_manifest.json").write_text(
        json.dumps(_dataset_manifest_dict(project_id)), encoding="utf-8"
    )
    return archive_dir


def _write_register_raw(repo_root: Path, content: str) -> None:
    # write_bytes, not write_text: the Register is canonical JSONL, and
    # archive_seal's reader enforces that format's two whole-file rules
    # (LF-only, one trailing newline) the same way
    # canonical_jsonl.read_canonical_jsonl does. A Windows text-mode
    # write would introduce CRLF and be refused -- correctly, and for
    # exactly the reason `_write_transition_records_raw` above already
    # writes bytes.
    #
    # **And then committed.** `archive_seal` reads the Register at HEAD,
    # never from the working tree, so a test that only wrote the file
    # would be exercising a Register the implementation is now required
    # to ignore. Committing here is what keeps every register test below
    # testing what it says it tests; the one thing that must *not* be
    # done is to relax the implementation so an unwritten-to-history
    # Register is honoured again -- see
    # `test_seal_uncommitted_working_tree_register_is_ignored`.
    #
    # The commit names the Register path explicitly rather than using
    # `add -A`: several tests below tamper with the archive in the
    # working tree and assert MISMATCH, which only holds while that
    # tamper stays uncommitted.
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    register_path = docs_dir / "archive_seal_register.jsonl"
    register_path.write_bytes(content.encode("utf-8"))
    _commit_register(repo_root)


def _commit_register(repo_root: Path) -> None:
    """Commit the Register alone, if `repo_root` is a git repository.
    A non-git `repo_root` is left as a plain file write: those tests
    assert the environmental refusal, not a Register outcome."""
    if not (repo_root / ".git").exists():
        return
    relative = "docs/archive_seal_register.jsonl"
    _git(["add", "--", relative], cwd=repo_root)
    _git(["commit", "-q", "-m", "register", "--", relative], cwd=repo_root)


def _write_register(repo_root: Path, records: list[dict[str, object]]) -> None:
    _write_register_raw(repo_root, "".join(json.dumps(record) + "\n" for record in records))


def _register_record(
    project_id: str,
    sealed_commit: str,
    *,
    sealed_by: str = "Test",
    supersedes: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "project_id": project_id,
        "sealed_commit": sealed_commit,
        "sealed_at": "2026-07-26T00:00:00Z",
        "sealed_by": sealed_by,
        "supersedes": supersedes,
    }


def _head_commit(repo: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_seal_empty_register_is_unverifiable(tmp_path: Path) -> None:
    # Test requirement 1: an empty (absent) Register -- no docs/ directory
    # at all under repo_root -- is UNVERIFIABLE, not an exception, and
    # never depends on repo_root being a git repository (register lookup
    # and project_id resolution are both plain file reads).
    archive_dir = tmp_path / "seal_no_register_project"
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)

    report = verify_archive(archive_dir, repo_root=tmp_path)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert report.seal.findings == ()


def test_seal_missing_project_id_is_unverifiable(tmp_path: Path) -> None:
    # Test requirement 2: archive_manifest.json present but with no
    # project_id field at all -- there is no key to look up in the
    # Register, so this must fail before any Register or git access.
    archive_dir = tmp_path / "no_project_id_project"
    archive_dir.mkdir()
    manifest = {
        "schema_version": 1,
        "created_at": "2026-07-25T00:00:00+00:00",
        "lifecycle_version": "v1",
    }
    (archive_dir / ARCHIVE_MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    _write_all_required_items(archive_dir)

    report = verify_archive(archive_dir, repo_root=tmp_path)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "project_id" in report.seal.reason


def test_seal_malformed_latest_record_is_unverifiable_never_falls_back(git_repo: Path) -> None:
    # Test requirement 3: the FIRST record for this project_id is
    # perfectly valid; the LATEST one (by file order, C-2) is missing
    # sealed_commit. This must fail closed to UNVERIFIABLE rather than
    # silently using the earlier valid record (AD-074 SS5.5 C-3).
    #
    # Runs in a git repository because the Register is now read from
    # committed content: a Register question can no longer be asked of a
    # non-git directory, and asking one there tests the environmental
    # refusal instead of the record-shape rule this test is about.
    tmp_path = git_repo
    project_id = "seal_malformed_project"
    archive_dir = tmp_path / project_id
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)

    valid_record = _register_record(project_id, "a" * 40)
    malformed_latest_record = {
        "schema_version": 1,
        "project_id": project_id,
        # sealed_commit deliberately omitted.
        "sealed_at": "2026-07-26T00:00:00Z",
        "sealed_by": "Test",
        "supersedes": "a" * 40,
    }
    _write_register(tmp_path, [valid_record, malformed_latest_record])

    report = verify_archive(archive_dir, repo_root=tmp_path)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "missing required field" in report.seal.reason


def test_seal_malformed_record_for_different_project_is_unaffected(tmp_path: Path) -> None:
    # A malformed latest record for an UNRELATED project_id must not
    # make this archive's own seal UNVERIFIABLE (AD-074 SS5.5 C-3
    # closing paragraph) -- here it simply means this project has no
    # record of its own at all, the same as an empty Register.
    project_id = "seal_unaffected_project"
    archive_dir = tmp_path / project_id
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)

    other_project_malformed = {
        "schema_version": 1,
        "project_id": "some_other_project",
        "sealed_at": "2026-07-26T00:00:00Z",
        "sealed_by": "Test",
        "supersedes": None,
        # sealed_commit deliberately omitted -- malformed, but for a
        # different project_id entirely.
    }
    _write_register(tmp_path, [other_project_malformed])

    report = verify_archive(archive_dir, repo_root=tmp_path)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "some_other_project" not in report.seal.reason


def test_seal_register_file_unreadable_is_unverifiable_not_raised(tmp_path: Path) -> None:
    # The Register path exists but is a directory, not a file -- an
    # OSError from read_text() must not escape verify_archive() (AD-074
    # SS5.5 C-3 third bullet: unreadable file, not a bad line).
    project_id = "seal_unreadable_register_project"
    archive_dir = tmp_path / project_id
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "archive_seal_register.jsonl").mkdir()

    report = verify_archive(archive_dir, repo_root=tmp_path)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None


def test_seal_verification_in_non_git_repo_root_is_unverifiable_not_raised(tmp_path: Path) -> None:
    # A matching Register record exists, but repo_root is not inside a
    # git working tree at all -- archive_seal.NotAGitRepositoryError must
    # be caught and translated, not escape verify_archive() (mirrors the
    # freeze branch's own environment-error handling).
    non_git_root = tmp_path / "not_a_repo"
    non_git_root.mkdir()
    project_id = "seal_no_git_project"
    archive_dir = non_git_root / project_id
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    _write_register(non_git_root, [_register_record(project_id, "a" * 40)])

    report = verify_archive(archive_dir, repo_root=non_git_root)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None


def test_seal_unresolvable_sealing_commit_is_unverifiable(git_repo: Path) -> None:
    project_id = "seal_bad_commit_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, "f" * 40)])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "does not exist" in report.seal.reason


def test_seal_valid_sealing_commit_with_matching_tree_is_matched_and_sound(git_repo: Path) -> None:
    # Test requirement 4: this is the first scenario in which
    # OverallStatus.SOUND is reachable at all (AC-74-11) -- completeness
    # COMPLETE, seal MATCHED, no freeze branch requested.
    project_id = "seal_ok_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    sealed_commit = _head_commit(git_repo)
    _write_register(git_repo, [_register_record(project_id, sealed_commit)])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED
    assert report.seal.findings == ()
    assert report.completeness.status is CompletenessStatus.COMPLETE
    assert report.overall_status is OverallStatus.SOUND


def test_seal_modified_archive_file_after_sealing_is_mismatch(git_repo: Path) -> None:
    # Test requirement 5: a committed edit to a sealed file after the
    # sealing commit must be caught via `git diff --quiet <sealed_commit>
    # -- <path>` (AD-074 SS7B D4), never via a raw byte comparison.
    project_id = "seal_modified_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    sealed_commit = _head_commit(git_repo)
    _write_register(git_repo, [_register_record(project_id, sealed_commit)])

    (archive_dir / "hypothesis.md").write_text("tampered after sealing\n", encoding="utf-8")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MISMATCH
    modified = {f.path for f in report.seal.findings if f.kind == "modified"}
    assert f"{project_id}/hypothesis.md" in modified
    assert report.overall_status is OverallStatus.UNSOUND


def test_seal_missing_and_unexpected_files_are_distinct_finding_kinds(git_repo: Path) -> None:
    # AC-74-3: "modified", "missing", and "unexpected" are three distinct
    # finding kinds, never collapsed.
    project_id = "seal_missing_unexpected_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    sealed_commit = _head_commit(git_repo)
    _write_register(git_repo, [_register_record(project_id, sealed_commit)])

    (archive_dir / "hypothesis.md").unlink()
    (archive_dir / "extra_file.md").write_text("added after sealing\n", encoding="utf-8")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MISMATCH
    kinds = {f.path.rsplit("/", 1)[-1]: f.kind for f in report.seal.findings}
    assert kinds["hypothesis.md"] == "missing"
    assert kinds["extra_file.md"] == "unexpected"


def test_seal_dataset_hash_files_are_excluded_from_comparison(git_repo: Path) -> None:
    # Test requirement 6: dataset_hashes/*.jsonl bytes are
    # DatasetIntegrityChecker's domain (AD-073 Decision part 8), never
    # the Seal's -- tampering with one must not produce a MISMATCH, and
    # the exclusion must be visible on the report (AC-74-4).
    project_id = "seal_exclusion_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    sealed_commit = _head_commit(git_repo)
    _write_register(git_repo, [_register_record(project_id, sealed_commit)])

    (archive_dir / "dataset_hashes" / "ETF.jsonl").write_text("tampered\n", encoding="utf-8")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED
    assert report.seal.findings == ()
    assert f"{project_id}/dataset_hashes/ETF.jsonl" in report.seal.excluded_paths


def test_seal_legacy_archive_is_unverifiable_never_matched_or_mismatch(tmp_path: Path) -> None:
    # Test requirement 7: a named legacy archive (no archive_manifest.json
    # at all) is UNVERIFIABLE on the Seal branch even though it is EXEMPT
    # on the completeness branch -- the two branches keep their own
    # vocabularies, and "exempt from a layout check" is not "sealed"
    # (AD-074 SS5.6).
    archive_dir = tmp_path / "reference_v1"
    archive_dir.mkdir()
    (archive_dir / "README.md").write_text("legacy\n", encoding="utf-8")

    report = verify_archive(archive_dir, repo_root=tmp_path)

    assert report.completeness.status is CompletenessStatus.EXEMPT
    assert report.seal.status is SealStatus.UNVERIFIABLE


# --- AD-074 Increment 2 integrity audit (2026-07-26) ------------------------
# Each test below pins one remediated audit item. Where the superseded
# implementation gave a *wrong* answer rather than no answer, the test
# asserts the wrong answer's mechanism too (e.g. that `git diff` really
# is fooled), so it fails if the fix is reverted rather than passing by
# coincidence.


def _git_output(args: list[str], *, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def _index_based_diff_is_clean(repo: Path, sealed_commit: str, relative_path: str) -> bool:
    """The superseded comparison, run directly: `git diff --quiet
    <sealed_commit> -- <path>`. Used only to prove that the index-based
    mechanism the audit rejected really does give the wrong answer in
    the scenarios below -- never as the implementation's own check."""
    result = subprocess.run(
        ["git", "diff", "--quiet", sealed_commit, "--", relative_path],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _sealed_archive(repo: Path, project_id: str, *, register: bool = True) -> tuple[Path, str]:
    """Build a closed, complete archive, commit it, and (by default)
    write a Register record naming that commit. Returns
    (archive_dir, sealed_commit)."""
    archive_dir = _write_seal_test_archive(repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-q", "-m", f"seal {project_id}"], cwd=repo)
    sealed_commit = _head_commit(repo)
    if register:
        _write_register(repo, [_register_record(project_id, sealed_commit)])
    return archive_dir, sealed_commit


# Audit item 1 -- the comparison must not depend on the git index.


def test_seal_assume_unchanged_cannot_hide_archive_mutation(git_repo: Path) -> None:
    # `git update-index --assume-unchanged` tells git to trust the index
    # entry and skip the working-tree stat check, so `git diff` reports a
    # tampered file as clean. The seal compares blob identities
    # (rev-parse <sealed>:<path> vs. hash-object --path) and never
    # consults the index, so the mutation is still caught.
    project_id = "seal_assume_unchanged_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id)
    relative_path = f"{project_id}/hypothesis.md"

    _git(["update-index", "--assume-unchanged", relative_path], cwd=git_repo)
    (archive_dir / "hypothesis.md").write_text("tampered while assume-unchanged\n", encoding="utf-8")

    # The mechanism the audit rejected is genuinely fooled here; if this
    # assertion ever fails, this test has stopped testing what it claims.
    assert _index_based_diff_is_clean(git_repo, sealed_commit, relative_path)

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MISMATCH
    assert {f.path for f in report.seal.findings if f.kind == "modified"} == {relative_path}
    assert report.overall_status is OverallStatus.UNSOUND


def test_seal_file_removed_from_index_with_identical_bytes_is_still_matched(git_repo: Path) -> None:
    # `git rm --cached` drops the index entry while leaving the bytes on
    # disk untouched. `git diff <sealed_commit> -- <path>` then reports a
    # deletion -- a false MISMATCH driven purely by index state. The
    # blob-identity comparison sees identical content on both sides.
    project_id = "seal_index_removed_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id)
    relative_path = f"{project_id}/hypothesis.md"
    sealed_bytes = (archive_dir / "hypothesis.md").read_bytes()

    _git(["rm", "--cached", "-q", relative_path], cwd=git_repo)

    assert (archive_dir / "hypothesis.md").read_bytes() == sealed_bytes  # bytes untouched
    assert not _index_based_diff_is_clean(git_repo, sealed_commit, relative_path)  # old mechanism: false mismatch

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED
    assert report.seal.findings == ()


# Audit item 2 -- NUL-delimited path enumeration.


def test_seal_non_ascii_archive_path_is_matched(git_repo: Path) -> None:
    # Without `-z`, `git ls-tree --name-only` quotes non-ASCII paths as
    # "r\303\251sum\303\251.md", which matches nothing in the
    # working-tree walk: the file would be reported both `missing` (the
    # quoted name) and `unexpected` (the real name) on a sound archive.
    project_id = "seal_non_ascii_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    (archive_dir / "résumé.md").write_text("non-ASCII filename\n", encoding="utf-8")
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive with a non-ASCII path"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED
    assert report.seal.findings == ()


# Audit item 3 -- a relative archive_dir must not raise.


def test_seal_relative_archive_path_does_not_raise(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # verify_archive(Path("relative/path")) previously reached
    # _working_tree_paths, whose Path.relative_to(<absolute repo_root>)
    # raised ValueError out of a verifier contracted never to raise for
    # a verification question. Resolution happens once, at the public
    # boundary, so the relative call now behaves exactly like the
    # absolute one.
    project_id = "seal_relative_path_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)
    monkeypatch.chdir(git_repo)

    report = verify_archive(Path(project_id), repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED
    assert report.overall_status is OverallStatus.SOUND
    assert report.archive_dir == archive_dir.resolve()


# Audit item 4 -- Register schema_version is required, integer, and 1.


@pytest.mark.parametrize(
    ("schema_version", "expected_fragment"),
    [
        (99, "unsupported"),
        (0, "unsupported"),
        ("wrong", "non-integer"),
        (None, "non-integer"),
        (True, "non-integer"),  # bool is an int subclass -- must not be read as 1
        (1.0, "non-integer"),
    ],
)
def test_seal_register_schema_version_is_enforced(
    git_repo: Path, schema_version: object, expected_fragment: str
) -> None:
    project_id = "seal_schema_version_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    record = _register_record(project_id, sealed_commit)
    record["schema_version"] = schema_version
    _write_register(git_repo, [record])

    report = verify_archive(archive_dir, repo_root=git_repo)

    # Fail-closed: an unreadable schema is never a MATCHED archive, even
    # though this archive's bytes are in fact intact.
    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert expected_fragment in report.seal.reason


def test_seal_register_missing_schema_version_is_unverifiable(git_repo: Path) -> None:
    project_id = "seal_no_schema_version_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    record = _register_record(project_id, sealed_commit)
    del record["schema_version"]
    _write_register(git_repo, [record])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "missing required field" in report.seal.reason


def test_seal_register_supported_schema_version_still_matches(git_repo: Path) -> None:
    # The enforcement above must not have closed the door on the one
    # value that is supported.
    project_id = "seal_schema_version_ok_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED


# Audit item 5 -- an unattributable line after a project's latest record
# invalidates that project's lookup, never falls back to the earlier one.


def test_seal_invalid_json_line_after_valid_record_invalidates_lookup(git_repo: Path) -> None:
    project_id = "seal_corrupt_append_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    _write_register_raw(git_repo, json.dumps(_register_record(project_id, sealed_commit)) + "\n{not valid json\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    # The archive genuinely matches `sealed_commit`; falling back to that
    # record would report MATCHED and be silently right this time, and
    # silently wrong the first time a corrupt append hides a re-seal.
    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "fails closed" in report.seal.reason


def test_seal_invalid_json_line_before_latest_record_is_ignored(git_repo: Path) -> None:
    # The other half of the positional rule: a bad line the project's own
    # latest record supersedes is not a reason to refuse the lookup.
    project_id = "seal_corrupt_prefix_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    _write_register_raw(git_repo, "{not valid json\n" + json.dumps(_register_record(project_id, sealed_commit)) + "\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED


def test_seal_invalid_json_line_does_not_affect_unrelated_project(git_repo: Path) -> None:
    # AD-074 SS5.5 C-3's closing paragraph: a single bad line is not a
    # reason to refuse the whole file. The project whose own record
    # follows the bad line is unaffected.
    corrupt_project = "seal_corrupt_victim_project"
    intact_project = "seal_corrupt_bystander_project"
    corrupt_dir, corrupt_commit = _sealed_archive(git_repo, corrupt_project, register=False)
    intact_dir, intact_commit = _sealed_archive(git_repo, intact_project, register=False)
    _write_register_raw(
        git_repo,
        json.dumps(_register_record(corrupt_project, corrupt_commit))
        + "\n[\"a JSON array, not an object\"]\n"
        + json.dumps(_register_record(intact_project, intact_commit))
        + "\n",
    )

    corrupt_report = verify_archive(corrupt_dir, repo_root=git_repo)
    intact_report = verify_archive(intact_dir, repo_root=git_repo)

    assert corrupt_report.seal.status is SealStatus.UNVERIFIABLE
    assert intact_report.seal.status is SealStatus.MATCHED


# Secondary item 2 -- supersedes must name the previous sealed_commit.


def test_seal_supersedes_naming_previous_sealed_commit_is_matched(git_repo: Path) -> None:
    project_id = "seal_supersession_ok_project"
    archive_dir, first_commit = _sealed_archive(git_repo, project_id, register=False)
    (archive_dir / "supplementary_note.md").write_text("added by a superseding artifact\n", encoding="utf-8")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "superseding artifact"], cwd=git_repo)
    second_commit = _head_commit(git_repo)
    _write_register(
        git_repo,
        [
            _register_record(project_id, first_commit),
            _register_record(project_id, second_commit, supersedes=first_commit),
        ],
    )

    report = verify_archive(archive_dir, repo_root=git_repo)

    # The latest record governs (C-2), and it chains to its predecessor.
    assert report.seal.status is SealStatus.MATCHED


def test_seal_supersedes_not_naming_previous_sealed_commit_is_unverifiable(git_repo: Path) -> None:
    project_id = "seal_supersession_broken_project"
    archive_dir, first_commit = _sealed_archive(git_repo, project_id, register=False)
    _write_register(
        git_repo,
        [
            _register_record(project_id, first_commit),
            _register_record(project_id, first_commit, supersedes=None),
        ],
    )

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "supersedes" in report.seal.reason


def test_seal_first_record_with_non_null_supersedes_is_unverifiable(git_repo: Path) -> None:
    project_id = "seal_supersession_orphan_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    _write_register(git_repo, [_register_record(project_id, sealed_commit, supersedes="b" * 40)])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "no earlier record" in report.seal.reason


# AC-74-5 -- an underivable exclusion set is UNVERIFIABLE, never a
# comparison over an unbounded set, and never MATCHED.


def test_seal_dataset_manifest_missing_at_sealing_commit_is_unverifiable(git_repo: Path) -> None:
    project_id = "seal_no_dataset_manifest_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    (archive_dir / "dataset_manifest.json").unlink()
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive without a dataset manifest"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.status is not SealStatus.MATCHED
    assert report.seal.reason is not None
    assert "exclusion set underivable" in report.seal.reason
    assert report.overall_status is not OverallStatus.SOUND


def test_seal_malformed_dataset_manifest_at_sealing_commit_is_unverifiable(git_repo: Path) -> None:
    project_id = "seal_bad_dataset_manifest_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    bad_manifest = _dataset_manifest_dict(project_id)
    bad_manifest["schema_version"] = 99  # not the schema dataset_manifest.py parses
    (archive_dir / "dataset_manifest.json").write_text(json.dumps(bad_manifest), encoding="utf-8")
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive with a malformed dataset manifest"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "could not be parsed" in report.seal.reason


def test_seal_dataset_manifest_is_read_at_sealing_commit_not_working_tree(git_repo: Path) -> None:
    # SS7B D2: the exclusion set comes from the manifest *as it reads at
    # the sealing commit*. A manifest absent at that commit stays
    # underivable no matter how valid the working-tree copy is -- a
    # working-tree read would let a post-seal edit silently widen or
    # narrow the seal's own scope.
    project_id = "seal_manifest_source_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    (archive_dir / "dataset_manifest.json").unlink()
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive without a dataset manifest"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])
    # Perfectly valid -- but written after the seal, and therefore not
    # part of what was sealed.
    (archive_dir / "dataset_manifest.json").write_text(
        json.dumps(_dataset_manifest_dict(project_id)), encoding="utf-8"
    )

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.excluded_paths == ()


# AC-74-2 / SS7A B-1 -- HEAD independence.


def test_seal_is_independent_of_head_position_and_branch_refs(git_repo: Path) -> None:
    # The seal's fixed point is the Register's sealing commit, never
    # HEAD. Commits after the seal, a detached HEAD, and the deletion of
    # the branch the seal was made on are all topology facts, and none
    # may change the answer.
    project_id = "seal_head_independence_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id)

    before = verify_archive(archive_dir, repo_root=git_repo)
    assert before.seal.status is SealStatus.MATCHED

    _commit(git_repo, "unrelated_a.md", "after the seal\n", "post-seal commit a")
    _commit(git_repo, "unrelated_b.md", "also after the seal\n", "post-seal commit b")
    branch = _git_output(["rev-parse", "--abbrev-ref", "HEAD"], cwd=git_repo)
    _git(["checkout", "--detach", "-q"], cwd=git_repo)
    _git(["branch", "-D", branch], cwd=git_repo)

    assert _git_output(["rev-parse", "HEAD"], cwd=git_repo) != sealed_commit
    assert branch not in _git_output(["branch", "--list"], cwd=git_repo)

    after = verify_archive(archive_dir, repo_root=git_repo)

    assert after.seal.status is SealStatus.MATCHED
    assert after.seal.findings == ()


# AC-74-4 -- protected_file_hashes.json paths are excluded and reported.


def test_seal_protected_file_hashes_paths_are_excluded_and_reported(git_repo: Path) -> None:
    project_id = "seal_protected_exclusion_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    fixtures_dir = git_repo / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    protected_path = f"{project_id}/methodology.md"
    (fixtures_dir / "protected_file_hashes.json").write_text(
        json.dumps({protected_path: "sha256:" + "0" * 64, "docs/some_platform_file.md": "sha256:" + "1" * 64}),
        encoding="utf-8",
    )
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    (archive_dir / "methodology.md").write_text("tampered, but not the Seal's to judge\n", encoding="utf-8")

    report = verify_archive(archive_dir, repo_root=git_repo)

    # Excluded: the fixture owns this file's expected content, so the
    # Seal never compares it (AC-74-4) -- and says so on the report.
    assert report.seal.status is SealStatus.MATCHED
    assert report.seal.findings == ()
    assert protected_path in report.seal.excluded_paths
    # Reported coverage describes *this archive's* comparison domain --
    # a platform file the fixture also names is not this seal's business.
    assert "docs/some_platform_file.md" not in report.seal.excluded_paths
    assert all(path.startswith(f"{project_id}/") for path in report.seal.excluded_paths)


# --- Archive Seal / FreezeVerifier independence (governance hardening --
# pass 2026-07-26). Static (AST-on-source) checks, matching the
# convention tests/test_import_boundaries.py already uses for domain
# boundaries, plus a dynamic check on the imported module object itself.
# core.governance.archive_seal's own module docstring states this as a
# contract ("Never calls freeze_verifier.verify_freeze(),
# decision_recorder.verify_chain_intact(), or
# decision_recorder.verify_chain_anchored()"); these tests are what
# would fail if that contract were quietly violated.


def _archive_seal_source_ast() -> ast.Module:
    source_path = Path(archive_seal.__file__)
    return ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))


def _imported_module_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _imported_symbol_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.update(alias.name for alias in node.names)
    return names


def test_archive_seal_source_does_not_import_freeze_verifier_module() -> None:
    """No ``import`` or ``from ... import`` statement in archive_seal.py
    names the ``freeze_verifier`` module itself, by full or relative
    path -- the two modules' git-comparison logic must stay independent
    at the source level, not merely by convention."""
    imported_modules = _imported_module_names(_archive_seal_source_ast())
    offending = {m for m in imported_modules if m == "freeze_verifier" or m.endswith(".freeze_verifier")}
    assert offending == set(), f"archive_seal.py imports freeze_verifier via: {offending}"


def test_archive_seal_source_does_not_import_verify_freeze_symbol() -> None:
    """``verify_freeze`` (under any name, including a ``from ... import
    verify_freeze as x`` alias) is never pulled into archive_seal.py --
    the Seal branch computes its own comparison and must never delegate
    even a fragment of it to the freeze branch."""
    imported_symbols = _imported_symbol_names(_archive_seal_source_ast())
    assert "verify_freeze" not in imported_symbols


def test_archive_seal_source_does_not_import_chain_verification_helpers() -> None:
    """Neither ``verify_chain_intact`` nor ``verify_chain_anchored`` --
    decision_recorder's own chain-verification authority (AD-073
    Responsibilities) -- is imported by archive_seal.py. The Seal reads
    ``dataset_manifest.json`` and ``archive_manifest.json`` as plain
    data; it is never itself a chain verifier."""
    imported_symbols = _imported_symbol_names(_archive_seal_source_ast())
    forbidden = {"verify_chain_intact", "verify_chain_anchored"}
    assert imported_symbols & forbidden == set()


def test_archive_seal_module_object_has_no_freeze_verifier_symbols() -> None:
    """Dynamic counterpart to the static AST checks above: the imported
    ``archive_seal`` module object itself carries none of
    ``freeze_verifier``'s public names as attributes. This is what would
    catch a violation the static check could miss (e.g. a
    ``from core.governance.freeze_verifier import *`` or an
    ``importlib``-mediated indirection) -- either would leave a
    detectable attribute on the module object even if it dodged the
    literal ``ast.ImportFrom`` shape the static checks look for."""
    forbidden_names = {"verify_freeze", "verify_chain_intact", "verify_chain_anchored"}
    present = forbidden_names & set(dir(archive_seal))
    assert present == set(), f"archive_seal module exposes freeze/chain-verification names: {present}"


def test_archive_seal_not_a_git_repository_error_is_its_own_class() -> None:
    """archive_seal.NotAGitRepositoryError is a distinct class object
    from freeze_verifier.NotAGitRepositoryError -- redefined, never
    imported, per archive_seal's own module docstring. A shared
    exception type would be the first thread pulling the two modules'
    responsibilities together (frozen-commit-to-HEAD vs.
    sealed-commit-to-archive-files), which this module deliberately
    refuses."""
    assert archive_seal.NotAGitRepositoryError is not freeze_verifier.NotAGitRepositoryError
    assert issubclass(archive_seal.NotAGitRepositoryError, RuntimeError)
    assert issubclass(freeze_verifier.NotAGitRepositoryError, RuntimeError)


# --- AD-074 Increment 2 governance hardening (2026-07-26) -------------------
# The adversarial audit that prompted this pass found latent *trust
# boundary* defects rather than logic errors: inputs that decide the seal
# result while living outside the sealing commit. Each test below drives
# one of those inputs directly and proves the seal refuses to answer, or
# answers correctly, rather than being steered.


def _register_record_json(record: dict[str, object]) -> str:
    # ensure_ascii=False, matching canonical_jsonl.canonical_line -- the
    # U+2028 test below depends on the character reaching the file
    # literally rather than as a \u2028 escape.
    return json.dumps(record, ensure_ascii=False)


# BLOCKER 1 -- the protected-file exclusion source is the sealing commit,
# never the working tree.


def test_seal_post_seal_protected_fixture_edit_cannot_launder_a_tampered_file(git_repo: Path) -> None:
    """The defect this closes: ``protected_file_hashes.json`` decides
    which paths the Seal declines to check. Read from the working tree,
    anyone who could write that file could exempt any archive path from
    verification after the fact -- no commit, no Register record, nothing
    a reviewer would see. Tampering plus a matching fixture append must
    stay MISMATCH."""
    project_id = "seal_fixture_tamper_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)
    tampered_path = f"{project_id}/methodology.md"

    (archive_dir / "methodology.md").write_text("tampered after sealing\n", encoding="utf-8")
    # The forged exemption: written after the seal, so it is not part of
    # what was sealed, and must have no effect whatsoever.
    fixtures_dir = git_repo / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    (fixtures_dir / "protected_file_hashes.json").write_text(
        json.dumps({tampered_path: "sha256:" + "0" * 64}), encoding="utf-8"
    )

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MISMATCH
    assert {f.path for f in report.seal.findings if f.kind == "modified"} == {tampered_path}
    assert tampered_path not in report.seal.excluded_paths
    assert report.overall_status is OverallStatus.UNSOUND


def test_seal_protected_fixture_absent_at_sealing_commit_excludes_nothing(git_repo: Path) -> None:
    """Absent at the sealing commit is a derived answer -- the fixture
    named no paths -- not an underivable one. The comparison that follows
    is strictly wider, so nothing escapes the seal."""
    project_id = "seal_no_fixture_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED
    assert report.seal.excluded_paths == tuple(
        sorted(f"{project_id}/dataset_hashes/{table}.jsonl" for table in ("ETF", "PriceBar", "TradingSession"))
    )


def test_seal_protected_fixture_malformed_at_sealing_commit_is_unverifiable(git_repo: Path) -> None:
    project_id = "seal_bad_fixture_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    fixtures_dir = git_repo / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    (fixtures_dir / "protected_file_hashes.json").write_text("{not valid json", encoding="utf-8")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive with a malformed fixture"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "exclusion set underivable" in report.seal.reason


# BLOCKER 2 -- the attribute stack cannot silently change seal meaning.


def test_seal_post_seal_gitattributes_edit_is_unverifiable(git_repo: Path) -> None:
    """``.gitattributes`` decides how ``hash-object --path`` normalizes
    the bytes it hashes, so editing it edits the comparison's own rules.
    The seal must report that it cannot verify under changed rules rather
    than quietly answering under them."""
    project_id = "seal_attr_drift_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    (git_repo / ".gitattributes").write_bytes(b"*.jsonl -text\n")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    assert verify_archive(archive_dir, repo_root=git_repo).seal.status is SealStatus.MATCHED

    (git_repo / ".gitattributes").write_bytes(b"*.jsonl -text\n*.md -text\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert ".gitattributes" in report.seal.reason


def test_seal_gitattributes_appearing_after_the_seal_is_unverifiable(git_repo: Path) -> None:
    """A ``.gitattributes`` that did not exist at the sealing commit is a
    new rule source, not an absence of one."""
    project_id = "seal_attr_new_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)

    (git_repo / ".gitattributes").write_bytes(b"*.md -text\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "does not exist at the sealing commit" in report.seal.reason


def test_seal_gitattributes_inside_the_archive_is_also_verified(git_repo: Path) -> None:
    """Attribute lookup walks every directory from the repository root
    down to the compared path, so a ``.gitattributes`` nested inside the
    archive governs it too and is verified on the same terms."""
    project_id = "seal_attr_nested_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    (archive_dir / ".gitattributes").write_bytes(b"*.md text\n")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    assert verify_archive(archive_dir, repo_root=git_repo).seal.status is SealStatus.MATCHED

    (archive_dir / ".gitattributes").write_bytes(b"*.md -text\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE


def test_seal_info_attributes_override_is_unverifiable(git_repo: Path) -> None:
    """``.git/info/attributes`` is the one attribute source no config or
    environment variable can disable (which is why it is refused rather
    than neutralized), and it is never committed -- so a seal result that
    could depend on it depends on a file no audit trail contains."""
    project_id = "seal_info_attrs_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)

    assert verify_archive(archive_dir, repo_root=git_repo).seal.status is SealStatus.MATCHED

    info_dir = git_repo / ".git" / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    (info_dir / "attributes").write_bytes(b"*.md -text\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "info" in report.seal.reason and "attributes" in report.seal.reason


def test_seal_clean_filter_on_a_compared_path_is_refused(git_repo: Path) -> None:
    """A ``filter`` attribute names a driver whose ``clean`` command
    lives in git *config*, not in any attributes file the seal can
    verify. That command is arbitrary code run over the bytes before
    hashing, so it can make a tampered file hash to the sealed blob. The
    seal refuses to compare through one rather than trust it."""
    project_id = "seal_filter_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    # A driver name with no configured clean command: git passes the
    # content through unchanged, so the archive still commits normally,
    # while `check-attr` reports the attribute exactly as it would for a
    # real driver.
    (git_repo / ".gitattributes").write_bytes(b"*.md filter=seal_test_filter\n")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "filter" in report.seal.reason


# BLOCKER 3 -- sealed_commit must be a fixed object id.


@pytest.mark.parametrize(
    "sealed_commit",
    [
        "HEAD",
        "master",
        "main",
        "HEAD~1",
        "v1.0",
        "refs/heads/master",
        "A" * 40,  # a full-length id, but not canonical lowercase
        "0" * 39,  # one short
        "0" * 41,  # one long
        "0" * 7,  # an abbreviated hash
        "not-a-hash",
    ],
)
def test_seal_non_fixed_object_id_is_rejected_before_resolution(git_repo: Path, sealed_commit: str) -> None:
    """A Register record naming ``HEAD`` or a branch would make the seal
    re-read its own expected value on every call: it would verify the
    archive against whatever that ref says today and could never detect a
    committed edit -- threat 2 of SS5.2, and the "compare against HEAD"
    design SS6 records as rejected, reached through data instead of code.
    Rejection is syntactic and happens before any resolution attempt."""
    project_id = "seal_symbolic_ref_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id, register=False)
    _write_register(git_repo, [_register_record(project_id, sealed_commit)])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "fixed object id" in report.seal.reason
    assert report.overall_status is not OverallStatus.SOUND


def test_seal_head_naming_the_sealed_commit_is_still_rejected(git_repo: Path) -> None:
    """The rejection is about what the record *names*, not about where
    the name happens to point right now: ``HEAD`` is refused even in the
    one moment it resolves to exactly the right commit."""
    project_id = "seal_head_literal_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    assert _head_commit(git_repo) == sealed_commit  # HEAD is correct today
    _write_register(git_repo, [_register_record(project_id, "HEAD")])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE


def test_seal_full_lowercase_object_id_is_accepted(git_repo: Path) -> None:
    """The other half of BLOCKER 3: the one form that *is* a fixed point
    must still verify."""
    project_id = "seal_full_sha_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id)

    assert len(sealed_commit) in (40, 64)
    assert sealed_commit == sealed_commit.lower()

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED
    assert report.overall_status is OverallStatus.SOUND


def test_seal_ref_named_like_an_object_id_is_ignored_by_git_itself(git_repo: Path) -> None:
    """A branch whose name is 40 hex characters cannot impersonate an
    object id -- but **not** because of anything this module does, which
    is why this test's assertions were rewritten (AD-074 Increment 2
    acceptance audit, RF-2).

    git deliberately ignores a ref whose name ends in 40 hex characters
    when a 40-hex string is given as a revision, so the decoy resolves to
    no object at all and the record fails as an *unreadable commit*. The
    round-trip identity check is never reached, so asserting only
    ``reason is not None`` here made this test pass whether or not that
    check existed. The reachable case for it is the annotated tag below;
    this test now pins the git behaviour it actually depends on."""
    project_id = "seal_ref_impersonation_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    _commit(git_repo, "unrelated.md", "a later commit\n", "later")
    later_commit = _head_commit(git_repo)
    decoy = "b" * 40
    _git(["branch", decoy, later_commit], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, decoy)])

    # The premise: git does not resolve the 40-hex refname at all.
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{decoy}^{{commit}}"],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resolved.returncode != 0, "git resolved a 40-hex refname; this test's premise no longer holds"

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert sealed_commit != later_commit
    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "does not exist or is not readable" in report.seal.reason
    # Explicitly *not* the round-trip identity failure: that branch is
    # unreachable by this route, which is the whole reason the test below
    # exists rather than this one standing in for it.
    assert "resolves to" not in report.seal.reason


def test_seal_annotated_tag_object_id_cannot_impersonate_its_commit(git_repo: Path) -> None:
    """The **reachable** case the round-trip identity check exists for
    (AD-074 Increment 2 acceptance audit, RF-2).

    An annotated tag is a real object whose id is a full-length lowercase
    hexadecimal string, so it passes the syntactic fixed-id check
    untouched -- and then *peels* to a different object, the commit. A
    Register record naming the tag object therefore does not name the
    object the comparison would actually run against, and the tag is a
    re-pointable ref besides. Nothing but comparing what came back
    against what went in catches this."""
    project_id = "seal_annotated_tag_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    _git(["tag", "-a", "seal_tag", "-m", "annotated tag over the sealing commit"], cwd=git_repo)
    tag_object_id = _git_output(["rev-parse", "seal_tag"], cwd=git_repo)

    # The setup is only meaningful if the tag object is a distinct object
    # that clears the syntactic check and peels to the sealing commit.
    assert _git_output(["cat-file", "-t", tag_object_id], cwd=git_repo) == "tag"
    assert tag_object_id != sealed_commit
    assert archive_seal._fixed_commit_id_error(tag_object_id) is None
    assert _git_output(["rev-parse", f"{tag_object_id}^{{commit}}"], cwd=git_repo) == sealed_commit

    _write_register(git_repo, [_register_record(project_id, tag_object_id)])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    # The identity check itself, not merely "some reason was given".
    assert "resolves to" in report.seal.reason
    assert tag_object_id in report.seal.reason
    assert sealed_commit in report.seal.reason
    assert report.overall_status is not OverallStatus.SOUND


# M-1 -- snapshot_path must resolve strictly inside dataset_hashes/.


@pytest.mark.parametrize(
    "snapshot_path",
    [
        "../decision_log.md",
        "dataset_hashes/../../docs/ARCHITECTURE_DECISIONS.md",
        "decision_log.md",
        "/etc/passwd",
        "dataset_hashes",
        "dataset_hashes/",
        "./dataset_hashes/ETF.jsonl",
        "dataset_hashes\\ETF.jsonl",
        "C:/dataset_hashes/ETF.jsonl",
    ],
)
def test_seal_escaping_snapshot_path_refuses_the_exclusion_set(git_repo: Path, snapshot_path: str) -> None:
    """An exclusion names a file the Seal will not check, so the
    exclusion set is a privilege. An unvalidated ``snapshot_path`` hands
    that privilege to the manifest: ``../decision_log.md`` would drop a
    governance artifact out of the comparison entirely."""
    project_id = "seal_snapshot_escape_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    manifest = _dataset_manifest_dict(project_id)
    datasets = manifest["datasets"]
    assert isinstance(datasets, list)
    entry = datasets[0]
    assert isinstance(entry, dict)
    entry["snapshot_path"] = snapshot_path
    (archive_dir / "dataset_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "snapshot_path" in report.seal.reason
    assert report.overall_status is not OverallStatus.SOUND


# M-3 -- legacy archives are never sealed, by mechanism.


def test_seal_legacy_project_id_with_a_register_record_is_still_unverifiable(git_repo: Path) -> None:
    """AC-74-9 held only by accident before this pass: the named legacy
    archives carry no ``archive_manifest.json``, so they failed at
    project_id resolution for an unrelated reason. Give one a manifest
    and a Register record and the old implementation would have reported
    MATCHED."""
    project_id = "reference_v1"
    archive_dir, _ = _sealed_archive(git_repo, project_id)

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.status is not SealStatus.MATCHED
    assert report.seal.reason is not None
    assert "legacy" in report.seal.reason


def test_seal_lifecycle_version_legacy_with_a_register_record_is_unverifiable(git_repo: Path) -> None:
    project_id = "seal_declared_legacy_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_manifest(archive_dir, lifecycle_version="legacy")
    _write_transition_record(archive_dir, to_phase="Archive")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.completeness.status is CompletenessStatus.EXEMPT
    assert report.seal.status is SealStatus.UNVERIFIABLE


# M-4 -- an excluded path skips content comparison, not existence.


def test_seal_deleted_excluded_dataset_file_is_a_missing_finding(git_repo: Path) -> None:
    """An exclusion assigns a file's *bytes* to another control. Neither
    DatasetIntegrityChecker (unimplemented) nor the Phase-0 fixture
    asserts that the file still exists, and SS5.2's threat table promises
    that a file deleted from a closed archive is detected. Deleting an
    excluded file outright previously produced no finding from any
    mechanism at all."""
    project_id = "seal_excluded_deletion_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)
    excluded_path = f"{project_id}/dataset_hashes/ETF.jsonl"
    assert excluded_path in verify_archive(archive_dir, repo_root=git_repo).seal.excluded_paths

    (archive_dir / "dataset_hashes" / "ETF.jsonl").unlink()

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MISMATCH
    assert {f.path for f in report.seal.findings if f.kind == "missing"} == {excluded_path}
    # Still excluded from *content* comparison, and still reported as
    # bounded coverage -- the two facts are independent.
    assert excluded_path in report.seal.excluded_paths


def test_seal_excluded_file_content_change_remains_matched(git_repo: Path) -> None:
    """The other half of M-4: existence is checked, content is still not.
    A dataset snapshot's bytes remain DatasetIntegrityChecker's claim."""
    project_id = "seal_excluded_content_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)

    (archive_dir / "dataset_hashes" / "ETF.jsonl").write_text("tampered\n", encoding="utf-8")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED


# M-5 -- symlinks and gitlinks are refused, not guessed at.


def test_seal_symlink_in_the_archive_is_unverifiable(git_repo: Path) -> None:
    """``hash-object`` computes a meaningful identity only for a regular
    file. Following a symlink would report on bytes that are not at the
    path being compared; the seal declines to state a guarantee its
    mechanism does not support. Skipped where the platform will not
    create a symlink (unprivileged Windows), never asserted as a
    platform-independent guarantee."""
    project_id = "seal_symlink_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)
    target = archive_dir / "hypothesis.md"
    link = archive_dir / "hypothesis_link.md"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("this platform does not permit creating symlinks")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "symlink" in report.seal.reason


# M-6 -- the Register is canonical JSONL, validated as such.


def test_seal_register_with_crlf_is_refused(git_repo: Path) -> None:
    project_id = "seal_register_crlf_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    _write_register_raw(git_repo, json.dumps(_register_record(project_id, sealed_commit)) + "\r\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "CR line endings" in report.seal.reason


def test_seal_register_missing_trailing_newline_is_refused(git_repo: Path) -> None:
    """How an append interrupted mid-record presents: the last line
    cannot be assumed complete, so the file is refused rather than parsed
    under a guess."""
    project_id = "seal_register_no_newline_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    _write_register_raw(git_repo, json.dumps(_register_record(project_id, sealed_commit)))

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "trailing newline" in report.seal.reason


def test_seal_register_record_containing_u2028_is_read_as_one_record(git_repo: Path) -> None:
    """``str.splitlines()`` breaks on U+2028, U+2029, U+0085, VT and FF
    -- all legal unescaped inside a JSON string under
    ``ensure_ascii=False``, which is what canonical JSONL writes. One
    such character in a ``sealed_by`` field would have split a valid
    record into two unparseable fragments and reported a corrupt Register
    for a file that was never corrupt."""
    project_id = "seal_register_u2028_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    record = _register_record(project_id, sealed_commit, sealed_by="Reviewer\u2028Governance")
    _write_register_raw(git_repo, _register_record_json(record) + "\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED


def test_seal_register_blank_line_after_latest_record_is_unattributable(git_repo: Path) -> None:
    """A blank line is a canonical-JSONL violation, not whitespace to
    skip. Under the positional rule it is unattributable, so appearing
    after a project's latest record fails that lookup closed."""
    project_id = "seal_register_blank_line_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)
    _write_register_raw(git_repo, json.dumps(_register_record(project_id, sealed_commit)) + "\n\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "fails closed" in report.seal.reason


def test_seal_gitattributes_cannot_certify_itself_through_a_clean_filter(git_repo: Path) -> None:
    """The circularity that forced `.gitattributes` to be compared as raw
    bytes rather than via ``hash-object``: an attribute file carrying a
    rule about *itself* would otherwise be hashed through the very filter
    it declares, and a clean filter is arbitrary code that can emit
    whatever the sealed blob contained. The file would certify its own
    integrity while silently changing the rules every other comparison
    runs under.

    The test proves the laundering mechanism genuinely works before
    asserting that the seal is not fooled by it -- otherwise it would
    pass for the wrong reason."""
    project_id = "seal_attr_selfcert_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    sealed_attributes = b"*.jsonl -text\n"
    (git_repo / ".gitattributes").write_bytes(sealed_attributes)
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    sealed_commit = _head_commit(git_repo)
    _write_register(git_repo, [_register_record(project_id, sealed_commit)])
    assert verify_archive(archive_dir, repo_root=git_repo).seal.status is SealStatus.MATCHED

    # A clean filter that always emits the sealed bytes, applied by the
    # tampered .gitattributes to itself.
    (git_repo / "sealed_attributes.txt").write_bytes(sealed_attributes)
    _git(["config", "filter.launder.clean", "cat sealed_attributes.txt"], cwd=git_repo)
    (git_repo / ".gitattributes").write_bytes(b".gitattributes filter=launder\n*.md -text\n")

    # The attack really is an attack: hashing the tampered file through
    # its own declared filter reproduces the sealed blob exactly.
    sealed_blob = _git_output(["rev-parse", f"{sealed_commit}:.gitattributes"], cwd=git_repo)
    laundered_blob = _git_output(
        ["hash-object", "--path", ".gitattributes", "--", ".gitattributes"], cwd=git_repo
    )
    assert laundered_blob == sealed_blob, "the laundering setup failed; this test no longer tests anything"

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert ".gitattributes" in report.seal.reason


def test_seal_gitattributes_differing_only_by_line_endings_is_not_drift(git_repo: Path) -> None:
    """The other half of the raw comparison: comparing bytes must not
    manufacture drift out of a checkout artifact. Under
    ``core.autocrlf=true`` a working-tree `.gitattributes` legitimately
    carries CRLF while its blob holds LF, so line endings are normalized
    on both sides before comparing -- sound here, and only here, because
    `.gitattributes` is a line-oriented config file whose meaning does
    not depend on line-ending style."""
    project_id = "seal_attr_crlf_project"
    archive_dir = _write_seal_test_archive(git_repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    (git_repo / ".gitattributes").write_bytes(b"*.jsonl -text\n")
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-q", "-m", "seal archive"], cwd=git_repo)
    _write_register(git_repo, [_register_record(project_id, _head_commit(git_repo))])

    # Exactly what a checkout under core.autocrlf=true produces.
    (git_repo / ".gitattributes").write_bytes(b"*.jsonl -text\r\n")

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.MATCHED


# RF-1 -- the attribute *source stack* is pinned, not just the attribute
# files. git >=2.40 added `attr.tree` / `GIT_ATTR_SOURCE`, which select
# which tree attributes are read from at all. Neither was pinned before
# this remediation, so either one could silently relax the comparison
# that decides MATCHED (AD-074 Increment 2 acceptance audit).


def _empty_attr_tree(repo: Path) -> str:
    """The object id of a tree with nothing in it -- an alternate
    attribute source carrying no ``.gitattributes`` rules whatsoever."""
    result = subprocess.run(
        ["git", "mktree"], cwd=repo, input="", capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _byte_exact_sealed_archive(repo: Path, project_id: str) -> tuple[Path, str, str]:
    """A sealed archive whose ``*.jsonl`` artifacts are committed
    ``-text`` -- byte-exact, no line-ending normalization licensed.

    That is what makes a CRLF rewrite of one of them a genuine content
    change rather than a checkout artifact, and therefore what makes
    "the attributes were relaxed" observable as MISMATCH -> MATCHED.
    ``core.autocrlf`` is set explicitly rather than inherited so the
    bypass reproduces identically on every platform.

    Returns ``(archive_dir, sealed_commit, tampered_relative_path)``."""
    _git(["config", "core.autocrlf", "true"], cwd=repo)
    archive_dir = _write_seal_test_archive(repo, project_id)
    _write_transition_record(archive_dir, to_phase="Archive")
    (repo / ".gitattributes").write_bytes(b"*.jsonl -text\n")
    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-q", "-m", f"seal {project_id}"], cwd=repo)
    sealed_commit = _head_commit(repo)
    _write_register(repo, [_register_record(project_id, sealed_commit)])
    return archive_dir, sealed_commit, f"{project_id}/{TRANSITION_RECORDS_FILENAME}"


def _rewrite_with_crlf(path: Path) -> None:
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))


def test_seal_git_attr_source_env_cannot_relax_the_comparison(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``GIT_ATTR_SOURCE`` names a tree to read ``.gitattributes`` from
    instead of the working tree. Pointing it at a tree with no rules
    strips the ``-text`` that makes the archive's JSONL byte-exact, so a
    CRLF-tampered artifact normalizes straight back to the sealed blob.

    The environment variable **overrides** ``attr.tree`` config, so
    ``-c attr.tree=`` alone does not close this -- the variable has to be
    removed from the environment of every invocation. That ordering is
    asserted here rather than assumed."""
    project_id = "seal_attr_source_env_project"
    archive_dir, sealed_commit, relative_path = _byte_exact_sealed_archive(git_repo, project_id)
    assert verify_archive(archive_dir, repo_root=git_repo).seal.status is SealStatus.MATCHED

    _rewrite_with_crlf(archive_dir / TRANSITION_RECORDS_FILENAME)
    sealed_blob = _git_output(["rev-parse", f"{sealed_commit}:{relative_path}"], cwd=git_repo)
    assert _git_output(["hash-object", "--path", relative_path, "--", relative_path], cwd=git_repo) != sealed_blob

    monkeypatch.setenv("GIT_ATTR_SOURCE", _empty_attr_tree(git_repo))

    # The bypass is real: with the ruleless attribute source in force, the
    # tampered file hashes back to exactly the sealed blob. If this ever
    # stops holding, the test below is no longer testing anything.
    assert (
        _git_output(["hash-object", "--path", relative_path, "--", relative_path], cwd=git_repo) == sealed_blob
    ), "the GIT_ATTR_SOURCE relaxation no longer reproduces; this test no longer tests anything"

    report = verify_archive(archive_dir, repo_root=git_repo)

    # The exact security property: a tampered archive is still reported as
    # tampered, attributed to the tampered path -- never MATCHED.
    assert report.seal.status is not SealStatus.MATCHED
    assert report.seal.status is SealStatus.MISMATCH
    assert {f.path for f in report.seal.findings if f.kind == "modified"} == {relative_path}
    assert report.overall_status is OverallStatus.UNSOUND


def test_seal_git_env_removes_attr_source_and_pins_every_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    """The structural half of RF-1, asserted where it is decided rather
    than only through an end-to-end scenario: ``GIT_ATTR_SOURCE`` must
    not survive into *any* git invocation used for verification, and the
    pins must be applied at the single place that builds the argument
    vector so no call site can omit them.

    Removal is checked as *absence of the key*, not as an empty value:
    an empty value is a third state git may read as an attempt to name a
    tree."""
    monkeypatch.setenv("GIT_ATTR_SOURCE", "0" * 40)

    env = archive_seal._git_env()

    assert "GIT_ATTR_SOURCE" not in env
    assert env["GIT_ATTR_NOSYSTEM"] == "1"
    # Both pins, in the one tuple both `_run_git` and `_run_git_bytes`
    # splice ahead of every subcommand.
    assert archive_seal._ATTRIBUTE_PINNING_ARGS == ("-c", "core.attributesFile=", "-c", "attr.tree=")


def test_seal_attr_tree_config_cannot_relax_the_comparison(git_repo: Path) -> None:
    """The config half of the same source-selection knob. ``attr.tree``
    is ordinary git config, so it can be set in the repository, in global
    config, or injected through ``GIT_CONFIG_*`` -- none of which any
    artifact the seal verifies would show. ``-c attr.tree=`` ahead of
    every subcommand pins it back to the working tree."""
    project_id = "seal_attr_tree_config_project"
    archive_dir, sealed_commit, relative_path = _byte_exact_sealed_archive(git_repo, project_id)
    assert verify_archive(archive_dir, repo_root=git_repo).seal.status is SealStatus.MATCHED

    _rewrite_with_crlf(archive_dir / TRANSITION_RECORDS_FILENAME)
    sealed_blob = _git_output(["rev-parse", f"{sealed_commit}:{relative_path}"], cwd=git_repo)

    _git(["config", "attr.tree", _empty_attr_tree(git_repo)], cwd=git_repo)

    assert (
        _git_output(["hash-object", "--path", relative_path, "--", relative_path], cwd=git_repo) == sealed_blob
    ), "the attr.tree relaxation no longer reproduces; this test no longer tests anything"

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is not SealStatus.MATCHED
    assert report.seal.status is SealStatus.MISMATCH
    assert {f.path for f in report.seal.findings if f.kind == "modified"} == {relative_path}


def test_seal_global_attributes_file_is_disabled(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """M2 -- the ``core.attributesFile`` pin, bound to a bypass rather
    than to a status.

    A hostile global attributes file assigning ``working-tree-encoding``
    makes ``hash-object --path`` decode the working-tree bytes and
    re-encode them before hashing: a file rewritten as UTF-16 then hashes
    to the UTF-8 blob it was sealed as. That is a tampered file reported
    MATCHED, and it is not caught by the ``filter`` refusal, which looks
    at a different attribute. ``-c core.attributesFile=`` is what stops
    it."""
    project_id = "seal_global_attrs_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id)
    relative_path = f"{project_id}/hypothesis.md"
    assert verify_archive(archive_dir, repo_root=git_repo).seal.status is SealStatus.MATCHED

    sealed_blob = _git_output(["rev-parse", f"{sealed_commit}:{relative_path}"], cwd=git_repo)
    sealed_bytes = subprocess.run(
        ["git", "cat-file", "blob", sealed_blob], cwd=git_repo, capture_output=True, check=True
    ).stdout

    # Tamper: the same characters, but different bytes on disk.
    target = archive_dir / "hypothesis.md"
    target.write_bytes(sealed_bytes.decode("utf-8").encode("utf-16"))
    assert target.read_bytes() != sealed_bytes

    hostile_attributes = git_repo / "hostile_attributes"
    hostile_attributes.write_bytes(b"hypothesis.md working-tree-encoding=UTF-16\n")
    hostile_config = git_repo / "hostile_global_config"
    hostile_config.write_text(
        f"[core]\n\tattributesFile = {hostile_attributes.as_posix()}\n", encoding="utf-8"
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", hostile_config.as_posix())

    # The bypass is real: unpinned, the tampered file hashes to the sealed
    # blob and the archive would be reported MATCHED.
    assert (
        _git_output(["hash-object", "--path", relative_path, "--", relative_path], cwd=git_repo) == sealed_blob
    ), "the global-attributes relaxation no longer reproduces; this test no longer tests anything"

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is not SealStatus.MATCHED
    assert report.seal.status is SealStatus.MISMATCH
    assert {f.path for f in report.seal.findings if f.kind == "modified"} == {relative_path}


# F-3 -- Windows reparse points. `Path.is_symlink()` is False for an NTFS
# junction, so the M-5 symlink refusal had a platform-shaped hole in it.


def test_seal_windows_junction_in_the_archive_is_unverifiable(git_repo: Path) -> None:
    """A junction is a reparse point that redirects a directory without
    being a symlink by ``is_symlink()``'s reckoning, so the walk descended
    into it and reported another directory's files as though they were the
    archive's own. Junctions need no privilege to create, unlike symlinks,
    which makes this the *more* reachable of the two on Windows."""
    if os.name != "nt":
        pytest.skip("NTFS junctions exist only on Windows")

    project_id = "seal_junction_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)
    assert verify_archive(archive_dir, repo_root=git_repo).seal.status is SealStatus.MATCHED

    outside = git_repo / "outside_the_archive"
    outside.mkdir()
    (outside / "planted.md").write_text("bytes that are not the archive's\n", encoding="utf-8")
    junction = archive_dir / "junction_dir"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"this platform would not create an NTFS junction: {result.stdout.strip()}")

    # The exact gap being closed: the old test is False, the new one True.
    assert not junction.is_symlink()
    assert os.path.isjunction(junction)

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "symlink" in report.seal.reason
    assert "junction_dir" in report.seal.reason


# M14 -- non-regular entries on the *sealed tree* side, which no test
# reached before: the working-tree symlink refusal is a different branch.


@pytest.mark.parametrize("mode", ["120000", "160000"])
def test_seal_non_regular_tree_entry_at_the_sealing_commit_is_unverifiable(git_repo: Path, mode: str) -> None:
    """A symlink entry (``120000``) stores its target path as the blob and
    a gitlink (``160000``) stores a commit id belonging to another
    repository. Neither is something ``hash-object`` can state a
    meaningful identity for, so the seal refuses rather than comparing.

    Written straight into the index with ``update-index --cacheinfo``, so
    the test needs no symlink privilege and no submodule."""
    project_id = "seal_irregular_tree_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)

    if mode == "120000":
        object_id = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=git_repo,
            input="hypothesis.md",
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    else:
        object_id = sealed_commit

    entry_path = f"{project_id}/irregular_entry"
    _git(["update-index", "--add", "--cacheinfo", f"{mode},{object_id},{entry_path}"], cwd=git_repo)
    _git(["commit", "-q", "-m", f"commit a mode {mode} tree entry"], cwd=git_repo)
    irregular_commit = _head_commit(git_repo)
    _write_register(git_repo, [_register_record(project_id, irregular_commit)])

    assert _git_output(["ls-tree", irregular_commit, "--", entry_path], cwd=git_repo).startswith(mode)

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert f"mode {mode}" in report.seal.reason
    assert entry_path in report.seal.reason
    assert report.seal.findings == ()


# M24 -- an uncomputable working-side hash is "cannot verify", never
# "modified". Conflating the two is exactly what D3 forbids.


def test_seal_uncomputable_working_side_hash_is_unverifiable_not_mismatch(git_repo: Path) -> None:
    """When ``hash-object`` cannot read the file at all, the comparison is
    *incomplete* -- and an incomplete comparison is never MATCHED and
    never MISMATCH, because "I could not read it" is not evidence that the
    bytes changed. Skipped where the platform will not make a file
    unreadable to its owner, never asserted as a platform-independent
    guarantee."""
    project_id = "seal_unreadable_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id)
    relative_path = f"{project_id}/hypothesis.md"
    target = archive_dir / "hypothesis.md"

    original_mode = stat.S_IMODE(target.stat().st_mode)
    try:
        os.chmod(target, 0)
        try:
            with open(target, "rb"):
                pytest.skip("this platform does not make a file unreadable to its owner via chmod(0)")
        except PermissionError:
            pass

        report = verify_archive(archive_dir, repo_root=git_repo)

        assert report.seal.status is SealStatus.UNVERIFIABLE
        assert report.seal.reason is not None
        assert "could not compute a blob identity" in report.seal.reason
        assert relative_path in report.seal.reason
        assert report.seal.findings == ()
    finally:
        os.chmod(target, original_mode or stat.S_IWRITE | stat.S_IREAD)


# --------------------------------------------------------------------------
# Register trust hardening (governance hardening pass 2026-07-26, post-AD-075
# implementation audit). Two defects, verified against the shipped code
# before being fixed, and demonstrated together below because they compose:
# the working-tree Register supplies the commit id, and the missing
# reachability check makes an unreferenced forged commit an acceptable one.
# --------------------------------------------------------------------------


def _forged_unreachable_commit(repo: Path, message: str = "forged, unreferenced") -> str:
    """A commit object that exists in the object database and is named by
    no ref and reachable from none -- exactly what `git commit-tree`
    produces, and exactly what `rev-parse --verify <id>^{commit}`
    resolves as readily as any other commit. Built from the current
    index, so a caller that has staged a tamper gets a commit whose tree
    contains it."""
    tree = subprocess.run(
        ["git", "write-tree"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    forged = subprocess.run(
        ["git", "commit-tree", tree, "-p", _head_commit(repo), "-m", message],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    _git(["reset", "-q"], cwd=repo)
    return forged


def test_seal_uncommitted_working_tree_register_is_ignored(git_repo: Path) -> None:
    """AD-074 SS7B D5's second case, closed: an *uncommitted* Register
    rewrite "leaves no commit to review at all", so history review cannot
    reach it. The Register is read at HEAD, as committed content, and a
    working-tree edit therefore has no effect whatsoever -- neither to
    grant a seal nor to revoke one."""
    project_id = "seal_dirty_register_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id)

    committed = verify_archive(archive_dir, repo_root=git_repo)
    assert committed.seal.status is SealStatus.MATCHED

    # Overwrite the Register in the working tree only -- never committed.
    register = git_repo / "docs" / "archive_seal_register.jsonl"
    register.write_bytes(
        (json.dumps(_register_record(project_id, "b" * 40)) + "\n").encode("utf-8")
    )
    assert "archive_seal_register.jsonl" in subprocess.run(
        ["git", "status", "--porcelain"], cwd=git_repo, capture_output=True, text=True, check=True
    ).stdout

    after = verify_archive(archive_dir, repo_root=git_repo)

    # The uncommitted record named a commit that does not exist. Had it
    # been read, this would be UNVERIFIABLE; it is ignored, so the seal is
    # still the committed one's.
    assert after.seal.status is SealStatus.MATCHED
    assert after.seal == committed.seal


def test_seal_uncommitted_register_cannot_grant_a_seal(git_repo: Path) -> None:
    """The direction that matters for tamper resistance: writing a
    perfectly well-formed Register record for an unsealed archive, and
    never committing it, grants nothing."""
    project_id = "seal_uncommitted_grant_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id, register=False)

    docs_dir = git_repo / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "archive_seal_register.jsonl").write_bytes(
        (json.dumps(_register_record(project_id, sealed_commit)) + "\n").encode("utf-8")
    )

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.reason is not None
    assert "no committed Archive Seal Register record" in report.seal.reason


def test_seal_unreachable_sealing_commit_is_unverifiable_not_matched(git_repo: Path) -> None:
    """The forged-commit attack SS7A B-1 assumed was impossible. B-1 removed
    the reachability requirement on the premise that "an unreachable
    sealing commit is already UNVERIFIABLE ... the commit-resolution step
    already fails first if the commit cannot be found at all." It does
    not: `git commit-tree` mints a resolvable commit that no ref reaches,
    so resolution succeeds and the seal would attest to a tree that is in
    no history and no review."""
    project_id = "seal_forged_commit_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id, register=False)

    # Stage a tampered archive and freeze it into an unreferenced commit.
    (archive_dir / "methodology.md").write_bytes(b"methodology\nTAMPERED\n")
    _git(["add", "-A"], cwd=git_repo)
    forged = _forged_unreachable_commit(git_repo)

    # The forged commit resolves exactly like a real one ...
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{forged}^{{commit}}"],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert resolved == forged
    # ... and is reachable from nothing.
    assert (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", forged, "HEAD"], cwd=git_repo, capture_output=True
        ).returncode
        == 1
    )

    _write_register(git_repo, [_register_record(project_id, forged)])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.status is not SealStatus.MATCHED
    assert report.seal.reason is not None
    assert "not reachable from HEAD" in report.seal.reason
    assert report.overall_status is OverallStatus.UNVERIFIABLE


def test_seal_unreachable_commit_reports_cannot_verify_never_tampering(git_repo: Path) -> None:
    """The same code path is how a *sound* archive presents after a
    legitimate squash/rebase merge, a branch deletion plus gc, or a
    shallow clone (AD-074 SS7B D3). It must therefore never read as
    MISMATCH, and its message must name the remedies rather than accuse."""
    project_id = "seal_unreachable_legit_project"
    archive_dir, _ = _sealed_archive(git_repo, project_id, register=False)
    _git(["add", "-A"], cwd=git_repo)
    orphan = _forged_unreachable_commit(git_repo, message="an orphaned but honest commit")
    _write_register(git_repo, [_register_record(project_id, orphan)])

    report = verify_archive(archive_dir, repo_root=git_repo)

    assert report.seal.status is SealStatus.UNVERIFIABLE
    assert report.seal.findings == ()
    reason = report.seal.reason or ""
    assert "shallow clone" in reason
    assert "superseding Register record" in reason


def test_seal_still_matched_when_head_moves_on_a_descendant(git_repo: Path) -> None:
    """Reachability is a bounded dependency on HEAD, not the "compare
    against HEAD" design SS6 rejected. Commits made after the seal leave
    the sealing commit reachable, so the result is unchanged -- what the
    check refuses is a commit outside the history entirely."""
    project_id = "seal_head_advance_project"
    archive_dir, sealed_commit = _sealed_archive(git_repo, project_id)

    before = verify_archive(archive_dir, repo_root=git_repo)
    assert before.seal.status is SealStatus.MATCHED

    _commit(git_repo, "unrelated.txt", "later work\n", "after the seal")

    after = verify_archive(archive_dir, repo_root=git_repo)

    assert after.seal.status is SealStatus.MATCHED
    assert after.overall_status is before.overall_status
