-- Phase 0 foundation schema: Calendar, TradingSession, ETF, PriceBar,
-- IngestionRun, PipelineState.

-- Calendar metadata. Sessions live in TradingSession, keyed by calendar_id.
CREATE TABLE IF NOT EXISTS Calendar (
    calendar_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timezone TEXT NOT NULL
);

-- Sessions for a given calendar. Not a full exchange calendar engine and no
-- holiday calculation logic: callers are responsible for populating the
-- sessions they need.
CREATE TABLE IF NOT EXISTS TradingSession (
    calendar_id TEXT NOT NULL REFERENCES Calendar (calendar_id),
    session_date TEXT NOT NULL,
    is_trading_day INTEGER NOT NULL CHECK (is_trading_day IN (0, 1)),
    close_time_utc TEXT,
    PRIMARY KEY (calendar_id, session_date)
);

CREATE TABLE IF NOT EXISTS ETF (
    etf_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    currency TEXT NOT NULL,
    calendar_id TEXT NOT NULL REFERENCES Calendar (calendar_id),
    created_at TEXT NOT NULL
);

-- Raw market data. Append-only: see immutability triggers below.
CREATE TABLE IF NOT EXISTS PriceBar (
    price_bar_id TEXT PRIMARY KEY,
    etf_id TEXT NOT NULL REFERENCES ETF (etf_id),
    session_date TEXT NOT NULL,
    open_amount TEXT NOT NULL,
    high_amount TEXT NOT NULL,
    low_amount TEXT NOT NULL,
    close_amount TEXT NOT NULL,
    volume INTEGER NOT NULL CHECK (volume >= 0),
    currency TEXT NOT NULL,
    source TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pricebar_etf_session
    ON PriceBar (etf_id, session_date);

CREATE TABLE IF NOT EXISTS IngestionRun (
    ingestion_run_id TEXT PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    pipeline_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT,
    -- A run is 'running' if and only if it has no completed_at: a run can
    -- never be left half-finished (a terminal status with no completion
    -- timestamp, or a timestamp on a still-running row).
    CHECK ((status = 'running') = (completed_at IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_ingestionrun_pipeline_status
    ON IngestionRun (pipeline_name, status, pipeline_date);

-- Explicit pipeline progress, one row per logical pipeline. Updated only
-- after a full pipeline run completes successfully; failed runs never
-- touch it. IngestionRun above remains the full, untouched execution
-- history -- this table is the derived "current progress" pointer.
CREATE TABLE IF NOT EXISTS PipelineState (
    pipeline_name TEXT PRIMARY KEY,
    last_successful_session TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Raw data immutability. PriceBar is insert-only: corrections must be
-- inserted as new records, never updated or deleted in place. The same
-- pattern must be applied to future raw tables (macro observations,
-- sentiment observations) when they are introduced.
CREATE TRIGGER IF NOT EXISTS trg_pricebar_no_update
BEFORE UPDATE ON PriceBar
BEGIN
    SELECT RAISE(ABORT, 'PriceBar is immutable raw data: UPDATE is not allowed, insert a new record instead');
END;

CREATE TRIGGER IF NOT EXISTS trg_pricebar_no_delete
BEFORE DELETE ON PriceBar
BEGIN
    SELECT RAISE(ABORT, 'PriceBar is immutable raw data: DELETE is not allowed, insert a new record instead');
END;
