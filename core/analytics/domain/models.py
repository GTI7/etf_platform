from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import NewType

from core.domain.exceptions import DomainError
from core.shared.ids import ETFId

# Defined locally rather than in core/shared/ids.py: these identify
# analytics-only entities and have no reuse outside this package.
IndicatorDefinitionId = NewType("IndicatorDefinitionId", str)
IndicatorValueId = NewType("IndicatorValueId", str)


class InsufficientPriceHistoryError(DomainError):
    """Raised when a window calculation needs N trading sessions of price
    history for an ETF and fewer than N are actually available -- whether
    because the ETF genuinely doesn't have that much history yet, or
    because the TradingCalendar hasn't been populated that far back.
    Deliberately not distinguished: both cases mean the window cannot be
    computed correctly, and both must fail loudly rather than silently
    produce a shorter, mislabeled window."""


def serialize_parameters(parameters: dict[str, object]) -> str:
    """Canonical JSON serialization for IndicatorDefinition.parameters.

    Always sort_keys=True: two logically identical parameter dicts must
    always produce the same string, or the UNIQUE(name, version,
    parameters) constraint silently stops meaning what it says.
    """
    return json.dumps(parameters, sort_keys=True)


@dataclass(frozen=True, slots=True)
class IndicatorDefinition:
    indicator_definition_id: IndicatorDefinitionId
    name: str
    version: int
    parameters: str  # build with serialize_parameters(), never json.dumps() directly
    created_at: datetime


@dataclass(frozen=True, slots=True)
class IndicatorValue:
    indicator_value_id: IndicatorValueId
    indicator_definition_id: IndicatorDefinitionId
    etf_id: ETFId
    session_date: date
    value: Decimal
    computed_at: datetime
