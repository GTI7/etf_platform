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
    drifting from what actually exists under research_archive/."""
    repo_root = Path(__file__).resolve().parent.parent
    actual = {p.name for p in (repo_root / "research_archive").iterdir() if p.is_dir()}
    assert LEGACY_ARCHIVE_PROJECT_IDS == actual


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
