"""``cfm`` command-line entry point. ``measure`` (M0) runs one fixed, hand-chosen
flag set through the mechanical pipeline; ``mine`` (M1) runs the full rule-based
search (doc/DESIGN.md sec. 6 Phases 1-5) end to end for one benchmark.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import db, orchestrator
from .agents.knowledge_agent import known_flags_for_cluster
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
        help="rule-based flag search (doc/DESIGN.md sec. 6 Phases 1-6): baseline, "
             "screen, confirm, greedy-combine, PGO + microarch multipliers",
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
    mine.add_argument(
        "--skip-pgo", action="store_true",
        help="skip Phase 6's real two-pass PGO multiplier trial (doc/DESIGN.md sec. 6) -- "
             "roughly 2x a normal confirmation's build cost (an instrumented build, a "
             "training run, and an optimized rebuild), useful for a cheaper/faster "
             "focused run",
    )
    mine.add_argument(
        "--skip-microarch", action="store_true",
        help="skip Phase 6's microarch multiplier trial (doc/DESIGN.md sec. 6) -- the "
             "detected host's -march=/-mtune= pair, layered on top of whatever PGO left "
             "behind",
    )
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
        # run_one_trial() only calls finish_experiment() itself on an unhandled
        # exception (spec_agent.py's own try/except) -- a normal return here,
        # even a build-failed/validate-failed one, means the single trial ran
        # to completion without crashing, same "converged" meaning `cfm mine`
        # already uses for a run that found nothing to accept. Without this,
        # every standalone `cfm measure` call leaves its own one-off experiment
        # stuck at status='running' forever, since nothing else ever closes it
        # out (caught 2026-08-25 via a real stale row from an earlier ad hoc
        # verification call -- CLAUDE.md's Non-obvious traps log).
        conn = db.connect(cfg.db_path)
        try:
            db.finish_experiment(conn, result["experiment_id"], status="converged")
        finally:
            conn.close()
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
                    remaining_budget = max(args.max_trials - len(baseline.trial_ids), 0)
                    if len(candidates) > remaining_budget:
                        budget_exhausted = True
                    candidates = candidates[:remaining_budget]

                # doc/DESIGN.md sec. 8 (M4): cross-benchmark knowledge transfer.
                # A candidate with a real *accepted* prior in this benchmark's
                # own cluster (baseline.resource_dominance) skips Phase 3's
                # screening trial entirely -- "already been screened once,
                # elsewhere" -- going straight to Phase 4 confirmation
                # (confirm_known_candidates()); everything else (a rejected
                # prior, or no prior at all) still goes through the normal
                # screen-then-confirm flow unchanged.
                cluster_key = baseline.resource_dominance or "unknown"
                known_flags = {}
                if candidates:  # skip the lookup entirely when there's nothing to split
                    known_flags = {
                        k.flag: k for k in known_flags_for_cluster(cfg, cluster_key=cluster_key)
                    }
                    for k in known_flags.values():
                        print(
                            f"info: known prior for {k.flag!r} in cluster {cluster_key!r} -- "
                            f"{'accepted' if k.has_accepted_track_record else 'rejected'} before "
                            f"(mean {k.mean_delta_pct:+.2f}%, n={k.n_trials}, last seen on "
                            f"{k.last_benchmark!r})"
                        )
                fast_tracked, remaining_candidates = orchestrator.split_candidates_by_known_prior(
                    candidates, known_flags,
                )

                screened = orchestrator.screen_candidates(
                    cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                    baseline=baseline, candidates=remaining_candidates,
                )
                confirmed = orchestrator.confirm_candidates(
                    cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                    baseline=baseline, screened=screened,
                )
                confirmed_known = orchestrator.confirm_known_candidates(
                    cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                    baseline=baseline, candidates=fast_tracked,
                )
                combination = orchestrator.greedy_combine(
                    cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                    baseline=baseline, confirmed=confirmed_known + confirmed,
                )

                pgo_result = None
                if not args.skip_pgo:
                    pgo_result = orchestrator.run_pgo_multiplier(
                        cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                        baseline=baseline, combination=combination, compiler=compiler,
                    )

                microarch_result = None
                if not args.skip_microarch:
                    # Chains off pgo_result when PGO ran (layering microarch on
                    # top of *whatever PGO left behind*, both real compounding
                    # multipliers stacking) -- falls back to combination
                    # (Phase 5's own result) when --skip-pgo was passed.
                    # run_microarch_multiplier() duck-types this argument, only
                    # reading .winning_flags/.winning_ci -- both CombinationResult
                    # and MultiplierResult expose them under the same names.
                    microarch_result = orchestrator.run_microarch_multiplier(
                        cfg, experiment_id=baseline.experiment_id, benchmark=args.benchmark,
                        baseline=baseline, combination=pgo_result or combination,
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

        # pgo_result/microarch_result are None only when their own --skip-* flag
        # was passed -- otherwise Phase 6 always runs (possibly skipping the
        # trial itself as implausible/inapplicable, still a MultiplierResult
        # either way), so winning_flags/winning_ci already collapse back to the
        # prior stage's own when a multiplier wasn't attempted or didn't win
        # (run_pgo_multiplier()/run_microarch_multiplier()'s own docstrings).
        # microarch_result chains off pgo_result (or combination, if PGO was
        # skipped) already, so its own winning_flags/winning_ci is always the
        # final answer once both multipliers have had their turn.
        if microarch_result:
            final_flags, final_ci = microarch_result.winning_flags, microarch_result.winning_ci
        elif pgo_result:
            final_flags, final_ci = pgo_result.winning_flags, pgo_result.winning_ci
        else:
            final_flags, final_ci = combination.winning_flags, combination.winning_ci
        gain_pct = (final_ci.mean - baseline.ci.mean) / baseline.ci.mean * 100.0
        summary = {
            "experiment_id": baseline.experiment_id,
            "benchmark": args.benchmark,
            "baseline_flags": baseline.flags,
            "baseline_ratio_mean": baseline.ci.mean,
            # The actual reference point Phase 3 screening compares against
            # (BaselineResult.most_recent_ratio, not the mean above) -- surfaced
            # directly so a future stale-baseline suspicion is checkable from a
            # run's own summary JSON, not just by querying cfm.db (CLAUDE.md's
            # Non-obvious traps log, 2026-08-24 sealcrypto entry).
            "baseline_most_recent_calibration_ratio": baseline.most_recent_ratio,
            "baseline_resource_dominance": baseline.resource_dominance,
            # M2's own "margin" signal (cfm/compilers/gcc.py's ranking pass) --
            # surfaced here for the same reason as every other baseline shape
            # field: a run's own summary JSON should show what its candidate
            # ordering was actually based on, not just the values downstream of it.
            "baseline_resource_dominance_pct": baseline.resource_dominance_pct,
            "baseline_vectorization_density": baseline.vectorization_density,
            "baseline_allocation_pressure": baseline.allocation_pressure,
            "baseline_characterization_source": baseline.characterization_source,
            "candidates_screened": len(screened),
            "candidates_confirmed": sum(1 for c in confirmed + confirmed_known if c.accepted),
            "candidates_fast_tracked_from_prior_knowledge": [c.flag for c in fast_tracked],
            "combination_winning_flags": combination.winning_flags,
            "combination_winning_ratio_mean": combination.winning_ci.mean,
            "pgo_attempted": pgo_result.attempted if pgo_result else False,
            "pgo_skip_reason": pgo_result.skip_reason if pgo_result else "--skip-pgo",
            "pgo_accepted": bool(pgo_result and pgo_result.outcome and pgo_result.outcome.accepted),
            "microarch_attempted": microarch_result.attempted if microarch_result else False,
            "microarch_skip_reason": microarch_result.skip_reason if microarch_result else "--skip-microarch",
            "microarch_accepted": bool(
                microarch_result and microarch_result.outcome and microarch_result.outcome.accepted
            ),
            "winning_flags": final_flags,
            "winning_ratio_mean": final_ci.mean,
            "gain_vs_baseline_pct": gain_pct,
            "budget_exhausted": budget_exhausted,
        }
        print(json.dumps(summary, indent=2, default=str))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
