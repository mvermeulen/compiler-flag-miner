"""SPEC Runner agent, M0 scope -- doc/DESIGN.md sec. 14 M0: "given one fixed,
hand-chosen flag set, generate a real peak config, build, run under wspy-run, and
get one validated, wspy-measured ratio." ``run_one_trial`` is that pipeline end to
end, with every step's outcome persisted to cfm.db regardless of result -- a
build/validate failure is still a real trial record (doc/DESIGN.md sec. 6 Phase 4's
"a documented negative result is exactly the kind of learning that should
transfer"), never silently dropped.

The other named agents in doc/DESIGN.md sec. 13's proposed layout
(``knowledge_agent``, ``hypothesis_agent``, ``report_agent``) don't exist yet --
they're M2/M3 scope, where there's an actual search loop and knowledge base for them
to operate over.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from .. import db
from ..config import CfmConfig
from ..instrumentation.wspy import WspyInstrumentation
from ..workloads.spec_cpu2026 import SpecCpu2026Workload


def new_run_id() -> str:
    # Sortable-by-time like wspy-run's own default run-id shape, without needing to
    # be byte-identical to it -- we always pass --run-id explicitly.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def run_one_trial(
    cfg: CfmConfig,
    *,
    benchmark: str,
    flags: list[str],
    tune: str = "peak",
    iterations: int = 3,
    phase: str = "screening",
    experiment_id: Optional[int] = None,
) -> dict:
    workload = SpecCpu2026Workload(cfg.spec_dir, cfg.spec_config)
    run_index_path = cfg.output_root / "cpu2026" / "run-index.jsonl"
    instrumentation = WspyInstrumentation(
        cfg.wspy_dir,
        store_db=cfg.output_root / "store.db",
        run_index_path=run_index_path,
        hostname=cfg.hostname,
    )

    problems = instrumentation.preflight()
    if problems:
        raise RuntimeError("wspy preflight failed:\n  " + "\n  ".join(problems))

    conn = db.connect(cfg.db_path)
    try:
        if experiment_id is None:
            experiment_id = db.create_experiment(
                conn, benchmark=benchmark, hostname=cfg.hostname, compiler="gcc",
            )

        config_path = workload.generate_config(benchmark, tune, flags)
        optimize_string = " ".join(flags)

        build_result = workload.build(benchmark, tune, config_path)
        if not build_result.ok:
            trial_id = db.record_trial(
                conn, experiment_id=experiment_id, phase=phase, flags=flags,
                optimize_string=optimize_string, build_status="build-failed",
            )
            return {
                "experiment_id": experiment_id, "trial_id": trial_id,
                "build_status": "build-failed", "build_output": build_result.raw_output,
            }

        run_id = new_run_id()
        command = workload.run_command(benchmark, tune, config_path, iterations=iterations)
        signature = instrumentation.characterize(
            command=command, suite="cpu2026", benchmark=benchmark, run_id=run_id,
            profile=cfg.wspy_profile, output_root=cfg.output_root,
        )
        run_result = workload.parse_result(benchmark, tune, signature.raw_output)

        build_status = "ok" if run_result.ok else "validate-failed"
        trial_id = db.record_trial(
            conn, experiment_id=experiment_id, phase=phase, flags=flags,
            optimize_string=optimize_string, build_status=build_status,
            wspy_run_ref=signature.wspy_run_ref, ratio=run_result.ratio,
        )

        return {
            "experiment_id": experiment_id, "trial_id": trial_id,
            "build_status": build_status, "wspy_run_ref": signature.wspy_run_ref,
            "wspy_validated": signature.validated, "spec_validated": run_result.validated,
            "resource_dominance": signature.resource_dominance, "ratio": run_result.ratio,
        }
    finally:
        conn.close()
