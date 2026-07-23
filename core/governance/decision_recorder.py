"""Mechanical, hash-chained phase-transition records (Phase 4 / Step 9,
increment C -- docs/ARCHITECTURE_DECISIONS.md AD-048, clarifying AD-045
rather than superseding it; docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md
Section 4.2's non-negotiable ordering placed this component after B-3
(``advance_phase()``), never before it -- AD-048 is void otherwise).

**Transcription, not certification.** Governance cannot import Validation
(``tools/check_import_boundaries.py``: ``ALLOWED_DEPENDENCIES["governance"]
== {"data"}``), so this module never sees a ``GateResult`` and cannot
re-derive whether a transcribed gate status is true. It certifies exactly
one thing: that the retained bytes of a record were not altered, reordered,
or interior-deleted since they were written. It never asserts that the
transcribed content -- a gate status, a freeze outcome, an authorization
-- is itself correct. Recording rationale, interpretation, narrative,
ranking, or known limitations remains AD-045's un-reopened prohibition;
this module's record shape is a **closed** field set precisely so that
never happens by accident.

**Tamper-evidence, at its true strength.** ``verify_chain_intact()``
recomputes each retained record's canonical hash and confirms record *N*'s
stored predecessor hash equals record *N-1*'s computed hash, with
contiguous sequence numbers from 1 and no gaps or duplicates. This detects
mutation, reorder, insertion, interior deletion, and a forged predecessor.
**It proves nothing about the tail.** Truncating the file after record *N*
leaves a perfectly valid, shorter chain -- a self-contained chain cannot
prove its own length, because the actor who could author retroactively is
the same actor who could truncate. Tail truncation is therefore
deliberately undetectable by ``verify_chain_intact()`` alone.
``verify_chain_anchored()`` is the only mechanism that closes that gap, and
only up to the cited sequence number: it takes an externally supplied
``(sequence_number, head_hash)`` pair -- a human reading a citation out of
that cycle's hand-authored ``decision_log.md`` -- and confirms the chain
still retains a record at that sequence number with that hash. **This
module never reads, parses, or writes ``decision_log.md``**; the anchor is
supplied by the caller, never located by this module.

**Single-writer assumption, stated and not enforced.** At most one process
is assumed to append to any one ``transition_records.jsonl`` at a time, on
behalf of the single human operator who authorized that transition.
**Nothing in this module enforces that.** There is no lock, no advisory
file, no process registry, and no runtime check -- and none is added here.
A violation is either detected after the fact by ``verify_chain_intact()``
(two writers landing conflicting sequence numbers) or, in the
last-writer-wins shape, not detected at all: the surviving file is
contiguous, correctly chained, and internally valid, and the lost record
is unrecoverable. ``os.replace()`` makes the *file replacement* atomic
only -- a reader never observes a half-written file -- it does **not**
make the read-append-rewrite **concurrency-safe**.

This module never commits, checks out, or resets anything, never reads a
system clock, and never invokes git: the UTC timestamp and the code commit
hash are both injected by the caller.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from core.governance.canonical_jsonl import canonical_line, read_canonical_jsonl

TRANSITION_RECORDS_FILENAME = "transition_records.jsonl"
ARCHIVE_MANIFEST_FILENAME = "archive_manifest.json"


class MissingArchiveManifestError(RuntimeError):
    """Raised when the cycle directory has no `archive_manifest.json`.
    The recorder never creates a directory or a manifest -- the cycle
    directory's existence is a precondition of the first record, never a
    consequence of it."""


class ProjectIdentityMismatchError(RuntimeError):
    """Raised unless `manifest.project_id`, the cycle directory's own
    name, and the record's `project_id` are all byte-identical. This is
    a three-way identity check only -- `lifecycle_version` is never read
    and archive completeness is never inspected."""


class ChainInvalidError(RuntimeError):
    """Raised when `append()` is asked to write onto a chain that
    `verify_chain_intact()` finds already broken. An invalid chain is
    retained exactly as found and is never repaired by this module."""


class ChainPrefixMismatchError(RuntimeError):
    """Raised when the chain file's on-disk bytes do not equal the
    canonical re-serialization of the rows `append()` just read from it
    -- i.e. the retained prefix is not itself already canonical JSONL."""


@dataclasses.dataclass(frozen=True, slots=True)
class AuthorizationRecord:
    """The recorded human authorization for one transition (mirrors
    docs/RESEARCH_GOVERNANCE_STANDARD.md Section 4's required fields).
    Recorded, never adjudicated: this module does not parse
    `reviewer_level` or enforce any hierarchy over it."""

    authorizer: str
    reviewer_level: str
    ambiguity_acknowledged: bool
    override_acknowledged: bool


@dataclasses.dataclass(frozen=True, slots=True)
class GateOutcome:
    """One gate's name and its status, recorded as a plain string --
    never `core.validation.gate_result.GateStatus` itself, which this
    domain cannot import."""

    gate_name: str
    status: str


@dataclasses.dataclass(frozen=True, slots=True)
class DecisionRecord:
    """One mechanical phase-transition record. Closed field set --
    `tests/test_governance_decision_recorder.py` pins the exact
    serialized key set, so adding a field fails a test and forces a new
    AD rather than a commit (AD-048)."""

    project_id: str
    sequence_number: int
    from_phase: str
    to_phase: str
    recorded_at: str
    commit_hash: str
    freeze_commit_ref: str
    freeze_verification_status: str
    freeze_covered_paths: tuple[str, ...]
    gate_outcomes: tuple[GateOutcome, ...]
    authorization: AuthorizationRecord
    evidence_refs: tuple[str, ...]
    reproduction_record_ref: str | None
    predecessor_hash: str | None


def hash_record(row: dict[str, Any]) -> str:
    """`sha256:<64 lowercase hex>` over the UTF-8 bytes of `row`'s
    canonical JSON serialization -- the exact line
    `write_canonical_jsonl` emits for it, excluding the terminating LF.
    This is both the hash a successor record cites as its
    `predecessor_hash` and the head hash a human cites in a
    `decision_log.md` anchor."""
    return "sha256:" + hashlib.sha256(canonical_line(row).encode("utf-8")).hexdigest()


def _row_to_record(row: dict[str, Any]) -> DecisionRecord:
    """Purely structural reconstruction of one row -- dict access and
    tuple conversion only. Never normalizes, enriches, interprets, or
    validates the semantic meaning of any field (a `from_phase` value
    that is not one of the eight `LifecyclePhase` names round-trips
    unchanged; validating it is not this module's job)."""
    authorization_row = row["authorization"]
    return DecisionRecord(
        project_id=row["project_id"],
        sequence_number=row["sequence_number"],
        from_phase=row["from_phase"],
        to_phase=row["to_phase"],
        recorded_at=row["recorded_at"],
        commit_hash=row["commit_hash"],
        freeze_commit_ref=row["freeze_commit_ref"],
        freeze_verification_status=row["freeze_verification_status"],
        freeze_covered_paths=tuple(row["freeze_covered_paths"]),
        gate_outcomes=tuple(
            GateOutcome(gate_name=g["gate_name"], status=g["status"]) for g in row["gate_outcomes"]
        ),
        authorization=AuthorizationRecord(
            authorizer=authorization_row["authorizer"],
            reviewer_level=authorization_row["reviewer_level"],
            ambiguity_acknowledged=authorization_row["ambiguity_acknowledged"],
            override_acknowledged=authorization_row["override_acknowledged"],
        ),
        evidence_refs=tuple(row["evidence_refs"]),
        reproduction_record_ref=row["reproduction_record_ref"],
        predecessor_hash=row["predecessor_hash"],
    )


def read_chain(path: Path) -> tuple[DecisionRecord, ...]:
    """Read every record in `path`, reconstructed structurally only (see
    `_row_to_record`). A missing file reads as an empty chain, matching
    `read_canonical_jsonl`'s treatment of a zero-byte file -- both are
    indistinguishable, from the file alone, from a cycle that has never
    transitioned."""
    if not path.exists():
        return ()
    return tuple(_row_to_record(row) for row in read_canonical_jsonl(path))


def verify_chain_intact(path: Path) -> bool:
    """Mechanical, internal-only verification: recompute each retained
    record's canonical hash and confirm contiguous sequence numbers from
    1 (no gaps, no duplicates) and that each record's `predecessor_hash`
    equals the previous record's computed hash, with `predecessor_hash`
    `None` at sequence 1 and nowhere else. Detects mutation, reorder,
    insertion, interior deletion, duplicate sequence numbers, gaps, and a
    forged predecessor.

    Deliberately does **not** detect tail truncation -- a shorter valid
    prefix of a longer chain passes this check, by design (see the module
    docstring). A missing file or an empty chain is vacuously intact."""
    if not path.exists():
        return True
    rows = read_canonical_jsonl(path)
    if not rows:
        return True

    expected_sequence = 1
    previous_row: dict[str, Any] | None = None
    for row in rows:
        if row.get("sequence_number") != expected_sequence:
            return False
        if expected_sequence == 1:
            if row.get("predecessor_hash") is not None:
                return False
        else:
            assert previous_row is not None
            if row.get("predecessor_hash") != hash_record(previous_row):
                return False
        previous_row = row
        expected_sequence += 1
    return True


def verify_chain_anchored(path: Path, expected_sequence_number: int, expected_head_hash: str) -> bool:
    """Anchored verification: `expected_sequence_number` and
    `expected_head_hash` are supplied by the caller -- a human reading a
    citation out of that cycle's `decision_log.md`. This module never
    reads, parses, or writes that file itself. Returns `True` only if the
    chain is internally intact (`verify_chain_intact`) *and* still
    retains a record at `expected_sequence_number` whose computed hash
    equals `expected_head_hash` -- the only way tail truncation at or
    before that sequence number is detectable at all."""
    if not verify_chain_intact(path):
        return False
    if not path.exists():
        return False
    for row in read_canonical_jsonl(path):
        if row.get("sequence_number") == expected_sequence_number:
            return hash_record(row) == expected_head_hash
    return False


class DecisionRecorder:
    """Appends `DecisionRecord`s to one cycle's
    `<archive_root>/<project_id>/transition_records.jsonl`. `archive_root`
    is an injected parameter, never a module-level constant. See the
    module docstring for this class's tamper-evidence and single-writer
    claims -- neither is stronger here than stated there."""

    def __init__(self, archive_root: Path) -> None:
        self._archive_root = archive_root

    def chain_path(self, project_id: str) -> Path:
        return self._archive_root / project_id / TRANSITION_RECORDS_FILENAME

    def append(
        self,
        *,
        project_id: str,
        from_phase: str,
        to_phase: str,
        recorded_at: str,
        commit_hash: str,
        freeze_commit_ref: str,
        freeze_verification_status: str,
        freeze_covered_paths: Sequence[str],
        gate_outcomes: Sequence[GateOutcome],
        authorization: AuthorizationRecord,
        evidence_refs: Sequence[str],
        reproduction_record_ref: str | None = None,
    ) -> DecisionRecord:
        """Append one record. `recorded_at` and `commit_hash` are
        injected by the caller -- this method never reads a clock and
        never invokes git. Never creates the cycle directory: it must
        already contain `archive_manifest.json` whose `project_id`
        matches both the directory name and `project_id` here, or this
        raises rather than proceeding."""
        archive_dir = self._archive_root / project_id
        manifest_path = archive_dir / ARCHIVE_MANIFEST_FILENAME
        if not manifest_path.exists():
            raise MissingArchiveManifestError(
                f"{manifest_path} does not exist -- the cycle directory's archive_manifest.json "
                "is a precondition of the first transition record, never a consequence of it "
                "(this method never creates a directory)"
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_project_id = manifest["project_id"]
        if not (manifest_project_id == archive_dir.name == project_id):
            raise ProjectIdentityMismatchError(
                f"identity mismatch: manifest.project_id={manifest_project_id!r}, "
                f"directory name={archive_dir.name!r}, record.project_id={project_id!r} -- "
                "all three must be byte-identical"
            )

        chain_path = self.chain_path(project_id)

        if not verify_chain_intact(chain_path):
            raise ChainInvalidError(
                f"{chain_path} is not intact -- refusing to append onto a corrupted chain. "
                "An invalid chain is not repaired by this module; it is retained exactly as found."
            )

        if chain_path.exists():
            raw_before = chain_path.read_bytes()
            existing_rows = read_canonical_jsonl(chain_path)
        else:
            raw_before = b""
            existing_rows = []

        expected_prefix = "".join(canonical_line(row) + "\n" for row in existing_rows).encode("utf-8")
        if raw_before != expected_prefix:
            raise ChainPrefixMismatchError(
                f"{chain_path}'s on-disk bytes do not equal the canonical re-serialization of its "
                "own retained rows -- refusing to append onto a file whose stored bytes are not "
                "already canonical JSONL."
            )

        sequence_number = len(existing_rows) + 1
        predecessor_hash = hash_record(existing_rows[-1]) if existing_rows else None

        record = DecisionRecord(
            project_id=project_id,
            sequence_number=sequence_number,
            from_phase=from_phase,
            to_phase=to_phase,
            recorded_at=recorded_at,
            commit_hash=commit_hash,
            freeze_commit_ref=freeze_commit_ref,
            freeze_verification_status=freeze_verification_status,
            freeze_covered_paths=tuple(freeze_covered_paths),
            gate_outcomes=tuple(gate_outcomes),
            authorization=authorization,
            evidence_refs=tuple(evidence_refs),
            reproduction_record_ref=reproduction_record_ref,
            predecessor_hash=predecessor_hash,
        )

        new_row = dataclasses.asdict(record)
        lines = [canonical_line(row) for row in existing_rows]
        lines.append(canonical_line(new_row))
        content = ("\n".join(lines) + "\n").encode("utf-8")

        # Atomic replacement only (temp file + os.replace) -- this makes the
        # *replacement* atomic, never the read-append-rewrite. It is not a
        # concurrency claim; see the module docstring's single-writer note.
        # Never mkdir: `archive_dir` was already confirmed to exist above.
        temp_path = chain_path.parent / (chain_path.name + ".tmp")
        temp_path.write_bytes(content)
        os.replace(temp_path, chain_path)

        return record
