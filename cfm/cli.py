"""``cfm`` command-line entry point. M0 scope only: ``measure`` runs one fixed,
hand-chosen flag set through the mechanical pipeline (doc/DESIGN.md sec. 14 M0).
There is no ``cfm mine`` (the search-driving command doc/DESIGN.md sec. 6
describes) yet -- that needs the orchestrator phase machine, M1.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import db
from .agents.spec_agent import run_one_trial
from .config import CfmConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cfm",
        description=(
            "compiler-flag-miner -- M0 scope only, see doc/DESIGN.md sec. 14. "
            "No search/hypothesis/LLM yet."
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
        )
        try:
            result = run_one_trial(
                cfg, benchmark=args.benchmark, flags=args.flags.split(),
                tune=args.tune, iterations=args.iterations,
            )
        except RuntimeError as exc:
            print(f"cfm measure: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("build_status") == "ok" else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
