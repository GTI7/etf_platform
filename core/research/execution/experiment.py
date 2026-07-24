"""`Experiment` (Protocol) and `ExperimentSpec` -- Phase F F-1
(docs/ARCHITECTURE_DECISIONS.md AD-061, AD-064).

`Experiment` is structural typing only, exactly like
`core.validation.gate.Gate` -- nothing here is a base class, and this
module defines no implementation. An `Experiment` is fully constructed by
its caller with whatever database handle, repository, or configuration it
needs; this Protocol is domain-blind and carries no ETF-specific logic.

`ExperimentSpec` is the caller-declared half of a run's identity. Its
field set is closed and pinned by test -- adding a field fails a test and
forces a new AD rather than a commit, mirroring
`core.governance.decision_recorder.DecisionRecord`'s convention.

**Code revision ownership (AD-061, AD-064).** The code revision reference
belongs here, on `ExperimentSpec`, as a field the caller declares --
never on `MeasurementBundle`, which an `Experiment` implementation emits.
This is a generic identity field, not a Git-specific one: the domain
model does not assert that the value is a Git commit hash, a hash of any
kind, or that Git is the version-control system in use. A later increment
may populate it from `core.governance.decision_recorder`'s existing
`code_commit_hash`-shaped inputs (e.g. a `TransitionRequest`'s own code
revision); this module makes no such connection and imports nothing to
make it. Where the caller has no code revision to supply, `None` is
recorded -- never omitted, never inferred, never derived here (no
`git rev-parse`, no environment sniffing).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Protocol

from core.research.execution.measurement_bundle import MeasurementBundle


@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    """Closed field set -- `tests/test_phase_f_measurement_types.py` pins
    the exact field set, so adding a field fails a test and forces a new
    AD rather than a commit."""

    project_id: str
    as_of: datetime
    parameters: Mapping[str, str]
    code_revision: str | None


class Experiment(Protocol):
    """Structural Protocol only. No implementation, no ETF-specific
    logic -- an `Experiment` implementation is written elsewhere, outside
    `core/`, by a later increment (docs/ARCHITECTURE_DECISIONS.md AD-061
    R-16)."""

    name: str

    def run(self, spec: ExperimentSpec) -> MeasurementBundle: ...
