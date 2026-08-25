"""Deterministic phase state machine -- doc/DESIGN.md sec. 5-6.

M1 scope (doc/DESIGN.md sec. 14): Phases 1 (baseline), 2 (candidate generation --
trivial, no signature-based filtering yet), 3 (screening), 4 (confirmation), and 5
(greedy combination). Phase 0 (preflight)/7 (finalize+report) are M1-adjacent or
later milestones, not this module's concern yet. Phase 6 (compounding
multipliers) has one slice implemented so far -- `run_pgo_multiplier()`'s real
two-pass PGO trial, 2026-08-22; LTO/microarch multipliers are still open.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Optional

from . import db
from . import reference_matrix
from .agents.knowledge_agent import KnownFlag
from .agents.spec_agent import run_one_trial
from .compilers.base import FlagCandidate
from .compilers.gcc import GccCompiler, benchmark_languages
from .config import CfmConfig
from .hostinfo import detect_microarch_flags
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
# Real, twice-independently-confirmed finding, not a hypothetical (CLAUDE.md's
# 2026-08-24/25 traps entries): baseline's own CONFIRMATION_REPETITIONS reps
# can still be visibly settling downward (e.g. 44.68 -> 43.44 -> 41.93,
# 727.cppcheck_r's own real run) by the time they're measured, immediately
# after Phase 1 starts with no warm-up at all -- unlike every later Phase
# 4/5/6 confirmation trial, which naturally benefits from whatever settling
# time has already elapsed earlier in the run. The 2026-08-24 fix
# (BaselineResult.most_recent_ratio) addressed Phase 3 screening's own point
# comparison; this addresses the deeper problem that a still-settling 3-rep
# sample also produces a too-wide baseline.ci -- confirmed live on
# 727.cppcheck_r to plausibly swallow a near-zero-variance, genuinely large
# PGO win (+11.05% against the settled reference, officially rejected against
# the unsettled one). These reps are real trials (real sustained load is what
# actually lets the system settle, not merely waiting), persisted to cfm.db
# like any other, just deliberately excluded from the ratios/CI that becomes
# `baseline.ci` -- cheap, bounded, one-time cost (BASELINE_WARMUP_REPETITIONS
# extra quick-profile trials per mining run, not per candidate).
# Deliberately does NOT address the separate, larger multi-hour *continuing*
# drift case (`782.lbm_r`'s own 2026-08-21 run, which never fully leveled off
# even after hours) -- a short, fixed warm-up can't fix a drift that keeps
# moving throughout the whole run's own duration; that's still a real, open,
# bigger design question.
BASELINE_WARMUP_REPETITIONS = 2
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

# Phase 6's real two-pass PGO trial (doc/DESIGN.md sec. 6/15). Must match
# cfm/workloads/spec_cpu2026.py's own `_PGO_USE_FLAG` -- that module's
# generate_config() is what actually keys off this literal's presence to render
# the real PASS1_OPTIMIZE/PASS2_OPTIMIZE two-pass config instead of the flat
# single-OPTIMIZE-line shape; this constant just needs the same string, not an
# import of that module's own concrete-workload internals into this
# backend-agnostic orchestrator (cfm/workloads/base.py's `WorkloadBackend`
# abstraction is deliberately never assumed to be the SPEC one here).
PGO_FLAG = "-fprofile-use"

# doc/DESIGN.md sec. 14 M2.5 item 3: Phase 4/5's accept bar requires not just a
# statistically non-overlapping CI but a *practically* significant delta -- a
# technically-non-overlapping-but-tiny gain (the "0.8% up or 0.8% down" case)
# defaults to reject, not to spending more reps trying to resolve it
# (deliberately asymmetric with the reject path -- a false accept permanently
# pollutes the peak config and the cross-benchmark knowledge table, a false
# reject just misses a small real win). DESIGN.md's principled source for this
# threshold is the reference-matrix corpus's own historical stddev/cv_percent,
# once available for a given benchmark; that's not wired in yet (M2.5 item 2
# shipped without the reference-matrix integration), so this is the documented
# fixed fallback instead.
MIN_PRACTICAL_SIGNIFICANCE_PCT = 1.0


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
    # "reference-matrix:<machine-slug>" or "local-deep-cpu-trial" -- doc/DESIGN.md sec. 14 M2.5 item 2,
    # _characterize_baseline()'s own provenance tag. Surfaced through to cli.py's summary JSON so a
    # mining run's output visibly says which shape source it actually used, not just the values.
    characterization_source: Optional[str] = None

    @property
    def most_recent_ratio(self) -> float:
        """The chronologically most recent calibration-grade ratio (``ratios[-1]``
        -- ``run_baseline()`` builds ``ratios`` via sequential appends, so this is
        genuinely the last-measured rep, not just the last list element by
        convention). ``screen_candidates()`` (Phase 3) compares against this
        instead of ``ci.mean`` -- confirmed live, 2026-08-24 (CLAUDE.md's
        Non-obvious traps log, the `750.sealcrypto_r` entry): baseline's own reps
        can still be visibly settling (e.g. 56.18 -> 54.80 -> 52.09) by the time
        Phase 3 starts immediately afterward, and comparing every screening trial
        against the full-run *mean* (pulled up by the earlier, higher reps) rather
        than wherever the benchmark's throughput had actually settled to biases
        every subsequent screening delta negative, regardless of the candidate
        flag's own real effect -- a real, non-hypothetical cause of a false prune,
        not just added noise. Falls back to ``ci.mean`` if ``ratios`` is somehow
        empty (`run_baseline()` itself never returns a `BaselineResult` with no
        usable ratio -- see its own `raise RuntimeError` -- but a hand-rolled
        `BaselineResult` built directly, e.g. in a test fixture, could still hit
        this; degrade rather than crash).
        """
        return self.ratios[-1] if self.ratios else self.ci.mean


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
    reference_matrix_fetch=reference_matrix.fetch_shape,
) -> dict:
    """doc/DESIGN.md sec. 14 M2.5 item 2: shape (``resource_dominance``/
    ``vectorization_density``/``allocation_pressure``), not the ratio -- tried first
    against the external reference-matrix corpus (``reference_matrix.fetch_shape()``,
    read-only/anonymous, ~a few HTTP calls), falling back to exactly one local
    ``deep-cpu`` characterization-grade trial (``CHARACTERIZATION_ITERATIONS`` -- shape
    needs one measurement, not a repetition-based CI) only when no matching published
    entry exists yet. This was a single local trial only until 2026-08-20; this
    function was already kept deliberately isolated for exactly this swap (see git
    history) -- ``run_baseline()`` and everything downstream only consume the
    resulting shape fields, never how they were obtained.

    ``reference_matrix_fetch`` is injectable so tests can force the local-trial path
    deterministically (a lambda returning ``None``) without a real network call --
    the default real function takes only ``(cfg, benchmark)``, matching
    ``reference_matrix.fetch_shape()``'s own signature exactly.

    The experiment row is created here unconditionally (not inside ``run_one_trial()``
    via ``experiment_id=None`` as before) since the reference-matrix path needs one
    regardless of whether a real local trial happens at all.
    """
    conn = db.connect(cfg.db_path)
    try:
        experiment_id = db.create_experiment(
            conn, benchmark=benchmark, hostname=cfg.hostname, compiler="gcc",
        )
    finally:
        conn.close()

    shape = reference_matrix_fetch(cfg, benchmark)
    if shape is not None:
        return {
            "experiment_id": experiment_id,
            "trial_id": None,
            "resource_dominance": shape.get("resource_dominance"),
            "vectorization_density": shape.get("vectorization_density"),
            "allocation_pressure": shape.get("allocation_pressure"),
            "characterization_source": "reference-matrix:%s" % shape.get("source_machine", "?"),
        }

    result = run_one_trial(
        cfg, benchmark=benchmark, flags=base_flags, phase="confirmation",
        profile=CHARACTERIZATION_PROFILE, iterations=CHARACTERIZATION_ITERATIONS,
        experiment_id=experiment_id, workload=workload, instrumentation=instrumentation,
    )
    result.setdefault("characterization_source", "local-deep-cpu-trial")
    return result


def run_baseline(
    cfg: CfmConfig,
    *,
    benchmark: str,
    base_flags: list[str],
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
    reference_matrix_fetch=reference_matrix.fetch_shape,
) -> BaselineResult:
    """doc/DESIGN.md sec. 6 Phase 1, sec. 14 M2.5 item 2: one characterization-grade
    trial (``_characterize_baseline()``, shape only -- its ratio is *not* part of
    the CI sample, so a deep-cpu-profile measurement never mixes with quick-profile
    ones in the same statistic), ``BASELINE_WARMUP_REPETITIONS`` real warm-up reps
    (real trials, deliberately excluded from the CI below -- see that constant's
    own docstring for the real 2026-08-24/25 finding that motivated this), then
    ``CONFIRMATION_REPETITIONS`` calibration-grade trials (``quick`` profile, cheap
    enough to repeat for a real CI where ``deep-cpu`` wasn't) establishing the
    running baseline every subsequent trial compares against. ``reference_matrix_fetch``
    passes straight through to ``_characterize_baseline()`` -- see its own docstring.
    """
    char_result = _characterize_baseline(
        cfg, benchmark=benchmark, base_flags=base_flags,
        workload=workload, instrumentation=instrumentation,
        reference_matrix_fetch=reference_matrix_fetch,
    )
    experiment_id = char_result["experiment_id"]
    resource_dominance = char_result.get("resource_dominance")
    vectorization_density = char_result.get("vectorization_density")
    allocation_pressure = char_result.get("allocation_pressure")
    characterization_source = char_result.get("characterization_source")
    # None when characterization came from the reference matrix -- no real trial
    # happened, nothing to add to the budget-spent list (doc/DESIGN.md sec. 14 M2.5
    # item 2: this is a strict improvement on top of the local-trial path's own
    # budget cost, not just a time saving).
    trial_ids: list[int] = [char_result["trial_id"]] if char_result["trial_id"] is not None else []

    # Warm-up reps: real trials under real sustained load (that's what actually
    # lets the system settle, not merely waiting) -- persisted to cfm.db like any
    # other trial (counted in trial_ids, so --max-trials budgeting stays
    # accurate), but their ratios are deliberately never fed into the
    # ratios/CI below. See BASELINE_WARMUP_REPETITIONS's own comment.
    conn = db.connect(cfg.db_path)
    try:
        for _ in range(BASELINE_WARMUP_REPETITIONS):
            warmup_result = run_one_trial(
                cfg, benchmark=benchmark, flags=base_flags, phase="confirmation",
                profile=CALIBRATION_PROFILE, iterations=CALIBRATION_ITERATIONS,
                experiment_id=experiment_id, workload=workload, instrumentation=instrumentation,
            )
            trial_ids.append(warmup_result["trial_id"])
            db.record_hypothesis(
                conn, trial_id=warmup_result["trial_id"], proposed_by="rule",
                rationale=(
                    "baseline warm-up rep -- deliberately excluded from the calibration "
                    "ratios/CI below (CLAUDE.md's 2026-08-24/25 traps entry: baseline's "
                    "own early reps can still be visibly settling, and a still-settling "
                    "CI has been shown to swallow real Phase 4+ wins, not just Phase 3 "
                    "screening noise)"
                ),
            )
    finally:
        conn.close()

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
        # Every individual run_one_trial() call above returned normally (no
        # exception -- spec_agent.py's own except-and-mark-failed doesn't apply
        # here), just with no usable ratio; this experiment can't proceed as a
        # baseline, so mark it failed ourselves rather than leaving it stuck at
        # `running` (CLAUDE.md's Non-obvious traps log, 2026-08-20 entry).
        conn = db.connect(cfg.db_path)
        try:
            db.finish_experiment(conn, experiment_id, status="failed")
        finally:
            conn.close()
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
        characterization_source=characterization_source,
    )


# resource_dominance-named topdown_signals -- config/gcc_flag_catalog.seed.json's
# real vocabulary, confirmed against the seed catalog -- checked directly against
# baseline.resource_dominance below. "memory-bound-corroborated" and
# "vectorization-density-high" are handled as their own special cases (they key
# off memory_attribution/vectorization_density, not resource_dominance alone);
# "retiring-high-narrow-margin" is deliberately never excluded (see
# _signal_is_implausible()'s docstring).
_RESOURCE_DOMINANCE_SIGNALS = frozenset({
    "frontend-bound", "speculation-bound", "compute-bound", "backend-bound",
})


def _signal_is_implausible(signal: str, baseline: BaselineResult) -> bool:
    """doc/DESIGN.md sec. 14 M2.5 item 3: is ``signal`` (one entry of a
    ``FlagCandidate.topdown_signals`` list) confidently contradicted by
    ``baseline``'s characterized shape? Only ever returns True on a *confident*
    mismatch -- absence of information (``None``/``"unknown"``) never counts as
    implausible, matching "de-prioritize/exclude a category whose relevant signal
    is essentially *absent*," not "exclude whenever unsure." ``"retiring-high-
    narrow-margin"`` is never flagged here -- doc/DESIGN.md sec. 4.3's own table
    calls it a "low priority, not exclude" signal (diminishing returns, not
    implausibility), and there's no "margin" field to judge it by; a real
    verdict on it belongs to M2's own resource_dominance-based ranking, not a
    guess here.
    """
    if signal == "vectorization-density-high":
        return baseline.vectorization_density == "low"
    if signal == "memory-bound-corroborated":
        if baseline.resource_dominance is not None and baseline.resource_dominance != "memory-bound":
            return True
        return False  # memory_attribution isn't tracked on BaselineResult (M1 scope)
    if signal in _RESOURCE_DOMINANCE_SIGNALS:
        return baseline.resource_dominance is not None and baseline.resource_dominance != signal
    return False


def _filter_implausible_candidates(
    candidates: list[FlagCandidate], baseline: BaselineResult,
) -> list[FlagCandidate]:
    """doc/DESIGN.md sec. 14 M2.5 item 3's "first, cheapest line of defense":
    drop a candidate only when *every one* of its ``topdown_signals`` is
    confidently contradicted by ``baseline``'s characterized shape (a candidate
    with no signals, or with at least one plausible/unknown signal among several,
    is always kept -- excluding only requires the whole claim to be implausible,
    not any part of it). Logged to stderr, not persisted -- there's no trial row
    to attach a hypothesis to for a candidate that never ran.
    """
    survivors = []
    for candidate in candidates:
        if candidate.topdown_signals and all(
            _signal_is_implausible(s, baseline) for s in candidate.topdown_signals
        ):
            print(
                f"info: excluding {candidate.flag!r} from Phase 2 candidates -- "
                f"topdown_signals {candidate.topdown_signals} implausible given baseline shape "
                f"(resource_dominance={baseline.resource_dominance!r}, "
                f"vectorization_density={baseline.vectorization_density!r})"
            )
            continue
        survivors.append(candidate)
    return survivors


def generate_candidates(
    cfg: CfmConfig, *, benchmark: str, baseline: BaselineResult,
    compiler: Optional[GccCompiler] = None,
) -> list[FlagCandidate]:
    """doc/DESIGN.md sec. 6 Phase 2. M1 scope: every catalog entry applicable to
    this benchmark's language(s), unranked by signature -- "static catalog
    priors only" (doc/DESIGN.md sec. 14); ``compilers/gcc.py``'s own
    ``candidate_flags_for_signature()`` still ignores ``signature`` entirely,
    per that method's own M1-vs-M2 doc boundary. M2.5 item 3 adds one cheap
    filtering pass on top of that M1 catalog read, though:
    ``_filter_implausible_candidates()`` drops only a candidate whose every
    ``topdown_signals`` entry is confidently contradicted by the baseline's
    already-characterized shape -- "never spend a trial on a mechanically-
    implausible flag" -- distinct from M2's still-pending real
    resource_dominance-based *ranking* (compilers/base.py's docstring), which
    this doesn't attempt.
    """
    compiler = compiler or GccCompiler()
    languages = benchmark_languages(cfg.spec_dir, benchmark)
    candidates = compiler.candidate_flags_for_signature(baseline.resource_dominance, languages)
    return _filter_implausible_candidates(candidates, baseline)


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
    estimate against ``baseline.most_recent_ratio`` (not ``baseline.ci.mean`` --
    see that property's own docstring for the real, live 2026-08-24 finding that
    motivated the change: comparing against the full-run mean while baseline is
    still settling systematically biases every screening delta negative); no CI
    needed at this stage ("exists to prune, not conclude"). A build/validate
    failure survives=False too (a real, persisted negative result), distinguished
    from a "measured but worse" reject by its ``reason`` text and ``ratio is None``.
    """
    outcomes: list[ScreeningOutcome] = []
    conn = db.connect(cfg.db_path)
    try:
        for candidate in candidates:
            # baseline.flags + [candidate.flag], never candidate.flag alone --
            # confirmed live, 2026-08-22 (CLAUDE.md's Non-obvious traps log):
            # testing a candidate flag in total isolation means no -O level at
            # all reaches the compiled binary, a ~-O0-vs--O3 comparison, not
            # "does this flag help on top of the baseline" -- this was masked
            # the whole time by the basepeak bug (nothing built for real before
            # its fix), so it had zero observable effect until now.
            result = run_one_trial(
                cfg, benchmark=benchmark, flags=baseline.flags + [candidate.flag], phase="screening",
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
                reference = baseline.most_recent_ratio
                delta_pct = (ratio - reference) / reference * 100.0
                survived = delta_pct >= -SCREENING_PRUNE_THRESHOLD_PCT
                outcome = ScreeningOutcome(
                    candidate=candidate, trial_id=result["trial_id"], ratio=ratio,
                    delta_vs_baseline_pct=delta_pct, survived=survived,
                    reason=(
                        f"screening ratio {ratio:.6g} vs baseline's most recent "
                        f"calibration rep {reference:.6g} ({delta_pct:+.2f}%)"
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
        # doc/DESIGN.md sec. 14 M2.5 item 3: statistical significance (non-
        # overlapping CI) alone isn't enough -- also require practical
        # significance (delta_pct clearing MIN_PRACTICAL_SIGNIFICANCE_PCT),
        # subsuming the old "ci.mean > compare_ci.mean" check (a positive delta
        # above a positive threshold is already a higher mean). A technically-
        # non-overlapping-but-tiny delta defaults to reject -- deliberately
        # asymmetric, no escalation attempted for a flag that misses this bar.
        accepted = non_overlapping(compare_ci, ci) and delta_pct >= MIN_PRACTICAL_SIGNIFICANCE_PCT
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
        # single flag -- meaningful for Phase 4's one-flag-at-a-time
        # confirmations and Phase 6's own single-flag PGO multiplier trial
        # (added 2026-08-22 -- run_pgo_multiplier() always calls this with
        # exactly one flag, PGO_FLAG, appended last, same "flags[-1] is the
        # thing under test" shape Phase 4 already has), but never Phase 5's
        # multi-flag cumulative/pair sets, and only when there's a real numeric
        # delta to aggregate (a total-failure confirmation is still persisted
        # above, as trials + hypotheses, just not folded into this numeric
        # aggregate). compiler_version/target_arch are both None -- no
        # host/GCC detection wired in yet (CLAUDE.md's traps log).
        #
        # phase in ("confirmation", "multiplier") -- not len(flags) == 1 -- is
        # what actually distinguishes Phase 4/6 from Phase 5 here: flags is now
        # always baseline.flags + [the one thing under test] (confirmed live,
        # 2026-08-22 -- see confirm_candidates()'s own comment for why it's no
        # longer just [candidate.flag] alone), so it's never length 1 by
        # itself, and Phase 5's own greedy-walk first step has the identical
        # length/shape (baseline.flags + [flag]) -- phase is the only reliable
        # signal. The candidate itself is flags[-1] (the newly-added one), not
        # flags[0] (now baseline's own first flag, e.g. "-O3").
        if phase in ("confirmation", "multiplier") and ratios:
            db.upsert_knowledge(
                conn, cluster_key=baseline.resource_dominance or "unknown", compiler="gcc",
                compiler_version=None, target_arch=None, flag=flags[-1], accepted=accepted,
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
    the *baseline*'s CI -- accept iff non-overlapping *and* practically
    significant (sec. 14 M2.5 item 3's ``MIN_PRACTICAL_SIGNIFICANCE_PCT``).
    ``screened`` is Phase 3's full output list (not pre-filtered) so a caller can
    just chain ``screen_candidates()``'s return value straight in.
    """
    return [
        # baseline.flags + [candidate.flag], never candidate.flag alone -- same
        # fix and same reasoning as screen_candidates() above.
        _confirm_flagset(
            cfg, experiment_id=experiment_id, benchmark=benchmark, baseline=baseline,
            flags=baseline.flags + [outcome.candidate.flag], phase="confirmation",
            compare_ci=baseline.ci, workload=workload, instrumentation=instrumentation,
        )
        for outcome in screened
        if outcome.survived
    ]


def split_candidates_by_known_prior(
    candidates: list[FlagCandidate], known_flags: dict[str, KnownFlag],
) -> tuple[list[FlagCandidate], list[FlagCandidate]]:
    """doc/DESIGN.md sec. 8 point 3 (M4): partitions Phase 2's candidate list
    into ``(fast_tracked, remaining)`` -- ``fast_tracked`` is every candidate
    whose flag has a real *accepted* prior in this cluster
    (``KnownFlag.has_accepted_track_record``), sorted by that prior's own
    ``mean_delta_pct`` descending (best-evidenced first, "seed Phase 2's
    candidate queue with those flags first, ahead of the generic rule-based
    catalog"). ``remaining`` is everything else, in original catalog order --
    including candidates with a real but *rejected* prior, which still get a
    full, real screening trial against this benchmark (a reject elsewhere
    isn't trusted as a reject here without a real measurement, same posture
    as accepts) -- unchanged from the pre-M4 pipeline.

    ``known_flags`` is a ``{flag: KnownFlag}`` mapping, typically built from
    ``knowledge_agent.known_flags_for_cluster()``'s own list -- kept as a plain
    dict here (not that function's own return shape) so this stays testable
    without a real ``cfm.db`` involved.
    """
    fast_tracked = sorted(
        (c for c in candidates if known_flags.get(c.flag) and known_flags[c.flag].has_accepted_track_record),
        key=lambda c: known_flags[c.flag].mean_delta_pct, reverse=True,
    )
    fast_tracked_flags = {c.flag for c in fast_tracked}
    remaining = [c for c in candidates if c.flag not in fast_tracked_flags]
    return fast_tracked, remaining


def confirm_known_candidates(
    cfg: CfmConfig,
    *,
    experiment_id: int,
    benchmark: str,
    baseline: BaselineResult,
    candidates: list[FlagCandidate],
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> list[ConfirmationOutcome]:
    """doc/DESIGN.md sec. 8 point 3 (M4): Phase 4 confirmation for candidates
    ``split_candidates_by_known_prior()`` fast-tracked -- skips Phase 3's
    screening trial entirely ("already been screened once, elsewhere"), going
    straight to a full, real confirmation-grade re-measurement against *this*
    benchmark's own baseline. Body is otherwise identical to
    ``confirm_candidates()``'s own list comprehension (same ``baseline.flags +
    [candidate.flag]`` shape, same ``phase="confirmation"`` -- a fast-tracked
    flag is still exactly a Phase 4 confirmation, just reached by a different
    route) -- a cross-benchmark prior changes *which* candidates get a trial
    and in what order, never the correctness bar a trial has to clear to be
    accepted (doc/DESIGN.md sec. 15's "external data is a hypothesis aid,
    never a substitute measurement," applied here to cross-benchmark
    knowledge exactly as it already is to the reference-matrix corpus).
    """
    return [
        _confirm_flagset(
            cfg, experiment_id=experiment_id, benchmark=benchmark, baseline=baseline,
            flags=baseline.flags + [candidate.flag], phase="confirmation",
            compare_ci=baseline.ci, workload=workload, instrumentation=instrumentation,
        )
        for candidate in candidates
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
        # flags[-1], not flags[0] -- Phase 4's ConfirmationOutcome.flags is now
        # baseline.flags + [the candidate] (confirmed live, 2026-08-22; see
        # confirm_candidates()'s own comment), so the actual candidate flag is
        # the last element, not the first (which is baseline's own, e.g. "-O3").
        flag = candidate.flags[-1]
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
    candidate_flags = [c.flags[-1] for c in accepted]  # see the greedy loop's own comment above
    pairs = list(itertools.combinations(candidate_flags, 2))
    rng.shuffle(pairs)
    for a, b in pairs[:max_pair_trials]:
        # baseline.flags + the two candidates, never the pair alone -- same
        # fix and same reasoning as screen_candidates()/confirm_candidates().
        pair_trials.append(_confirm_flagset(
            cfg, experiment_id=experiment_id, benchmark=benchmark, baseline=baseline,
            flags=baseline.flags + sorted({a, b}), phase="combination", compare_ci=baseline.ci,
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


@dataclass
class MultiplierResult:
    """Phase 6's output for a single compounding multiplier -- PGO (real
    two-pass `-fprofile-use`, cfm/workloads/spec_cpu2026.py's PASS1/PASS2
    rendering) or the microarch multiplier (`cfm/hostinfo.py`'s detected
    `-march=`/`-mtune=` pair); LTO isn't a separate multiplier here -- it
    already flows through the ordinary Phase 2-5 per-flag path instead
    (`config/gcc_flag_catalog.seed.json`'s own `-flto` entry). ``attempted``
    is False when the multiplier was skipped entirely -- no trial spent --
    either because it was implausible against baseline's characterized shape
    (PGO's own check, mirroring Phase 2's `_filter_implausible_candidates()`)
    or because nothing could be confidently detected/applicable (microarch's
    own check: no `-march=`/`-mtune=` pair detected, or one already present in
    the incoming winning set). ``winning_flags``/``winning_ci`` are always
    populated: the incoming set/CI unchanged when nothing was attempted or
    nothing won, or the accepted trial's own flags/CI when one did.
    ``outcomes`` holds every individual trial actually attempted (PGO tries
    at most one; microarch can try up to two independent candidates), for
    traceability even when the winning one differs from the last attempted --
    mirrors `CombinationResult.steps`/`pair_trials`' own "keep every attempt"
    posture. ``outcome`` is the winning trial if one was accepted, otherwise
    the last trial attempted -- never ``None`` once at least one trial ran
    (only when ``attempted`` is ``False`` is it ``None``), kept for existing
    single-outcome call sites that just want "the one relevant result."
    """

    attempted: bool
    winning_flags: list[str]
    winning_ci: ConfidenceInterval
    skip_reason: Optional[str] = None
    outcome: Optional[ConfirmationOutcome] = None
    outcomes: list[ConfirmationOutcome] = field(default_factory=list)


def run_pgo_multiplier(
    cfg: CfmConfig,
    *,
    experiment_id: int,
    benchmark: str,
    baseline: BaselineResult,
    combination: CombinationResult,
    compiler: Optional[GccCompiler] = None,
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> MultiplierResult:
    """doc/DESIGN.md sec. 6 Phase 6 (PGO slice): real two-pass PGO layered on top
    of Phase 5's winning flagset (``combination.winning_flags``), compared
    against Phase 5's own winning CI -- not the original baseline -- same
    "compare against the current running set" principle `greedy_combine()`'s own
    cumulative steps already use via `_confirm_flagset()`'s `compare_ci` param.

    Cheap plausibility check first, mirroring `_filter_implausible_candidates()`
    (Phase 2): skip PGO entirely, spending no trial, when *every one* of the
    `-fprofile-use` catalog entry's own `topdown_signals` is confidently
    contradicted by ``baseline``'s characterized shape (unknown/absent signal
    data never counts as implausible, same as Phase 2's own rule) -- PGO is a
    real two-compile-plus-training-run trial (roughly 2x a normal confirmation's
    build cost), not free, so this is worth the same cheap check every other
    catalog entry already gets, even though PGO itself was deliberately excluded
    from that shared per-flag path (`compilers/gcc.py`'s `category == "pgo"`
    exclusion) since testing it standalone there would be meaningless.

    Always renders `flags = combination.winning_flags + [PGO_FLAG]` --
    `generate_config()` keys off `PGO_FLAG`'s literal presence to render the
    real PASS1_OPTIMIZE/PASS2_OPTIMIZE two-pass config, and this is the same
    "flags is the trial's full logical identity" convention every other
    candidate in this module already uses.
    """
    compiler = compiler or GccCompiler()
    signals = compiler.pgo_topdown_signals()
    if signals and all(_signal_is_implausible(s, baseline) for s in signals):
        reason = (
            f"skipping PGO -- topdown_signals {signals} implausible given baseline shape "
            f"(resource_dominance={baseline.resource_dominance!r}, "
            f"vectorization_density={baseline.vectorization_density!r})"
        )
        print(f"info: {reason}")
        return MultiplierResult(
            attempted=False, winning_flags=combination.winning_flags,
            winning_ci=combination.winning_ci, skip_reason=reason,
        )

    outcome = _confirm_flagset(
        cfg, experiment_id=experiment_id, benchmark=benchmark, baseline=baseline,
        flags=combination.winning_flags + [PGO_FLAG], phase="multiplier",
        compare_ci=combination.winning_ci, workload=workload, instrumentation=instrumentation,
    )
    if outcome.accepted:
        return MultiplierResult(
            attempted=True, winning_flags=outcome.flags, winning_ci=outcome.ci,
            outcome=outcome, outcomes=[outcome],
        )
    return MultiplierResult(
        attempted=True, winning_flags=combination.winning_flags,
        winning_ci=combination.winning_ci, outcome=outcome, outcomes=[outcome],
    )


def run_microarch_multiplier(
    cfg: CfmConfig,
    *,
    experiment_id: int,
    benchmark: str,
    baseline: BaselineResult,
    combination,
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
) -> MultiplierResult:
    """doc/DESIGN.md sec. 6 Phase 6 (microarch slice): tries `cfm/hostinfo.py`'s
    small, detected `-march=`/`-mtune=` pair, each independently layered on top
    of the incoming winning flagset and compared against its winning CI -- same
    "compare against the current running set" principle as `run_pgo_multiplier()`
    and `greedy_combine()`'s own cumulative steps. ``combination`` is duck-typed
    (only `.winning_flags`/`.winning_ci` are read) so this can chain directly
    off either Phase 5's own `CombinationResult` or `run_pgo_multiplier()`'s own
    `MultiplierResult` -- letting `cli.py` run PGO first, then microarch layered
    on top of *whatever PGO left behind*, both real compounding multipliers
    stacking the way doc/DESIGN.md sec. 6 Phase 6 describes.

    Skips entirely -- no trial spent -- when `detect_microarch_flags()` returns
    nothing (an unbuilt/missing `cpu_info`, or a host/core label it can't
    confidently map without guessing, see that module's own docstring), or when
    the incoming winning set already contains an `-march=`/`-mtune=` flag (most
    likely `-march=native`, tried and possibly accepted via the ordinary Phase
    2-5 per-flag path already -- adding a second, different `-march=`/`-mtune=`
    choice on top would conflict rather than compound).

    Both detected flags are tried independently (not combined with each other --
    `-march=X` already implies `-mtune=X` as its own default, so pairing them
    would be redundant, not a distinct third choice), each its own confirmation-
    grade trial; if more than one is accepted, the larger delta wins, mirroring
    `greedy_combine()`'s own pair-tournament "replace only if it clears the same
    bar" logic.
    """
    detected = detect_microarch_flags(cfg.wspy_dir)
    if not detected:
        reason = "skipping microarch multiplier -- no confidently-detected -march=/-mtune= choice"
        print(f"info: {reason}")
        return MultiplierResult(
            attempted=False, winning_flags=combination.winning_flags,
            winning_ci=combination.winning_ci, skip_reason=reason,
        )
    if any(f.startswith("-march=") or f.startswith("-mtune=") for f in combination.winning_flags):
        reason = (
            f"skipping microarch multiplier -- winning set {combination.winning_flags} already "
            "has an -march=/-mtune= flag, adding another would conflict rather than compound"
        )
        print(f"info: {reason}")
        return MultiplierResult(
            attempted=False, winning_flags=combination.winning_flags,
            winning_ci=combination.winning_ci, skip_reason=reason,
        )

    current_flags = combination.winning_flags
    current_ci = combination.winning_ci
    outcomes: list[ConfirmationOutcome] = []
    for flag in detected:
        outcome = _confirm_flagset(
            cfg, experiment_id=experiment_id, benchmark=benchmark, baseline=baseline,
            flags=combination.winning_flags + [flag], phase="multiplier",
            compare_ci=combination.winning_ci, workload=workload, instrumentation=instrumentation,
        )
        outcomes.append(outcome)
        if outcome.accepted and outcome.ci.mean > current_ci.mean:
            current_flags = outcome.flags
            current_ci = outcome.ci

    # The winning outcome if one was accepted, else the last one tried --
    # never None once at least one trial ran, same contract run_pgo_multiplier()
    # already has for its own (always exactly one) trial.
    winner = next((o for o in outcomes if o.flags == current_flags), None) or outcomes[-1]
    return MultiplierResult(
        attempted=True, winning_flags=current_flags, winning_ci=current_ci,
        outcome=winner, outcomes=outcomes,
    )
