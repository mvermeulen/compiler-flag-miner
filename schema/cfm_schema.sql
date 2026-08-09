-- cfm.db schema -- compiler-flag-miner's own experiment/trial/knowledge state.
-- See doc/DESIGN.md section 7 for the design rationale. Deliberately separate from
-- wspy's own store.db (schema owned by wspy, ingested via `wspy-store --run-index`):
-- this file never duplicates counter data, only references wspy runs by
-- "hostname:run_id" foreign keys, the same boundary wspy-testpoint's own runs.json
-- draws against wspy-store. Not yet wired to any code -- schema-first, so the
-- orchestrator/db.py layer (doc/DESIGN.md section 13) has a stable target to build
-- typed accessors against.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
INSERT OR IGNORE INTO schema_meta(key, value) VALUES ('schema_version', '1');

-- One mining run against one benchmark, one compiler, one host.
CREATE TABLE IF NOT EXISTS experiments (
  id                 INTEGER PRIMARY KEY,
  benchmark          TEXT NOT NULL,          -- e.g. '706.stockfish_r'
  hostname           TEXT NOT NULL,
  compiler           TEXT NOT NULL,          -- 'gcc'
  compiler_version   TEXT,
  target_arch        TEXT,                   -- detected microarch, e.g. 'znver4'
  started_at         TEXT NOT NULL,          -- ISO-8601 UTC
  finished_at        TEXT,
  budget_trials      INTEGER,
  budget_wallclock_s INTEGER,
  status             TEXT NOT NULL DEFAULT 'running'
                      CHECK (status IN ('running','converged','budget-exhausted','failed')),
  baseline_run_ref   TEXT                    -- 'hostname:run_id' into wspy's store.db
);

-- One SPEC build+run attempt for one candidate flag set.
CREATE TABLE IF NOT EXISTS trials (
  id                     INTEGER PRIMARY KEY,
  experiment_id          INTEGER NOT NULL REFERENCES experiments(id),
  phase                  TEXT NOT NULL
                         CHECK (phase IN ('screening','confirmation','combination','multiplier')),
  parent_trial_id        INTEGER REFERENCES trials(id),  -- greedy-combination lineage (sec. 6 Phase 5)
  flags_json             TEXT NOT NULL,       -- exact flag list tried, JSON array of strings
  optimize_string        TEXT NOT NULL,       -- rendered OPTIMIZE line, for reproducibility
  build_status           TEXT NOT NULL
                         CHECK (build_status IN ('ok','build-failed','validate-failed')),
  wspy_run_ref           TEXT,                -- 'hostname:run_id', null if build failed
  ratio                  REAL,                -- SPEC estimated ratio/score, null if invalid
  delta_vs_baseline_pct  REAL,
  verdict                TEXT
                         CHECK (verdict IS NULL OR verdict IN ('accept','reject','inconclusive')),
  ci_overlap             INTEGER,             -- 0/1, from wspy-summary's CI comparison
  wallclock_s            REAL,
  created_at             TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trials_experiment ON trials(experiment_id);
CREATE INDEX IF NOT EXISTS idx_trials_verdict ON trials(verdict);

-- Rationale trail: why a trial was proposed.
CREATE TABLE IF NOT EXISTS hypotheses (
  id             INTEGER PRIMARY KEY,
  trial_id       INTEGER NOT NULL REFERENCES trials(id),
  proposed_by    TEXT NOT NULL CHECK (proposed_by IN ('rule','analogical','llm')),
  rationale      TEXT NOT NULL,
  evidence_json  TEXT,                        -- counter/signature snapshot that motivated it
  confidence     REAL
);
CREATE INDEX IF NOT EXISTS idx_hypotheses_trial ON hypotheses(trial_id);

-- Cross-benchmark generalization table -- the actual "retained learning"
-- (doc/DESIGN.md section 8). Keyed by archetype cluster, not benchmark name.
CREATE TABLE IF NOT EXISTS knowledge (
  id               INTEGER PRIMARY KEY,
  cluster_key      TEXT NOT NULL,             -- wspy-archetype resource_dominance label,
                                               -- or a --kmeans centroid id once available
  compiler         TEXT NOT NULL,
  compiler_version TEXT,                      -- scope by version; see DESIGN.md sec. 11/15
  target_arch      TEXT,                      -- scope by microarch family
  flag             TEXT NOT NULL,
  n_trials         INTEGER NOT NULL DEFAULT 0,
  n_accepted       INTEGER NOT NULL DEFAULT 0,
  mean_delta_pct   REAL,
  stddev_delta_pct REAL,
  last_benchmark   TEXT,
  last_updated     TEXT NOT NULL,
  UNIQUE(cluster_key, compiler, compiler_version, target_arch, flag)
);
CREATE INDEX IF NOT EXISTS idx_knowledge_cluster ON knowledge(cluster_key);
