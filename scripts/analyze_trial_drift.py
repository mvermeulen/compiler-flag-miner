#!/usr/bin/env python3
"""Mine cfm.db's own trials/hypotheses tables for run-duration "settling"/drift
signal -- across every past experiment at once, not one doc write-up's manual
eyeballing of one run's trial table at a time.

Why this script exists: four real `cfm mine` runs so far (`782.lbm_r`
2026-08-21, `714.cpython_r` 2026-08-21, `706.stockfish_r` 2026-08-23,
`750.sealcrypto_r` 2026-08-24 -- see each doc/mining_results.*.md) each
independently noticed a "ratio isn't stable through the first several minutes/
hours of a run, and it doesn't track which flag was under test" pattern, in
three different shapes (a multi-hour near-monotonic ramp, a fast-baseline-then-
stable-step, and a fast-settling-then-flat baseline). Only one of the four
(`750.sealcrypto_r`) was actually checked against real thermal telemetry, and
it came back *not* correlated with die temp -- see
doc/settling_baseline_drift_investigation.2026-08-24.md for the full writeup
this script supports.

Every past trial already carries what's needed to look at this systematically
instead of by eye:
  - trials.created_at / trials.ratio / trials.phase / trials.flags_json --
    always present.
  - hypotheses table, rationale text, two best-effort rows per trial
    (agents/spec_agent.py's `_summarize_compiled_flags_audit()` and
    `_extract_cpu_temp_c()`): a "compiled-flags audit -- ..." row and a
    "host cpu_temp at measurement: XX.X C" row. Both were added 2026-08-21/22
    for unrelated reasons (the basepeak/isolated-flags investigations) and
    have been silently accumulating on every trial since, unread until now.

This script joins all three, per experiment, and reports:
  1. A chronological per-trial table (elapsed minutes since the experiment's
     own `started_at`, phase, flags, ratio, cpu_temp_c, any audit WARNING).
  2. Pearson correlation of ratio against elapsed time, and against cpu_temp_c,
     per experiment (only computed when SciPy/NumPy aren't required -- plain
     stdlib arithmetic, consistent with cfm/stats.py's own from-scratch
     approach rather than adding a new dependency for this).
  3. A flag on any trial whose audit row contains the "no -O optimization
     level found" warning, or where cpu_temp_c couldn't be parsed at all
     (missing data point, not a zero).

Deliberately read-only: never writes to cfm.db, opens it in a plain
`sqlite3.connect` without cfm.db.connect()'s own schema-apply side effect
(a report script shouldn't touch a db it's just supposed to be reading).

Usage:
    python3 scripts/analyze_trial_drift.py --db /path/to/cfm.db
    python3 scripts/analyze_trial_drift.py --db cfm.db --experiment 13
    python3 scripts/analyze_trial_drift.py --db cfm.db --csv-dir /tmp/drift_csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # see audit_flags_from_spec_results.py's own comment on why

_CPU_TEMP_RATIONALE_RE = re.compile(r"host cpu_temp at measurement:\s*([\d.]+)\s*C")
_AUDIT_WARNING_MARKER = "⚠ WARNING"  # "⚠ WARNING", matches spec_agent.py's own literal text


def _parse_iso(ts: str) -> datetime:
    """Parses cfm.db's own `utcnow_iso()` format (`%Y-%m-%dT%H:%M:%SZ`, always
    UTC, always second-precision -- see cfm/db.py). Kept permissive (accepts a
    trailing 'Z' or an explicit '+00:00') in case a hand-edited row differs.
    """
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _pearson(xs: list[float], ys: list[float]) -> Optional[float]:
    """Plain-stdlib Pearson correlation coefficient -- no numpy/scipy dependency,
    same posture as cfm/stats.py's own from-scratch confidence-interval math.
    Returns None if there are fewer than 3 points or either series has zero
    variance (a flat series has no defined correlation, not a 0.0 one).
    """
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return cov / (var_x * var_y) ** 0.5


def _list_experiment_ids(conn: sqlite3.Connection) -> list[int]:
    return [row[0] for row in conn.execute("SELECT id FROM experiments ORDER BY id")]


def _fetch_experiment(conn: sqlite3.Connection, experiment_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
    return dict(row) if row else None


def _fetch_trials(conn: sqlite3.Connection, experiment_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM trials WHERE experiment_id=? ORDER BY id", (experiment_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def _fetch_hypotheses_for_trial(conn: sqlite3.Connection, trial_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT rationale FROM hypotheses WHERE trial_id=? ORDER BY id", (trial_id,)
    ).fetchall()
    return [row[0] for row in rows]


def _cpu_temp_from_rationales(rationales: list[str]) -> Optional[float]:
    for r in rationales:
        m = _CPU_TEMP_RATIONALE_RE.search(r)
        if m:
            return float(m.group(1))
    return None


def _audit_warning_from_rationales(rationales: list[str]) -> bool:
    return any(_AUDIT_WARNING_MARKER in r for r in rationales)


def _identify_baseline_trial_ids(trials: list[dict]) -> set[int]:
    """Baseline calibration reps (Phase 1, run_baseline()) are recorded with
    the same phase='confirmation' value ordinary Phase 4 confirmation trials
    use (see cfm/orchestrator.py -- there is no distinct 'baseline' phase in
    the schema's own CHECK constraint) -- distinguished only by being the
    leading run of trials that all share the very first trial's own
    flags_json, since baseline always runs before Phase 2/3/4 chronologically.
    """
    if not trials:
        return set()
    first_flags = trials[0]["flags_json"]
    baseline_ids = set()
    for t in trials:
        if t["flags_json"] != first_flags:
            break
        baseline_ids.add(t["id"])
    return baseline_ids


def analyze_experiment(conn: sqlite3.Connection, experiment_id: int, csv_dir: Optional[Path]) -> None:
    experiment = _fetch_experiment(conn, experiment_id)
    if experiment is None:
        print(f"experiment {experiment_id}: not found", file=sys.stderr)
        return
    trials = _fetch_trials(conn, experiment_id)
    if not trials:
        print(f"experiment {experiment_id} ({experiment['benchmark']}): no trials recorded")
        return

    started_at = _parse_iso(experiment["started_at"])
    baseline_ids = _identify_baseline_trial_ids(trials)

    print(f"\n=== experiment {experiment_id}: {experiment['benchmark']} "
          f"on {experiment['hostname']} (status={experiment['status']}) ===")
    print(f"started_at={experiment['started_at']}  finished_at={experiment['finished_at']}")

    rows = []
    for t in trials:
        rationales = _fetch_hypotheses_for_trial(conn, t["id"])
        cpu_temp_c = _cpu_temp_from_rationales(rationales)
        audit_warning = _audit_warning_from_rationales(rationales)
        created_at = _parse_iso(t["created_at"])
        elapsed_min = (created_at - started_at).total_seconds() / 60.0
        flags = json.loads(t["flags_json"])
        rows.append({
            "trial_id": t["id"],
            "elapsed_min": elapsed_min,
            "phase": "baseline" if t["id"] in baseline_ids else t["phase"],
            "flags": " ".join(flags),
            "ratio": t["ratio"],
            "cpu_temp_c": cpu_temp_c,
            "audit_warning": audit_warning,
            "verdict": t["verdict"],
        })

    print(f"{'trial':>6} {'elapsed_min':>11} {'phase':>12} {'ratio':>9} {'temp_c':>7} "
          f"{'verdict':>8}  flags")
    for r in rows:
        temp_str = f"{r['cpu_temp_c']:.1f}" if r["cpu_temp_c"] is not None else "  n/a"
        ratio_str = f"{r['ratio']:.3f}" if r["ratio"] is not None else "     n/a"
        warn = "  <-- ⚠ audit warning (no -O level found)" if r["audit_warning"] else ""
        print(f"{r['trial_id']:>6} {r['elapsed_min']:>11.1f} {r['phase']:>12} {ratio_str:>9} "
              f"{temp_str:>7} {str(r['verdict']):>8}  {r['flags']}{warn}")

    # Correlations, using only trials with both a real ratio and (for the temp
    # one) a real parsed cpu_temp_c -- a null in either just drops that point,
    # never treated as 0.
    ratio_pairs = [(r["elapsed_min"], r["ratio"]) for r in rows if r["ratio"] is not None]
    temp_pairs = [(r["cpu_temp_c"], r["ratio"]) for r in rows
                  if r["ratio"] is not None and r["cpu_temp_c"] is not None]

    r_elapsed = _pearson([p[0] for p in ratio_pairs], [p[1] for p in ratio_pairs])
    r_temp = _pearson([p[0] for p in temp_pairs], [p[1] for p in temp_pairs])

    def _fmt(v: Optional[float]) -> str:
        return f"{v:+.3f}" if v is not None else "n/a (too few points or a flat series)"

    print(f"\nPearson r(ratio, elapsed_min)  = {_fmt(r_elapsed)}  (n={len(ratio_pairs)})")
    print(f"Pearson r(ratio, cpu_temp_c)   = {_fmt(r_temp)}  (n={len(temp_pairs)})")
    if r_elapsed is not None and abs(r_elapsed) >= 0.5 and (r_temp is None or abs(r_temp) < 0.3):
        print("  -> ratio tracks elapsed time much more tightly than it tracks cpu_temp_c: "
              "consistent with the settling/drift pattern documented in "
              "doc/mining_results.782.lbm_r.2026-08-21.md and "
              "doc/mining_results.750.sealcrypto_r.2026-08-24.md, and NOT primarily thermal "
              "(die-temp) -- see doc/settling_baseline_drift_investigation.2026-08-24.md.")

    if csv_dir is not None:
        csv_dir.mkdir(parents=True, exist_ok=True)
        out_path = csv_dir / f"experiment_{experiment_id}_{experiment['benchmark']}.csv"
        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"  wrote {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True, help="Path to the real cfm.db to read (read-only).")
    parser.add_argument("--experiment", type=int, action="append", default=None,
                         help="Limit to this experiment id (repeatable). Default: every experiment.")
    parser.add_argument("--csv-dir", type=Path, default=None,
                         help="If given, also write one CSV per experiment here for external plotting.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"error: {db_path} does not exist -- run this on the machine that ran `cfm mine`, "
              f"pointed at its real cfm.db (default path is ./cfm.db relative to the cwd `cfm mine` "
              f"was invoked from).", file=sys.stderr)
        return 1

    # Read-only connection (SQLite URI mode) -- deliberately does not go through
    # cfm.db.connect(), which applies schema/cfm_schema.sql as a side effect;
    # a report script shouldn't be able to modify the db it's reading.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    experiment_ids = args.experiment or _list_experiment_ids(conn)
    if not experiment_ids:
        print("no experiments found in this db")
        return 0

    for experiment_id in experiment_ids:
        analyze_experiment(conn, experiment_id, args.csv_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
