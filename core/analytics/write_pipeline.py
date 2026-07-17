from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from core.analytics.domain.models import IndicatorDefinition, ScoringProfile
from core.analytics.indicator_calculation import calculate_rsi, calculate_sma
from core.analytics.scoring_pipeline import calculate_score
from core.market_data.domain.models import ETF
from core.market_data.ingestion.price_ingestion import ingest_daily_prices
from core.market_data.persistence.repository import get_price_bars
from core.market_data.providers.base import DataProvider
from core.shared.clock import Clock


@dataclass(frozen=True, slots=True)
class WritePipelineResult:
    """The four run ids produced by one run_write_pipeline() call.

    Nothing new is persisted -- this only surfaces identifiers the four
    stage functions already produce. price_ingestion_run_id is None when
    the ingestion stage was skipped (a PriceBar already existed for this
    exact etf/session_date); the other three are never skipped by
    run_write_pipeline itself, so they are only absent if an exception
    propagated before this result was constructed.
    """

    price_ingestion_run_id: str | None
    sma_run_id: str
    rsi_run_id: str
    score_run_id: str


def run_write_pipeline(
    conn: sqlite3.Connection,
    clock: Clock,
    provider: DataProvider,
    etf: ETF,
    session_date: date,
    sma_definition: IndicatorDefinition,
    rsi_definition: IndicatorDefinition,
    scoring_profile: ScoringProfile,
) -> WritePipelineResult:
    """Compose the existing write-side stages for one ETF and one trading
    session: ingest prices -> calculate SMA -> calculate RSI -> calculate
    score.

    Orchestration only -- no SQL, no calculation logic, and no
    transaction of its own. Each stage below owns exactly one
    run_pipeline call already; this function only decides which stage to
    call next, never wraps more than one stage's writes together. A
    single call therefore produces up to four independent, sequential
    transactions, never one meta-transaction across stages.

    Ingestion idempotency: `ingest_daily_prices` has no storage-level
    dedup of its own (PriceBar carries no UNIQUE constraint), so this
    function skips it when a PriceBar already exists for this exact
    (etf_id, session_date) -- checked directly via get_price_bars(),
    never via a pipeline watermark. A watermark is a monotonic MAX
    (advance_pipeline_watermark) and does not distinguish an
    already-ingested session from an earlier, never-ingested backfill
    session that merely sits before a later watermark; only an exact
    existence check is correct under out-of-order/backfill execution.
    This check protects only this composed path -- ingest_daily_prices()
    called directly is unchanged from v0.5.0. SMA, RSI, and scoring are
    called unconditionally on every invocation: each is already
    idempotent by construction (ON CONFLICT DO NOTHING / an explicit
    get_score() guard), so no additional pre-check is added for them.

    Fail-fast: the first stage to raise propagates immediately and no
    later stage runs. Earlier stages' commits are not undone -- retrying
    only re-attempts the failed stage onward, since ingestion, SMA, and
    scoring are all independently idempotent-safe to call again.
    """
    existing_bars = get_price_bars(conn, etf.etf_id, start_date=session_date, end_date=session_date)
    price_ingestion_run_id = (
        None if existing_bars else ingest_daily_prices(conn, clock, provider, etf, session_date)
    )

    sma_run_id = calculate_sma(conn, clock, etf, sma_definition, session_date)
    rsi_run_id = calculate_rsi(conn, clock, etf, rsi_definition, session_date)
    score_run_id = calculate_score(conn, clock, etf, scoring_profile, session_date)

    return WritePipelineResult(
        price_ingestion_run_id=price_ingestion_run_id,
        sma_run_id=sma_run_id,
        rsi_run_id=rsi_run_id,
        score_run_id=score_run_id,
    )
