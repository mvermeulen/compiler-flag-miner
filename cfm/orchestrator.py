"""Deterministic phase state machine -- doc/DESIGN.md sec. 5-6.

M1 scope (doc/DESIGN.md sec. 14): Phases 1 (baseline), 2 (candidate generation --
trivial, no signature-based filtering yet), and 3 (screening) only. Phase 4
(confirmation)/5 (greedy combination) land in a follow-up PR; Phase 0 (preflight)/
6 (LTO/PGO/microarch multipliers)/7 (finalize+report) are M1-adjacent or later
milestones, not this module's concern yet. No `cfm mine` CLI wiring here either --
that's PR 6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import db
from .agents.spec_agent import run_one_trial
from .compilers.base import FlagCandidate
from .compilers.gcc import GccCompiler, benchmark_languages
from .config import CfmConfig
from .instrumentation.base import InstrumentationBackend
from .stats import ConfidenceInterval, confidence_interval
from .workloads.base import WorkloadBackend

# Repeated-measurement counts, doc/DESIGN.md sec. 6: Phase 1 (baseline) and Phase 4
# (confirmation) both need >=3 confirmation-grade repetitions (wspy-summary's own
# "thin" threshold -- cfm/stats.py's ConfidenceInterval.verdict is "WARN:thin"
# below it). Phase 3 (screening) is deliberately one cheap run each -- "exists to
# prune, not conclude" (doc/DESIGN.md sec. 6 Phase 3).
BASELINE_REPETITIONS = 3
SCREENING_ITERATIONS = 1
CONFIRMATION_PROFILE = "deep-cpu"  # needs PR 1's multi-pass identity fix
SCREENING_PROFILE = "quick"

# Phase 3's prune bar: a candidate whose single screening run's point-estimate
# ratio is more than this many percent *below* the baseline's mean is dropped as
# "clearly worse" without spending a confirmation-grade trial on it. Deliberately
# generous, not a statistical bar -- Phase 3 has no CI to lean on with just one run
# -- so a marginal or noisy-but-plausible result still reaches Phase 4 rather than
# being pruned on a single noisy measurement.
SCREENING_PRUNE_THRESHOLD_PCT = 5.0


@dataclass
class BaselineResult:
    """Phase 1's output: the running baseline every subsequent trial is compared
    against, plus the resource_dominance signature Phase 2 keys off (M2; M1 accepts
    it but doesn't filter on it -- see compilers/base.py's module docstring).
    """

    experiment_id: int
    flags: list[str]
    ratios: list[float]
    ci: ConfidenceInterval
    resource_dominance: Optional[str]
    trial_ids: list[int] = field(default_factory=list)


@dataclass
class ScreeningOutcome:
    """One Phase 3 result. ``survived`` candidates are Phase 4's (PR 5) input --
    everything else, including a build/validate failure, is a documented negative
    result already persisted as a trial + hypothesis row, per doc/DESIGN.md sec. 6
    Phase 4's "a documented negative result is exactly the kind of learning that
    should transfer" (screening failures are exactly as informative as
    confirmation-stage ones for this purpose).
    """

    candidate: FlagCandidate
    trial_id: int
    ratio: Optional[float]
    delta_vs_baseline_pct: Optional[float]
    survived: bool
    reason: str


def run_baseline(
    cfg: CfmConfig,
    *,
    benchmark: str,
    base_flags: list[str],
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> BaselineResult:
    """doc/DESIGN.md sec. 6 Phase 1: build+run the starting configuration at
    confirmation-grade repetition (``BASELINE_REPETITIONS`` separate trials, each
    its own full SPEC build/run/measure cycle, ``deep-cpu`` profile -- PR 1's fix
    is what makes this profile usable at all), establishing the running baseline
    every subsequent trial compares against.
    """
    experiment_id: Optional[int] = None
    trial_ids: list[int] = []
    ratios: list[float] = []
    resource_dominances: list[Optional[str]] = []
    wspy_run_refs: list[str] = []

    for _ in range(BASELINE_REPETITIONS):
        result = run_one_trial(
            cfg, benchmark=benchmark, flags=base_flags, phase="confirmation",
            profile=CONFIRMATION_PROFILE, experiment_id=experiment_id,
            workload=workload, instrumentation=instrumentation,
        )
        experiment_id = result["experiment_id"]
        trial_ids.append(result["trial_id"])
        if result.get("ratio") is not None:
            ratios.append(result["ratio"])
        if result.get("wspy_run_ref"):
            wspy_run_refs.append(result["wspy_run_ref"])
        resource_dominances.append(result.get("resource_dominance"))

    if not ratios:
        raise RuntimeError(
            f"baseline for {benchmark!r} produced no valid ratio across "
            f"{BASELINE_REPETITIONS} repetitions -- see trials {trial_ids} in cfm.db"
        )

    distinct = {rd for rd in resource_dominances if rd is not None}
    if len(distinct) > 1:
        # A real "worth knowing" signal (the host/measurement may be noisy enough
        # to flip the topdown classification between repetitions), not fatal --
        # degrade, don't fail, same posture as elsewhere in this codebase (e.g.
        # instrumentation/wspy.py's check_regression()).
        print(
            f"warning: baseline resource_dominance disagreed across repetitions "
            f"for {benchmark!r}: {resource_dominances}"
        )

    ci = confidence_interval(ratios)
    conn = db.connect(cfg.db_path)
    try:
        if wspy_run_refs:
            db.set_baseline_run_ref(conn, experiment_id, wspy_run_refs[0])
    finally:
        conn.close()

    return BaselineResult(
        experiment_id=experiment_id, flags=base_flags, ratios=ratios, ci=ci,
        resource_dominance=resource_dominances[0] if resource_dominances else None,
        trial_ids=trial_ids,
    )


def generate_candidates(
    cfg: CfmConfig, *, benchmark: str, baseline: BaselineResult,
    compiler: Optional[GccCompiler] = None,
) -> list[FlagCandidate]:
    """doc/DESIGN.md sec. 6 Phase 2, M1 scope: every catalog entry applicable to
    this benchmark's language(s), unranked and unfiltered by signature -- "static
    catalog priors only" (doc/DESIGN.md sec. 14). M2 replaces this with real
    resource_dominance-based filtering/ranking (compilers/base.py's docstring).
    """
    compiler = compiler or GccCompiler()
    languages = benchmark_languages(cfg.spec_dir, benchmark)
    return compiler.candidate_flags_for_signature(baseline.resource_dominance, languages)


def screen_candidates(
    cfg: CfmConfig,
    *,
    experiment_id: int,
    benchmark: str,
    baseline: BaselineResult,
    candidates: list[FlagCandidate],
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> list[ScreeningOutcome]:
    """doc/DESIGN.md sec. 6 Phase 3: each candidate flag tried individually, one
    cheap run at the ``quick`` profile -- prunes only a *clearly* worse point
    estimate against the baseline's mean; no CI needed at this stage ("exists to
    prune, not conclude"). A build/validate failure survives=False too (a real,
    persisted negative result), distinguished from a "measured but worse" reject
    by its ``reason`` text and ``ratio is None``.
    """
    outcomes: list[ScreeningOutcome] = []
    conn = db.connect(cfg.db_path)
    try:
        for candidate in candidates:
            result = run_one_trial(
                cfg, benchmark=benchmark, flags=[candidate.flag], phase="screening",
                profile=SCREENING_PROFILE, iterations=SCREENING_ITERATIONS,
                experiment_id=experiment_id, workload=workload, instrumentation=instrumentation,
            )
            ratio = result.get("ratio")

            if ratio is None:
                outcome = ScreeningOutcome(
                    candidate=candidate, trial_id=result["trial_id"], ratio=None,
                    delta_vs_baseline_pct=None, survived=False,
                    reason=f"no usable ratio (build_status={result['build_status']!r})",
                )
            else:
                delta_pct = (ratio - baseline.ci.mean) / baseline.ci.mean * 100.0
                survived = delta_pct >= -SCREENING_PRUNE_THRESHOLD_PCT
                outcome = ScreeningOutcome(
                    candidate=candidate, trial_id=result["trial_id"], ratio=ratio,
                    delta_vs_baseline_pct=delta_pct, survived=survived,
                    reason=(
                        f"screening ratio {ratio:.6g} vs baseline mean "
                        f"{baseline.ci.mean:.6g} ({delta_pct:+.2f}%)"
                    ),
                )

            db.record_hypothesis(
                conn, trial_id=result["trial_id"], proposed_by="rule", rationale=outcome.reason,
            )
            outcomes.append(outcome)
    finally:
        conn.close()

    return outcomes
