from __future__ import annotations

import ast
import dataclasses
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from core.governance.freeze_verifier import FreezeStatus
from core.shared.clock import FixedClock
from core.validation.gate_context import GateContext
from core.validation.gate_result import DecisionMetadata, GateResult, GateStatus
from core.validation.gate_run_record import GateExecutionOutcome, GateRunRecord
from core.validation.gate_runner import GateRunner


def _git(args: list[str], *, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(["init", "-q"], cwd=tmp_path)
    _git(["config", "user.email", "test@example.com"], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=tmp_path)
    return tmp_path


def _commit(repo: Path, filename: str, content: str, message: str) -> str:
    (repo / filename).write_text(content, encoding="utf-8")
    _git(["add", filename], cwd=repo)
    _git(["commit", "-q", "-m", message], cwd=repo)
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _decision() -> DecisionMetadata:
    return DecisionMetadata(reviewer="test-reviewer", review_level="Level 2", decided_at="2026-07-24")


def _context(freeze_hash: str, path: str = "acceptance_criteria.md") -> GateContext:
    return GateContext(
        measurements={},
        frozen_criteria={},
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=[path],
        evidence_refs=(),
        decision=_decision(),
    )


class _RecordingGate:
    def __init__(self, name: str, status: GateStatus = GateStatus.PASS) -> None:
        self.name = name
        self.required_review_level = "Level 1"
        self.calls = 0
        self._status = status

    def run(self, context: GateContext) -> GateResult:
        self.calls += 1
        return GateResult(
            gate_name=self.name,
            status=self._status,
            summary=f"{self.name} ran",
            evidence_refs=(),
            decision=context.decision,
        )


class _RaisingGate:
    def __init__(self, name: str) -> None:
        self.name = name
        self.required_review_level = "Level 1"
        self.calls = 0

    def run(self, context: GateContext) -> GateResult:
        self.calls += 1
        raise RuntimeError("boom")


def _fixed_clock() -> FixedClock:
    return FixedClock(datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc))


# --- registry semantics -------------------------------------------------


def test_duplicate_gate_registration_raises_value_error() -> None:
    runner = GateRunner()
    runner.register_gate(_RecordingGate("economic_rationale"))

    with pytest.raises(ValueError):
        runner.register_gate(_RecordingGate("economic_rationale"))


def test_run_gate_unknown_name_raises_key_error(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    runner = GateRunner()

    with pytest.raises(KeyError):
        runner.run_gate("nonexistent", _context(freeze_hash))


def test_run_gate_dispatches_to_registered_gate(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    runner = GateRunner()
    gate = _RecordingGate("economic_rationale")
    runner.register_gate(gate)

    result = runner.run_gate("economic_rationale", _context(freeze_hash))

    assert result.gate_name == "economic_rationale"
    assert gate.calls == 1


# --- run_sequence: atomic preflight -------------------------------------


def test_unknown_gate_name_in_sequence_refuses_before_any_gate_runs(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    runner = GateRunner()
    known = _RecordingGate("economic_rationale")
    runner.register_gate(known)

    with pytest.raises(KeyError):
        runner.run_sequence(
            ["economic_rationale", "nonexistent"],
            _context(freeze_hash),
            clock=_fixed_clock(),
            code_commit_hash="deadbeef",
            repo_root=repo,
        )

    assert known.calls == 0


# --- run_sequence: no short-circuit -------------------------------------


def test_run_sequence_runs_every_gate_even_after_a_fail(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    runner = GateRunner()
    failing = _RecordingGate("economic_rationale", status=GateStatus.FAIL)
    passing = _RecordingGate("signal_independence", status=GateStatus.PASS)
    runner.register_gate(failing)
    runner.register_gate(passing)

    record = runner.run_sequence(
        ["economic_rationale", "signal_independence"],
        _context(freeze_hash),
        clock=_fixed_clock(),
        code_commit_hash="deadbeef",
        repo_root=repo,
    )

    assert failing.calls == 1
    assert passing.calls == 1
    assert [o.gate_name for o in record.outcomes] == ["economic_rationale", "signal_independence"]
    assert record.outcomes[0].result is not None and record.outcomes[0].result.status is GateStatus.FAIL
    assert record.outcomes[1].result is not None and record.outcomes[1].result.status is GateStatus.PASS


# --- run_sequence: gate crash is an envelope error, never a status ------


def test_gate_exception_is_captured_as_envelope_error_not_a_status(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    runner = GateRunner()
    raiser = _RaisingGate("economic_rationale")
    survivor = _RecordingGate("signal_independence", status=GateStatus.PASS)
    runner.register_gate(raiser)
    runner.register_gate(survivor)

    record = runner.run_sequence(
        ["economic_rationale", "signal_independence"],
        _context(freeze_hash),
        clock=_fixed_clock(),
        code_commit_hash="deadbeef",
        repo_root=repo,
    )

    raised_outcome = record.outcomes[0]
    assert raised_outcome.result is None
    assert raised_outcome.error is not None
    assert "RuntimeError" in raised_outcome.error
    assert "boom" in raised_outcome.error

    # the gate after the crash still ran -- no short-circuit on a crash either
    assert survivor.calls == 1
    assert record.outcomes[1].result is not None
    assert record.outcomes[1].error is None


def test_gate_execution_outcome_rejects_both_result_and_error() -> None:
    with pytest.raises(ValueError):
        GateExecutionOutcome(
            gate_name="x",
            result=GateResult(
                gate_name="x", status=GateStatus.PASS, summary="", evidence_refs=(), decision=_decision()
            ),
            error="boom",
        )


def test_gate_execution_outcome_rejects_neither_result_nor_error() -> None:
    with pytest.raises(ValueError):
        GateExecutionOutcome(gate_name="x", result=None, error=None)


# --- run_sequence: freeze bracket (§6.6) --------------------------------


def test_clean_bracket_is_not_invalidated(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    runner = GateRunner()
    runner.register_gate(_RecordingGate("economic_rationale"))

    record = runner.run_sequence(
        ["economic_rationale"],
        _context(freeze_hash),
        clock=_fixed_clock(),
        code_commit_hash="deadbeef",
        repo_root=repo,
    )

    assert record.pre_freeze_verification.status is FreezeStatus.VERIFIED
    assert record.post_freeze_verification.status is FreezeStatus.VERIFIED
    assert record.bracket_invalidated is False


def test_freeze_drift_mid_sequence_invalidates_bracket_but_retains_results(repo: Path) -> None:
    """F-1: gate 1 verifies clean; the operator edits a frozen file; a
    later gate's own internal verify_freeze call sees DRIFTED. The
    runner's own post-sequence check must catch this even though each
    individual gate result is retained as evidence."""
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")

    class _DriftingGate:
        name = "economic_rationale"
        required_review_level = "Level 1"

        def run(self, context: GateContext) -> GateResult:
            (repo / "acceptance_criteria.md").write_text("edited after freeze\n", encoding="utf-8")
            return GateResult(
                gate_name=self.name, status=GateStatus.PASS, summary="ran before drift", evidence_refs=(), decision=context.decision
            )

    runner = GateRunner()
    runner.register_gate(_DriftingGate())

    record = runner.run_sequence(
        ["economic_rationale"],
        _context(freeze_hash),
        clock=_fixed_clock(),
        code_commit_hash="deadbeef",
        repo_root=repo,
    )

    assert record.pre_freeze_verification.status is FreezeStatus.VERIFIED
    assert record.post_freeze_verification.status is not FreezeStatus.VERIFIED
    assert record.bracket_invalidated is True
    # the gate's own result is retained as evidence despite the invalidated bracket
    assert record.outcomes[0].result is not None
    assert record.outcomes[0].result.status is GateStatus.PASS


# --- determinism (INV-11, restated for Phase D's in-memory scope) -------


def test_identical_inputs_produce_identical_context_digest(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    context = GateContext(
        measurements={"economic_rationale": Decimal("0.05")},
        frozen_criteria={},
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=(),
        decision=_decision(),
    )
    runner = GateRunner()
    runner.register_gate(_RecordingGate("economic_rationale"))

    record_1 = runner.run_sequence(
        ["economic_rationale"], context, clock=_fixed_clock(), code_commit_hash="deadbeef", repo_root=repo
    )
    record_2 = runner.run_sequence(
        ["economic_rationale"], context, clock=_fixed_clock(), code_commit_hash="deadbeef", repo_root=repo
    )

    assert record_1.context_digest == record_2.context_digest
    assert record_1.context_digest.startswith("sha256:")


def test_different_measurements_produce_different_context_digest(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    runner = GateRunner()
    runner.register_gate(_RecordingGate("economic_rationale"))

    context_a = GateContext(
        measurements={"economic_rationale": Decimal("0.05")},
        frozen_criteria={},
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=(),
        decision=_decision(),
    )
    context_b = GateContext(
        measurements={"economic_rationale": Decimal("0.06")},
        frozen_criteria={},
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=(),
        decision=_decision(),
    )

    record_a = runner.run_sequence(
        ["economic_rationale"], context_a, clock=_fixed_clock(), code_commit_hash="deadbeef", repo_root=repo
    )
    record_b = runner.run_sequence(
        ["economic_rationale"], context_b, clock=_fixed_clock(), code_commit_hash="deadbeef", repo_root=repo
    )

    assert record_a.context_digest != record_b.context_digest


# --- measurement_provenance and code_commit_hash pass through unmodified


def test_measurement_provenance_and_commit_hash_pass_through(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen\n", "freeze")
    context = GateContext(
        measurements={},
        frozen_criteria={},
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=(),
        decision=_decision(),
        measurement_provenance="research_archive/reference_h4/reproduction_record.json",
    )
    runner = GateRunner()
    runner.register_gate(_RecordingGate("economic_rationale"))

    record = runner.run_sequence(
        ["economic_rationale"], context, clock=_fixed_clock(), code_commit_hash="abc123", repo_root=repo
    )

    assert record.measurement_provenance == "research_archive/reference_h4/reproduction_record.json"
    assert record.code_commit_hash == "abc123"
    assert record.recorded_at == datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc)


# --- no aggregate field (AD-049 part 3) ----------------------------------


def test_gate_run_record_has_no_aggregate_or_verdict_field() -> None:
    """Closed field set, same convention as
    core.governance.decision_recorder.DecisionRecord: adding an
    aggregate/verdict/sequence_status field here must fail this test and
    force a new AD (AD-049 part 3), never land as a quiet addition."""
    field_names = {f.name for f in dataclasses.fields(GateRunRecord)}

    assert field_names == {
        "requested_gate_names",
        "outcomes",
        "pre_freeze_verification",
        "post_freeze_verification",
        "bracket_invalidated",
        "context_digest",
        "measurement_provenance",
        "code_commit_hash",
        "recorded_at",
    }
    forbidden = {"verdict", "aggregate", "aggregate_status", "sequence_status"}
    assert field_names.isdisjoint(forbidden)


# --- Phase D boundary: no persistence, no DecisionRecorder import -------


def _imported_module_names(module_file: str) -> set[str]:
    tree = ast.parse(Path(module_file).read_text(encoding="utf-8"))
    names = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    }
    names |= {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    return names


@pytest.mark.parametrize(
    "module",
    [
        "core.validation.gate_runner",
        "core.validation.gate_run_record",
        "core.validation.gate_context",
        "core.validation.validation_registry",
    ],
)
def test_phase_d_modules_never_import_decision_recorder(module: str) -> None:
    """R1 ruling (2026-07-24): Phase D never imports DecisionRecorder --
    persistence and the governance chain remain Phase E's concern."""
    imported = _imported_module_names(__import__(module, fromlist=["__file__"]).__file__)

    assert not any(
        name == "core.governance.decision_recorder" or name.startswith("core.governance.decision_recorder.")
        for name in imported
    )


def test_gate_runner_module_has_no_file_write_calls() -> None:
    """No persistence layer in Phase D -- the runner never opens a file
    for writing and never calls a canonical-JSONL write helper."""
    import core.validation.gate_runner as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "write_canonical_jsonl" not in source
    assert "write_bytes" not in source
    assert "write_text" not in source
