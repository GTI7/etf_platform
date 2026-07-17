"""The exact pipeline_name conventions run_pipeline()-based stages use.

Kept in one place, shared by every write-side stage and by any read-side
query needing to resolve the same name, so the two can never drift apart.
Changing any of these strings would break backwards compatibility with
already-stored IngestionRun rows -- treat them as fixed once released, the
same discipline migrations/README.md already applies to frozen schema.
"""

from __future__ import annotations


def price_ingestion_pipeline_name(ticker: str) -> str:
    return f"price_ingestion:{ticker}"


def indicator_pipeline_name(indicator_name: str, indicator_version: int, ticker: str) -> str:
    return f"indicator:{indicator_name}:v{indicator_version}:{ticker}"


def scoring_pipeline_name(profile_name: str, profile_version: int, ticker: str) -> str:
    return f"scoring:{profile_name}:v{profile_version}:{ticker}"
