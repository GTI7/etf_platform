"""`ExperimentSpec` + `MeasurementBundle` -> `dict` -- Phase F F-1
(docs/ARCHITECTURE_DECISIONS.md AD-061, condition F-C2 / F-C1 SS2.3
item 1).

Pure serializer only: no filesystem, no `ArchiveWriter`, no Governance
import (not `core.governance.canonical_jsonl`, not anything else under
`core.governance`) -- it takes an `ExperimentSpec` and a
`MeasurementBundle` by type and imports nothing outside
`core.research.execution`. This is the shape
`core.reporting.json_renderer` already has: a pure renderer that imports
exactly the record type it serializes and nothing beyond its own
package.

**Closed output key set (AD-061).** Exactly eight keys: `experiment_name`,
`as_of`, `parameters`, `measurements`, `evidence_refs`, `dataset_refs`,
`provenance_ref`, `code_revision`. `project_id` is not one of them --
AD-061 lists the artifact's serialized field set without it; the project
is already named by the archive path (AD-062), not duplicated in the
payload.

**Determinism.**

- `parameters` and `measurements` are `Mapping`s -- unordered by
  contract -- so they are re-keyed into a plain `dict` in sorted-key
  order regardless of the input mapping's own iteration order.
- `evidence_refs` and `dataset_refs` are ordered tuples -- order is
  meaningful (e.g. an appended ref) -- so they become `list`s in their
  original element order, never sorted.
- `as_of` (a `datetime`) becomes its `isoformat()` string, verbatim.
- Every `Decimal` value in `measurements` becomes its `str()`, never a
  `float` -- exact decimal text is preserved, not float rounding.
- Explicit `None` values (`provenance_ref`, `code_revision`) are kept as
  `None` in the output, never omitted.

**No timezone normalization, and nothing here claims any.** `as_of` is
serialized exactly as the caller supplied it: a non-UTC offset is written
with that offset, and a naive `datetime` is written with no offset at
all. This module neither converts to UTC nor refuses a naive instant, and
"deterministic" above means *same input, same output* -- never that two
equal instants carrying different `tzinfo` serialize to the same string.
Timezone-awareness is a property of the injected clock, not of this
serializer: AD-061 (R-7) places the refusal of a naive instant at
`FixedClock` (`core/shared/clock.py:19`), and `SystemClock.now()` returns
`datetime.now(timezone.utc)`. `ResearchRunner` reads that clock once and
freezes the instant -- and `ResearchRunner` is F-2. B1 has no runner and
no clock, so it has nothing to normalize against, and a normalization
rule added here would duplicate, at the wrong altitude, the one that
governs.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

from core.research.execution.experiment import ExperimentSpec
from core.research.execution.measurement_bundle import MeasurementBundle


def serialize_measurement_artifact(spec: ExperimentSpec, bundle: MeasurementBundle) -> dict[str, Any]:
    """Combine `spec` (the run's declared inputs) and `bundle` (what the
    experiment measured) into the AD-061 measurement-artifact payload."""
    return {
        "experiment_name": bundle.experiment_name,
        "as_of": _serialize_datetime(spec.as_of),
        "parameters": _serialize_mapping(spec.parameters),
        "measurements": _serialize_measurements(bundle.measurements),
        "evidence_refs": list(bundle.evidence_refs),
        "dataset_refs": list(bundle.dataset_refs),
        "provenance_ref": bundle.provenance_ref,
        "code_revision": spec.code_revision,
    }


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _serialize_mapping(mapping: Mapping[str, str]) -> dict[str, str]:
    return {key: mapping[key] for key in sorted(mapping)}


def _serialize_measurements(mapping: Mapping[str, Decimal]) -> dict[str, str]:
    return {key: str(mapping[key]) for key in sorted(mapping)}
