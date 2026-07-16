from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import NewType

from core.domain.exceptions import DomainError
from core.shared.ids import ETFId, ScoreId

# Defined locally rather than in core/shared/ids.py: these identify
# analytics-only entities and have no reuse outside this package. ScoreId
# itself is NOT defined here -- it was already reserved in
# core/shared/ids.py since Phase 0, and Score is simply its first user.
IndicatorDefinitionId = NewType("IndicatorDefinitionId", str)
IndicatorValueId = NewType("IndicatorValueId", str)
ScoringProfileId = NewType("ScoringProfileId", str)


class InsufficientPriceHistoryError(DomainError):
    """Raised when a window calculation needs N trading sessions of price
    history for an ETF and fewer than N are actually available -- whether
    because the ETF genuinely doesn't have that much history yet, or
    because the TradingCalendar hasn't been populated that far back.
    Deliberately not distinguished: both cases mean the window cannot be
    computed correctly, and both must fail loudly rather than silently
    produce a shorter, mislabeled window."""


class MissingIndicatorValueError(DomainError):
    """Raised when a ScoringProfile requires an IndicatorValue (for a given
    ETF, session, indicator name and version) that has not been computed
    yet. Same treatment as InsufficientPriceHistoryError: fail loudly
    inside the pipeline run rather than silently producing a partial or
    default score."""


def serialize_parameters(parameters: dict[str, object]) -> str:
    """Canonical JSON serialization for parameters columns
    (IndicatorDefinition.parameters, ScoringProfile.parameters).

    Always sort_keys=True: two logically identical parameter dicts must
    always produce the same string, or a UNIQUE(name, version,
    parameters) constraint silently stops meaning what it says.
    """
    return json.dumps(parameters, sort_keys=True)


def _validate_canonical_parameters(parameters: str) -> None:
    """Reject a parameters string that isn't exactly what
    serialize_parameters() would have produced.

    This is what makes UNIQUE(name, version, parameters) actually mean
    what it says: without it, two logically identical parameter dicts
    could serialize differently (e.g. different key order) and silently
    bypass the uniqueness constraint. Enforced at construction, the same
    way Money validates its own invariants in __post_init__.
    """
    if not isinstance(parameters, str):
        raise TypeError(f"parameters must be a str, got {type(parameters).__name__}")
    try:
        parsed = json.loads(parameters)
    except json.JSONDecodeError as exc:
        raise ValueError(f"parameters is not valid JSON: {parameters!r}") from exc
    if serialize_parameters(parsed) != parameters:
        raise ValueError(
            "parameters must be built with serialize_parameters() "
            f"(canonical, sort_keys=True form); got {parameters!r}"
        )


@dataclass(frozen=True, slots=True)
class IndicatorDefinition:
    indicator_definition_id: IndicatorDefinitionId
    name: str
    version: int
    parameters: str  # build with serialize_parameters(), never json.dumps() directly
    created_at: datetime

    def __post_init__(self) -> None:
        _validate_canonical_parameters(self.parameters)


@dataclass(frozen=True, slots=True)
class IndicatorValue:
    indicator_value_id: IndicatorValueId
    indicator_definition_id: IndicatorDefinitionId
    etf_id: ETFId
    session_date: date
    value: Decimal
    computed_at: datetime


class Dimension(str, Enum):
    """The scoring dimensions this reference implementation supports.

    Deliberately a minimal placeholder (two values) proving the scoring
    engine mechanism -- not a real dimension taxonomy. Adding real
    dimensions later is a pure data change (new enum members + a migration
    updating the CHECK constraint), not an architectural one."""

    MOMENTUM = "MOMENTUM"
    VALUE = "VALUE"


@dataclass(frozen=True, slots=True)
class ScoringProfile:
    scoring_profile_id: ScoringProfileId
    name: str
    version: int
    parameters: str  # build with serialize_parameters(), never json.dumps() directly
    created_at: datetime

    def __post_init__(self) -> None:
        _validate_canonical_parameters(self.parameters)


@dataclass(frozen=True, slots=True)
class Score:
    score_id: ScoreId
    etf_id: ETFId
    scoring_profile_id: ScoringProfileId
    session_date: date
    overall_score: Decimal
    computed_at: datetime


@dataclass(frozen=True, slots=True)
class DimensionScore:
    score_id: ScoreId
    dimension: Dimension
    value: Decimal
    computed_at: datetime
