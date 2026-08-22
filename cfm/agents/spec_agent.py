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

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from .. import db
from ..config import CfmConfig
from ..instrumentation.base import InstrumentationBackend
from ..instrumentation.wspy import WspyInstrumentation
from ..workloads.base import WorkloadBackend
from ..workloads.spec_cpu2026 import SpecCpu2026Workload


def new_run_id() -> str:
    # Sortable-by-time like wspy-run's own default run-id shape, without needing to
    # be byte-identical to it -- we always pass --run-id explicitly.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


# GCC rewrites these before recording them into .GCC.command.line (-march=native/
# -mtune=native expand into dozens of concrete -m*/--param= flags, e.g.
# "-march=znver5 -mmmx -mpopcnt ..." -- confirmed live, 2026-08-21, no literal
# "native" survives anywhere in the recording) -- a literal substring check
# against these two specifically would always report "missing" even on a
# perfectly correct build, so audit_compiled_flags()'s check skips them rather
# than raising a false alarm.
_AUDIT_UNVERIFIABLE_LITERAL_FLAGS = frozenset({"-march=native", "-mtune=native"})


# Confirmed live, 2026-08-22 (CLAUDE.md's Non-obvious traps log): a real GCC
# ".GCC.command.line" dump for a genuinely-optimized build always has exactly
# one of these. Its complete absence is a strong, cheap, generic signal that
# something upstream handed this trial a flags list with no -O level at all --
# exactly the shape of the screen_candidates()/confirm_candidates() bug this
# same investigation found (candidate flags tested in total isolation, never
# combined with the baseline's own -O3). This check doesn't know or care
# *why* -O is missing -- it would catch a similar mistake in a future caller
# just as well, not just this one.
_OPTIMIZATION_LEVEL_RE = re.compile(r"-O(?:0|1|2|3|s|g|z|fast)\b")


def _summarize_compiled_flags_audit(flags: list[str], audit_dump: str) -> str:
    """Best-effort literal-substring check of each requested flag against
    audit_compiled_flags()'s raw `.GCC.command.line` dump -- confirms what SPEC
    actually compiled with, independent of runcpu's own "Build successes"
    report (CLAUDE.md's Non-obvious traps log, 2026-08-21 basepeak entry, on
    why that report alone isn't sufficient). Not a hard pass/fail signal: every
    catalog flag *other* than the two in _AUDIT_UNVERIFIABLE_LITERAL_FLAGS
    (-flto, -fprofile-*, -freorder-*, -fno-semantic-interposition,
    -mprefer-vector-width=N, ...) is recorded by GCC verbatim, so a real
    substring match is meaningful for them.

    Also flags -- loudly, unconditionally -- if no `-O` optimization level
    shows up in the compiled binary at all, regardless of whether one was
    expected in `flags`. This is deliberately *not* gated on `flags` itself
    containing an `-O` entry: the whole point is to catch a case where the
    caller's own `flags` list was already wrong (missing the baseline's own
    `-O3`) before anyone has to notice by manually diffing two trials' audit
    rows against each other, which is what actually happened the first time
    (2026-08-22).
    """
    found, missing, skipped = [], [], []
    for flag in flags:
        if flag in _AUDIT_UNVERIFIABLE_LITERAL_FLAGS:
            skipped.append(flag)
        elif flag in audit_dump:
            found.append(flag)
        else:
            missing.append(flag)
    parts = []
    if found:
        parts.append(f"confirmed compiled in: {found}")
    if missing:
        parts.append(f"NOT FOUND in compiled binary (see CLAUDE.md's basepeak trap): {missing}")
    if skipped:
        parts.append(f"not independently checkable (GCC expands these before recording): {skipped}")
    if not _OPTIMIZATION_LEVEL_RE.search(audit_dump):
        parts.append(
            "⚠ WARNING: no -O optimization level found in the compiled binary at all -- "
            "this trial's build very likely got no real optimization (see CLAUDE.md's Non-obvious "
            "traps log, 2026-08-22 entry on screen_candidates()/confirm_candidates() once testing a "
            "candidate flag in total isolation from the baseline's own -O3)"
        )
    return "compiled-flags audit -- " + "; ".join(parts)


# wspy's system.c prints "cpu temp             XX.X C" (SYSTEM_TEMP, on by
# default in system_mask, present whenever a profile passes --system -- every
# "quick"-profile trial already does, cfm/orchestrator.py's CALIBRATION_PROFILE/
# SCREENING_PROFILE both being "quick"). This data has been sitting in every
# trial's own RunSignature.raw_output all along -- not a new collection
# mechanism, just the first time anything parses it out. Motivated by a real
# 2026-08-21 near-incident (CLAUDE.md's Non-obvious traps log): an ad hoc
# verification script that bypassed cfm/lock.py briefly ran two concurrent
# SPECrate builds and got the host to the edge of OOM again -- a per-trial
# thermal record, squirreled away cheaply, is exactly the kind of data that
# would help debug a "why did this run's later trials look different" question
# after the fact, without needing to actively gate/wait on it mid-run (which
# risks adding untested blocking logic to an unattended overnight run before a
# sensible threshold/timeout exists to tune it against).
_CPU_TEMP_RE = re.compile(r"cpu temp\s+([\d.]+)\s*C", re.IGNORECASE)


def _extract_cpu_temp_c(raw_output: str) -> Optional[float]:
    match = _CPU_TEMP_RE.search(raw_output)
    return float(match.group(1)) if match else None


def run_one_trial(
    cfg: CfmConfig,
    *,
    benchmark: str,
    flags: list[str],
    tune: str = "peak",
    iterations: int = 3,
    phase: str = "screening",
    profile: Optional[str] = None,
    experiment_id: Optional[int] = None,
    parent_trial_id: Optional[int] = None,
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> dict:
    """``workload``/``instrumentation`` are injectable (defaulting to the real
    ``SpecCpu2026Workload``/``WspyInstrumentation`` backends built from ``cfg``) so
    ``cfm/orchestrator.py``'s tests can pass in fakes conforming to
    ``workloads.base.WorkloadBackend``/``instrumentation.base.InstrumentationBackend``
    and exercise the orchestrator's phase logic with no real SPEC/wspy calls --
    ``cfm measure`` (``cli.py``) and every M0 caller keep working unchanged, since
    both default to ``None``. ``profile`` overrides ``cfg.wspy_profile`` for this
    one call -- the orchestrator needs a different wspy profile per phase (``quick``
    for screening and calibration, ``deep-cpu`` for baseline's one-off
    characterization rep, doc/DESIGN.md sec. 6 and sec. 14 M2.5 item 2),
    which a single fixed ``cfg.wspy_profile`` can't express across calls sharing one
    ``CfmConfig``. ``parent_trial_id`` is passed straight through to
    ``db.record_trial()`` -- doc/DESIGN.md sec. 6 Phase 5's greedy-combination
    lineage (``trials.parent_trial_id``), unused before M1's confirmation stage.
    """
    workload = workload or SpecCpu2026Workload(cfg.spec_dir, cfg.spec_config)
    run_index_path = cfg.output_root / "cpu2026" / "run-index.jsonl"
    instrumentation = instrumentation or WspyInstrumentation(
        cfg.wspy_dir,
        store_db=cfg.output_root / "store.db",
        run_index_path=run_index_path,
    )
    profile = profile or cfg.wspy_profile

    problems = instrumentation.preflight()
    if problems:
        raise RuntimeError("wspy preflight failed:\n  " + "\n  ".join(problems))

    conn = db.connect(cfg.db_path)
    try:
        if experiment_id is None:
            experiment_id = db.create_experiment(
                conn, benchmark=benchmark, hostname=cfg.hostname, compiler="gcc",
            )

        try:
            config_path = workload.generate_config(benchmark, tune, flags)
            optimize_string = " ".join(flags)

            build_result = workload.build(benchmark, tune, config_path)
            if not build_result.ok:
                trial_id = db.record_trial(
                    conn, experiment_id=experiment_id, phase=phase, flags=flags,
                    optimize_string=optimize_string, build_status="build-failed",
                    parent_trial_id=parent_trial_id,
                )
                return {
                    "experiment_id": experiment_id, "trial_id": trial_id,
                    "build_status": "build-failed", "build_output": build_result.raw_output,
                }

            run_id = new_run_id()
            command = workload.run_command(benchmark, tune, config_path, iterations=iterations)
            signature = instrumentation.characterize(
                command=command, suite="cpu2026", benchmark=benchmark, run_id=run_id,
                profile=profile, output_root=cfg.output_root,
            )
            run_result = workload.parse_result(benchmark, tune, signature.raw_output)

            build_status = "ok" if run_result.ok else "validate-failed"
            trial_id = db.record_trial(
                conn, experiment_id=experiment_id, phase=phase, flags=flags,
                optimize_string=optimize_string, build_status=build_status,
                wspy_run_ref=signature.wspy_run_ref, ratio=run_result.ratio,
                parent_trial_id=parent_trial_id,
            )

            # Independent audit of what SPEC actually compiled with, not just
            # what runcpu's own "Build successes" report claims -- see
            # workloads/spec_cpu2026.py's audit_compiled_flags() docstring and
            # CLAUDE.md's Non-obvious traps log (2026-08-21 basepeak entry) for
            # why that report alone wasn't enough once already. getattr-guarded
            # since fake WorkloadBackends in tests don't implement this
            # (optional, degrade-gracefully signal, never load-bearing for the
            # trial's own build_status).
            audit_fn = getattr(workload, "audit_compiled_flags", None)
            if audit_fn is not None:
                audit_dump = audit_fn(benchmark, tune)
                if audit_dump is not None:
                    db.record_hypothesis(
                        # proposed_by="rule": schema/cfm_schema.sql's hypotheses.proposed_by
                        # CHECK constraint only allows ('rule','analogical','llm') -- this is
                        # a deterministic, rule-based check like every other hypothesis this
                        # module records, not a fundamentally new category; the "compiled-flags
                        # audit --" rationale prefix is what distinguishes it at a glance.
                        conn, trial_id=trial_id, proposed_by="rule",
                        rationale=_summarize_compiled_flags_audit(flags, audit_dump),
                    )

            # Per-trial thermal record -- see _extract_cpu_temp_c()'s own
            # comment for why this is worth squirreling away even though
            # nothing here actively gates or waits on it.
            cpu_temp_c = _extract_cpu_temp_c(signature.raw_output)
            if cpu_temp_c is not None:
                db.record_hypothesis(
                    conn, trial_id=trial_id, proposed_by="rule",
                    rationale=f"host cpu_temp at measurement: {cpu_temp_c:.1f} C",
                )

            return {
                "experiment_id": experiment_id, "trial_id": trial_id,
                "build_status": build_status, "wspy_run_ref": signature.wspy_run_ref,
                "wspy_validated": signature.validated, "spec_validated": run_result.validated,
                "resource_dominance": signature.resource_dominance,
                "vectorization_density": signature.vectorization_density,
                "allocation_pressure": signature.allocation_pressure,
                "ratio": run_result.ratio,
                "cpu_temp_c": cpu_temp_c,
            }
        except Exception:
            # An unhandled exception here (not a build/validate *failure*, which
            # is itself a normal, recorded trial outcome above) means this trial
            # blew up in a way nothing downstream can recover from -- every
            # orchestrator phase (screen/confirm/combine) lets such an exception
            # propagate straight out to `cfm mine`'s CLI handler with no
            # per-candidate catch, so the whole experiment is aborting regardless
            # of which call raised. Mark it `failed` here, at the one place that
            # always knows the experiment_id, rather than leaving the row stuck
            # at `running` forever (CLAUDE.md's Non-obvious traps log,
            # 2026-08-20 entry -- this is exactly the gap that entry flagged).
            db.finish_experiment(conn, experiment_id, status="failed")
            raise
    finally:
        conn.close()
