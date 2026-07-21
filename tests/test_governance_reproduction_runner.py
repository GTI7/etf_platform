"""End-to-end test of core.governance.reproduction_runner: a throwaway
git repo standing in for the real etf_platform repo, with its own
committed migrations/ and a tiny experiment.py, pinned to a commit and
executed through the full guard -> worktree -> reconstruction ->
identity-check pipeline.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from types import ModuleType

import pytest

from core.governance.canonical_jsonl import sha256_of_file, write_canonical_jsonl
from core.governance.dataset_manifest import MANIFEST_SCHEMA_VERSION
from core.governance.dataset_snapshots import etf_to_row
from core.governance.reproduction_record import ReproductionStatus
from core.governance.reproduction_runner import run_reproduction
from core.market_data.domain.models import ETF

REAL_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

_EXPERIMENT_SOURCE = '''\
import sqlite3

RAN_WITH_NETWORK_ATTEMPT = False


def run(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO IndicatorDefinition (indicator_definition_id, name, version, parameters, created_at) "
            "VALUES ('def-1', 'SMA', 1, '{}', '2026-07-20T00:00:00+00:00')"
        )
        conn.commit()
    finally:
        conn.close()
    return "ok"
'''

_NETWORK_EXPERIMENT_SOURCE = '''\
import socket


def run(db_path):
    socket.create_connection(("example.invalid", 80))
'''


def _git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_migrations_and_experiment(repo: Path, experiment_source: str) -> str:
    _git(["init", "-q"], cwd=repo)
    _git(["config", "user.email", "test@example.com"], cwd=repo)
    _git(["config", "user.name", "Test"], cwd=repo)

    migrations_dir = repo / "migrations"
    migrations_dir.mkdir()
    for migration_file in REAL_MIGRATIONS_DIR.glob("*.sql"):
        shutil.copy(migration_file, migrations_dir / migration_file.name)

    (repo / "experiment.py").write_text(experiment_source, encoding="utf-8")

    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-q", "-m", "pin this commit"], cwd=repo)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def _etf(ticker: str, etf_id: str) -> ETF:
    return ETF(
        etf_id=etf_id,
        ticker=ticker,
        name=f"{ticker} Fund",
        currency="USD",
        calendar_id="XNYS",
        created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )


def _build_cycle(tmp_path: Path) -> tuple[Path, Path]:
    cycle_dir = tmp_path / "cycle"
    (cycle_dir / "dataset_hashes").mkdir(parents=True)

    def _entry(source_table: str, filename: str, rows: list[dict]) -> dict:
        path = cycle_dir / "dataset_hashes" / filename
        write_canonical_jsonl(rows, path)
        return {
            "dataset_id": f"{source_table.lower()}_v1",
            "type": "test_fixture_data",
            "source_table": source_table,
            "row_count": len(rows),
            "snapshot_path": f"dataset_hashes/{filename}",
            "content_hash": sha256_of_file(path),
            "schema_version": 1,
        }

    entries = [
        _entry("ETF", "etf.jsonl", [etf_to_row(_etf("SPY", "etf-spy"))]),
        _entry("TradingSession", "trading_session.jsonl", []),
        _entry("PriceBar", "pricebar.jsonl", []),
    ]
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project_id": "test_cycle",
        "generated_at": "2026-08-01T00:00:00+00:00",
        "datasets": entries,
    }
    manifest_path = cycle_dir / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return cycle_dir, manifest_path


def _run_module(module: ModuleType, db_path: Path) -> None:
    module.run(db_path)


def test_full_reproduction_verifies(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.VERIFIED


def test_experiment_code_runs_from_the_pinned_commit_not_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)

    # HEAD moves on to a version that would fail (bad table name) --
    # reproduction must still use the pinned commit's own version.
    (repo / "experiment.py").write_text(
        "def run(db_path):\n    raise RuntimeError('HEAD code must never run during reproduction')\n",
        encoding="utf-8",
    )
    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-q", "-m", "HEAD moved on"], cwd=repo)

    cycle_dir, manifest_path = _build_cycle(tmp_path)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.VERIFIED


def test_network_attempt_during_run_produces_reproduction_failed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _NETWORK_EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.REPRODUCTION_FAILED
    assert "blocked outbound socket connection" in outcome.detail


def test_guard_is_uninstalled_after_the_attempt_completes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError):
            sock.connect(("127.0.0.1", 1))
    finally:
        sock.close()
