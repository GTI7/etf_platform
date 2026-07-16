from __future__ import annotations

from core.analytics.domain.models import Dimension, MissingIndicatorValueError
from core.domain.exceptions import DomainError


def test_missing_indicator_value_error_is_a_domain_error() -> None:
    assert issubclass(MissingIndicatorValueError, DomainError)


def test_dimension_values_are_stable_strings() -> None:
    assert Dimension.MOMENTUM.value == "MOMENTUM"
    assert Dimension.VALUE.value == "VALUE"


def test_dimension_round_trips_through_its_value() -> None:
    assert Dimension("MOMENTUM") is Dimension.MOMENTUM
