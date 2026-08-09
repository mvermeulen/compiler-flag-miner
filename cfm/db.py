"""cfm.db access -- schema/cfm_schema.sql loaded and applied here, plus typed
accessors for the experiments/trials tables (doc/DESIGN.md sec. 7). Deliberately
thin: every accessor is a direct, obvious SQL statement, no ORM -- same posture
wspy's own Python tools (``web/joblib.py``, ``wspy-store``) take toward SQLite.
"""

from __future__ import annotations

import json
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


def get_experiment(conn: sqlite3.Connection, experiment_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
    return dict(row) if row else None


def list_trials(conn: sqlite3.Connection, experiment_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM trials WHERE experiment_id=? ORDER BY id", (experiment_id,)
    ).fetchall()
    return [dict(row) for row in rows]
