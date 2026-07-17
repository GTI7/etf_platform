from __future__ import annotations

from core.shared.pipeline_names import (
    indicator_pipeline_name,
    price_ingestion_pipeline_name,
    scoring_pipeline_name,
)


def test_price_ingestion_pipeline_name_exact_format() -> None:
    assert price_ingestion_pipeline_name("SPY") == "price_ingestion:SPY"


def test_indicator_pipeline_name_exact_format() -> None:
    assert indicator_pipeline_name("SMA", 1, "SPY") == "indicator:SMA:v1:SPY"


def test_indicator_pipeline_name_differs_by_version() -> None:
    assert indicator_pipeline_name("SMA", 1, "SPY") != indicator_pipeline_name("SMA", 2, "SPY")


def test_scoring_pipeline_name_exact_format() -> None:
    assert scoring_pipeline_name("REFERENCE", 1, "SPY") == "scoring:REFERENCE:v1:SPY"


def test_scoring_pipeline_name_differs_by_ticker() -> None:
    assert scoring_pipeline_name("REFERENCE", 1, "SPY") != scoring_pipeline_name("REFERENCE", 1, "QQQ")
