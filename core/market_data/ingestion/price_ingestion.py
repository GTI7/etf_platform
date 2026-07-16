from __future__ import annotations

import sqlite3
import uuid
from datetime import date

from core.market_data.domain.models import ETF, PriceBar
from core.market_data.ingestion.pipeline_run import run_pipeline
from core.market_data.persistence.repository import insert_price_bar, is_trading_day
from core.market_data.providers.base import DataProvider
from core.shared.clock import Clock
from core.shared.money import Money


def ingest_daily_prices(
    conn: sqlite3.Connection,
    clock: Clock,
    provider: DataProvider,
    etf: ETF,
    session_date: date,
) -> str:
    """Ingest one ETF's price bar for one trading session from `provider`.

    TradingCalendar-aware: a `session_date` that is not a trading day on the
    ETF's calendar is a no-op success -- there is nothing to ingest -- and
    the pipeline watermark still advances past it. This is one pipeline run
    per (etf, session_date): the provider fetch happens inside the run, but
    outside any DB transaction; every write it causes (PriceBar inserts,
    run completion, watermark advance) commits or rolls back together as a
    single unit, per run_pipeline's transaction boundary.
    """
    pipeline_name = f"price_ingestion:{etf.ticker}"
    with run_pipeline(conn, clock, pipeline_name, session_date) as ingestion_run_id:
        if is_trading_day(conn, etf.calendar_id, session_date):
            provider_bars = provider.fetch_daily_bars(etf.ticker, session_date, session_date)
            for provider_bar in provider_bars:
                if provider_bar.session_date != session_date:
                    continue
                bar = PriceBar(
                    price_bar_id=uuid.uuid4().hex,
                    etf_id=etf.etf_id,
                    session_date=provider_bar.session_date,
                    open=Money(provider_bar.open, provider_bar.currency),
                    high=Money(provider_bar.high, provider_bar.currency),
                    low=Money(provider_bar.low, provider_bar.currency),
                    close=Money(provider_bar.close, provider_bar.currency),
                    volume=provider_bar.volume,
                    source=provider.name,
                    ingested_at=clock.now(),
                )
                insert_price_bar(conn, bar)
    return ingestion_run_id
