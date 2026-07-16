-- Phase 2 additive schema: IndicatorDefinition, IndicatorValue.
-- 0001 is frozen (see migrations/README.md); this migration only adds.

-- One row per (name, version, parameters) triple. A calculation-logic
-- change is a new version, never an edit to an existing row. `parameters`
-- must always be built with core.analytics.domain.models.serialize_parameters
-- (json.dumps(..., sort_keys=True)) so the UNIQUE constraint below actually
-- catches duplicates instead of being silently bypassed by key ordering.
CREATE TABLE IF NOT EXISTS IndicatorDefinition (
    indicator_definition_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    parameters TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (name, version, parameters)
);

-- Raw computed output. Append-only, like PriceBar: recomputation under
-- changed logic ties to a new IndicatorDefinition version, never an
-- UPDATE of an existing row. UNIQUE + immutability together give
-- idempotent writes: a rerun of the same (definition, etf, session) is a
-- no-op insert, never a duplicate and never a silent overwrite.
CREATE TABLE IF NOT EXISTS IndicatorValue (
    indicator_value_id TEXT PRIMARY KEY,
    indicator_definition_id TEXT NOT NULL REFERENCES IndicatorDefinition (indicator_definition_id),
    etf_id TEXT NOT NULL REFERENCES ETF (etf_id),
    session_date TEXT NOT NULL,
    value TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    UNIQUE (indicator_definition_id, etf_id, session_date)
);

CREATE INDEX IF NOT EXISTS idx_indicatorvalue_definition_etf_session
    ON IndicatorValue (indicator_definition_id, etf_id, session_date);

CREATE TRIGGER IF NOT EXISTS trg_indicatorvalue_no_update
BEFORE UPDATE ON IndicatorValue
BEGIN
    SELECT RAISE(ABORT, 'IndicatorValue is immutable: UPDATE is not allowed, recompute under a new IndicatorDefinition version instead');
END;

CREATE TRIGGER IF NOT EXISTS trg_indicatorvalue_no_delete
BEFORE DELETE ON IndicatorValue
BEGIN
    SELECT RAISE(ABORT, 'IndicatorValue is immutable: DELETE is not allowed, recompute under a new IndicatorDefinition version instead');
END;
