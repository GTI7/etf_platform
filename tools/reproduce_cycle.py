"""``python -m tools.reproduce_cycle <cycle>``: run one end-to-end
reproduction attempt for a ``research_archive/<cycle>`` directory.

Resolves ``commit_hash`` from the cycle's own ``reproduction_record.json``
and the dataset manifest from its own ``dataset_manifest.json`` -- the
two files Standard §5 already places there. The experiment module's own
path is not part of either schema, and no field is invented for it here,
so it is the one required flag.

**Why this is `tools/` and not `core/`.** It was
``core.governance.reproduction_runner._cli_main`` until 2026-07-27, when
Engine Boundary cleanup item C4 stopped Governance from constructing the
audited workload's objects. `run_reproduction` now takes `parse_row` and
`load_rows` as parameters, and *something* has to choose which workload's
implementations to pass. That choice is composition, and a composition
root that names both Governance and the ETF workload cannot live inside
Governance -- `governance -> etf` is a forbidden edge (AD-068 decision
2), which is exactly the coupling this cleanup discharged. `tools/` is
outside the domain graph `tools/check_import_boundaries.py` scans and is
already where this repository puts callable entry points that wire `core`
packages together.

The library half did not move. `core.governance.reproduction_runner.run_reproduction`
is unchanged in behaviour and is still the only thing that runs a
reproduction; this module chooses its arguments and prints its result.

**Import resolution is unaffected.** `reproduction_runner`'s docstring
records that a pinned script's ``core.*`` imports resolve through HEAD's
package because ``sys.modules['core']`` is already populated by the time
the pinned script runs. That is still true from here -- importing
`core.governance.reproduction_runner` at module scope below is what
populates it -- so this relocation changes nothing about the pinned
worktree's isolation, for better or worse.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from core.analytics.persistence.frozen_dataset import load_snapshot_rows, parse_snapshot_row
from core.governance.pinned_worktree import REPO_ROOT
from core.governance.reproduction_record import ReproductionStatus
from core.governance.reproduction_runner import run_reproduction


def _run_experiment_entrypoint(module: ModuleType, db_path: Path) -> Any:
    """The one calling convention every pinned experiment script exposes
    (amendment SS F.2: "Run `run(db_path=<scratch path>, ...)` from the
    worktree's own copy of the experiment script")."""
    return module.run(db_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.reproduce_cycle",
        description="Run one end-to-end reproduction attempt for a research_archive/<cycle> directory.",
    )
    parser.add_argument(
        "cycle",
        type=Path,
        help="path to the cycle directory (must contain reproduction_record.json and dataset_manifest.json)",
    )
    parser.add_argument(
        "--experiment-module",
        type=Path,
        required=True,
        help="path, relative to --repo-root, to the pinned commit's own experiment script (must expose run(db_path))",
    )
    parser.add_argument(
        "--migrations",
        type=Path,
        default=Path("migrations"),
        help="path, relative to --repo-root, to the migrations directory (default: migrations)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="repository root to resolve commit_hash against (default: this repository)",
    )
    parser.add_argument(
        "--scratch-db",
        type=Path,
        default=None,
        help="scratch database path (default: a fresh path under a new temp directory)",
    )
    args = parser.parse_args(argv)

    cycle_dir: Path = args.cycle
    record_path = cycle_dir / "reproduction_record.json"
    try:
        record_raw = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {record_path}: {exc}", file=sys.stderr)
        return 2
    commit_hash = record_raw.get("commit_hash")
    if not commit_hash:
        print(f"error: {record_path} has no commit_hash", file=sys.stderr)
        return 2

    scratch_db_path = args.scratch_db
    if scratch_db_path is None:
        scratch_db_path = Path(tempfile.mkdtemp(prefix="reproduction_scratch_")) / "scratch.db"

    outcome = run_reproduction(
        repo_root=args.repo_root,
        cycle_dir=cycle_dir,
        dataset_manifest_path=cycle_dir / "dataset_manifest.json",
        migrations_relative_path=str(args.migrations),
        experiment_module_relative_path=str(args.experiment_module),
        commit_hash=commit_hash,
        scratch_db_path=scratch_db_path,
        run_experiment=_run_experiment_entrypoint,
        parse_row=parse_snapshot_row,
        load_rows=load_snapshot_rows,
    )

    print(f"{outcome.status.value}: {outcome.detail}")
    return 0 if outcome.status is ReproductionStatus.VERIFIED else 1


if __name__ == "__main__":
    raise SystemExit(main())
