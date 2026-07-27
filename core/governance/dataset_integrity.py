"""Dataset integrity verification (Governance) -- the branch AD-073
Decision part 8 delegated and AD-074 SS9 item 6 / AD-075 SS4 item 3
recorded as the delegate's still-absent implementation.

**What this closes, stated as the gap it was found to be.** AD-073
Decision part 8 assigns one authoritative content-hash record per
archived file. For everything ``dataset_manifest.json`` describes by
``content_hash`` -- concretely ``dataset_hashes/*.jsonl`` -- that record
is the manifest's, and ``DatasetIntegrityChecker``'s domain. The Archive
Seal therefore *excludes* those paths from its content comparison
(AD-074 SS5.1, SS7B D2), which is correct only if something else actually
checks them. Nothing did. The measured consequence, before this module:
appending a line to ``research_archive/reference_h4/dataset_hashes/ETF.jsonl``
left ``verify_archive()`` reporting ``OverallStatus.SOUND``, because the
one control that covers those bytes was a hash record no code ever
recomputed. Their *existence* was checked (AC-74-4); their *bytes* were
not.

**The expected value is read at the sealing commit, never from the
working tree.** This is the same rule every other seal input already
obeys (AD-074 SS7B D2/D9, hardening item ``BLOCKER 1``) and it is
load-bearing for the identical reason: ``dataset_manifest.json`` is the
file that *states* the expected hashes, so an attacker who can edit the
working-tree copy can restate them to match whatever they just wrote into
the snapshot. Recomputing a hash and comparing it against a number the
same actor controls is not verification. The comparison this module
performs is therefore

    **manifest at the sealing commit -> snapshot bytes on the archive
    filesystem**

-- the same direction, and the same fixed point, as ``archive_seal``'s
own. The sealing commit is resolved by
``archive_seal.resolve_sealing_commit()`` rather than re-derived here:
two components resolving a sealing commit two ways would be the
duplicate-source-of-truth failure Decision part 8 exists to prevent, one
level up.

**Nothing here is a new integrity algorithm.** The hash and row-count
checks are exactly the two
``core.governance.reconstruction_loader._verify_dataset_integrity``
already performs at reconstruction preflight, over the same
``canonical_jsonl`` primitives (``sha256_of_file``,
``read_canonical_jsonl``). What that function cannot be is a governance
*verifier*: it raises a typed exception on the first failure, because its
caller is about to build a database and must stop. A verifier must answer
for every entry and never raise. That difference in contract -- not a
difference in algorithm -- is why this module exists rather than a call
into that one, and it is the same relationship
``archive_verifier``'s completeness branch already has to the Standard.

**Status vocabulary.** Three values, this branch's own, deliberately not
merged with ``CompletenessStatus``, ``SealStatus``, or ``FreezeStatus``
(AD-073 Status vocabulary):

- ``VERIFIED`` -- a manifest was read at the sealing commit and every
  entry's snapshot is present, hashes to its declared ``content_hash``,
  and holds its declared ``row_count``.
- ``DRIFTED`` -- at least one entry is confirmed wrong: a hash mismatch,
  a row-count mismatch, or a snapshot the manifest names and the archive
  does not contain. A *confirmed problem*, and the value that maps to
  ``OverallStatus.UNSOUND``.
- ``FAILED`` -- the question could not be answered: no seal, no manifest
  at the sealing commit, an unparsable manifest, a snapshot that cannot
  be read at all. "Could not verify", never "verified", and it maps to
  ``OverallStatus.UNVERIFIABLE``. It is named ``FAILED`` rather than
  ``UNVERIFIABLE`` because that is the vocabulary this branch was
  specified with; the *fact* it denotes is the shared one AD-073's Status
  vocabulary describes -- this branch could not reach a verdict.

**Read-only.** Hashes files and reads git objects at a fixed commit;
writes, repairs, and re-hashes nothing (AD-073 Decision part 7).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.governance import archive_seal
from core.governance.canonical_jsonl import read_canonical_jsonl, sha256_of_file
from core.governance.dataset_manifest import (
    DATASET_MANIFEST_FILENAME,
    DatasetEntry,
    DatasetManifestError,
    parse_dataset_manifest_text,
)


class DatasetIntegrityStatus(str, Enum):
    """This branch's own three-valued vocabulary -- see the module
    docstring. Never merged with another branch's."""

    VERIFIED = "verified"
    DRIFTED = "drifted"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DatasetFinding:
    """One manifest entry's outcome. ``kind`` is exactly one of
    ``"content_hash_mismatch"``, ``"row_count_mismatch"``, ``"missing"``
    (the manifest names a snapshot the archive does not contain), or
    ``"unreadable"`` (the snapshot exists but its bytes or its rows could
    not be obtained). The first three are confirmed problems; the fourth
    is not, and the two are never collapsed -- that distinction is what
    keeps ``DRIFTED`` from absorbing ``FAILED``."""

    dataset_id: str
    snapshot_path: str
    kind: str
    detail: str


# The finding kinds that are a confirmed problem with the archive's
# bytes, as opposed to a failure to determine anything about them.
_DRIFT_KINDS = frozenset({"content_hash_mismatch", "row_count_mismatch", "missing"})


@dataclass(frozen=True, slots=True)
class DatasetIntegrityReport:
    """``verified_datasets`` names the entries that passed both checks,
    so a reader can see the branch's coverage rather than infer it from
    the absence of findings -- the same reason ``SealReport`` carries
    ``excluded_paths`` (AD-074 SS5.6: bounded coverage a reader cannot
    see is coverage a reader cannot trust). ``sealed_commit`` is the
    commit the expected values were read at, or None when none could be
    resolved."""

    status: DatasetIntegrityStatus
    findings: tuple[DatasetFinding, ...]
    reason: str | None
    verified_datasets: tuple[str, ...] = ()
    sealed_commit: str | None = None


def _failed(reason: str, *, sealed_commit: str | None = None) -> DatasetIntegrityReport:
    return DatasetIntegrityReport(
        status=DatasetIntegrityStatus.FAILED,
        findings=(),
        reason=reason,
        sealed_commit=sealed_commit,
    )


def _check_entry(entry: DatasetEntry, archive_dir: Path) -> DatasetFinding | None:
    """The one entry's two checks, in the order that makes the cheaper
    disqualification come first. None when both pass."""
    entry_id = entry.dataset_id
    snapshot_path = entry.snapshot_path
    expected_hash = entry.content_hash
    expected_rows = entry.row_count
    filesystem_path = archive_dir / snapshot_path
    if not filesystem_path.is_file():
        return DatasetFinding(
            dataset_id=entry_id,
            snapshot_path=snapshot_path,
            kind="missing",
            detail=f"the sealed manifest names {snapshot_path!r} but no file exists at {filesystem_path}",
        )
    try:
        actual_hash = sha256_of_file(filesystem_path)
    except OSError as exc:
        return DatasetFinding(
            dataset_id=entry_id,
            snapshot_path=snapshot_path,
            kind="unreadable",
            detail=f"{filesystem_path} could not be read to hash it ({exc.__class__.__name__}: {exc})",
        )
    if actual_hash != expected_hash:
        return DatasetFinding(
            dataset_id=entry_id,
            snapshot_path=snapshot_path,
            kind="content_hash_mismatch",
            detail=(
                f"the sealed manifest declares {expected_hash}, but {snapshot_path} on the archive "
                f"filesystem hashes to {actual_hash}"
            ),
        )
    # The row count is a redundant check over content the hash already
    # covers, and is kept for the reason the manifest records it
    # separately: it names *what* changed in terms a reader can act on
    # ("2725 rows became 2724") where a hash mismatch names only *that*
    # something did. It can only ever fire alongside a hash mismatch, so
    # it is reached only once the hash has matched -- a row-count finding
    # on its own would mean `row_count` and the bytes disagree in the
    # sealed manifest itself, which is a manifest defect, not drift.
    try:
        actual_rows = len(read_canonical_jsonl(filesystem_path))
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        return DatasetFinding(
            dataset_id=entry_id,
            snapshot_path=snapshot_path,
            kind="unreadable",
            detail=(
                f"{filesystem_path} hashes correctly but its rows could not be counted "
                f"({exc.__class__.__name__}: {exc}) -- the row_count check is undetermined"
            ),
        )
    if actual_rows != expected_rows:
        return DatasetFinding(
            dataset_id=entry_id,
            snapshot_path=snapshot_path,
            kind="row_count_mismatch",
            detail=(
                f"the sealed manifest declares row_count={expected_rows}, but {snapshot_path} holds "
                f"{actual_rows} row(s) -- the manifest's own two records of this file disagree"
            ),
        )
    return None


def verify_dataset_integrity(archive_dir: Path, *, repo_root: Path | None = None) -> DatasetIntegrityReport:
    """Verify every dataset snapshot `archive_dir` contains against the
    ``content_hash`` and ``row_count`` its ``dataset_manifest.json``
    declared **at the sealing commit**.

    Never raises for a verification question. Raises only
    ``archive_seal.NotAGitRepositoryError``, for an environmental problem
    (`repo_root` is not inside a git working tree), exactly as
    ``archive_seal.verify_seal()`` and ``freeze_verifier.verify_freeze()``
    already do -- the caller translates it."""
    resolved_dir = archive_dir.resolve()
    sealing, sealing_error = archive_seal.resolve_sealing_commit(resolved_dir, repo_root=repo_root)
    if sealing is None:
        return _failed(
            f"no sealing commit could be resolved, so no trustworthy expected hash exists to "
            f"compare against: {sealing_error or 'unknown reason'}"
        )

    manifest_repo_path = f"{sealing.archive_relative_prefix}/{DATASET_MANIFEST_FILENAME}"
    content = archive_seal.read_text_at_commit(
        sealing.sealed_commit, manifest_repo_path, repo_root=sealing.repo_root
    )
    if content is None:
        return _failed(
            f"{manifest_repo_path!r} does not exist or is not readable UTF-8 at sealing commit "
            f"{sealing.sealed_commit!r} -- there is no sealed expected value to verify against, and "
            f"the working-tree copy is not a substitute for one",
            sealed_commit=sealing.sealed_commit,
        )
    try:
        manifest = parse_dataset_manifest_text(content, source=f"{sealing.sealed_commit}:{manifest_repo_path}")
    except DatasetManifestError as exc:
        return _failed(
            f"dataset_manifest.json at sealing commit {sealing.sealed_commit!r} could not be parsed: {exc}",
            sealed_commit=sealing.sealed_commit,
        )

    findings: list[DatasetFinding] = []
    verified: list[str] = []
    for entry in manifest.datasets:
        # The same containment rule the Seal applies to this identical
        # field (AD-074 SS5.1, hardening item M-1), reused rather than
        # restated. Here it bounds what this branch will *read* rather
        # than what the Seal will *skip*, but a manifest that can name
        # `../../decision_log.md` can make this branch hash and report on
        # a file outside the archive it claims to describe.
        if not archive_seal.is_contained_snapshot_path(entry.snapshot_path):
            return _failed(
                f"dataset_manifest.json at sealing commit {sealing.sealed_commit!r} declares "
                f"snapshot_path {entry.snapshot_path!r} for dataset {entry.dataset_id!r}, which does "
                f"not resolve strictly inside 'dataset_hashes/' -- the manifest is refused rather "
                f"than followed outside the archive it describes",
                sealed_commit=sealing.sealed_commit,
            )
        finding = _check_entry(entry, resolved_dir)
        if finding is None:
            verified.append(entry.dataset_id)
        else:
            findings.append(finding)

    findings.sort(key=lambda finding: (finding.snapshot_path, finding.kind))
    drifted = [finding for finding in findings if finding.kind in _DRIFT_KINDS]
    if drifted:
        return DatasetIntegrityReport(
            status=DatasetIntegrityStatus.DRIFTED,
            findings=tuple(findings),
            reason=(
                f"{len(drifted)} dataset snapshot(s) do not match the manifest sealed at "
                f"{sealing.sealed_commit}"
            ),
            verified_datasets=tuple(verified),
            sealed_commit=sealing.sealed_commit,
        )
    if findings:
        # Only "unreadable" findings remain: an incomplete verification is
        # never VERIFIED, and it is not DRIFTED either -- nothing was
        # confirmed wrong.
        return DatasetIntegrityReport(
            status=DatasetIntegrityStatus.FAILED,
            findings=tuple(findings),
            reason=(
                f"{len(findings)} dataset snapshot(s) could not be checked against the manifest "
                f"sealed at {sealing.sealed_commit} -- the verification is incomplete, not passing"
            ),
            verified_datasets=tuple(verified),
            sealed_commit=sealing.sealed_commit,
        )
    return DatasetIntegrityReport(
        status=DatasetIntegrityStatus.VERIFIED,
        findings=(),
        reason=None,
        verified_datasets=tuple(verified),
        sealed_commit=sealing.sealed_commit,
    )
