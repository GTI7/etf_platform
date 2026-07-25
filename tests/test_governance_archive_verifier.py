from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

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
    # Seal is a Phase-1 stub -- always UNVERIFIABLE -- so overall status
    # can never be SOUND yet, even for a fully complete, closed archive.
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


def test_seal_stub_is_always_unverifiable(tmp_path: Path) -> None:
    complete_archive = _closed_complete_archive(tmp_path, name="complete_one")
    empty_archive = tmp_path / "empty_one"
    empty_archive.mkdir()

    complete_report = verify_archive(complete_archive)
    empty_report = verify_archive(empty_archive)

    for report in (complete_report, empty_report):
        assert report.seal.status is SealStatus.UNVERIFIABLE
        assert report.seal.findings == ()
        assert report.seal.reason is not None


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
