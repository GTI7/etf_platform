"""Standing integrity check for the sealed `reference_h4` archive (AD-075).

This module is the automated control that
`docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` D-9 found missing: an
edit, an addition, or a deletion anywhere under
`research_archive/reference_h4/` fails here, where before AD-075 it failed
nowhere at all. It asserts the property, never re-implements it -- every
comparison is performed by `core.governance.archive_verifier.verify_archive()`
delegating to `core.governance.archive_seal.verify_seal()`, and this file
computes no hash, invokes no git command, and reads no archived byte of its
own.

**This file also owns the one delegation list on the platform**
(`SEAL_COVERED_ARCHIVE_PREFIXES`, AC-75-7).
`tests/test_repository_integrity_snapshot.py` imports it rather than
spelling the prefixes a second time: a delegation that can be written two
ways is a delegation that can drift into a gap between the two controls.

**The fixture/Seal boundary is a partition, not an overlap, and the
disjointness is load-bearing** (AD-075 §3). `tests/fixtures/protected_file_hashes.json`
is immutable Phase-0 data covering the three legacy archives and the
historical scripts; the Seal covers `research_archive/reference_h4/**`
against sealing commit `29553b7`. These must never intersect -- not because
redundancy would be wasteful, but because the Seal reads that fixture's key
set **at the sealing commit as its exclusion set** (AD-074 §7B D9, hardening
item `BLOCKER 1`). A fixture key naming a sealed path would therefore
*remove* that path from the Seal's content comparison. Adding `reference_h4`
to the fixture would not double-protect it; it would unprotect it. That is
why `test_fixture_and_seal_coverage_are_disjoint` exists, and why the
exclusion clauses in the snapshot test were re-based onto Seal authority
rather than dropped.

**What this file does not assert.** `OverallStatus.SOUND` means exactly what
AD-074 AC-74-13 says: the completeness check passed and the sealed archive
paths match the sealing commit tree. It is not a claim about dataset-hash
verification (`DatasetIntegrityChecker` is still unimplemented, so the three
`dataset_hashes/*.jsonl` files are excluded from the content comparison and
covered by a recorded hash that nothing verifies), about research
reproducibility, or about experiment validity. Nor does the Seal defeat
history rewrite or the loss of the repository (AD-074 §5.2) -- see
`_unverifiable_guidance` below, which is where that ceiling is turned into
an actionable failure message instead of a mystery.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.governance.archive_verifier import (
    CompletenessStatus,
    OverallStatus,
    SealStatus,
    verify_archive,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "protected_file_hashes.json"

# The single delegation list (AC-75-7). Every repo-relative path beginning
# with one of these prefixes has its integrity asserted by the Archive Seal
# and is therefore excluded from the Phase-0 gained/lost-files snapshot in
# `tests/test_repository_integrity_snapshot.py`, which imports this tuple.
# Extending this tuple delegates a directory away from the Phase-0 fixture,
# so it may only be extended for an archive that has an issued Archive Seal
# Register record -- otherwise the delegation points at nothing and the
# directory becomes unprotected, which is precisely D-9.
SEAL_COVERED_ARCHIVE_PREFIXES = (
    "research_archive/reference_h4/",
)

# The `reference_h4` cycle's tooling, which no seal can reach: both scripts
# live outside `research_archive/`, and the Seal's subject is
# `research_archive/<project_id>/**` (AD-074 §5.1). They are also outside the
# Phase-0 fixture, which may not be extended. They are therefore covered by
# no automated integrity control -- AD-075 §4 records this as **R-4b**, open
# and unassigned. Pinned here so the residual stays exactly two files and
# cannot grow silently.
_REFERENCE_H4_UNSEALED_TOOLING = frozenset(
    {
        "experiments/run_reference_h4_lifecycle.py",
        "experiments/validate_h4_kurtosis.py",
    }
)

# `positive_control_phase3` is a different, still-open cycle: its pilot
# script is excluded from the Phase-0 snapshot for the reason that test's own
# docstring gives, and it is not part of AD-075's boundary. Named here only
# so the "exactly two unprotected `reference_h4` scripts" assertion below can
# be exact rather than approximate.
_OPEN_CYCLE_PILOT_SCRIPT = "experiments/positive_control_phase3_pilot.py"

SEALED_ARCHIVE_DIR = REPO_ROOT / "research_archive" / "reference_h4"


def _load_fixture_keys() -> frozenset[str]:
    return frozenset(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _unverifiable_guidance(report_reason: str | None) -> str:
    """The remediation text attached to a failing seal assertion.

    A seal that cannot be verified is **not** a seal that failed: AD-074
    §5.2 and §7B D3 require that "unreachable" is never conflated with
    "modified", and a test that reports the two identically undoes that
    distinction at the only place an operator actually reads it. Every
    environmental cause below leaves the archived bytes untouched, and none
    of them is evidence of tampering."""
    return (
        f"\n\nseal reason: {report_reason}\n\n"
        "If the seal reports UNVERIFIABLE rather than MISMATCH, the archived bytes are "
        "very likely intact and the *sealing commit* is what became unreachable. The three "
        "environmental causes, none of which is evidence of tampering:\n"
        "  1. SHALLOW CLONE -- this working tree was created with `--depth`, so commit "
        "29553b7e5d96118b3f38ecc4de27362a07a210d1 is simply absent from the local object "
        "database. Fix: `git fetch --unshallow` (or fetch that object specifically).\n"
        "  2. UNREACHABLE SEALING COMMIT AFTER A HISTORY REWRITE -- a squash or rebase "
        "merge, `git commit --amend`, `filter-repo`, a force-push, or a branch deletion "
        "followed by `git gc` can drop the sealing commit from every ref and then prune it. "
        "No same-repo mechanism defeats this (AD-074 §3 S-4); the seal reporting "
        "UNVERIFIABLE here is the design working, not failing.\n"
        "  3. NON-GIT REPOSITORY -- the archive was copied out of a git working tree "
        "entirely (an export, a zip, a vendored copy), so there is no history to compare "
        "against at all.\n\n"
        "Remediation, in order of preference:\n"
        "  (a) RESTORE THE OBJECT. Recover commit 29553b7e5d96118b3f38ecc4de27362a07a210d1 "
        "from a remote, another clone, or the reflog, so the recorded seal verifies again. "
        "The Register record stays as it is -- nothing about the archive changed.\n"
        "  (b) ISSUE A SUPERSEDING REGISTER RECORD. Only if the sealing commit is "
        "irrecoverable. Append a new record to docs/archive_seal_register.jsonl whose "
        "`supersedes` names 29553b7e5d96118b3f38ecc4de27362a07a210d1 and whose "
        "`sealed_commit` names a commit that still exists and still contains the archive. "
        "This is a recorded human act (AD-074 §5.3, §9 item 3): no tool, hook, CLI command, "
        "or CI job may perform it, and `sealed_by` must name the human who did.\n\n"
        "Do NOT resolve this by extending tests/fixtures/protected_file_hashes.json over "
        "the archive, and do NOT delete the delegation in SEAL_COVERED_ARCHIVE_PREFIXES. "
        "The first would remove the archive from the Seal's own comparison (the fixture's "
        "key set is the Seal's exclusion set, AD-074 §7B D9); the second would return the "
        "archive to the unprotected state D-9 recorded."
    )


def test_reference_h4_archive_is_sealed_and_sound() -> None:
    """`research_archive/reference_h4/` verifies against its sealing commit.

    No skip, no xfail, no warning downgrade (AC-75-5): this is the control
    that replaced the expired exclusion clause, and a control that can decline
    to run is the state D-9 already found unacceptable. If the environment
    cannot support the check, that is a failure to be fixed, with the
    remediation spelled out in the message rather than papered over."""
    report = verify_archive(SEALED_ARCHIVE_DIR)

    assert report.completeness.status is CompletenessStatus.COMPLETE, (
        f"reference_h4 archive completeness is {report.completeness.status.value!r}, expected "
        f"'complete' -- all eight required items (Standard §5's seven plus archive_manifest.json) "
        f"must be present and of the right kind, and the cycle must be closed. "
        f"reason: {report.completeness.reason}\n"
        f"findings: {[f for f in report.completeness.findings if f.outcome != 'present']}"
    )

    assert report.seal.status is SealStatus.MATCHED, (
        f"reference_h4 archive seal is {report.seal.status.value!r}, expected 'matched'. "
        f"The archive's working-tree bytes no longer agree with sealing commit "
        f"29553b7e5d96118b3f38ecc4de27362a07a210d1, or the comparison could not be made.\n"
        f"findings: {list(report.seal.findings)}\n"
        f"excluded from content comparison (existence still checked): "
        f"{list(report.seal.excluded_paths)}\n"
        f"If the findings above are non-empty, an archived file was modified, added, or "
        f"deleted. research_archive/reference_h4/ is immutable (Phase G decision §8): the "
        f"remedy is to restore the archived bytes, never to re-issue the seal over the "
        f"change and never to edit the archive to match a new expectation."
        + _unverifiable_guidance(report.seal.reason)
    )

    assert report.overall_status is OverallStatus.SOUND, (
        f"reference_h4 overall status is {report.overall_status.value!r}, expected 'sound'. "
        f"completeness={report.completeness.status.value}, seal={report.seal.status.value}. "
        f"SOUND here means exactly 'the completeness check passed and the sealed archive "
        f"paths match the sealing commit tree' (AD-074 AC-74-13) -- it asserts nothing about "
        f"dataset-hash verification, reproducibility, or experiment validity."
        + _unverifiable_guidance(report.seal.reason)
    )


def test_fixture_and_seal_coverage_are_disjoint() -> None:
    """No Phase-0 fixture key may name a Seal-covered path (AC-75-8).

    This is not a tidiness rule. The Seal reads the fixture's key set at the
    sealing commit and treats every key as a path whose content it will
    **not** compare (AD-074 §7B D9, hardening item `BLOCKER 1`). An entry
    here for a sealed path would therefore silently narrow the seal, and the
    archive would keep reporting `MATCHED` while that file went unchecked.
    The two controls partition the repository; they never overlap."""
    overlapping = sorted(
        key for key in _load_fixture_keys() if key.startswith(SEAL_COVERED_ARCHIVE_PREFIXES)
    )
    assert not overlapping, (
        f"tests/fixtures/protected_file_hashes.json names {len(overlapping)} path(s) that are "
        f"delegated to the Archive Seal: {overlapping}.\n"
        f"A fixture key is an EXCLUSION to the Seal, not a second layer of protection -- these "
        f"paths would be dropped from the seal's content comparison entirely. Remove them from "
        f"the fixture, or remove the prefix from SEAL_COVERED_ARCHIVE_PREFIXES; never both "
        f"controls over one path. Note that the fixture is immutable Phase-0 data "
        f"(AD-074 §3 S-3, §9 item 7), so in practice the delegation is what must give way."
    )


def test_reference_h4_unsealed_tooling_is_exactly_two_known_scripts() -> None:
    """R-4b's residual is exactly two files, and stays exactly two (AC-75-13).

    `experiments/run_reference_h4_lifecycle.py` and
    `experiments/validate_h4_kurtosis.py` are the cycle's orchestration and
    Phase 5 implementation artifacts. They sit outside `research_archive/`,
    so the Seal's subject cannot reach them, and outside the Phase-0 fixture,
    which may not be extended -- so they are covered by no automated
    integrity control at all. That is D-9's finding surviving AD-075 for two
    files, disclosed as R-4b and deliberately not claimed as closed.

    This test does not protect those files; nothing does. It bounds them, so
    that a third unprotected script cannot join the residual silently."""
    fixture_keys = _load_fixture_keys()

    unprotected_scripts = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "experiments").glob("*.py")
        if path.relative_to(REPO_ROOT).as_posix() not in fixture_keys
    }

    assert unprotected_scripts == _REFERENCE_H4_UNSEALED_TOOLING | {_OPEN_CYCLE_PILOT_SCRIPT}, (
        f"the set of experiments/*.py scripts covered by no Phase-0 fixture entry has changed.\n"
        f"expected: {sorted(_REFERENCE_H4_UNSEALED_TOOLING | {_OPEN_CYCLE_PILOT_SCRIPT})}\n"
        f"actual:   {sorted(unprotected_scripts)}\n"
        f"A new unprotected script is a new integrity gap. If it belongs to a cycle that has "
        f"closed and been sealed, it still cannot be sealed (the Seal covers research_archive/ "
        f"only) -- widen R-4b's disclosure in docs/ARCHITECTURE_DECISIONS.md AD-075 §4 "
        f"deliberately rather than widening this literal."
    )

    for relative_path in sorted(_REFERENCE_H4_UNSEALED_TOOLING):
        assert (REPO_ROOT / relative_path).is_file(), (
            f"{relative_path} is missing. It is unprotected by any automated control (R-4b), "
            f"which is exactly why its disappearance must fail loudly here."
        )
        assert not relative_path.startswith(SEAL_COVERED_ARCHIVE_PREFIXES), (
            f"{relative_path} is under a Seal-delegated prefix, but the Seal's subject is "
            f"research_archive/<project_id>/** (AD-074 §5.1) -- a delegation that names a path "
            f"outside research_archive/ delegates to a control that will never see it."
        )
        assert relative_path not in fixture_keys, (
            f"{relative_path} has a Phase-0 fixture entry, so it is protected after all and "
            f"R-4b's disclosure in AD-075 §4 overstates the gap -- correct the disclosure."
        )
