"""Reference implementation of the `archive_manifest.json` schema.

See docs/RESEARCH_ARCHIVE_MANIFEST.md for the schema itself and the
rationale. This module is tooling, not `core/governance/` business
logic (that package remains intentionally empty in Phase 0 of
docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md) -- it builds and writes
one small JSON file plus empty evidence directories for a *new*
project's archive directory, nothing more (AD-038). It never reads or
interprets an existing manifest, and never implements
`ArchiveVerifier`.

Pure/IO split, matching the rest of this repository's discipline
(AD-007's injectable `Clock`, `core/analytics/domain/calculations.py`'s
"no I/O in domain functions" pattern): `build_manifest()` is a pure
function of its arguments; `write_manifest()` is the only function that
touches the filesystem, and it refuses two specific things outright --
writing into a legacy archive directory, or overwriting an existing
manifest.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.shared.clock import Clock

SCHEMA_VERSION = 1

# The three archive directories that predate this manifest concept.
# Never modified by this module or any future caller of it -- see
# docs/RESEARCH_ARCHIVE_MANIFEST.md's "Applicability" note.
LEGACY_ARCHIVE_PROJECT_IDS = frozenset({"reference_v1", "reference_v2_h1", "reference_h3"})

MANIFEST_FILENAME = "archive_manifest.json"


class LegacyArchiveWriteError(RuntimeError):
    """Raised when a caller attempts to write a manifest into one of the
    three archive directories that predate this concept."""


class ManifestAlreadyExistsError(RuntimeError):
    """Raised when `write_manifest()` would overwrite an existing
    manifest file -- this module never silently overwrites."""


def build_manifest(
    project_id: str,
    clock: Clock,
    *,
    lifecycle_version: str = "v1",
) -> dict:
    """Pure construction of a manifest dict matching
    docs/RESEARCH_ARCHIVE_MANIFEST.md's schema v1. No filesystem access.

    `clock` is a required, injected `Clock` (AD-007) -- no hidden
    default, matching this repository's "no implicit wall-clock read"
    discipline used throughout `core/`. Callers wanting real time pass
    `core.shared.clock.SystemClock()` explicitly.
    """
    if lifecycle_version not in ("legacy", "v1"):
        raise ValueError(f"lifecycle_version must be 'legacy' or 'v1', got {lifecycle_version!r}")
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "created_at": clock.now().isoformat(),
        "lifecycle_version": lifecycle_version,
    }


def write_manifest(archive_dir: Path, manifest: dict) -> Path:
    """Write `manifest` as `archive_dir/archive_manifest.json`.

    Refuses to write into any directory named after one of the three
    legacy archives, and refuses to overwrite an existing manifest file
    -- both refusals raise rather than silently doing nothing, matching
    maintenance/remediate_h3_invalid_pricebar_rows.py's "refuse to
    overwrite an existing archive artifact" precedent.
    """
    if archive_dir.name in LEGACY_ARCHIVE_PROJECT_IDS:
        raise LegacyArchiveWriteError(
            f"Refusing to write a manifest into {archive_dir} -- this is a legacy archive "
            "directory that predates the manifest concept (docs/RESEARCH_ARCHIVE_MANIFEST.md)."
        )
    manifest_path = archive_dir / MANIFEST_FILENAME
    if manifest_path.exists():
        raise ManifestAlreadyExistsError(
            f"{manifest_path} already exists -- refusing to overwrite an existing manifest."
        )
    archive_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=False), encoding="utf-8")
    return manifest_path


# The three evidence directories from docs/RESEARCH_GOVERNANCE_STANDARD.md
# Section 5 that this scaffold creates empty. It never creates
# hypothesis.md, methodology.md, dataset_manifest.json, or
# decision_log.md -- those are authored content, not structure, and
# scaffolding them empty would invite a future reader to mistake an
# empty stub for actual evidence (see AD-038).
EVIDENCE_SUBDIRECTORIES = ("dataset_hashes", "experiment_results", "reviewer_reports")

GITKEEP_FILENAME = ".gitkeep"


def scaffold_project_archive(
    project_id: str,
    archive_root: Path,
    clock: Clock,
    *,
    lifecycle_version: str = "v1",
) -> Path:
    """Create a new project's archive directory: its manifest plus the
    three empty evidence subdirectories from Standard Section 5.

    Thin composition of the existing pure/IO-split primitives above --
    `build_manifest()` then `write_manifest()` -- so both of
    `write_manifest()`'s refusals (legacy directory, existing manifest)
    apply here unchanged. Directories are created with a `.gitkeep` file
    each so git tracks the empty structure; no evidence content file is
    ever created here (AD-038) -- authoring `hypothesis.md`,
    `methodology.md`, `dataset_manifest.json`, and `decision_log.md`
    remains a separate, human act.
    """
    archive_dir = archive_root / project_id
    manifest = build_manifest(project_id, clock, lifecycle_version=lifecycle_version)
    manifest_path = write_manifest(archive_dir, manifest)

    for subdirectory in EVIDENCE_SUBDIRECTORIES:
        evidence_dir = archive_dir / subdirectory
        evidence_dir.mkdir(parents=True, exist_ok=True)
        (evidence_dir / GITKEEP_FILENAME).touch()

    return manifest_path
