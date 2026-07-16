from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from core.analytics.domain.models import (
    IndicatorDefinition,
    InsufficientPriceHistoryError,
    ScoringProfile,
    serialize_parameters,
)
from core.domain.exceptions import DomainError


def test_serialize_parameters_is_key_order_independent() -> None:
    a = {"window": 20, "field": "close"}
    b = {"field": "close", "window": 20}

    assert serialize_parameters(a) == serialize_parameters(b)


def test_insufficient_price_history_error_is_a_domain_error() -> None:
    assert issubclass(InsufficientPriceHistoryError, DomainError)


def test_indicator_definition_accepts_canonical_parameters() -> None:
    IndicatorDefinition(
        indicator_definition_id=uuid.uuid4().hex,
        name="SMA",
        version=1,
        parameters=serialize_parameters({"window": 20}),
        created_at=datetime.now(timezone.utc),
    )  # does not raise


def test_indicator_definition_rejects_non_canonical_parameters() -> None:
    non_canonical = json.dumps({"window": 20, "field": "close"})  # no sort_keys

    with pytest.raises(ValueError):
        IndicatorDefinition(
            indicator_definition_id=uuid.uuid4().hex,
            name="SMA",
            version=1,
            parameters=non_canonical,
            created_at=datetime.now(timezone.utc),
        )


def test_indicator_definition_rejects_malformed_json() -> None:
    with pytest.raises(ValueError):
        IndicatorDefinition(
            indicator_definition_id=uuid.uuid4().hex,
            name="SMA",
            version=1,
            parameters="{not valid json",
            created_at=datetime.now(timezone.utc),
        )


def test_indicator_definition_rejects_non_str_parameters() -> None:
    with pytest.raises(TypeError):
        IndicatorDefinition(
            indicator_definition_id=uuid.uuid4().hex,
            name="SMA",
            version=1,
            parameters=None,  # type: ignore[arg-type]
            created_at=datetime.now(timezone.utc),
        )


def test_scoring_profile_accepts_canonical_parameters() -> None:
    ScoringProfile(
        scoring_profile_id=uuid.uuid4().hex,
        name="REFERENCE",
        version=1,
        parameters=serialize_parameters(
            {"dimensions": {"MOMENTUM": {"indicator_name": "SMA", "indicator_version": 1}}}
        ),
        created_at=datetime.now(timezone.utc),
    )  # does not raise


def test_scoring_profile_rejects_non_canonical_parameters() -> None:
    non_canonical = json.dumps({"z": 1, "a": 2})  # no sort_keys

    with pytest.raises(ValueError):
        ScoringProfile(
            scoring_profile_id=uuid.uuid4().hex,
            name="REFERENCE",
            version=1,
            parameters=non_canonical,
            created_at=datetime.now(timezone.utc),
        )


def test_scoring_profile_rejects_malformed_json() -> None:
    with pytest.raises(ValueError):
        ScoringProfile(
            scoring_profile_id=uuid.uuid4().hex,
            name="REFERENCE",
            version=1,
            parameters="not json at all",
            created_at=datetime.now(timezone.utc),
        )


def test_scoring_profile_rejects_non_str_parameters() -> None:
    with pytest.raises(TypeError):
        ScoringProfile(
            scoring_profile_id=uuid.uuid4().hex,
            name="REFERENCE",
            version=1,
            parameters=None,  # type: ignore[arg-type]
            created_at=datetime.now(timezone.utc),
        )
