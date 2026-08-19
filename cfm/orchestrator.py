"""Deterministic phase state machine -- doc/DESIGN.md sec. 5-6.

M1 scope (doc/DESIGN.md sec. 14): Phases 1 (baseline), 2 (candidate generation --
trivial, no signature-based filtering yet), 3 (screening), 4 (confirmation), and 5
(greedy combination). Phase 0 (preflight)/6 (LTO/PGO/microarch multipliers)/7
(finalize+report) are M1-adjacent or later milestones, not this module's concern
yet. No `cfm mine` CLI wiring here either -- that's PR 6.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Optional

from . import db
from .agents.spec_agent import run_one_trial
from .compilers.base import FlagCandidate
from .compilers.gcc import GccCompiler, benchmark_languages
from .config import CfmConfig
from .instrumentation.base import InstrumentationBackend
from .stats import ConfidenceInterval, confidence_interval, non_overlapping
from .workloads.base import WorkloadBackend

# Repeated-measurement count, doc/DESIGN.md sec. 6: Phase 1 (baseline) and Phase 4
# (confirmation)/5 (combination) all need >=3 confirmation-grade repetitions
# (wspy-summary's own "thin" threshold -- cfm/stats.py's
# ConfidenceInterval.verdict is "WARN:thin" below it) of the *same* flagset, each
# its own full SPEC build/run/measure cycle. Phase 3 (screening) is deliberately
# one cheap run each -- "exists to prune, not conclude" (doc/DESIGN.md sec. 6
# Phase 3).
#
# doc/DESIGN.md sec. 14 M2.5 item 2: "characterization" (workload shape --
# resource_dominance/vectorization_density/allocation_pressure) and "calibration"
# (the actual ratio) are split into two different wspy profiles/costs, since a
# confirmation-grade deep-cpu trial against a real SPEC benchmark measured in the
# hours on this host (PMU multiplexing -- 6 counter slots can't fit deep-cpu's
# full sweep in one pass) while shape only needs measuring once per baseline, not
# once per repetition. CHARACTERIZATION_* is spent exactly once per baseline
# (_characterize_baseline() below); CALIBRATION_* is what CONFIRMATION_REPETITIONS
# now actually repeats, for baseline (Phase 1) and every Phase 4/5 re-confirmation
# alike -- cheap enough that repeating it CONFIRMATION_REPETITIONS times for a CI
# is affordable where deep-cpu wasn't.
CONFIRMATION_REPETITIONS = 3
SCREENING_ITERATIONS = 1
CHARACTERIZATION_PROFILE = "deep-cpu"  # needs PR 1's multi-pass identity fix
CHARACTERIZATION_ITERATIONS = 1  # shape needs one measurement, not a 3-rep CI --
# the real repetition/robustness for characterization purposes comes from
# deep-cpu's own ~8-way pass-level multiplexing, not from stacking SPEC's own
# iteration count on top of it (confirmed with the user, doc/DESIGN.md sec. 14).
CALIBRATION_PROFILE = "quick"  # same underlying wspy profile as screening's own
# SCREENING_PROFILE -- named separately since the two are semantically distinct
# (screening prunes, calibration measures the number everything else compares
# against), not because they differ mechanically.
CALIBRATION_ITERATIONS = 1  # mirrors SCREENING_ITERATIONS's own reasoning: the
# robustness calibration wants comes from CONFIRMATION_REPETITIONS independent
# quick-profile trials feeding one CI, not from stacking SPEC's own within-trial
# iteration count on top of that too.
SCREENING_PROFILE = "quick"

# Phase 3's prune bar: a candidate whose single screening run's point-estimate
# ratio is more than this many percent *below* the baseline's mean is dropped as
# "clearly worse" without spending a confirmation-grade trial on it. Deliberately
# generous, not a statistical bar -- Phase 3 has no CI to lean on with just one run
# -- so a marginal or noisy-but-plausible result still reaches Phase 4 rather than
# being pruned on a single noisy measurement.
SCREENING_PRUNE_THRESHOLD_PCT = 5.0

# Phase 5's random-pair tournament is bounded to at most this many trials
# regardless of how many flags survived confirmation, "so it doesn't blow the
# budget" (doc/DESIGN.md sec. 6 Phase 5).
MAX_PAIR_TOURNAMENT_TRIALS = 10


@dataclass
class BaselineResult:
    """Phase 1's output: the running baseline every subsequent trial is compared
    against, plus the characterized shape (resource_dominance/vectorization_density/
    allocation_pressure) Phase 2 filters on (doc/DESIGN.md sec. 14 M2.5 item 3) and
    knowledge-transfer upserts key off. ``ci`` is computed only over calibration-
    grade (quick-profile) ratios -- doc/DESIGN.md sec. 14 M2.5 item 2's
    characterization/calibration split, see ``_characterize_baseline()``.
    """

    experiment_id: int
    flags: list[str]
    ratios: list[float]
    ci: ConfidenceInterval
    resource_dominance: Optional[str]
    vectorization_density: Optional[str] = None
    allocation_pressure: Optional[str] = None
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


def _characterize_baseline(
    cfg: CfmConfig,
    *,
    benchmark: str,
    base_flags: list[str],
    workload: Optional[WorkloadBackend],
    instrumentation: Optional[InstrumentationBackend],
) -> dict:
    """doc/DESIGN.md sec. 14 M2.5 item 2: exactly one characterization-grade trial
    (``deep-cpu``, ``CHARACTERIZATION_ITERATIONS`` -- shape needs one measurement,
    not a repetition-based CI) to capture the baseline's ``RunSignature`` fields.
    Deliberately its own function, not inlined into ``run_baseline()``: today this
    is a single local trial (the DESIGN.md-documented fallback for "no
    reference-matrix entry exists yet for this benchmark"), but a future version
    that tries the external reference-matrix corpus first -- shape is expected to
    be portable across similarly-behaved machines even though the ratio never is,
    see this PR's own notes -- only ever needs to replace this one function's
    body; ``run_baseline()`` and everything downstream only consume the resulting
    shape fields, never how they were obtained.
    """
    return run_one_trial(
        cfg, benchmark=benchmark, flags=base_flags, phase="confirmation",
        profile=CHARACTERIZATION_PROFILE, iterations=CHARACTERIZATION_ITERATIONS,
        experiment_id=None, workload=workload, instrumentation=instrumentation,
    )


def run_baseline(
    cfg: CfmConfig,
    *,
    benchmark: str,
    base_flags: list[str],
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> BaselineResult:
    """doc/DESIGN.md sec. 6 Phase 1, sec. 14 M2.5 item 2: one characterization-grade
    trial (``_characterize_baseline()``, shape only -- its ratio is *not* part of
    the CI sample, so a deep-cpu-profile measurement never mixes with quick-profile
    ones in the same statistic) followed by ``CONFIRMATION_REPETITIONS``
    calibration-grade trials (``quick`` profile, cheap enough to repeat for a real
    CI where ``deep-cpu`` wasn't) establishing the running baseline every
    subsequent trial compares against.
    """
    char_result = _characterize_baseline(
        cfg, benchmark=benchmark, base_flags=base_flags,
        workload=workload, instrumentation=instrumentation,
    )
    experiment_id = char_result["experiment_id"]
    resource_dominance = char_result.get("resource_dominance")
    vectorization_density = char_result.get("vectorization_density")
    allocation_pressure = char_result.get("allocation_pressure")
    trial_ids: list[int] = [char_result["trial_id"]]

    ratios: list[float] = []
    wspy_run_refs: list[str] = []
    for _ in range(CONFIRMATION_REPETITIONS):
        result = run_one_trial(
            cfg, benchmark=benchmark, flags=base_flags, phase="confirmation",
            profile=CALIBRATION_PROFILE, iterations=CALIBRATION_ITERATIONS,
            experiment_id=experiment_id, workload=workload, instrumentation=instrumentation,
        )
        trial_ids.append(result["trial_id"])
        if result.get("ratio") is not None:
            ratios.append(result["ratio"])
        if result.get("wspy_run_ref"):
            wspy_run_refs.append(result["wspy_run_ref"])

    if not ratios:
        raise RuntimeError(
            f"baseline for {benchmark!r} produced no valid ratio across "
            f"{CONFIRMATION_REPETITIONS} calibration repetitions -- see trials "
            f"{trial_ids} in cfm.db"
        )

    ci = confidence_interval(ratios)
    conn = db.connect(cfg.db_path)
    try:
        if wspy_run_refs:
            # The first *calibration* trial's ref, not the characterization
            # trial's -- everything else this experiment measures/compares is a
            # calibration-profile (quick) run too, so this stays apples-to-apples
            # for whatever wspy-summary --check-regression does with it.
            db.set_baseline_run_ref(conn, experiment_id, wspy_run_refs[0])
    finally:
        conn.close()

    return BaselineResult(
        experiment_id=experiment_id, flags=base_flags, ratios=ratios, ci=ci,
        resource_dominance=resource_dominance,
        vectorization_density=vectorization_density,
        allocation_pressure=allocation_pressure,
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


@dataclass
class ConfirmationOutcome:
    """One Phase 4/5 result: ``flags`` is the exact flagset re-confirmed (a single
    candidate's flag for Phase 4, a cumulative or pair set for Phase 5). ``ci`` is
    ``None`` iff every repetition failed to produce a usable ratio -- a real,
    persisted negative result (each repetition's own trial row already recorded
    why), rejected outright since there's nothing to compute a CI from.
    """

    flags: list[str]
    trial_ids: list[int]
    ratios: list[float]
    ci: Optional[ConfidenceInterval]
    delta_vs_baseline_pct: Optional[float]
    accepted: bool
    reason: str


def _summarize_regression(rows: list[dict]) -> str:
    if not rows:
        return "check_regression: no baseline history yet (or run not found)"
    flagged = [r for r in rows if r["status"] in ("above", "below") or r["baseline_verdict"].startswith("WARN")]
    if not flagged:
        return f"check_regression: {len(rows)} metric(s) checked, all within baseline range"
    parts = [f"{r['metric']}={r['status']}/{r['baseline_verdict']}" for r in flagged]
    return f"check_regression: {len(flagged)}/{len(rows)} metric(s) flagged: {', '.join(parts)}"


def _confirm_flagset(
    cfg: CfmConfig,
    *,
    experiment_id: int,
    benchmark: str,
    baseline: BaselineResult,
    flags: list[str],
    phase: str,
    compare_ci: ConfidenceInterval,
    parent_trial_id: Optional[int] = None,
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> ConfirmationOutcome:
    """Shared confirmation-grade measurement + accept/reject machinery for both
    Phase 4 (doc/DESIGN.md sec. 6, one candidate flag re-run against the
    *baseline*) and Phase 5 (a cumulative or pair flagset re-run against the
    *current running set* -- ``compare_ci`` is which of those two this call means,
    letting Phase 5 re-use this unchanged rather than duplicating it).
    """
    trial_results = []
    for _ in range(CONFIRMATION_REPETITIONS):
        trial_results.append(run_one_trial(
            cfg, benchmark=benchmark, flags=flags, phase=phase,
            profile=CALIBRATION_PROFILE, iterations=CALIBRATION_ITERATIONS,
            experiment_id=experiment_id,
            parent_trial_id=parent_trial_id, workload=workload, instrumentation=instrumentation,
        ))

    trial_ids = [r["trial_id"] for r in trial_results]
    ratios = [r["ratio"] for r in trial_results if r.get("ratio") is not None]

    if not ratios:
        ci = None
        delta_pct = None
        accepted = False
        build_statuses = [r["build_status"] for r in trial_results]
        reason = (
            f"no usable ratio across {CONFIRMATION_REPETITIONS} repetitions "
            f"(build_status={build_statuses})"
        )
    else:
        ci = confidence_interval(ratios)
        delta_pct = (ci.mean - compare_ci.mean) / compare_ci.mean * 100.0
        accepted = non_overlapping(compare_ci, ci) and ci.mean > compare_ci.mean
        reason = (
            f"{phase} mean {ci.mean:.6g} (n={ci.n}, 95% CI [{ci.low:.6g}, {ci.high:.6g}]) vs "
            f"comparison mean {compare_ci.mean:.6g} (95% CI [{compare_ci.low:.6g}, "
            f"{compare_ci.high:.6g}]) -- {'accept' if accepted else 'reject'} ({delta_pct:+.2f}%)"
        )

    verdict = "accept" if accepted else "reject"
    ci_overlap = None if ci is None else not non_overlapping(compare_ci, ci)

    conn = db.connect(cfg.db_path)
    try:
        for result in trial_results:
            db.update_trial_verdict(
                conn, result["trial_id"], verdict=verdict,
                delta_vs_baseline_pct=delta_pct, ci_overlap=ci_overlap,
            )
            db.record_hypothesis(conn, trial_id=result["trial_id"], proposed_by="rule", rationale=reason)

        # check_regression() is a secondary environment/counter-sanity guardrail,
        # only worth spending on a flagset we're actually about to accept --
        # doc/DESIGN.md sec. 6 Phase 4, cfm/instrumentation/wspy.py's own docstring
        # for why it's never the accept/reject decision itself.
        if accepted and instrumentation is not None:
            for result in trial_results:
                if result.get("wspy_run_ref"):
                    regression_rows = instrumentation.check_regression(result["wspy_run_ref"])
                    db.record_hypothesis(
                        conn, trial_id=result["trial_id"], proposed_by="rule",
                        rationale=_summarize_regression(regression_rows),
                    )

        # Cross-benchmark knowledge transfer (doc/DESIGN.md sec. 8) is keyed by a
        # single flag -- only meaningful for Phase 4's one-flag-at-a-time
        # confirmations, not Phase 5's multi-flag cumulative/pair sets, and only
        # when there's a real numeric delta to aggregate (a total-failure
        # confirmation is still persisted above, as trials + hypotheses, just not
        # folded into this numeric aggregate). compiler_version/target_arch are
        # both None -- no host/GCC detection wired in yet (CLAUDE.md's traps log).
        if len(flags) == 1 and ratios:
            db.upsert_knowledge(
                conn, cluster_key=baseline.resource_dominance or "unknown", compiler="gcc",
                compiler_version=None, target_arch=None, flag=flags[0], accepted=accepted,
                delta_pct=delta_pct, last_benchmark=benchmark,
            )
    finally:
        conn.close()

    return ConfirmationOutcome(
        flags=flags, trial_ids=trial_ids, ratios=ratios, ci=ci,
        delta_vs_baseline_pct=delta_pct, accepted=accepted, reason=reason,
    )


def confirm_candidates(
    cfg: CfmConfig,
    *,
    experiment_id: int,
    benchmark: str,
    baseline: BaselineResult,
    screened: list[ScreeningOutcome],
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> list[ConfirmationOutcome]:
    """doc/DESIGN.md sec. 6 Phase 4: each Phase 3 survivor re-run at
    ``CONFIRMATION_REPETITIONS``, ``CALIBRATION_PROFILE`` (``quick`` -- sec. 14
    M2.5 item 2, shape doesn't need re-deriving per candidate), compared against
    the *baseline*'s CI -- accept iff non-overlapping and better. ``screened`` is
    Phase 3's full output list (not pre-filtered) so a caller can just chain
    ``screen_candidates()``'s return value straight in.
    """
    return [
        _confirm_flagset(
            cfg, experiment_id=experiment_id, benchmark=benchmark, baseline=baseline,
            flags=[outcome.candidate.flag], phase="confirmation", compare_ci=baseline.ci,
            workload=workload, instrumentation=instrumentation,
        )
        for outcome in screened
        if outcome.survived
    ]


@dataclass
class CombinationResult:
    """Phase 5's output: ``winning_flags``/``winning_ci`` is the final peak
    flagset for this experiment (never worse than the baseline -- greedy/pair
    additions are only kept when they clear the statistical bar). ``steps`` is
    every cumulative-set confirmation tried during the greedy walk, in order;
    ``pair_trials`` is the random-pair tournament's own trials -- both kept for
    traceability even though only the winning path matters for the final config.
    """

    winning_flags: list[str]
    winning_ci: ConfidenceInterval
    steps: list[ConfirmationOutcome] = field(default_factory=list)
    pair_trials: list[ConfirmationOutcome] = field(default_factory=list)


def greedy_combine(
    cfg: CfmConfig,
    *,
    experiment_id: int,
    benchmark: str,
    baseline: BaselineResult,
    confirmed: list[ConfirmationOutcome],
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
    max_pair_trials: int = MAX_PAIR_TOURNAMENT_TRIALS,
    rng: Optional[random.Random] = None,
) -> CombinationResult:
    """doc/DESIGN.md sec. 6 Phase 5: confirmed-positive flags (``confirmed``,
    typically ``confirm_candidates()``'s own output) combined greedily by observed
    lift, each cumulative step re-confirmed against the *current running set* (not
    the original baseline -- interaction effects aren't assumed additive), stopping
    when the next addition doesn't clear the bar. A small random-pair tournament
    over the same accepted set catches synergy the greedy order might miss,
    bounded to ``max_pair_trials`` "so it doesn't blow the budget."
    """
    rng = rng or random.Random()
    accepted = sorted(
        (c for c in confirmed if c.accepted), key=lambda c: c.delta_vs_baseline_pct, reverse=True,
    )

    current_flags: list[str] = list(baseline.flags)
    current_ci = baseline.ci
    parent_trial_id: Optional[int] = None
    steps: list[ConfirmationOutcome] = []

    for candidate in accepted:
        flag = candidate.flags[0]
        if flag in current_flags:
            continue
        trial_flags = current_flags + [flag]
        step = _confirm_flagset(
            cfg, experiment_id=experiment_id, benchmark=benchmark, baseline=baseline,
            flags=trial_flags, phase="combination", compare_ci=current_ci,
            parent_trial_id=parent_trial_id, workload=workload, instrumentation=instrumentation,
        )
        steps.append(step)
        if step.accepted:
            current_flags = trial_flags
            current_ci = step.ci
            parent_trial_id = step.trial_ids[0]

    # Each pair is evaluated standalone against the *baseline* (not fused with
    # whatever the greedy walk already accumulated) -- the whole point is to catch
    # a synergistic pair the greedy one-at-a-time walk would never have tried
    # together on its own (e.g. two flags each individually rejected that only
    # help in combination), not to re-explore what greedy already covered.
    pair_trials: list[ConfirmationOutcome] = []
    candidate_flags = [c.flags[0] for c in accepted]
    pairs = list(itertools.combinations(candidate_flags, 2))
    rng.shuffle(pairs)
    for a, b in pairs[:max_pair_trials]:
        pair_trials.append(_confirm_flagset(
            cfg, experiment_id=experiment_id, benchmark=benchmark, baseline=baseline,
            flags=sorted({a, b}), phase="combination", compare_ci=baseline.ci,
            workload=workload, instrumentation=instrumentation,
        ))

    # A pair trial replaces the greedy winner only if it clears the *same* bar
    # each greedy step already had to clear -- non-overlapping CI and a higher
    # mean against the current running set, not just "beats baseline" (which
    # `trial.accepted` alone would only mean). "Catches synergy the greedy order
    # might miss" only has teeth if a winning pair can actually win (doc/DESIGN.md
    # sec. 6 Phase 5).
    for trial in pair_trials:
        if trial.ci is not None and trial.ci.mean > current_ci.mean and non_overlapping(current_ci, trial.ci):
            current_flags = trial.flags
            current_ci = trial.ci

    return CombinationResult(
        winning_flags=current_flags, winning_ci=current_ci, steps=steps, pair_trials=pair_trials,
    )
