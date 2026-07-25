from __future__ import annotations

import json
from pathlib import Path

from core.governance.archive_verifier import (
    ARCHIVE_MANIFEST_FILENAME,
    CompletenessStatus,
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


def _write_transition_record(archive_dir: Path, *, to_phase: str, sequence_number: int = 1) -> None:
    record = {
        "project_id": archive_dir.name,
        "sequence_number": sequence_number,
        "from_phase": "Decision",
        "to_phase": to_phase,
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
    # write_bytes, not write_text: canonical_jsonl.read_canonical_jsonl()
    # rejects CRLF, and Windows text-mode writes would introduce it.
    (archive_dir / TRANSITION_RECORDS_FILENAME).write_bytes((json.dumps(record) + "\n").encode("utf-8"))


def _closed_complete_archive(tmp_path: Path, name: str = "some_project") -> Path:
    archive_dir = tmp_path / name
    _write_manifest(archive_dir)
    _write_all_required_items(archive_dir)
    _write_transition_record(archive_dir, to_phase="Archive")
    return archive_dir


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
