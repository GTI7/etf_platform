"""Tests for tools/archive_manifest.py -- the reference implementation of
the docs/RESEARCH_ARCHIVE_MANIFEST.md schema. These tests never touch
the real research_archive/ directory; every write goes to pytest's
tmp_path.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.shared.clock import FixedClock
from tools.archive_manifest import (
    EVIDENCE_SUBDIRECTORIES,
    LEGACY_ARCHIVE_PROJECT_IDS,
    LegacyArchiveWriteError,
    ManifestAlreadyExistsError,
    build_manifest,
    scaffold_project_archive,
    write_manifest,
)

FIXED_NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def test_build_manifest_matches_schema_v1() -> None:
    manifest = build_manifest("h4", FixedClock(FIXED_NOW))

    assert manifest == {
        "schema_version": 1,
        "project_id": "h4",
        "created_at": FIXED_NOW.isoformat(),
        "lifecycle_version": "v1",
    }


def test_build_manifest_accepts_legacy_lifecycle_version() -> None:
    manifest = build_manifest("some_past_cycle", FixedClock(FIXED_NOW), lifecycle_version="legacy")
    assert manifest["lifecycle_version"] == "legacy"


def test_build_manifest_rejects_unknown_lifecycle_version() -> None:
    with pytest.raises(ValueError):
        build_manifest("h4", FixedClock(FIXED_NOW), lifecycle_version="v2")


def test_write_manifest_creates_file_with_exact_content(tmp_path: Path) -> None:
    manifest = build_manifest("h4", FixedClock(FIXED_NOW))
    archive_dir = tmp_path / "h4"

    written_path = write_manifest(archive_dir, manifest)

    assert written_path == archive_dir / "archive_manifest.json"
    assert json.loads(written_path.read_text(encoding="utf-8")) == manifest


def test_write_manifest_refuses_to_overwrite_existing_manifest(tmp_path: Path) -> None:
    manifest = build_manifest("h4", FixedClock(FIXED_NOW))
    archive_dir = tmp_path / "h4"
    write_manifest(archive_dir, manifest)

    with pytest.raises(ManifestAlreadyExistsError):
        write_manifest(archive_dir, manifest)


@pytest.mark.parametrize("legacy_project_id", sorted(LEGACY_ARCHIVE_PROJECT_IDS))
def test_write_manifest_refuses_legacy_archive_directories(tmp_path: Path, legacy_project_id: str) -> None:
    manifest = build_manifest(legacy_project_id, FixedClock(FIXED_NOW), lifecycle_version="legacy")
    archive_dir = tmp_path / legacy_project_id

    with pytest.raises(LegacyArchiveWriteError):
        write_manifest(archive_dir, manifest)

    assert not (archive_dir / "archive_manifest.json").exists()


def test_legacy_archive_ids_match_real_research_archive_directories() -> None:
    """Guards against this module's protected-directory list silently
    drifting from what actually exists under research_archive/.

    Equality (rather than subset) was correct only as long as no new
    project archive had been created since this manifest concept was
    introduced (docs/RESEARCH_ARCHIVE_MANIFEST.md: "does not generate a
    manifest for any hypothesis currently open on this platform ...
    H3 is closed; H4 has not opened"). Now that a new project archive
    (`positive_control_phase3/`, scaffolded via
    `scaffold_project_archive()`) exists alongside the three legacy
    ones, the correct invariant is: every legacy id still has a real
    directory (unchanged -- historical evidence stays protected), and
    every *other* directory has adopted the manifest schema rather than
    being an undocumented ad hoc addition.
    """
    repo_root = Path(__file__).resolve().parent.parent
    research_archive_dir = repo_root / "research_archive"
    actual = {p.name for p in research_archive_dir.iterdir() if p.is_dir()}
    assert LEGACY_ARCHIVE_PROJECT_IDS <= actual

    for project_id in actual - LEGACY_ARCHIVE_PROJECT_IDS:
        manifest_path = research_archive_dir / project_id / "archive_manifest.json"
        assert manifest_path.is_file(), (
            f"{project_id} is a new (non-legacy) research_archive/ directory but has no "
            "archive_manifest.json -- new project archives must be created via "
            "tools/archive_manifest.py's scaffold_project_archive(), not an ad hoc directory."
        )


def test_scaffold_project_archive_creates_manifest(tmp_path: Path) -> None:
    manifest_path = scaffold_project_archive("h4", tmp_path, FixedClock(FIXED_NOW))

    assert manifest_path == tmp_path / "h4" / "archive_manifest.json"
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == {
        "schema_version": 1,
        "project_id": "h4",
        "created_at": FIXED_NOW.isoformat(),
        "lifecycle_version": "v1",
    }


def test_scaffold_project_archive_creates_three_evidence_directories(tmp_path: Path) -> None:
    scaffold_project_archive("h4", tmp_path, FixedClock(FIXED_NOW))
    archive_dir = tmp_path / "h4"

    assert EVIDENCE_SUBDIRECTORIES == ("dataset_hashes", "experiment_results", "reviewer_reports")
    for subdirectory in EVIDENCE_SUBDIRECTORIES:
        assert (archive_dir / subdirectory).is_dir()


def test_scaffold_project_archive_creates_gitkeep_files(tmp_path: Path) -> None:
    scaffold_project_archive("h4", tmp_path, FixedClock(FIXED_NOW))
    archive_dir = tmp_path / "h4"

    for subdirectory in EVIDENCE_SUBDIRECTORIES:
        gitkeep = archive_dir / subdirectory / ".gitkeep"
        assert gitkeep.is_file()
        assert gitkeep.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize("legacy_project_id", sorted(LEGACY_ARCHIVE_PROJECT_IDS))
def test_scaffold_project_archive_refuses_legacy_archive_directories(
    tmp_path: Path, legacy_project_id: str
) -> None:
    with pytest.raises(LegacyArchiveWriteError):
        scaffold_project_archive(legacy_project_id, tmp_path, FixedClock(FIXED_NOW), lifecycle_version="legacy")

    archive_dir = tmp_path / legacy_project_id
    assert not (archive_dir / "archive_manifest.json").exists()
    for subdirectory in EVIDENCE_SUBDIRECTORIES:
        assert not (archive_dir / subdirectory).exists()


def test_scaffold_project_archive_refuses_to_overwrite_existing_manifest(tmp_path: Path) -> None:
    scaffold_project_archive("h4", tmp_path, FixedClock(FIXED_NOW))

    with pytest.raises(ManifestAlreadyExistsError):
        scaffold_project_archive("h4", tmp_path, FixedClock(FIXED_NOW))


def test_scaffold_project_archive_does_not_create_evidence_content_files(tmp_path: Path) -> None:
    scaffold_project_archive("h4", tmp_path, FixedClock(FIXED_NOW))
    archive_dir = tmp_path / "h4"

    assert not (archive_dir / "hypothesis.md").exists()
    assert not (archive_dir / "methodology.md").exists()
    assert not (archive_dir / "dataset_manifest.json").exists()
    assert not (archive_dir / "decision_log.md").exists()
