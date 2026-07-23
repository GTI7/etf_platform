"""Regression guard for docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Phase
0's "must remain untouched" list: every file under research_archive/,
every experiments/*.py script, and the maintenance/ remediation script.

tests/fixtures/protected_file_hashes.json is a one-time snapshot of
each protected file's SHA-256 content hash, taken before Phase 0 made
any change to the repository. If any of these files is ever edited,
moved, or deleted, this test fails -- the fixture itself must never be
regenerated to make a real change to a protected file pass silently;
regenerating it is only legitimate for a *deliberately reviewed and
approved* change to one of these files, which this platform's own
governance discipline requires to be rare (docs/RESEARCH_GOVERNANCE_STANDARD.md
Section 5, "nothing in this package is ever silently overwritten").
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "protected_file_hashes.json"


def _load_expected_hashes() -> dict[str, str]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


EXPECTED_HASHES = _load_expected_hashes()


@pytest.mark.parametrize("relative_path", sorted(EXPECTED_HASHES))
def test_protected_file_content_is_unchanged(relative_path: str) -> None:
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"{relative_path} is missing -- protected files must never be moved or deleted"
    assert _sha256(path) == EXPECTED_HASHES[relative_path], (
        f"{relative_path} content has changed since the Phase 0 snapshot was taken"
    )


def test_no_protected_directory_gained_or_lost_files() -> None:
    """Catches a new file silently added to (or removed from) a protected
    tree that the per-file check above, by construction, cannot see.

    Unlike research_archive/ (fully closed -- every file there is
    historical H3/REFERENCE evidence) and experiments/*.py (every script
    is historical, per-cycle evidence), maintenance/ is only partially
    frozen: docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Section 4 itself
    designates maintenance/verify_price_coverage.py as new, additive,
    reusable tooling -- not a historical artifact -- so maintenance/ is
    a closed set only over the specific file(s) already recorded in
    EXPECTED_HASHES (today: remediate_h3_invalid_pricebar_rows.py), the
    same way experiments/ is already scoped to *.py rather than every
    file physically present.

    Positive Control Phase 3 addendum: `research_archive/positive_control_phase3/`
    and `experiments/positive_control_phase3_pilot.py` are excluded from
    this check by the same reasoning already established for `maintenance/`'s
    exception above -- they are new, currently open Phase 3 Pre-validation
    evidence for a cycle that has not reached Phase 8 Archive (see that
    directory's own decision_log.md), not historical closed-cycle evidence
    the Phase 0 snapshot was meant to freeze. The three already-closed
    cycles (`reference_v1/`, `reference_v2_h1/`, `reference_h3/`) and every
    experiments/*.py script already present at the Phase 0 snapshot remain
    fully protected by this test unchanged -- this exception is scoped
    narrowly to the one new directory and one new script this addendum
    introduces, not to research_archive/ or experiments/ generally.
    """
    current_files = set()
    for base in ("research_archive", "experiments", "maintenance"):
        base_dir = REPO_ROOT / base
        for path in base_dir.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                if base == "experiments" and path.suffix != ".py":
                    continue  # experiments/README.md is documentation, not a protected script
                relative_path = path.relative_to(REPO_ROOT).as_posix()
                if base == "maintenance" and relative_path not in EXPECTED_HASHES:
                    continue  # new reusable tooling, not historical evidence -- see docstring above
                if relative_path.startswith("research_archive/positive_control_phase3/"):
                    continue  # new, open Phase 3 cycle -- see addendum above
                if relative_path == "experiments/positive_control_phase3_pilot.py":
                    continue  # new, open Phase 3 cycle -- see addendum above
                if relative_path == "research_archive/reference_h4/archive_manifest.json":
                    continue  # write-once archive identity artifact introduced by B-3b, not an evolving research artifact
                current_files.add(relative_path)

    assert current_files == set(EXPECTED_HASHES)
