"""cfm.db access -- schema/cfm_schema.sql loaded and applied here, plus typed
accessors for the experiments/trials tables (doc/DESIGN.md sec. 7). Deliberately
thin: every accessor is a direct, obvious SQL statement, no ORM -- same posture
wspy's own Python tools (``web/joblib.py``, ``wspy-store``) take toward SQLite.
"""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "cfm_schema.sql"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(db_path) -> sqlite3.Connection:
    """Opens (creating if needed) db_path and ensures the schema is applied."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Idempotent: schema/cfm_schema.sql uses ``CREATE TABLE IF NOT EXISTS``/
    ``CREATE INDEX IF NOT EXISTS``/``INSERT OR IGNORE`` throughout, so re-running
    this against an already-initialized db is always safe. No migration-step
    dispatch yet (wspy's ``store.c`` STORE_SCHEMA_VERSION pattern is the model to
    follow once cfm.db's schema actually needs to change under existing data --
    see CLAUDE.md's versioning-discipline section).
    """
    conn.executescript(_SCHEMA_PATH.read_text())
    conn.commit()


def create_experiment(
    conn: sqlite3.Connection,
    *,
    benchmark: str,
    hostname: str,
    compiler: str,
    compiler_version: Optional[str] = None,
    target_arch: Optional[str] = None,
    budget_trials: Optional[int] = None,
    budget_wallclock_s: Optional[int] = None,
    status: str = "running",
) -> int:
    cur = conn.execute(
        "INSERT INTO experiments "
        "(benchmark, hostname, compiler, compiler_version, target_arch, started_at, "
        " budget_trials, budget_wallclock_s, status) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            benchmark, hostname, compiler, compiler_version, target_arch,
            utcnow_iso(), budget_trials, budget_wallclock_s, status,
        ),
    )
    conn.commit()
    return cur.lastrowid


def finish_experiment(
    conn: sqlite3.Connection, experiment_id: int, status: str,
    baseline_run_ref: Optional[str] = None,
) -> None:
    conn.execute(
        "UPDATE experiments SET status=?, finished_at=?, "
        "baseline_run_ref=COALESCE(?, baseline_run_ref) WHERE id=?",
        (status, utcnow_iso(), baseline_run_ref, experiment_id),
    )
    conn.commit()


def set_baseline_run_ref(conn: sqlite3.Connection, experiment_id: int, baseline_run_ref: str) -> None:
    """Records Phase 1's baseline reference on a still-*running* experiment --
    deliberately not ``finish_experiment()`` reused with ``status="running"``,
    which would also unconditionally stamp ``finished_at`` (that column means what
    it says: the experiment actually ending, doc/DESIGN.md sec. 6 Phase 7). A
    single-purpose UPDATE avoids that side effect entirely.
    """
    conn.execute(
        "UPDATE experiments SET baseline_run_ref=? WHERE id=?",
        (baseline_run_ref, experiment_id),
    )
    conn.commit()


def record_trial(
    conn: sqlite3.Connection,
    *,
    experiment_id: int,
    phase: str,
    flags: list[str],
    optimize_string: str,
    build_status: str,
    wspy_run_ref: Optional[str] = None,
    ratio: Optional[float] = None,
    delta_vs_baseline_pct: Optional[float] = None,
    verdict: Optional[str] = None,
    ci_overlap: Optional[bool] = None,
    wallclock_s: Optional[float] = None,
    parent_trial_id: Optional[int] = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO trials "
        "(experiment_id, phase, parent_trial_id, flags_json, optimize_string, "
        " build_status, wspy_run_ref, ratio, delta_vs_baseline_pct, verdict, "
        " ci_overlap, wallclock_s, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            experiment_id, phase, parent_trial_id, json.dumps(flags), optimize_string,
            build_status, wspy_run_ref, ratio, delta_vs_baseline_pct, verdict,
            None if ci_overlap is None else int(ci_overlap), wallclock_s, utcnow_iso(),
        ),
    )
    conn.commit()
    return cur.lastrowid


def update_trial_verdict(
    conn: sqlite3.Connection,
    trial_id: int,
    *,
    verdict: str,
    delta_vs_baseline_pct: Optional[float] = None,
    ci_overlap: Optional[bool] = None,
) -> None:
    """Sets a trial row's verdict/delta_vs_baseline_pct/ci_overlap after the fact
    -- these can't be known at ``record_trial()``'s insert time.
    ``agents.spec_agent.run_one_trial()`` creates the row immediately as each
    individual measurement completes, before the orchestrator has aggregated a
    candidate's repeated confirmation-stage trials into one accept/reject decision
    (doc/DESIGN.md sec. 6 Phase 4) -- this is the update that applies that decision
    to every trial row that contributed to it.
    """
    conn.execute(
        "UPDATE trials SET verdict=?, delta_vs_baseline_pct=?, ci_overlap=? WHERE id=?",
        (verdict, delta_vs_baseline_pct, None if ci_overlap is None else int(ci_overlap), trial_id),
    )
    conn.commit()


def get_experiment(conn: sqlite3.Connection, experiment_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
    return dict(row) if row else None


def list_trials(conn: sqlite3.Connection, experiment_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM trials WHERE experiment_id=? ORDER BY id", (experiment_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def list_trials_by_phase(conn: sqlite3.Connection, experiment_id: int, phase: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM trials WHERE experiment_id=? AND phase=? ORDER BY id",
        (experiment_id, phase),
    ).fetchall()
    return [dict(row) for row in rows]


def record_hypothesis(
    conn: sqlite3.Connection,
    *,
    trial_id: int,
    proposed_by: str,
    rationale: str,
    evidence_json: Optional[str] = None,
    confidence: Optional[float] = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO hypotheses (trial_id, proposed_by, rationale, evidence_json, confidence) "
        "VALUES (?,?,?,?,?)",
        (trial_id, proposed_by, rationale, evidence_json, confidence),
    )
    conn.commit()
    return cur.lastrowid


def _welford_update(
    old_mean: float, old_stddev: float, old_n: int, new_value: float,
) -> tuple[float, float]:
    """Incremental sample mean/stddev (``n-1`` denominator, matching
    ``cfm/stats.py``'s convention) computed from the stored aggregates alone --
    reconstructs the running sum-of-squared-differences from ``old_stddev``/
    ``old_n`` rather than needing a dedicated schema column to carry it between
    calls. Standard Welford's-algorithm update, applied one observation at a time.
    """
    new_n = old_n + 1
    delta = new_value - old_mean
    new_mean = old_mean + delta / new_n
    old_m2 = (old_stddev ** 2) * (old_n - 1) if old_n >= 2 else 0.0
    new_m2 = old_m2 + delta * (new_value - new_mean)
    new_stddev = math.sqrt(new_m2 / (new_n - 1)) if new_n >= 2 else 0.0
    return new_mean, new_stddev


def upsert_knowledge(
    conn: sqlite3.Connection,
    *,
    cluster_key: str,
    compiler: str,
    compiler_version: Optional[str],
    target_arch: Optional[str],
    flag: str,
    accepted: bool,
    delta_pct: float,
    last_benchmark: str,
) -> None:
    """Records one trial's outcome against (cluster_key, compiler, compiler_version,
    target_arch, flag) -- the cross-benchmark "retained learning" table
    (doc/DESIGN.md sec. 8). A documented negative result (``accepted=False``)
    updates ``n_trials``/``mean_delta_pct``/``stddev_delta_pct`` exactly like a
    positive one, only ``n_accepted`` differs -- "a documented negative result is
    exactly the kind of learning that should transfer" (doc/DESIGN.md sec. 6
    Phase 4). Looks up the existing row with SQL ``IS`` (not ``=``) against
    ``compiler_version``/``target_arch`` so a row where either is legitimately
    ``NULL`` is still found on a repeat call -- and updates it **by id** rather
    than an ``INSERT ... ON CONFLICT(...)``: SQLite's (standard SQL's) ``UNIQUE``
    constraint never treats two ``NULL``s as conflicting, so ``ON CONFLICT`` simply
    never fires for a row with a ``NULL`` ``compiler_version``/``target_arch`` --
    it would silently insert a duplicate row every call instead of accumulating
    into the one that already exists. Caught by
    ``test_upsert_knowledge_null_compiler_version_and_target_arch_still_upserts``,
    not by inspection.
    """
    existing = conn.execute(
        "SELECT id, n_trials, n_accepted, mean_delta_pct, stddev_delta_pct FROM knowledge "
        "WHERE cluster_key=? AND compiler=? AND compiler_version IS ? AND target_arch IS ? "
        "  AND flag=?",
        (cluster_key, compiler, compiler_version, target_arch, flag),
    ).fetchone()

    if existing is None:
        conn.execute(
            "INSERT INTO knowledge "
            "(cluster_key, compiler, compiler_version, target_arch, flag, n_trials, "
            " n_accepted, mean_delta_pct, stddev_delta_pct, last_benchmark, last_updated) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                cluster_key, compiler, compiler_version, target_arch, flag, 1,
                1 if accepted else 0, delta_pct, 0.0, last_benchmark, utcnow_iso(),
            ),
        )
    else:
        new_mean, new_stddev = _welford_update(
            existing["mean_delta_pct"], existing["stddev_delta_pct"] or 0.0,
            existing["n_trials"], delta_pct,
        )
        conn.execute(
            "UPDATE knowledge SET n_trials=?, n_accepted=?, mean_delta_pct=?, "
            "  stddev_delta_pct=?, last_benchmark=?, last_updated=? WHERE id=?",
            (
                existing["n_trials"] + 1, existing["n_accepted"] + (1 if accepted else 0),
                new_mean, new_stddev, last_benchmark, utcnow_iso(), existing["id"],
            ),
        )
    conn.commit()
