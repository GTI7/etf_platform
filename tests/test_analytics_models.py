from __future__ import annotations

from core.analytics.domain.models import InsufficientPriceHistoryError, serialize_parameters
from core.domain.exceptions import DomainError


def test_serialize_parameters_is_key_order_independent() -> None:
    a = {"window": 20, "field": "close"}
    b = {"field": "close", "window": 20}

    assert serialize_parameters(a) == serialize_parameters(b)


def test_insufficient_price_history_error_is_a_domain_error() -> None:
    assert issubclass(InsufficientPriceHistoryError, DomainError)
