"""`MeasurementBundle` -- Phase F F-1 (docs/ARCHITECTURE_DECISIONS.md
AD-064).

Closed field set. Five fields, and the absences are the design:

- No `status`, `verdict`, or `passed` -- a measurer that could also
  conclude would collapse measurement into judgment.
- No `threshold`, `criterion`, or `direction` -- the yardstick comes from
  the operator's frozen methodology, never from the thing being measured.
- No `summary`, `notes`, or `rationale` -- AD-045's prohibition on
  narrative in a mechanical record is not reopened at a new altitude.
- No code revision field -- that identity element belongs to the caller,
  on `ExperimentSpec` (AD-061, AD-064), never to what an `Experiment`
  emits.

`tests/test_phase_f_measurement_types.py` pins the exact field set, so
adding a field fails a test and forces a new AD rather than a commit,
mirroring `core.governance.decision_recorder.DecisionRecord`'s
convention.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True, slots=True)
class MeasurementBundle:
    experiment_name: str
    measurements: Mapping[str, Decimal]
    evidence_refs: tuple[str, ...]
    dataset_refs: tuple[str, ...]
    provenance_ref: str | None
