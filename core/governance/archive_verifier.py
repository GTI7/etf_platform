"""Archive verification (Governance) -- AD-073 Phase 1 + Phase B + AD-074
Increment 2.

Implements the completeness branch, the Archive Seal branch, and the
freeze branch of ``ArchiveVerifier``, per ``docs/ARCHITECTURE_DECISIONS.md``
AD-073 (as amended 2026-07-26) and AD-074. ``verify_archive()`` is the
one public entry point (AC-1): it takes an archive *location*, not a
``ProjectId`` (AD-073 conflict C-1 -- Governance may never import
Research's ``ProjectRegistry``, exactly the tension AD-033 already
resolved for ``FreezeVerifier``).

**Scope.** Three branches from AD-073's Architecture overview:

- **Completeness** -- Standard §5's seven required items plus
  ``archive_manifest.json``, checked for presence and kind only (AC-6,
  AC-7 do not apply here; this branch never reads file content). Legacy
  archives (AD-030's three named exceptions, or any archive whose
  manifest states ``lifecycle_version: "legacy"``) are exempt. A
  ``lifecycle_version: "v1"`` archive whose cycle has not closed
  (``transition_records.jsonl``'s terminal record's ``to_phase`` is not
  ``"Archive"``) is ``UNVERIFIABLE`` (AC-15).
- **Archive Seal** -- delegates to ``core.governance.archive_seal.verify_seal()``
  (AD-074 Increment 2), which compares the archive's working-tree bytes
  against the sealing commit tree named by an Archive Seal Register
  record (``docs/archive_seal_register.jsonl``). This module contains no
  integrity algorithm of its own (AC-2): every ``modified``/``missing``/
  ``unexpected`` finding originates in ``archive_seal``. The Register is
  empty as of this increment (AD-074 SS11 Increment 2 scope, SS9 item 3
  -- no automatic issuance, and no record has been issued for any
  archive yet), so every real archive still reports ``UNVERIFIABLE``
  today -- but now because *no seal has been issued for this project*, a
  per-archive fact, rather than because *no sealed-manifest format
  exists*, a platform-wide one (AD-074 SS11).
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
- **Dataset integrity** -- delegates to
  ``core.governance.dataset_integrity.verify_dataset_integrity()``,
  which recomputes each ``dataset_hashes/*.jsonl`` snapshot's SHA-256 and
  row count against the ``dataset_manifest.json`` **read at the sealing
  commit**. This is the branch AD-073 Decision part 8 delegated when it
  excluded those bytes from the Seal's coverage, and AD-073 *Future
  work* left as a decision between orchestration and independence;
  orchestration is what is built here, so the exclusion is now a handoff
  to a control that exists rather than to a named absence. Invoked
  unconditionally, like the Seal: the subject is archive-local bytes
  against a value fixed at archive close, which is the Seal's stability
  property, not the freeze branch's. This module contains no hash
  algorithm of its own, exactly as it contains no seal algorithm (AC-2).

  **Disclosed cost: the sealing commit is resolved twice, deliberately.**
  ``_verify_seal`` and ``_verify_dataset_branch`` are two independently
  invoked branches, each calling ``archive_seal.resolve_sealing_commit()``
  on its own -- once inside ``archive_seal.verify_seal()``, once inside
  ``dataset_integrity.verify_dataset_integrity()`` -- so every archive
  verified with both branches present pays the Register read, the
  syntactic and round-trip commit checks, and the ``git merge-base
  --is-ancestor`` reachability check (§7A B-1, reversed) twice over,
  as two separate sets of ``git`` subprocess invocations. This is the
  accepted price of the one-authoritative-resolution rule the
  ``SealingCommit`` dataclass exists to keep: threading a single resolved
  ``SealingCommit`` between the two branches would require this module to
  resolve it once at the top of ``verify_archive()`` and pass it down,
  which would make ``ArchiveVerifier`` itself perform sealing-commit
  resolution -- a duplicate-source-of-truth risk one level up, and the
  exact failure Decision part 8 exists to prevent, traded for a
  micro-optimisation over a handful of read-only, local ``git``
  invocations. Not a performance concern at today's archive counts and
  not planned to be revisited unless it becomes one.

**Read-only, always.** Nothing here opens a file for writing. Closure and
applicability determination read ``archive_manifest.json`` (plain JSON
parse) and ``transition_records.jsonl`` via
``core.governance.decision_recorder.read_chain()`` -- a structural
reader, not a verification authority. This module never calls
``verify_chain_intact()`` or ``verify_chain_anchored()``; chain
verification remains exclusively ``decision_recorder``'s question
(AD-073 Responsibilities, ``ArchiveVerifier`` -- does; Compatibility
AD-063 note). ``freeze_verifier.verify_freeze()`` is likewise read-only
over git (rev-parse, cat-file -e, diff, status --porcelain only), and so
is ``archive_seal.verify_seal()`` (cat-file, ls-tree -z, show,
rev-parse, check-attr, and hash-object without ``-w`` -- see that
module's own docstring for what it defeats, what it does not, why its
comparison deliberately avoids ``git diff``'s dependency on the index,
and how the attribute stack that governs ``hash-object`` is itself
pinned to the sealing commit rather than trusted as live state).

**Overall status.** ``ArchiveReport.overall_status`` is never stored --
it is a property, recomputed on every access from the invoked branch
statuses under ``derive_overall_status()``'s documented, fixed
precedence (AD-073 Decision part 6, AC-5): a confirmed problem
(``INCOMPLETE`` / ``MISMATCH`` / ``DRIFTED``) outranks ``UNVERIFIABLE``,
which outranks a confirmed-good result. An absent freeze branch (the
caller did not request one) takes no part in this computation -- it is
not the same fact as an invoked branch reporting ``UNVERIFIABLE``.

**What ``OverallStatus.SOUND`` means, and does not mean (AD-074
AC-74-13, narrowed 2026-07-26 by the dataset branch).** ``SOUND`` means
exactly "the completeness check passed (or was exempt), the sealed
archive paths match the sealing commit tree, every dataset snapshot
matches the hash and row count sealed for it, and -- if the caller
requested it -- the freeze claim verified". It does not mean, and must
never be reported as meaning, that research reproducibility or
experiment validity have been confirmed; those remain Standard SS4's
human question. AC-74-13's dataset-hash carve-out is discharged rather
than restated: the reason it existed was that
``DatasetIntegrityChecker`` was unimplemented.

**``SOUND`` and the freeze branch.** A caller that does not request
freeze verification can still reach ``SOUND``, because AD-073's
aggregation rule makes an uninvoked freeze branch absent rather than
failing, deliberately: freeze binding is the one branch whose subject is
*live repository state*, so folding it into the archive's own verdict
would make that verdict change with facts outside the archive (AD-073
Architecture overview, "the third row is the load-bearing one"). A
governance caller that wants all four dimensions asserted at once passes
``verify_freeze=True``, which is what the standing CI check does.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from core.governance import archive_seal
from core.governance.archive_identity import (
    ARCHIVE_MANIFEST_FILENAME,
    LEGACY_ARCHIVE_PROJECT_IDS,
)
from core.governance.dataset_integrity import (
    DatasetIntegrityReport,
    DatasetIntegrityStatus,
    verify_dataset_integrity as _verify_dataset_integrity,
)
from core.governance.decision_recorder import (
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

class CompletenessStatus(str, Enum):
    """Four-valued -- this branch's own vocabulary (AD-073 Architecture
    overview, Status vocabulary), never merged with the Seal's or the
    Freeze branch's."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    EXEMPT = "exempt"
    UNVERIFIABLE = "unverifiable"


class SealStatus(str, Enum):
    """The Seal's own three-valued vocabulary (AD-073 Status vocabulary,
    as amended by AD-074). ``MATCHED`` requires an Archive Seal Register
    record naming a sealing commit whose tree matches the working tree;
    since the Register is empty as of AD-074 Increment 2 (no issuance
    yet), every real archive still reports ``UNVERIFIABLE`` today."""

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
    """One path's comparison outcome (AC-7's three distinguishable
    finding kinds, never collapsed): ``"modified"``, ``"missing"``
    (present at the sealing commit, absent from the working tree), or
    ``"unexpected"`` (present in the working tree, absent from the
    sealing commit)."""

    path: str
    kind: str


@dataclass(frozen=True, slots=True)
class SealReport:
    """``excluded_paths`` (AD-074 AC-74-4, added in Increment 2): the
    dataset-manifest ``snapshot_path`` entries and
    ``protected_file_hashes.json`` paths this comparison excluded from
    scope, reported explicitly rather than left implicit -- "bounded
    coverage that a reader cannot see is coverage a reader cannot
    trust" (AD-074 SS5.6). Empty when no exclusion set could be (or
    needed to be) computed, e.g. an UNVERIFIABLE result reached before
    that point."""

    status: SealStatus
    findings: tuple[SealFinding, ...]
    reason: str | None
    excluded_paths: tuple[str, ...] = ()


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
    dataset: DatasetIntegrityReport
    freeze: VerificationResult | None = None

    @property
    def overall_status(self) -> OverallStatus:
        freeze_status = self.freeze.status if self.freeze is not None else None
        return derive_overall_status(
            self.completeness.status,
            self.seal.status,
            freeze_status,
            dataset=self.dataset.status,
        )


def derive_overall_status(
    completeness: CompletenessStatus,
    seal: SealStatus,
    freeze: FreezeStatus | None = None,
    *,
    dataset: DatasetIntegrityStatus,
) -> OverallStatus:
    """AD-073's *Overall status aggregation rule*. Fixed precedence,
    first match wins: confirmed problem, then unverifiable, then
    confirmed good -- AD-051's own precedence, applied across branches
    (AD-073 Architecture overview). ``freeze=None`` means the branch was
    not invoked (the caller did not request freeze verification) and
    takes no part in the computation -- not the same fact as an invoked
    branch reporting ``FreezeStatus.UNVERIFIABLE``.

    ``dataset`` is the fourth branch (AD-073 *Future work*,
    ``DatasetIntegrityChecker``, resolved in favour of orchestration).
    It is keyword-only and has no default: unlike the freeze branch, this
    one is invoked unconditionally, exactly as the Seal branch is, so
    there is no "not invoked" state for it to default to, and a caller
    reasoning about the rule "in isolation" would otherwise silently
    reason about a branch this module no longer allows to be absent. Its
    two non-good values slot into the *existing* precedence rather than
    extending it -- ``DRIFTED`` is a confirmed problem alongside
    ``FreezeStatus.DRIFTED``, ``FAILED`` is this branch's spelling of
    "could not reach a verdict" -- so no fourth outcome, weighting, or
    partial-credit case is introduced, which AD-073's rule forbids."""
    if (
        completeness is CompletenessStatus.INCOMPLETE
        or seal is SealStatus.MISMATCH
        or freeze is FreezeStatus.DRIFTED
        or dataset is DatasetIntegrityStatus.DRIFTED
    ):
        return OverallStatus.UNSOUND
    if (
        completeness is CompletenessStatus.UNVERIFIABLE
        or seal is SealStatus.UNVERIFIABLE
        or freeze is FreezeStatus.UNVERIFIABLE
        or dataset is DatasetIntegrityStatus.FAILED
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


_SEAL_STATUS_BY_OUTCOME = {
    "matched": SealStatus.MATCHED,
    "mismatch": SealStatus.MISMATCH,
    "unverifiable": SealStatus.UNVERIFIABLE,
}


def _verify_seal(archive_dir: Path, *, repo_root: Path | None) -> SealReport:
    """Delegates entirely to ``archive_seal.verify_seal()`` (AD-074
    Increment 2, AC-2): this function computes no hash and contains no
    integrity algorithm of its own, only the translation from
    ``archive_seal.SealOutcome`` to this module's own ``SealReport``
    shape. ``archive_seal.verify_seal()`` never raises for a failed
    verification -- only ``archive_seal.NotAGitRepositoryError``, for an
    environmental problem (``repo_root`` not inside a git working tree),
    which is caught and translated the same way the freeze branch
    already translates ``freeze_verifier.NotAGitRepositoryError``."""
    try:
        outcome = archive_seal.verify_seal(archive_dir, repo_root=repo_root)
    except archive_seal.NotAGitRepositoryError as exc:
        return SealReport(
            status=SealStatus.UNVERIFIABLE,
            findings=(),
            reason=f"seal verification environment error: {exc}",
            excluded_paths=(),
        )
    findings = tuple(SealFinding(path=finding.path, kind=finding.kind) for finding in outcome.findings)
    return SealReport(
        status=_SEAL_STATUS_BY_OUTCOME[outcome.status],
        findings=findings,
        reason=outcome.reason,
        excluded_paths=outcome.excluded_paths,
    )


def _verify_dataset_branch(archive_dir: Path, *, repo_root: Path | None) -> DatasetIntegrityReport:
    """Delegates entirely to ``dataset_integrity.verify_dataset_integrity()``
    (AD-073 Decision part 8): this function computes no hash of its own,
    exactly as ``_verify_seal`` computes none. Invoked unconditionally,
    alongside completeness and the Seal -- the dataset snapshots are
    archive-local bytes compared against an expected value fixed at the
    sealing commit, so this branch has the Seal's stability properties,
    not the freeze branch's, and nothing about it is the caller's to
    elect. Translates the one environmental exception the same way the
    Seal and freeze branches already do."""
    try:
        return _verify_dataset_integrity(archive_dir, repo_root=repo_root)
    except archive_seal.NotAGitRepositoryError as exc:
        return DatasetIntegrityReport(
            status=DatasetIntegrityStatus.FAILED,
            findings=(),
            reason=f"dataset integrity verification environment error: {exc}",
        )


def verify_archive(
    archive_dir: Path,
    *,
    verify_freeze: bool = False,
    repo_root: Path | None = None,
) -> ArchiveReport:
    """The single public entry point for the archive-soundness question
    (AC-1). Read-only: composes the completeness branch, the Seal
    branch, and (when requested) the freeze branch into one report with
    per-branch attribution (AC-4). Does not touch anything under
    research_archive/ beyond reading it, and never writes, commits, or
    otherwise mutates the repository FreezeVerifier or the Seal branch
    reads.

    ``verify_freeze`` is the caller's request (AD-073's "where
    appropriate" == caller request, and nothing else) -- ``False`` (the
    default) omits the freeze branch entirely, matching Phase 1's
    behaviour exactly. The Seal branch, unlike the freeze branch, is
    always invoked (AD-074 SS5.4: "invoked unconditionally, alongside
    completeness"). ``repo_root`` is forwarded unchanged to both
    ``archive_seal.verify_seal()`` and (when requested)
    ``freeze_verifier.verify_freeze()`` (``None`` defers to each one's
    own default).

    ``archive_dir`` is **resolved exactly once, here** (integrity audit
    item 3, 2026-07-26), and the resolved path is what every branch
    receives and what ``ArchiveReport.archive_dir`` records -- a report
    naming a relative path would be ambiguous evidence the moment the
    reader's working directory differed from the caller's. A relative
    ``archive_dir`` previously reached the Seal branch unresolved and
    raised ``ValueError`` out of a verifier contracted never to raise
    for a verification question; ``archive_seal.verify_seal()`` resolves
    at its own public boundary too, for callers that reach it directly,
    and resolving an already-resolved path is a no-op."""
    resolved_dir = archive_dir.resolve()
    return ArchiveReport(
        archive_dir=resolved_dir,
        completeness=_verify_completeness(resolved_dir),
        seal=_verify_seal(resolved_dir, repo_root=repo_root),
        dataset=_verify_dataset_branch(resolved_dir, repo_root=repo_root),
        freeze=_verify_freeze_branch(resolved_dir, repo_root=repo_root) if verify_freeze else None,
    )
