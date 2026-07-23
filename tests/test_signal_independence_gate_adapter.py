from __future__ import annotations

import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

from core.validation.gate_context import FrozenCriterion, GateContext
from core.validation.gate_result import DecisionMetadata
from core.validation.gates.signal_independence import GATE_NAME, evaluate_signal_independence_gate
from core.validation.gates.signal_independence_adapter import SignalIndependenceGateAdapter


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


def test_adapter_name_matches_gate_name() -> None:
    adapter = SignalIndependenceGateAdapter(required_review_level="Level 2")
    assert adapter.name == GATE_NAME


def test_adapter_dispatch_matches_direct_call(repo: Path) -> None:
    """Adapter equivalence: dispatching through the adapter returns
    exactly what calling evaluate_signal_independence_gate directly
    returns -- proves the adapter changed no behavior (§6.2)."""
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen criteria\n", "freeze")
    decision = _decision()

    direct_result = evaluate_signal_independence_gate(
        measured_overlap=Decimal("0.20"),
        frozen_threshold=Decimal("0.30"),
        threshold_direction="at_most",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=("ref-1",),
        decision=decision,
        repo_root=repo,
    )

    adapter = SignalIndependenceGateAdapter(required_review_level="Level 2", repo_root=repo)
    context = GateContext(
        measurements={GATE_NAME: Decimal("0.20")},
        frozen_criteria={GATE_NAME: FrozenCriterion(threshold=Decimal("0.30"), direction="at_most")},
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=("ref-1",),
        decision=decision,
    )

    adapter_result = adapter.run(context)

    assert adapter_result == direct_result


def test_adapter_missing_frozen_criterion_is_ambiguous(repo: Path) -> None:
    freeze_hash = _commit(repo, "acceptance_criteria.md", "frozen criteria\n", "freeze")
    decision = _decision()

    adapter = SignalIndependenceGateAdapter(required_review_level="Level 2", repo_root=repo)
    context = GateContext(
        measurements={GATE_NAME: Decimal("0.20")},
        frozen_criteria={},
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=(),
        decision=decision,
    )

    from core.validation.gate_result import GateStatus

    result = adapter.run(context)

    assert result.status is GateStatus.AMBIGUOUS
    assert result.summary == "Acceptance criterion was not frozen before validation."
