"""Archive verification (Governance) -- AD-073 Phase 1 + Phase B.

Implements the completeness branch, the Archive Seal *stub*, and the
freeze branch of ``ArchiveVerifier``, per ``docs/ARCHITECTURE_DECISIONS.md``
AD-073. ``verify_archive()`` is the one public entry point (AC-1): it
takes an archive *location*, not a ``ProjectId`` (AD-073 conflict C-1 --
Governance may never import Research's ``ProjectRegistry``, exactly the
tension AD-033 already resolved for ``FreezeVerifier``).

**Scope.** Three branches from AD-073's Architecture overview:

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
- **Freeze** -- invoked only when the caller requests it (AD-073's
  "where appropriate" means exactly and only "the caller asked").
  ``verify_archive(archive_dir, verify_freeze=True)`` reads
  ``freeze_commit_ref`` and ``freeze_covered_paths`` from
  ``transition_records.jsonl``'s terminal record -- the same record, the
  same selection rule, for both fields -- and hands them to
  ``core.governance.freeze_verifier.verify_freeze()`` unmodified. This
  module never reimplements freeze verification: ``FreezeStatus`` and
  ``VerificationResult`` remain exactly as ``freeze_verifier`` defines
  them, and no wrapper type is introduced. A caller that does not
  request freeze verification gets no freeze branch: ``ArchiveReport.freeze``
  is ``None`` and the branch takes no part in ``overall_status``.

**Read-only, always.** Nothing here opens a file for writing. Closure and
applicability determination read ``archive_manifest.json`` (plain JSON
parse) and ``transition_records.jsonl`` via
``core.governance.decision_recorder.read_chain()`` -- a structural
reader, not a verification authority. This module never calls
``verify_chain_intact()`` or ``verify_chain_anchored()``; chain
verification remains exclusively ``decision_recorder``'s question
(AD-073 Responsibilities, ``ArchiveVerifier`` -- does; Compatibility
AD-063 note). ``freeze_verifier.verify_freeze()`` is likewise read-only
over git (rev-parse, cat-file -e, diff, status --porcelain only).

**Overall status.** ``ArchiveReport.overall_status`` is never stored --
it is a property, recomputed on every access from the invoked branch
statuses under ``derive_overall_status()``'s documented, fixed
precedence (AD-073 Decision part 6, AC-5): a confirmed problem
(``INCOMPLETE`` / ``MISMATCH`` / ``DRIFTED``) outranks ``UNVERIFIABLE``,
which outranks a confirmed-good result. An absent freeze branch (the
caller did not request one) takes no part in this computation -- it is
not the same fact as an invoked branch reporting ``UNVERIFIABLE``.
Because the Seal branch is a stub that can only ever report
``UNVERIFIABLE``, ``overall_status`` can never be ``SOUND`` yet -- an
accurate reflection of "content integrity has never actually been
checked", not a defect in the derivation.
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
    DecisionRecord,
    read_chain,
)
from core.governance.freeze_verifier import (
    FreezeStatus,
    NotAGitRepositoryError,
    VerificationResult,
    verify_freeze as _verify_freeze_claim,
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
    -- it is recomputed from ``completeness.status``, ``seal.status``,
    and (when present) ``freeze.status`` on every access, and can never
    drift from them. ``freeze`` is ``None`` when the caller did not
    request freeze verification (AD-073's "where appropriate" == caller
    request) -- the branch's own vocabulary and result shape
    (``FreezeStatus`` / ``VerificationResult``) are exactly
    ``freeze_verifier``'s, never a duplicate or a wrapper."""

    archive_dir: Path
    completeness: CompletenessReport
    seal: SealReport
    freeze: VerificationResult | None = None

    @property
    def overall_status(self) -> OverallStatus:
        freeze_status = self.freeze.status if self.freeze is not None else None
        return derive_overall_status(self.completeness.status, self.seal.status, freeze_status)


def derive_overall_status(
    completeness: CompletenessStatus,
    seal: SealStatus,
    freeze: FreezeStatus | None = None,
) -> OverallStatus:
    """AD-073's *Overall status aggregation rule*. Fixed precedence,
    first match wins: confirmed problem, then unverifiable, then
    confirmed good -- AD-051's own precedence, applied across branches
    (AD-073 Architecture overview). ``freeze=None`` means the branch was
    not invoked (the caller did not request freeze verification) and
    takes no part in the computation -- not the same fact as an invoked
    branch reporting ``FreezeStatus.UNVERIFIABLE``."""
    if (
        completeness is CompletenessStatus.INCOMPLETE
        or seal is SealStatus.MISMATCH
        or freeze is FreezeStatus.DRIFTED
    ):
        return OverallStatus.UNSOUND
    if (
        completeness is CompletenessStatus.UNVERIFIABLE
        or seal is SealStatus.UNVERIFIABLE
        or freeze is FreezeStatus.UNVERIFIABLE
    ):
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


def _terminal_record(archive_dir: Path) -> DecisionRecord | None:
    """Determines transition_records.jsonl's terminal record (highest
    sequence_number). Called independently by the completeness closure
    gate (``_cycle_closed``) and the freeze branch
    (``_verify_freeze_branch``) -- each call re-reads and re-parses the
    file; there is no cross-call memoization, so a caller invoking both
    branches (``verify_archive(..., verify_freeze=True)``) reads
    transition_records.jsonl twice. What is shared is the *function* and
    its selection rule, not the read itself: AD-073's "the same record,
    the same selection rule, for both inputs" is satisfied by both call
    sites going through this one function, not by a single I/O read. Uses
    read_chain() only -- a structural reader -- never
    verify_chain_intact() or verify_chain_anchored(). read_chain() raises
    on anything it cannot turn into a well-formed DecisionRecord: invalid
    JSON (json.JSONDecodeError), non-canonical bytes (ValueError, from
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
    terminal record exists" here and are treated the same, never
    re-raised -- callers translate ``None`` into their own branch's
    UNVERIFIABLE. The ``max()`` selection itself is inside this same try
    block: a malformed ``sequence_number`` (e.g. a mix of ``int`` and
    ``str`` values, or ``None``) makes the comparison itself raise
    ``TypeError`` during selection, not during parsing, and is exactly as
    unable to establish a terminal record as any of the above."""
    try:
        records = read_chain(archive_dir / TRANSITION_RECORDS_FILENAME)
        if not records:
            return None
        return max(records, key=lambda record: record.sequence_number)
    except (json.JSONDecodeError, ValueError, KeyError, TypeError, OSError):
        return None


def _cycle_closed(archive_dir: Path) -> bool:
    """True iff transition_records.jsonl's terminal record has
    to_phase == "Archive"."""
    terminal = _terminal_record(archive_dir)
    if terminal is None:
        return False
    return terminal.to_phase == _ARCHIVE_TERMINAL_PHASE


def _verify_freeze_branch(archive_dir: Path, *, repo_root: Path | None) -> VerificationResult:
    """Invoked only when the caller requests freeze verification (AD-073
    "where appropriate" == caller request, and nothing about the
    archive's own content decides whether this branch exists). Reads
    freeze_commit_ref and freeze_covered_paths off the same terminal
    record ``_terminal_record`` reads for closure, unmodified, and hands
    them to ``freeze_verifier.verify_freeze()`` exactly as read -- this
    module never re-implements freeze verification itself.

    If the terminal record cannot be established at all (absent, empty,
    or malformed transition_records.jsonl -- the same conditions
    ``_terminal_record`` already treats as "no terminal record"), or the
    terminal record carries an empty freeze_commit_ref, the freeze claim
    itself is absent: this constructs an UNVERIFIABLE VerificationResult
    directly rather than calling verify_freeze() with nothing to check,
    per AD-073's "a freeze claim the archive does not state is
    UNVERIFIABLE, never absent-and-therefore-fine." An empty
    freeze_covered_paths on an otherwise-present claim is not handled
    here -- it is passed to verify_freeze() unmodified, which already
    reports UNVERIFIABLE for it (AD-051).

    ``verify_freeze()`` raises ``NotAGitRepositoryError`` for an
    environmental failure (``repo_root`` is not inside a git working
    tree) rather than returning a ``VerificationResult`` -- by its own
    docstring's contract, that exception is not a failed verification.
    ``ArchiveVerifier`` is a governance verifier whose own contract is to
    never raise for a verification question (see the module docstring's
    completeness branch, which already treats every input failure the
    same way): an environment that makes freeze verification impossible
    is exactly as UNVERIFIABLE as an absent freeze claim, so it is caught
    here and translated rather than left to propagate."""
    terminal = _terminal_record(archive_dir)
    if terminal is None or not terminal.freeze_commit_ref:
        return VerificationResult(
            commit_ref=terminal.freeze_commit_ref if terminal is not None else "",
            resolved_hash=None,
            status=FreezeStatus.UNVERIFIABLE,
            drifted_files=(),
            errors=(
                "no freeze claim: transition_records.jsonl is absent, empty, malformed, "
                "or its terminal record's freeze_commit_ref is empty",
            ),
            covered_paths=terminal.freeze_covered_paths if terminal is not None else (),
        )
    try:
        return _verify_freeze_claim(terminal.freeze_commit_ref, terminal.freeze_covered_paths, repo_root=repo_root)
    except NotAGitRepositoryError as exc:
        return VerificationResult(
            commit_ref=terminal.freeze_commit_ref,
            resolved_hash=None,
            status=FreezeStatus.UNVERIFIABLE,
            drifted_files=(),
            errors=(f"freeze verification environment error: {exc}",),
            covered_paths=terminal.freeze_covered_paths,
        )


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


def verify_archive(
    archive_dir: Path,
    *,
    verify_freeze: bool = False,
    repo_root: Path | None = None,
) -> ArchiveReport:
    """The single public entry point for the archive-soundness question
    (AC-1). Read-only: composes the completeness branch, the Seal stub,
    and (when requested) the freeze branch into one report with
    per-branch attribution (AC-4). Does not touch anything under
    research_archive/ beyond reading it, and never writes, commits, or
    otherwise mutates the repository FreezeVerifier reads.

    ``verify_freeze`` is the caller's request (AD-073's "where
    appropriate" == caller request, and nothing else) -- ``False`` (the
    default) omits the freeze branch entirely, matching Phase 1's
    behaviour exactly. ``repo_root`` is forwarded to
    ``freeze_verifier.verify_freeze()`` unchanged (``None`` defers to its
    own default) and is ignored when ``verify_freeze`` is ``False``."""
    return ArchiveReport(
        archive_dir=archive_dir,
        completeness=_verify_completeness(archive_dir),
        seal=_verify_seal(archive_dir),
        freeze=_verify_freeze_branch(archive_dir, repo_root=repo_root) if verify_freeze else None,
    )
