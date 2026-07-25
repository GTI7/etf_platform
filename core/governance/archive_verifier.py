"""Archive verification (Governance) -- AD-073 Phase 1.

Implements the completeness branch and the Archive Seal *stub* of
``ArchiveVerifier``, per ``docs/ARCHITECTURE_DECISIONS.md`` AD-073.
``verify_archive()`` is the one public entry point (AC-1): it takes an
archive *location*, not a ``ProjectId`` (AD-073 conflict C-1 -- Governance
may never import Research's ``ProjectRegistry``, exactly the tension
AD-033 already resolved for ``FreezeVerifier``).

**Phase 1 scope.** Two of the three branches described by AD-073's
Architecture overview:

- **Completeness** -- Standard §5's seven required items plus
  ``archive_manifest.json``, checked for presence and kind only (AC-6,
  AC-7 do not apply here; this branch never reads file content). Legacy
  archives (AD-030's three named exceptions, or any archive whose
  manifest states ``lifecycle_version: "legacy"``) are exempt. A
  ``lifecycle_version: "v1"`` archive whose cycle has not closed
  (``transition_records.jsonl``'s terminal record's ``to_phase`` is not
  ``"Archive"``) is ``UNVERIFIABLE`` (AC-15).
- **Archive Seal** -- a stub only, per AD-073 Migration item 2: no sealed
  manifest format exists yet (Non-goals item 1), so this branch reports
  ``UNVERIFIABLE`` for every archive, unconditionally. It computes no
  hash and reads no archived bytes (AC-2, AC-3). Seal *logic* is
  deliberately not implemented here -- that is future work gated on a
  sealed-manifest format decision this AD does not make.

The **freeze branch is not wired in Phase 1** and does not appear in
``ArchiveReport``. AD-073's "where appropriate" freeze integration
(reading ``transition_records.jsonl``'s terminal record's
``freeze_commit_ref`` / ``freeze_covered_paths`` and invoking
``FreezeVerifier.verify_freeze()``) is a later increment; this module
never imports or calls ``freeze_verifier``.

**Read-only, always.** Nothing here opens a file for writing. Closure and
applicability determination read ``archive_manifest.json`` (plain JSON
parse) and ``transition_records.jsonl`` via
``core.governance.decision_recorder.read_chain()`` -- a structural
reader, not a verification authority. This module never calls
``verify_chain_intact()`` or ``verify_chain_anchored()``; chain
verification remains exclusively ``decision_recorder``'s question
(AD-073 Responsibilities, ``ArchiveVerifier`` -- does; Compatibility
AD-063 note).

**Overall status.** ``ArchiveReport.overall_status`` is never stored --
it is a property, recomputed on every access from the two branch
statuses under ``derive_overall_status()``'s documented, fixed
precedence (AD-073 Decision part 6, AC-5): a confirmed problem
(``INCOMPLETE`` / ``MISMATCH``) outranks ``UNVERIFIABLE``, which
outranks a confirmed-good result. Because the Seal branch is a stub that
can only ever report ``UNVERIFIABLE`` in Phase 1, ``overall_status`` can
never be ``SOUND`` yet -- an accurate reflection of "content integrity
has never actually been checked", not a defect in the derivation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from core.governance.decision_recorder import (
    ARCHIVE_MANIFEST_FILENAME,
    TRANSITION_RECORDS_FILENAME,
    read_chain,
)

# The three archive directories that predate archive_manifest.json
# (docs/RESEARCH_ARCHIVE_MANIFEST.md "Applicability"). Duplicated from
# tools/archive_manifest.py's own LEGACY_ARCHIVE_PROJECT_IDS rather than
# imported from it: core/ never imports tools/ (the dependency runs the
# other way), matching how core/governance/decision_recorder.py already
# duplicates ARCHIVE_MANIFEST_FILENAME instead of reaching into tools/.
LEGACY_ARCHIVE_PROJECT_IDS = frozenset({"reference_v1", "reference_v2_h1", "reference_h3"})

_ARCHIVE_TERMINAL_PHASE = "Archive"

# Standard §5's seven required items, plus archive_manifest.json -- a
# required item under AD-030's own applicability contract, never counted
# as one of the seven (the Standard does not name it), checked by this
# same branch alongside them with no per-item exception.
_REQUIRED_ITEMS: tuple[tuple[str, str], ...] = (
    ("hypothesis.md", "file"),
    ("methodology.md", "file"),
    ("dataset_manifest.json", "file"),
    ("dataset_hashes", "directory"),
    ("experiment_results", "directory"),
    ("reviewer_reports", "directory"),
    ("decision_log.md", "file"),
    (ARCHIVE_MANIFEST_FILENAME, "file"),
)

_SEAL_STUB_REASON = (
    "seal comparison deferred: no sealed-manifest format exists yet "
    "(AD-073 Non-goals item 1, Migration item 2) -- reports UNVERIFIABLE "
    "for every archive until one is decided"
)


class CompletenessStatus(str, Enum):
    """Four-valued -- this branch's own vocabulary (AD-073 Architecture
    overview, Status vocabulary), never merged with the Seal's or the
    Freeze branch's."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    EXEMPT = "exempt"
    UNVERIFIABLE = "unverifiable"


class SealStatus(str, Enum):
    """The Seal's own three-valued vocabulary. ``MATCHED`` and
    ``MISMATCH`` are unreachable through this module's public API in
    Phase 1 -- the stub only ever produces ``UNVERIFIABLE`` -- but both
    are defined here because they are this branch's real vocabulary
    under AD-073, not a Phase-1-only shape."""

    MATCHED = "matched"
    MISMATCH = "mismatch"
    UNVERIFIABLE = "unverifiable"


class OverallStatus(str, Enum):
    """The report's derived, never-stored overall status (AD-073
    Decision part 6, AC-5)."""

    SOUND = "sound"
    UNSOUND = "unsound"
    UNVERIFIABLE = "unverifiable"


@dataclass(frozen=True, slots=True)
class CompletenessFinding:
    """One required item's presence/kind check. ``outcome`` is exactly
    one of ``"present"``, ``"missing"``, ``"wrong_kind"`` -- content is
    never examined (an empty file or directory is ``"present"``)."""

    item: str
    expected_kind: str
    outcome: str


@dataclass(frozen=True, slots=True)
class CompletenessReport:
    status: CompletenessStatus
    findings: tuple[CompletenessFinding, ...]
    reason: str | None


@dataclass(frozen=True, slots=True)
class SealFinding:
    """Reserved shape for a future, non-stub Seal implementation
    (AC-7's three distinguishable finding kinds: ``"modified"``,
    ``"missing"``, ``"unexpected"``). Always empty in Phase 1."""

    path: str
    kind: str


@dataclass(frozen=True, slots=True)
class SealReport:
    status: SealStatus
    findings: tuple[SealFinding, ...]
    reason: str | None


@dataclass(frozen=True, slots=True)
class ArchiveReport:
    """One archive's verification report, per-branch attributed
    (AD-073 AC-4). ``overall_status`` is a property, not a stored field
    -- it is recomputed from ``completeness.status`` and ``seal.status``
    on every access, and can never drift from them."""

    archive_dir: Path
    completeness: CompletenessReport
    seal: SealReport

    @property
    def overall_status(self) -> OverallStatus:
        return derive_overall_status(self.completeness.status, self.seal.status)


def derive_overall_status(completeness: CompletenessStatus, seal: SealStatus) -> OverallStatus:
    """AD-073's *Overall status aggregation rule*, restricted to the two
    branches Phase 1 invokes. Fixed precedence, first match wins:
    confirmed problem, then unverifiable, then confirmed good -- AD-051's
    own precedence, applied across branches (AD-073 Architecture
    overview)."""
    if completeness is CompletenessStatus.INCOMPLETE or seal is SealStatus.MISMATCH:
        return OverallStatus.UNSOUND
    if completeness is CompletenessStatus.UNVERIFIABLE or seal is SealStatus.UNVERIFIABLE:
        return OverallStatus.UNVERIFIABLE
    return OverallStatus.SOUND


def _read_manifest(archive_dir: Path) -> dict[str, Any] | None:
    manifest_path = archive_dir / ARCHIVE_MANIFEST_FILENAME
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _check_item(archive_dir: Path, name: str, expected_kind: str) -> CompletenessFinding:
    path = archive_dir / name
    if not path.exists():
        return CompletenessFinding(item=name, expected_kind=expected_kind, outcome="missing")
    is_directory = path.is_dir()
    if (expected_kind == "directory") != is_directory:
        return CompletenessFinding(item=name, expected_kind=expected_kind, outcome="wrong_kind")
    return CompletenessFinding(item=name, expected_kind=expected_kind, outcome="present")


def _cycle_closed(archive_dir: Path) -> bool:
    """True iff transition_records.jsonl's terminal record (highest
    sequence_number) has to_phase == "Archive". Uses read_chain() only
    -- a structural reader -- never verify_chain_intact() or
    verify_chain_anchored(). read_chain() raises on anything it cannot
    turn into a well-formed DecisionRecord: invalid JSON
    (json.JSONDecodeError), non-canonical bytes (ValueError, from
    read_canonical_jsonl's CRLF/trailing-newline checks, which also
    covers invalid UTF-8: UnicodeDecodeError is a ValueError subclass),
    a row missing a required DecisionRecord field (KeyError), a row
    whose shape is incompatible -- a non-dict row, a non-dict
    "authorization", a non-list "gate_outcomes" -- each surfacing as
    TypeError from the dict/tuple access in _row_to_record, or the file
    being unreadable at the filesystem level -- a directory in place of
    transition_records.jsonl, or a permissions failure (OSError, e.g.
    IsADirectoryError / PermissionError; read_chain()'s own
    path.exists() guard only rules out a missing path, not a path that
    exists but cannot be read as a file). None of these establishes a
    terminal record, so all are indistinguishable from "no valid
    terminal record exists" here and are treated the same as an
    unclosed cycle, never re-raised."""
    try:
        records = read_chain(archive_dir / TRANSITION_RECORDS_FILENAME)
    except (json.JSONDecodeError, ValueError, KeyError, TypeError, OSError):
        return False
    if not records:
        return False
    terminal = max(records, key=lambda record: record.sequence_number)
    return terminal.to_phase == _ARCHIVE_TERMINAL_PHASE


def _verify_completeness(archive_dir: Path) -> CompletenessReport:
    try:
        manifest = _read_manifest(archive_dir)
    except json.JSONDecodeError:
        return CompletenessReport(
            status=CompletenessStatus.UNVERIFIABLE,
            findings=(),
            reason=(
                f"{ARCHIVE_MANIFEST_FILENAME} is not valid JSON -- cannot determine legacy "
                "exemption or cycle closure"
            ),
        )
    except (UnicodeDecodeError, OSError) as exc:
        # UnicodeDecodeError: the file exists but is not valid UTF-8.
        # OSError (IsADirectoryError, PermissionError, or any other
        # filesystem read failure): _read_manifest's own path.exists()
        # guard only rules out a missing path, not a path that exists
        # but cannot be read as a file -- e.g. archive_manifest.json
        # replaced by a directory. Either way this is exactly as unable
        # to determine legacy exemption or cycle closure as invalid JSON
        # is, so it gets the same UNVERIFIABLE treatment rather than
        # propagating a crash.
        return CompletenessReport(
            status=CompletenessStatus.UNVERIFIABLE,
            findings=(),
            reason=(
                f"{ARCHIVE_MANIFEST_FILENAME} could not be read ({exc.__class__.__name__}) -- "
                "cannot determine legacy exemption or cycle closure"
            ),
        )

    if manifest is not None and not isinstance(manifest, dict):
        # Valid JSON but not a JSON object (e.g. a top-level array or a
        # bare scalar) -- .get() below would raise AttributeError. This
        # is exactly as unable to establish legacy exemption or cycle
        # closure as invalid JSON is, so it gets the same UNVERIFIABLE
        # treatment rather than propagating a crash.
        return CompletenessReport(
            status=CompletenessStatus.UNVERIFIABLE,
            findings=(),
            reason=(
                f"{ARCHIVE_MANIFEST_FILENAME} does not contain a JSON object (found "
                f"{type(manifest).__name__} instead) -- cannot determine legacy exemption or "
                "cycle closure"
            ),
        )

    if manifest is None and archive_dir.name in LEGACY_ARCHIVE_PROJECT_IDS:
        return CompletenessReport(
            status=CompletenessStatus.EXEMPT,
            findings=(),
            reason=(
                f"{archive_dir.name!r} is a named legacy archive with no archive_manifest.json "
                "(RESEARCH_ARCHIVE_MANIFEST.md Applicability) -- exempt from the v1 layout check"
            ),
        )

    if manifest is not None and manifest.get("lifecycle_version") == "legacy":
        return CompletenessReport(
            status=CompletenessStatus.EXEMPT,
            findings=(),
            reason="archive_manifest.json declares lifecycle_version=legacy -- exempt from the v1 layout check",
        )

    if manifest is not None:
        # A present manifest not declared legacy is v1 (or a value outside
        # {"legacy", "v1"}, which archive_manifest.py's own build_manifest()
        # already refuses to write) -- either way the closure gate applies
        # before any item is checked (AC-15).
        if not _cycle_closed(archive_dir):
            return CompletenessReport(
                status=CompletenessStatus.UNVERIFIABLE,
                findings=(),
                reason=(
                    "cycle not closed: transition_records.jsonl is absent, empty, or its terminal "
                    "record's to_phase is not 'Archive'"
                ),
            )

    # manifest is None and not a named legacy archive (archive_manifest.json
    # itself will surface as a "missing" finding below), or manifest is
    # present and the cycle has closed: check all eight required items.
    findings = tuple(_check_item(archive_dir, name, kind) for name, kind in _REQUIRED_ITEMS)
    status = (
        CompletenessStatus.COMPLETE
        if all(finding.outcome == "present" for finding in findings)
        else CompletenessStatus.INCOMPLETE
    )
    return CompletenessReport(status=status, findings=findings, reason=None)


def _verify_seal(archive_dir: Path) -> SealReport:
    """Stub only (AD-073 Migration item 2). ``archive_dir`` is accepted
    for interface stability with the future non-stub implementation but
    is not otherwise inspected: no file under it is opened, hashed, or
    enumerated."""
    del archive_dir
    return SealReport(status=SealStatus.UNVERIFIABLE, findings=(), reason=_SEAL_STUB_REASON)


def verify_archive(archive_dir: Path) -> ArchiveReport:
    """The single public entry point for the archive-soundness question
    (AC-1). Read-only: composes the completeness branch and the Seal
    stub into one report with per-branch attribution (AC-4). Does not
    invoke FreezeVerifier (not wired in Phase 1) and does not touch
    anything under research_archive/ beyond reading it."""
    return ArchiveReport(
        archive_dir=archive_dir,
        completeness=_verify_completeness(archive_dir),
        seal=_verify_seal(archive_dir),
    )
