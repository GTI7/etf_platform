"""Phase F -- Research Execution Engine (Phase 4 / Phase F, F-1 "measurement
types" slice; docs/ARCHITECTURE_DECISIONS.md AD-061, AD-064).

This package holds the `Experiment` Protocol and the closed-field-set
record types an experiment run produces (`ExperimentSpec`,
`MeasurementBundle`) plus their pure serializer. It defines no runner, no
archive writer, no gate-context assembly, and no transition composition --
those are later Phase F increments (F-2 .. F-10), not this one.
"""

from __future__ import annotations
