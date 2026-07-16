-- Phase 3 additive schema: ScoringProfile, Score, DimensionScore.
-- 0001 and 0002 are frozen (see migrations/README.md); this migration
-- only adds.

-- One row per (name, version, parameters) triple, same discipline as
-- IndicatorDefinition (0002). A methodology change is a new version,
-- never an edit to an existing row. `parameters` must always be built
-- with core.analytics.domain.models.serialize_parameters
-- (json.dumps(..., sort_keys=True)). Insert-only by discipline, like
-- IndicatorDefinition -- no DB trigger, protected only by UNIQUE.
CREATE TABLE IF NOT EXISTS ScoringProfile (
    scoring_profile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    parameters TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (name, version, parameters)
);

-- One overall score per (etf, scoring_profile, session). Append-only,
-- like PriceBar/IndicatorValue: recomputation under changed methodology
-- ties to a new ScoringProfile version, never an UPDATE. UNIQUE here is a
-- defense-in-depth backstop -- the primary idempotency mechanism is the
-- orchestration layer checking get_score() before computing anything, so
-- a rerun never even attempts to insert a duplicate Score or an orphaned
-- DimensionScore referencing a Score that was skipped.
CREATE TABLE IF NOT EXISTS Score (
    score_id TEXT PRIMARY KEY,
    etf_id TEXT NOT NULL REFERENCES ETF (etf_id),
    scoring_profile_id TEXT NOT NULL REFERENCES ScoringProfile (scoring_profile_id),
    session_date TEXT NOT NULL,
    overall_score TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    UNIQUE (etf_id, scoring_profile_id, session_date)
);

CREATE INDEX IF NOT EXISTS idx_score_etf_profile_session
    ON Score (etf_id, scoring_profile_id, session_date);

-- One row per (score, dimension) -- no separate surrogate id, since a
-- DimensionScore has no identity independent of the Score it belongs to.
-- 'dimension' is the Dimension enum's value; the CHECK constraint mirrors
-- how IngestionRun.status backs the IngestionStatus enum.
CREATE TABLE IF NOT EXISTS DimensionScore (
    score_id TEXT NOT NULL REFERENCES Score (score_id),
    dimension TEXT NOT NULL CHECK (dimension IN ('MOMENTUM', 'VALUE')),
    value TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (score_id, dimension)
);

-- Raw computed output is immutable, same pattern as PriceBar/IndicatorValue.
CREATE TRIGGER IF NOT EXISTS trg_score_no_update
BEFORE UPDATE ON Score
BEGIN
    SELECT RAISE(ABORT, 'Score is immutable: UPDATE is not allowed, recompute under a new ScoringProfile version instead');
END;

CREATE TRIGGER IF NOT EXISTS trg_score_no_delete
BEFORE DELETE ON Score
BEGIN
    SELECT RAISE(ABORT, 'Score is immutable: DELETE is not allowed, recompute under a new ScoringProfile version instead');
END;

CREATE TRIGGER IF NOT EXISTS trg_dimensionscore_no_update
BEFORE UPDATE ON DimensionScore
BEGIN
    SELECT RAISE(ABORT, 'DimensionScore is immutable: UPDATE is not allowed, recompute under a new ScoringProfile version instead');
END;

CREATE TRIGGER IF NOT EXISTS trg_dimensionscore_no_delete
BEFORE DELETE ON DimensionScore
BEGIN
    SELECT RAISE(ABORT, 'DimensionScore is immutable: DELETE is not allowed, recompute under a new ScoringProfile version instead');
END;
