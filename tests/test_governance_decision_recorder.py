from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from core.governance.canonical_jsonl import canonical_bytes, canonical_line, read_canonical_jsonl
from core.governance.decision_recorder import (
    ChainInvalidError,
    ChainPrefixMismatchError,
    DecisionRecord,
    DecisionRecorder,
    GateOutcome,
    MissingArchiveManifestError,
    ProjectIdentityMismatchError,
    TRANSITION_RECORDS_FILENAME,
    AuthorizationRecord,
    hash_record,
    read_chain,
    verify_chain_anchored,
    verify_chain_intact,
)

EXPECTED_CLOSED_FIELD_SET = frozenset(
    {
        "project_id",
        "sequence_number",
        "from_phase",
        "to_phase",
        "recorded_at",
        "commit_hash",
        "freeze_commit_ref",
        "freeze_verification_status",
        "freeze_covered_paths",
        "gate_outcomes",
        "authorization",
        "evidence_refs",
        "reproduction_record_ref",
        "predecessor_hash",
    }
)


def _make_archive(tmp_path: Path, project_id: str = "reference_h4") -> tuple[Path, Path]:
    archive_root = tmp_path / "research_archive"
    archive_dir = archive_root / project_id
    archive_dir.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "project_id": project_id,
        "created_at": "2026-07-22T00:00:00+00:00",
        "lifecycle_version": "v1",
    }
    (archive_dir / "archive_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return archive_root, archive_dir


def _authorization(**overrides: object) -> AuthorizationRecord:
    kwargs: dict[str, object] = dict(
        authorizer="alice",
        reviewer_level="1",
        ambiguity_acknowledged=False,
        override_acknowledged=False,
    )
    kwargs.update(overrides)
    return AuthorizationRecord(**kwargs)  # type: ignore[arg-type]


def _append(recorder: DecisionRecorder, project_id: str, **overrides: object) -> DecisionRecord:
    kwargs: dict[str, object] = dict(
        project_id=project_id,
        from_phase="Hypothesis",
        to_phase="Research Proposal",
        recorded_at="2026-07-23T00:00:00+00:00",
        commit_hash="a" * 40,
        freeze_commit_ref="b" * 40,
        freeze_verification_status="verified",
        freeze_covered_paths=("docs/x.md",),
        gate_outcomes=(GateOutcome(gate_name="gate_a", status="pass"),),
        authorization=_authorization(),
        evidence_refs=("research_archive/x/experiment_results/run1.json",),
        reproduction_record_ref=None,
    )
    kwargs.update(overrides)
    return recorder.append(**kwargs)  # type: ignore[arg-type]


# --- DecisionRecord: closed field set -----------------------------------


def test_decision_record_closed_field_set_is_pinned(tmp_path: Path) -> None:
    archive_root, _ = _make_archive(tmp_path)
    record = _append(DecisionRecorder(archive_root), "reference_h4")

    assert set(dataclasses.asdict(record).keys()) == EXPECTED_CLOSED_FIELD_SET


def test_decision_record_is_frozen() -> None:
    record = DecisionRecord(
        project_id="p",
        sequence_number=1,
        from_phase="Hypothesis",
        to_phase="Research Proposal",
        recorded_at="2026-01-01T00:00:00+00:00",
        commit_hash="a" * 40,
        freeze_commit_ref="b" * 40,
        freeze_verification_status="verified",
        freeze_covered_paths=(),
        gate_outcomes=(),
        authorization=_authorization(),
        evidence_refs=(),
        reproduction_record_ref=None,
        predecessor_hash=None,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.sequence_number = 2  # type: ignore[misc]


# --- append(): identity checks -------------------------------------------


def test_append_raises_when_manifest_missing(tmp_path: Path) -> None:
    archive_root = tmp_path / "research_archive"
    archive_root.mkdir()
    recorder = DecisionRecorder(archive_root)

    with pytest.raises(MissingArchiveManifestError):
        _append(recorder, "no_such_project")

    assert not (archive_root / "no_such_project").exists()


def test_append_raises_when_manifest_project_id_mismatches_directory_name(tmp_path: Path) -> None:
    archive_root = tmp_path / "research_archive"
    archive_dir = archive_root / "dir_name"
    archive_dir.mkdir(parents=True)
    manifest = {"schema_version": 1, "project_id": "other_id", "created_at": "2026-01-01T00:00:00+00:00"}
    (archive_dir / "archive_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ProjectIdentityMismatchError):
        _append(DecisionRecorder(archive_root), "dir_name")


def test_append_raises_when_directory_manifest_disagrees_with_passed_project_id(tmp_path: Path) -> None:
    # archive_dir is always derived from the project_id argument, so
    # directory-name and record.project_id are equal by construction
    # (A8-C9) -- the only reachable mismatch axis is manifest.project_id
    # disagreeing with that pair, which this exercises via a manifest
    # whose stored project_id belongs to a different cycle.
    archive_root = tmp_path / "research_archive"
    archive_dir = archive_root / "reference_h4"
    archive_dir.mkdir(parents=True)
    manifest = {"schema_version": 1, "project_id": "reference_h3", "created_at": "2026-01-01T00:00:00+00:00"}
    (archive_dir / "archive_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ProjectIdentityMismatchError):
        _append(DecisionRecorder(archive_root), "reference_h4")


def test_append_never_consults_lifecycle_version_or_completeness(tmp_path: Path) -> None:
    archive_root = tmp_path / "research_archive"
    archive_dir = archive_root / "reference_h4"
    archive_dir.mkdir(parents=True)
    # No lifecycle_version key at all, and no evidence subdirectories --
    # append() must not consult either.
    manifest = {"schema_version": 1, "project_id": "reference_h4", "created_at": "2026-01-01T00:00:00+00:00"}
    (archive_dir / "archive_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    record = _append(DecisionRecorder(archive_root), "reference_h4")

    assert record.sequence_number == 1


# --- append(): chain construction -----------------------------------------


def test_append_writes_genesis_record_with_null_predecessor(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    record = _append(DecisionRecorder(archive_root), "reference_h4")

    assert record.sequence_number == 1
    assert record.predecessor_hash is None

    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME
    rows = read_canonical_jsonl(chain_path)
    assert len(rows) == 1
    assert rows[0]["predecessor_hash"] is None
    assert rows[0]["sequence_number"] == 1


def test_append_second_record_chains_to_first(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    _append(recorder, "reference_h4")
    second = _append(recorder, "reference_h4", from_phase="Research Proposal", to_phase="Pre-validation")

    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME
    rows = read_canonical_jsonl(chain_path)
    assert len(rows) == 2
    assert second.sequence_number == 2
    assert second.predecessor_hash == "sha256:" + hashlib.sha256(canonical_bytes(rows[0])).hexdigest()
    assert rows[1]["predecessor_hash"] == second.predecessor_hash


def test_append_leaves_no_temp_file_behind(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    _append(DecisionRecorder(archive_root), "reference_h4")

    leftovers = list(archive_dir.glob("*.tmp"))
    assert leftovers == []


def test_append_refuses_onto_invalid_chain(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME
    # A hand-written, chain-invalid file: sequence 2 claims a predecessor hash
    # that does not match sequence 1's actual canonical hash.
    row1 = {
        "project_id": "reference_h4",
        "sequence_number": 1,
        "from_phase": "Hypothesis",
        "to_phase": "Research Proposal",
        "recorded_at": "2026-01-01T00:00:00+00:00",
        "commit_hash": "a" * 40,
        "freeze_commit_ref": "b" * 40,
        "freeze_verification_status": "verified",
        "freeze_covered_paths": [],
        "gate_outcomes": [],
        "authorization": {
            "authorizer": "alice",
            "reviewer_level": "1",
            "ambiguity_acknowledged": False,
            "override_acknowledged": False,
        },
        "evidence_refs": [],
        "reproduction_record_ref": None,
        "predecessor_hash": None,
    }
    row2 = dict(row1, sequence_number=2, predecessor_hash="sha256:" + "0" * 64)
    chain_path.write_bytes((canonical_line(row1) + "\n" + canonical_line(row2) + "\n").encode("utf-8"))

    with pytest.raises(ChainInvalidError):
        _append(DecisionRecorder(archive_root), "reference_h4")


def test_append_refuses_when_on_disk_prefix_is_not_canonical(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME
    row1 = {
        "project_id": "reference_h4",
        "sequence_number": 1,
        "from_phase": "Hypothesis",
        "to_phase": "Research Proposal",
        "recorded_at": "2026-01-01T00:00:00+00:00",
        "commit_hash": "a" * 40,
        "freeze_commit_ref": "b" * 40,
        "freeze_verification_status": "verified",
        "freeze_covered_paths": [],
        "gate_outcomes": [],
        "authorization": {
            "authorizer": "alice",
            "reviewer_level": "1",
            "ambiguity_acknowledged": False,
            "override_acknowledged": False,
        },
        "evidence_refs": [],
        "reproduction_record_ref": None,
        "predecessor_hash": None,
    }
    # Semantically identical to canonical_line(row1), but with non-compact
    # separators -- valid JSON, valid single chain-intact genesis record,
    # yet not byte-identical to what write_canonical_jsonl would produce.
    non_canonical = json.dumps(row1, sort_keys=True) + "\n"
    chain_path.write_bytes(non_canonical.encode("utf-8"))

    with pytest.raises(ChainPrefixMismatchError):
        _append(DecisionRecorder(archive_root), "reference_h4")


# --- verify_chain_intact() -------------------------------------------------


def _write_chain(archive_dir: Path, rows: list[dict]) -> Path:
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME
    content = "".join(canonical_line(row) + "\n" for row in rows)
    chain_path.write_bytes(content.encode("utf-8"))
    return chain_path


def _build_valid_chain(recorder: DecisionRecorder, project_id: str, count: int) -> list[dict]:
    for i in range(count):
        _append(recorder, project_id, from_phase=f"phase_{i}", to_phase=f"phase_{i + 1}")
    chain_path = recorder.chain_path(project_id)
    return read_canonical_jsonl(chain_path)


def test_verify_chain_intact_true_for_nonexistent_file(tmp_path: Path) -> None:
    assert verify_chain_intact(tmp_path / "no_such_file.jsonl") is True


def test_verify_chain_intact_true_for_valid_chain(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    _build_valid_chain(recorder, "reference_h4", 3)

    assert verify_chain_intact(archive_dir / TRANSITION_RECORDS_FILENAME) is True


def test_verify_chain_intact_detects_mutation(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 3)

    rows[1] = dict(rows[1], to_phase="Tampered")
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_intact(chain_path) is False


def test_verify_chain_intact_detects_reorder(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 3)

    rows[1], rows[2] = rows[2], rows[1]
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_intact(chain_path) is False


def test_verify_chain_intact_detects_insertion(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 2)

    inserted = dict(rows[0], sequence_number=2, to_phase="Injected", predecessor_hash=hash_record(rows[0]))
    rows = [rows[0], inserted, rows[1]]
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_intact(chain_path) is False


def test_verify_chain_intact_detects_interior_deletion(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 3)

    del rows[1]
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_intact(chain_path) is False


def test_verify_chain_intact_detects_duplicate_sequence(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 2)

    rows[1] = dict(rows[1], sequence_number=1)
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_intact(chain_path) is False


def test_verify_chain_intact_detects_gap(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 3)

    rows[2] = dict(rows[2], sequence_number=4)
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_intact(chain_path) is False


def test_verify_chain_intact_detects_forged_predecessor(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 2)

    rows[1] = dict(rows[1], predecessor_hash="sha256:" + "f" * 64)
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_intact(chain_path) is False


def test_verify_chain_intact_does_not_detect_tail_truncation(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 3)

    del rows[2]  # drop the tail record only
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_intact(chain_path) is True


def test_verify_chain_intact_raises_on_crlf_corruption(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    _build_valid_chain(recorder, "reference_h4", 1)
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME

    raw = chain_path.read_bytes()
    chain_path.write_bytes(raw.replace(b"\n", b"\r\n"))

    with pytest.raises(ValueError, match="CR line endings"):
        verify_chain_intact(chain_path)


# --- verify_chain_anchored() ------------------------------------------------


def test_verify_chain_anchored_true_for_matching_citation(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 2)
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME

    assert verify_chain_anchored(chain_path, 2, hash_record(rows[1])) is True


def test_verify_chain_anchored_false_for_wrong_hash(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    _build_valid_chain(recorder, "reference_h4", 2)
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME

    assert verify_chain_anchored(chain_path, 2, "sha256:" + "0" * 64) is False


def test_verify_chain_anchored_false_after_tail_truncation_past_anchor(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 3)
    anchor_hash = hash_record(rows[2])
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME

    del rows[2]
    _write_chain(archive_dir, rows)

    assert verify_chain_anchored(chain_path, 3, anchor_hash) is False


def test_verify_chain_anchored_false_when_chain_not_intact(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    rows = _build_valid_chain(recorder, "reference_h4", 3)
    # Tamper the interior record (sequence 2) -- it has a successor at
    # sequence 3 whose predecessor_hash will no longer match, so this is
    # detectable, unlike tampering the tail record would be.
    rows[1] = dict(rows[1], to_phase="Tampered")
    chain_path = _write_chain(archive_dir, rows)

    assert verify_chain_anchored(chain_path, 1, hash_record(rows[0])) is False


# --- read_chain() ------------------------------------------------------------


def test_read_chain_reconstructs_structural_values(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    _append(recorder, "reference_h4", from_phase="Hypothesis", to_phase="Research Proposal")
    _append(recorder, "reference_h4", from_phase="Research Proposal", to_phase="Pre-validation")

    records = read_chain(archive_dir / TRANSITION_RECORDS_FILENAME)

    assert [r.sequence_number for r in records] == [1, 2]
    assert records[0].from_phase == "Hypothesis"
    assert records[1].to_phase == "Pre-validation"
    assert records[1].predecessor_hash == hash_record(dataclasses.asdict(records[0]))


def test_read_chain_does_not_validate_phase_values(tmp_path: Path) -> None:
    archive_root, archive_dir = _make_archive(tmp_path)
    recorder = DecisionRecorder(archive_root)
    _append(recorder, "reference_h4", from_phase="not_a_real_phase", to_phase="also_not_real")

    records = read_chain(archive_dir / TRANSITION_RECORDS_FILENAME)

    assert records[0].from_phase == "not_a_real_phase"
    assert records[0].to_phase == "also_not_real"


def test_read_chain_returns_empty_tuple_for_missing_file(tmp_path: Path) -> None:
    assert read_chain(tmp_path / "no_such_file.jsonl") == ()
