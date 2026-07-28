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

from tests.test_sealed_archive_integrity import SEAL_COVERED_ARCHIVE_PREFIXES

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

    `reference_h4` first-real-cycle addendum (2026-07-25): by the identical
    reasoning, `research_archive/reference_h4/` (superseding the narrower
    archive_manifest.json-only exception B-3b introduced -- that file is
    now one of several live evidence files in a directory that is itself
    a new, currently open cycle, not a closed one) and both
    `experiments/run_reference_h4_lifecycle.py` (cycle orchestration
    tooling) and `experiments/validate_h4_kurtosis.py` (the Phase 5
    implementation artifact) are excluded until this cycle reaches Phase 8
    Archive and is closed.

    **`reference_h4` re-basing (2026-07-26, AD-075).** That cycle reached
    Phase 8 Archive at `29553b7` on 2026-07-25, so the "until this cycle
    closes" condition above expired -- the finding recorded as D-9 in
    `docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md`. The exclusion is
    **not** dropped in response, and the difference matters. Dropping it
    would put those 16 files back into the walk below, whose closing
    assertion is `current_files == set(EXPECTED_HASHES)`; that then fails
    unless the Phase-0 fixture gains a key for each of them, and the
    fixture is immutable Phase-0 data (see the module docstring). Worse,
    a fixture key is exactly what `core.governance.archive_seal` reads
    **at the sealing commit as its exclusion set** (AD-074 §7B D9), so
    extending the fixture over `reference_h4` would remove that archive
    from the Archive Seal's own comparison rather than protect it twice.

    The exclusion is therefore **re-based onto Seal authority**: it is no
    longer a temporary waiver for an open cycle but a permanent
    delegation to a control that now exists. Every path under
    `SEAL_COVERED_ARCHIVE_PREFIXES` (imported from
    `tests/test_sealed_archive_integrity.py`, which is where that list is
    declared, once) has its bytes asserted there against sealing commit
    `29553b7`, and `test_fixture_and_seal_coverage_are_disjoint` asserts
    that the two controls never overlap. This test and that one partition
    the repository between them; neither weakens the other.

    The two `experiments/` scripts stay excluded for a different and less
    comfortable reason, stated plainly rather than folded into the
    sentence above: they live outside `research_archive/`, so the Seal's
    subject cannot reach them (AD-074 §5.1), and the Phase-0 fixture may
    not be extended to them either. They are covered by **no** automated
    integrity control -- D-9 surviving for two files, disclosed as
    **R-4b** in AD-075 §4, open and unassigned. Their residual is bounded
    by `test_reference_h4_unsealed_tooling_is_exactly_two_known_scripts`,
    which pins the set at exactly those two so it cannot grow silently.

    `reference_h2` addendum: by the same reasoning as the Positive Control
    Phase 3 addendum above (not the `reference_h4` re-basing, since
    `reference_h2` has no issued Archive Seal), `research_archive/reference_h2/`
    and its two `experiments/` scripts
    (`experiments/run_reference_h2_lifecycle.py`, the cycle's lifecycle-
    transition tooling, and `experiments/validate_h2_gate1_independence.py`,
    its Gate 1 evidence-generation script) are excluded: this is a new,
    currently open Pre-validation cycle (PRE_VALIDATION per
    `research_archive/reference_h2/transition_records.jsonl`, sequence 1),
    not historical closed-cycle evidence the Phase 0 snapshot was meant to
    freeze. Both scripts are additionally bounded by
    `test_reference_h4_unsealed_tooling_is_exactly_two_known_scripts`'s
    literal set in `tests/test_sealed_archive_integrity.py`, so a further
    unaccounted-for script still fails loudly there even though this test
    excludes the directory and these two specific files. This exclusion is
    scoped narrowly to `reference_h2`'s own directory and these two named
    scripts, not to `research_archive/` or `experiments/` generally.
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
                if relative_path.startswith(SEAL_COVERED_ARCHIVE_PREFIXES):
                    continue  # delegated to the Archive Seal (AD-075) -- see re-basing above
                if relative_path in (
                    "experiments/run_reference_h4_lifecycle.py",
                    "experiments/validate_h4_kurtosis.py",
                ):
                    continue  # unsealed, uncovered residual R-4b -- see re-basing above
                if relative_path.startswith("research_archive/reference_h2/"):
                    continue  # new, open Pre-validation cycle -- see reference_h2 addendum above
                if relative_path in (
                    "experiments/run_reference_h2_lifecycle.py",
                    "experiments/validate_h2_gate1_independence.py",
                ):
                    continue  # new, open Pre-validation cycle -- see reference_h2 addendum above
                current_files.add(relative_path)

    assert current_files == set(EXPECTED_HASHES)
