"""Standing governance verification over every archive in the repository.

A thin command-line front end for
``core.governance.archive_verifier.verify_archive()`` -- it computes
nothing, verifies nothing, and owns no rule of its own. It exists so that
"run archive verification" is a single command a CI job (or a human) can
invoke, which is the *wiring* AD-073 named as future work and deliberately
did not decide, not a new mechanism.

**All four branches, every archive.** Each archive under
``research_archive/`` is verified with ``verify_freeze=True``, so the
freeze branch is invoked rather than omitted -- a standing governance
check is exactly the caller AD-073's "where appropriate == the caller
requested it" contemplates, and the one place where all four dimensions
should be asserted at once.

**Exit code, and what it deliberately does not gate on.** Non-zero for
``UNSOUND`` only. ``UNVERIFIABLE`` is reported prominently but does not
fail the run, because it is the *correct* status for archives that are
not sealed and never will be: the three legacy archives (AD-073 Non-goals
item 8) report the Seal branch ``UNVERIFIABLE`` permanently and by
design. Failing on it would make the check red on a healthy repository,
which is the fastest way to teach people to ignore it. The archives that
*must* be ``SOUND`` are asserted individually, and hard, by
``tests/test_sealed_archive_integrity.py`` -- that file is the gate;
this script is the sweep.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Runnable as `python tools/verify_archives.py` from anywhere, which puts
# tools/ on sys.path rather than the repository root. pytest gets the
# root from pyproject.toml's `pythonpath = ["."]`; a plain script has no
# equivalent, so it is added here rather than requiring callers to
# remember `python -m`.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.governance.archive_verifier import OverallStatus, verify_archive  # noqa: E402

RESEARCH_ARCHIVE_DIR = REPO_ROOT / "research_archive"


def main() -> int:
    if not RESEARCH_ARCHIVE_DIR.is_dir():
        print(f"No research_archive/ directory at {RESEARCH_ARCHIVE_DIR} -- nothing to verify.")
        return 0

    archives = sorted(path for path in RESEARCH_ARCHIVE_DIR.iterdir() if path.is_dir())
    if not archives:
        print("research_archive/ contains no archive directories -- nothing to verify.")
        return 0

    unsound: list[str] = []
    unverifiable: list[str] = []
    for archive_dir in archives:
        report = verify_archive(archive_dir, verify_freeze=True, repo_root=REPO_ROOT)
        freeze = report.freeze.status.value if report.freeze is not None else "not invoked"
        print(f"{archive_dir.name}: {report.overall_status.value.upper()}")
        print(f"    completeness : {report.completeness.status.value}")
        print(f"    seal         : {report.seal.status.value}")
        print(f"    dataset      : {report.dataset.status.value}")
        print(f"    freeze       : {freeze}")
        for reason in (report.completeness.reason, report.seal.reason, report.dataset.reason):
            if reason:
                print(f"    - {reason}")
        for finding in report.seal.findings:
            print(f"    - seal {finding.kind}: {finding.path}")
        for finding in report.dataset.findings:
            print(f"    - dataset {finding.kind}: {finding.detail}")

        if report.overall_status is OverallStatus.UNSOUND:
            unsound.append(archive_dir.name)
        elif report.overall_status is OverallStatus.UNVERIFIABLE:
            unverifiable.append(archive_dir.name)

    print()
    print(f"Verified {len(archives)} archive(s).")
    if unverifiable:
        print(
            f"UNVERIFIABLE ({len(unverifiable)}): {', '.join(unverifiable)} -- reported, not failed; "
            f"this is the correct and permanent status for an unsealed or legacy archive."
        )
    if unsound:
        print(f"UNSOUND ({len(unsound)}): {', '.join(unsound)}")
        return 1
    print("No archive reports UNSOUND.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
