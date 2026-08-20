"""``cfm`` command-line entry point. ``measure`` (M0) runs one fixed, hand-chosen
flag set through the mechanical pipeline; ``mine`` (M1) runs the full rule-based
search (doc/DESIGN.md sec. 6 Phases 1-5) end to end for one benchmark.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import db, orchestrator
from .agents.spec_agent import run_one_trial
from .compilers.gcc import GccCompiler
from .config import CfmConfig
from .lock import host_lock


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cfm",
        description=(
            "compiler-flag-miner -- see doc/DESIGN.md sec. 14. M1: rule-based "
            "search only (Phases 1-5), no signature-aware filtering (M2) or LLM "
            "(M3) yet."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    measure = sub.add_parser(
        "measure",
        help="build+run+measure one SPEC CPU2026 benchmark with one fixed flag set",
    )
    measure.add_argument("benchmark", help="e.g. 706.stockfish_r")
    measure.add_argument(
        "--flags", required=True,
        help="space-separated OPTIMIZE flags, e.g. '-O3 -march=native -flto'",
    )
    measure.add_argument(
        "--tune", default="peak", choices=["peak"],
        help="v1 mines peak only (doc/DESIGN.md sec. 15); base tuning is M6",
    )
    measure.add_argument("--iterations", type=int, default=3)
    measure.add_argument("--spec-dir", default=None)
    measure.add_argument("--spec-config", default=None)
    measure.add_argument("--wspy-dir", default=None)
    measure.add_argument("--output-root", default=None)
    measure.add_argument("--db", dest="db_path", default=None)
    measure.add_argument("--wspy-profile", default=None)
    measure.add_argument("--lock-file", default=None)

    mine = sub.add_parser(
        "mine",
        help="rule-based flag search (doc/DESIGN.md sec. 6 Phases 1-5): baseline, "
             "screen, confirm, greedy-combine",
    )
    mine.add_argument("benchmark", help="e.g. 706.stockfish_r")
    mine.add_argument(
        "--base-flags", default="-O3",
        help="starting/baseline OPTIMIZE flags (default: '-O3')",
    )
    mine.add_argument(
        "--max-trials", type=int, default=None,
        help="best-effort budget ceiling (doc/DESIGN.md sec. 5/11) -- caps Phase "
             "2's candidate list, the pipeline's widest fan-out point; Phase "
             "4/5's own trial count still depends on how many of those survive "
             "screening, not separately capped yet. Omit for no cap.",
    )
    mine.add_argument("--catalog", default=None, help="override the GCC flag catalog path")
    mine.add_argument("--spec-dir", default=None)
    mine.add_argument("--spec-config", default=None)
    mine.add_argument("--wspy-dir", default=None)
    mine.add_argument("--output-root", default=None)
    mine.add_argument("--db", dest="db_path", default=None)
    mine.add_argument("--lock-file", default=None)

    init_db = sub.add_parser("init-db", help="create/upgrade cfm.db at the configured path")
    init_db.add_argument("--db", dest="db_path", default=None)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "init-db":
        cfg = CfmConfig.from_env(db_path=args.db_path)
        db.connect(cfg.db_path).close()
        print(f"cfm.db ready at {cfg.db_path}")
        return 0

    if args.command == "measure":
        cfg = CfmConfig.from_env(
            spec_dir=args.spec_dir, spec_config=args.spec_config, wspy_dir=args.wspy_dir,
            output_root=args.output_root, db_path=args.db_path, wspy_profile=args.wspy_profile,
            lock_file=args.lock_file,
        )
        try:
            with host_lock(cfg, command=f"cfm measure {args.benchmark}"):
                result = run_one_trial(
                    cfg, benchmark=args.benchmark, flags=args.flags.split(),
                    tune=args.tune, iterations=args.iterations,
                )
        except RuntimeError as exc:
            print(f"cfm measure: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("build_status") == "ok" else 1

    if args.command == "mine":
        cfg = CfmConfig.from_env(
            spec_dir=args.spec_dir, spec_config=args.spec_config, wspy_dir=args.wspy_dir,
            output_root=args.output_root, db_path=args.db_path, lock_file=args.lock_file,
        )
        compiler = GccCompiler(catalog_path=args.catalog) if args.catalog else GccCompiler()
        base_flags = args.base_flags.split()

        try:
            with host_lock(cfg, command=f"cfm mine {args.benchmark}"):
                baseline = orchestrator.run_baseline(cfg, benchmark=args.benchmark, base_flags=base_flags)

                candidates = orchestrator.generate_candidates(
                    cfg, benchmark=args.benchmark, baseline=baseline, compiler=compiler,
                )
                budget_exhausted = False
                if args.max_trials is not None:
                    remaining = max(args.max_trials - len(baseline.trial_ids), 0)
                    if len(candidates) > remaining:
                        budget_exhausted = True
                    candidates = candidates[:remaining]

                screened = orchestrator.screen_candidates(
                    cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                    baseline=baseline, candidates=candidates,
                )
                confirmed = orchestrator.confirm_candidates(
                    cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                    baseline=baseline, screened=screened,
                )
                combination = orchestrator.greedy_combine(
                    cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                    baseline=baseline, confirmed=confirmed,
                )
        except RuntimeError as exc:
            print(f"cfm mine: {exc}", file=sys.stderr)
            return 1

        conn = db.connect(cfg.db_path)
        try:
            db.finish_experiment(
                conn, baseline.experiment_id,
                status="budget-exhausted" if budget_exhausted else "converged",
            )
        finally:
            conn.close()

        gain_pct = (combination.winning_ci.mean - baseline.ci.mean) / baseline.ci.mean * 100.0
        summary = {
            "experiment_id": baseline.experiment_id,
            "benchmark": args.benchmark,
            "baseline_flags": baseline.flags,
            "baseline_ratio_mean": baseline.ci.mean,
            "baseline_resource_dominance": baseline.resource_dominance,
            "baseline_vectorization_density": baseline.vectorization_density,
            "baseline_allocation_pressure": baseline.allocation_pressure,
            "candidates_screened": len(screened),
            "candidates_confirmed": sum(1 for c in confirmed if c.accepted),
            "winning_flags": combination.winning_flags,
            "winning_ratio_mean": combination.winning_ci.mean,
            "gain_vs_baseline_pct": gain_pct,
            "budget_exhausted": budget_exhausted,
        }
        print(json.dumps(summary, indent=2, default=str))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
