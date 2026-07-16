from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from core.shared.ids import ETFId
from core.shared.money import Money


@dataclass(frozen=True, slots=True)
class ETF:
    etf_id: ETFId
    ticker: str
    name: str
    currency: str
    calendar_id: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Calendar:
    calendar_id: str
    name: str
    exchange: str
    timezone: str


@dataclass(frozen=True, slots=True)
class TradingSession:
    calendar_id: str
    session_date: date
    is_trading_day: bool
    close_time_utc: datetime | None


@dataclass(frozen=True, slots=True)
class PriceBar:
    price_bar_id: str
    etf_id: ETFId
    session_date: date
    open: Money
    high: Money
    low: Money
    close: Money
    volume: int
    source: str
    ingested_at: datetime


class IngestionStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class IngestionRun:
    ingestion_run_id: str
    pipeline_name: str
    pipeline_date: date
    status: IngestionStatus
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None


@dataclass(frozen=True, slots=True)
class PipelineState:
    pipeline_name: str
    last_successful_session: date
    updated_at: datetime
