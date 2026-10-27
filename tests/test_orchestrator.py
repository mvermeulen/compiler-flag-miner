"""Unit tests for cfm/orchestrator.py's Phase 1 (baseline)/2 (candidates)/3
(screening) logic -- entirely against fake WorkloadBackend/InstrumentationBackend
implementations (ScriptedBackends below), no real SPEC/wspy calls, matching every
other test tier's "no real runcpu/wspy" posture (CLAUDE.md's Build & test section).
"""

from __future__ import annotations

import json
import random
import stat
from collections import deque
from pathlib import Path

import pytest

import cfm.db as db
from cfm.agents.knowledge_agent import KnownFlag
from cfm.compilers.base import FlagCandidate
from cfm.compilers.gcc import GccCompiler
from cfm.config import CfmConfig
from cfm.instrumentation.base import InstrumentationBackend, RunSignature
from cfm.orchestrator import (
    BASELINE_WARMUP_REPETITIONS,
    MAX_PAIR_TOURNAMENT_TRIALS,
    MIN_PRACTICAL_SIGNIFICANCE_PCT,
    PGO_FLAG,
    BaselineResult,
    CombinationResult,
    ConfirmationOutcome,
    ScreeningOutcome,
    _filter_implausible_candidates,
    defer_vector_width_candidates,
    find_near_miss_flags,
    confirm_candidates,
    confirm_known_candidates,
    generate_candidates,
    greedy_combine,
    recheck_baseline,
    run_baseline,
    run_microarch_multiplier,
    run_pgo_multiplier,
    run_vector_width_multiplier,
    screen_candidates,
    split_candidates_by_known_prior,
)
from cfm.stats import confidence_interval
from cfm.workloads.base import BuildResult, RunResult, WorkloadBackend


class ScriptedBackends(WorkloadBackend, InstrumentationBackend):
    """One object playing both backend roles -- a per-flags-tuple queue of ratios
    to return in order (so repeated baseline/confirmation calls with the same
    flags can express real measurement variance), an optional per-call
    resource_dominance sequence, and a set of flag-tuples whose "build" should
    fail. Good enough to drive the orchestrator's phase logic without a single
    real subprocess call.
    """

    def __init__(
        self,
        ratio_sequences: dict[tuple, list],
        resource_dominance: str = "memory-bound",
        resource_dominance_sequence: list = None,
        vectorization_density: str = None,
        allocation_pressure: str = None,
        build_fails_for: frozenset = frozenset(),
        regression_rows: list = None,
        code_for: dict = None,
    ):
        self._queues = {k: deque(v) for k, v in ratio_sequences.items()}
        self.resource_dominance = resource_dominance
        self._rd_sequence = deque(resource_dominance_sequence) if resource_dominance_sequence else None
        self.vectorization_density = vectorization_density
        self.allocation_pressure = allocation_pressure
        self.build_fails_for = build_fails_for
        self._current_flags = None
        self.regression_rows = regression_rows if regression_rows is not None else []
        self.check_regression_calls: list[str] = []
        # flags-tuple -> code fingerprint; flagsets not listed have none (never skipped).
        self.code_for = code_for or {}
        self.timed_runs: list[tuple] = []

    # -- WorkloadBackend --
    def generate_config(self, bench, tune, flags):
        self._current_flags = tuple(flags)
        return Path("/fake/config.cfg")

    def build(self, bench, tune, config_path):
        if self._current_flags in self.build_fails_for:
            return BuildResult(ok=False, log_path=Path("/fake/build.log"), raw_output="fake build failure")
        return BuildResult(ok=True, log_path=Path("/fake/build.log"), raw_output="ok")

    def run_command(self, bench, tune, config_path, iterations):
        self.timed_runs.append(self._current_flags)
        return ["fake-run"]

    def code_fingerprint(self, bench, tune):
        return self.code_for.get(self._current_flags)

    def parse_result(self, bench, tune, raw_output):
        queue = self._queues.get(self._current_flags)
        if not queue:
            return RunResult(
                ok=False, validated=False, ratio=None, seconds=None,
                status="validate-failed", raw_output=raw_output,
            )
        return RunResult(
            ok=True, validated=True, ratio=queue.popleft(), seconds=1.0,
            status="ok", raw_output=raw_output,
        )

    # -- InstrumentationBackend --
    def preflight(self):
        return []

    def characterize(self, command, suite, benchmark, run_id, profile, output_root):
        rd = self._rd_sequence.popleft() if self._rd_sequence else self.resource_dominance
        return RunSignature(
            wspy_run_ref=f"fakehost:{run_id}", validated=True,
            resource_dominance=rd, resource_dominance_pct=80.0,
            memory_attribution="corroborated",
            vectorization_density=self.vectorization_density,
            allocation_pressure=self.allocation_pressure,
            metrics={}, raw_output="",
        )

    def check_regression(self, wspy_run_ref):
        self.check_regression_calls.append(wspy_run_ref)
        return self.regression_rows


def _cfg(tmp_path):
    return CfmConfig.from_env(
        spec_dir=str(tmp_path / "spec"), wspy_dir=str(tmp_path / "wspy-unused"),
        output_root=str(tmp_path / "results"), db_path=str(tmp_path / "cfm.db"),
    )


def _no_reference_matrix(cfg, benchmark):
    """Forces _characterize_baseline()'s local-trial fallback path deterministically --
    run_baseline()'s real default (reference_matrix.fetch_shape) makes real network calls, which no
    unit test may do (CLAUDE.md's Build & test section). Matches reference_matrix.fetch_shape()'s own
    (cfg, benchmark) signature exactly."""
    return None


def _fake_reference_matrix_shape(cfg, benchmark):
    """The other real _characterize_baseline() path -- a found reference-matrix
    entry, no local trial needed at all. Same shape reference_matrix.fetch_shape()
    itself returns (cfm/reference_matrix.py's own docstring)."""
    return {
        "resource_dominance": "frontend-bound",
        "resource_dominance_pct": 71.0,
        "vectorization_density": "low",
        "allocation_pressure": "moderate",
        "source_machine": "fake-ref-host",
    }


# -- run_baseline -------------------------------------------------------------

def test_run_baseline_computes_ci_over_repeated_trials(tmp_path):
    cfg = _cfg(tmp_path)
    # First pop is the one characterization-grade (deep-cpu) trial -- a
    # deliberately off-value (999.0) to prove it's excluded from the CI
    # sample. Next BASELINE_WARMUP_REPETITIONS (2) pops are warm-up reps --
    # also deliberately off-value (777.0 each) to prove they're excluded too
    # (2026-08-24/25 finding, CLAUDE.md's traps entry). The remaining three
    # are the real calibration-grade (quick) trials that actually feed the CI.
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): [999.0, 777.0, 777.0, 100.0, 102.0, 98.0]},
        vectorization_density="low", allocation_pressure="moderate",
    )

    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends,
        reference_matrix_fetch=_no_reference_matrix,
    )

    assert isinstance(result, BaselineResult)
    assert result.ratios == [100.0, 102.0, 98.0]
    assert result.ci.n == 3
    assert result.ci.mean == pytest.approx(100.0)
    assert result.ci.verdict == "PASS"
    assert result.resource_dominance == "memory-bound"
    assert result.resource_dominance_pct == pytest.approx(80.0)  # ScriptedBackends.characterize()'s fixed value
    assert result.vectorization_density == "low"
    assert result.allocation_pressure == "moderate"
    assert len(result.trial_ids) == 6  # 1 characterization + 2 warm-up + 3 calibration

    conn = db.connect(cfg.db_path)
    try:
        exp = db.get_experiment(conn, result.experiment_id)
        assert exp["baseline_run_ref"] is not None
        assert exp["baseline_run_ref"].startswith("fakehost:")
        assert exp["status"] == "running"  # set_baseline_run_ref must not finish it
        trials = db.list_trials_by_phase(conn, result.experiment_id, "confirmation")
        assert len(trials) == 6  # 1 characterization + 2 warm-up + 3 calibration
    finally:
        conn.close()


def test_run_baseline_threads_resource_dominance_pct_through_the_reference_matrix_path(tmp_path):
    # The *other* real _characterize_baseline() path -- a found reference-matrix
    # entry, no local characterization trial at all -- had no orchestrator-level
    # test coverage before this (only the local-trial fallback path, exercised by
    # every other run_baseline() test via _no_reference_matrix, did). Confirms
    # resource_dominance_pct (M2's own "margin" signal) survives this path too,
    # not just the local-trial one.
    cfg = _cfg(tmp_path)
    backends = ScriptedBackends(ratio_sequences={("-O3",): [777.0, 777.0, 100.0, 102.0, 98.0]})

    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends,
        reference_matrix_fetch=_fake_reference_matrix_shape,
    )

    assert result.resource_dominance == "frontend-bound"
    assert result.resource_dominance_pct == pytest.approx(71.0)
    assert result.vectorization_density == "low"
    assert result.allocation_pressure == "moderate"
    assert result.characterization_source == "reference-matrix:fake-ref-host"
    assert result.ratios == [100.0, 102.0, 98.0]
    assert len(result.trial_ids) == 5  # 0 characterization (found, no local trial) + 2 warm-up + 3 calibration


def test_run_baseline_records_a_warmup_hypothesis_per_warmup_rep(tmp_path):
    # Real 2026-08-24/25 finding (727.cppcheck_r, CLAUDE.md's traps entry):
    # baseline's own reps can still be visibly settling by the time they're
    # measured, and a still-settling CI has been shown to swallow real Phase
    # 4+ wins. BASELINE_WARMUP_REPETITIONS real, persisted-but-excluded warm-up
    # reps address this -- each one gets its own explanatory hypothesis row so
    # a future reader of cfm.db (or scripts/analyze_trial_drift.py) can tell
    # them apart from the real calibration reps that feed the CI.
    cfg = _cfg(tmp_path)
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): [999.0, 777.0, 777.0, 100.0, 102.0, 98.0]},
    )

    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends,
        reference_matrix_fetch=_no_reference_matrix,
    )

    conn = db.connect(cfg.db_path)
    try:
        rows = conn.execute(
            "SELECT trial_id, rationale FROM hypotheses WHERE rationale LIKE 'baseline warm-up rep%'",
        ).fetchall()
        assert len(rows) == BASELINE_WARMUP_REPETITIONS
        # The two warm-up trial_ids should be exactly the 2nd and 3rd trials
        # recorded for this experiment (after the 1st, the characterization
        # trial, and before the 3 real calibration ones).
        warmup_trial_ids = {row["trial_id"] for row in rows}
        assert warmup_trial_ids == {result.trial_ids[1], result.trial_ids[2]}
    finally:
        conn.close()


def test_run_baseline_raises_when_every_repetition_fails_to_build(tmp_path):
    cfg = _cfg(tmp_path)
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): []}, build_fails_for=frozenset({("-O3",)}),
    )
    with pytest.raises(RuntimeError, match="fake_r"):
        run_baseline(cfg, benchmark="fake_r", base_flags=["-O3"], workload=backends, instrumentation=backends,
                     reference_matrix_fetch=_no_reference_matrix)

    # The experiment characterize_baseline() already created must not be left
    # stuck at status='running' -- this is exactly the gap CLAUDE.md's
    # Non-obvious traps log (2026-08-20 entry) flagged and cfm/orchestrator.py
    # now closes.
    conn = db.connect(cfg.db_path)
    try:
        cur = conn.execute(
            "SELECT status FROM experiments WHERE benchmark=? ORDER BY id DESC LIMIT 1",
            ("fake_r",),
        )
        assert cur.fetchone()[0] == "failed"
    finally:
        conn.close()


# -- screen_candidates ----------------------------------------------------------

def _baseline(mean_ratio=100.0, resource_dominance="memory-bound",
              vectorization_density=None, allocation_pressure=None, resource_dominance_pct=80.0):
    # resource_dominance_pct defaults to a confident 80% so the shape-based
    # exclusion tests exercise the exclusion itself, not CONFIDENT_SHAPE_MIN_PCT's gate.
    ci = confidence_interval([mean_ratio, mean_ratio, mean_ratio])
    return BaselineResult(
        experiment_id=1, flags=["-O3"], ratios=[mean_ratio] * 3, ci=ci,
        resource_dominance=resource_dominance, resource_dominance_pct=resource_dominance_pct,
        vectorization_density=vectorization_density, allocation_pressure=allocation_pressure,
        trial_ids=[1, 2, 3],
    )


def _candidate(flag):
    return FlagCandidate(flag=flag, category="misc", risk="safe", languages=["c"])


def test_screen_candidates_prunes_clearly_worse_keeps_better_and_marginal(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    candidates = [_candidate("-good"), _candidate("-bad"), _candidate("-marginal")]
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-good"): [110.0],      # +10% -- clearly better, survives
        ("-O3", "-bad"): [80.0],        # -20% -- clearly worse, pruned
        ("-O3", "-marginal"): [96.0],   # -4% -- within the 5% prune bar, survives
    })

    outcomes = screen_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        candidates=candidates, workload=backends, instrumentation=backends,
    )

    by_flag = {o.candidate.flag: o for o in outcomes}
    assert by_flag["-good"].survived is True
    assert by_flag["-marginal"].survived is True
    assert by_flag["-bad"].survived is False
    assert by_flag["-bad"].delta_vs_baseline_pct == pytest.approx(-20.0)


def test_screen_candidates_compares_against_most_recent_baseline_rep_not_the_mean(tmp_path):
    # Real 2026-08-24 finding (750.sealcrypto_r, CLAUDE.md's Non-obvious traps
    # log): baseline settling downward across its own 3 reps (56.18 -> 54.80 ->
    # 52.09, mean 54.35) meant every screening trial right afterward was
    # compared against a stale, too-high mean, biasing every delta negative
    # regardless of the candidate's own real effect. A candidate scoring 50.6
    # looks clearly worse against the mean (-6.9%, past the 5% prune bar) but
    # only mildly worse against baseline's own last, most-recent rep (-2.8%,
    # well inside it) -- most_recent_ratio is what screen_candidates() must use.
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    ratios = [56.18, 54.80, 52.09]
    baseline = BaselineResult(
        experiment_id=exp_id, flags=["-O3"], ratios=ratios, ci=confidence_interval(ratios),
        resource_dominance="compute-bound", trial_ids=[1, 2, 3],
    )
    candidates = [_candidate("-ofast-like")]
    backends = ScriptedBackends(ratio_sequences={("-O3", "-ofast-like"): [50.6]})

    outcomes = screen_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        candidates=candidates, workload=backends, instrumentation=backends,
    )

    assert outcomes[0].survived is True  # would have been pruned against the 54.35 mean
    assert outcomes[0].delta_vs_baseline_pct == pytest.approx((50.6 - 52.09) / 52.09 * 100.0)
    assert "most recent" in outcomes[0].reason
    assert "52.09" in outcomes[0].reason


def test_baseline_result_most_recent_ratio_is_the_last_rep_chronologically(tmp_path):
    ratios = [56.18, 54.80, 52.09]
    baseline = BaselineResult(
        experiment_id=1, flags=["-O3"], ratios=ratios, ci=confidence_interval(ratios),
        resource_dominance="compute-bound",
    )
    assert baseline.most_recent_ratio == pytest.approx(52.09)
    assert baseline.most_recent_ratio != pytest.approx(baseline.ci.mean)  # mean would be 54.35...


def test_baseline_result_most_recent_ratio_falls_back_to_ci_mean_when_ratios_empty(tmp_path):
    baseline = BaselineResult(
        experiment_id=1, flags=["-O3"], ratios=[], ci=confidence_interval([100.0, 100.0, 100.0]),
        resource_dominance="memory-bound",
    )
    assert baseline.most_recent_ratio == pytest.approx(100.0)


def test_screen_candidates_build_failure_does_not_survive(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline()
    candidates = [_candidate("-broken")]
    backends = ScriptedBackends(
        ratio_sequences={("-O3", "-broken"): []}, build_fails_for=frozenset({("-O3", "-broken")}),
    )

    outcomes = screen_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        candidates=candidates, workload=backends, instrumentation=backends,
    )

    assert len(outcomes) == 1
    assert outcomes[0].survived is False
    assert outcomes[0].ratio is None
    assert "build_status" in outcomes[0].reason


def test_screen_candidates_persists_a_hypothesis_row_per_trial(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline()
    candidates = [_candidate("-good")]
    backends = ScriptedBackends(ratio_sequences={("-O3", "-good"): [110.0]})
    outcomes = screen_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        candidates=candidates, workload=backends, instrumentation=backends,
    )

    conn = db.connect(cfg.db_path)
    try:
        # Filtered by rationale prefix, not "the only row" -- run_one_trial()
        # also best-effort-records a host package_power reading per trial
        # (2026-08-24, cfm/hostinfo.py's read_package_power_watts()) whenever
        # this test happens to run on a host with a real amdgpu hwmon sensor,
        # same "a hand-rolled test shouldn't assume incidental host hardware
        # state" lesson as several other tests in this file already apply.
        row = conn.execute(
            "SELECT * FROM hypotheses WHERE trial_id=? AND rationale LIKE 'screening ratio%'",
            (outcomes[0].trial_id,),
        ).fetchone()
        assert row is not None
        assert row["proposed_by"] == "rule"
        assert row["rationale"] == outcomes[0].reason
    finally:
        conn.close()


# -- generate_candidates --------------------------------------------------------

def _write_object_pm(spec_dir, bench, benchlang):
    object_pm = spec_dir / "benchspec" / "CPU" / bench / "Spec" / "object.pm"
    object_pm.parent.mkdir(parents=True)
    object_pm.write_text(f"$benchlang = '{benchlang}';\n")


def test_generate_candidates_filters_by_language_regardless_of_shape(tmp_path):
    cfg = _cfg(tmp_path)
    _write_object_pm(Path(cfg.spec_dir), "fake_r", "C")

    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({
        "schema_version": 1, "source": "test", "note": "test",
        "flags": [
            {"flag": "-c-flag", "languages": ["c"], "category": "misc", "risk": "safe",
             "requires": [], "conflicts": [], "notes": "", "topdown_signals": []},
            {"flag": "-cxx-flag", "languages": ["cxx"], "category": "misc", "risk": "safe",
             "requires": [], "conflicts": [], "notes": "", "topdown_signals": []},
        ],
    }))
    compiler = GccCompiler(catalog_path=catalog_path)

    # Same call, two different (fabricated) baseline signatures -- neither catalog
    # entry carries any topdown_signals, so M2.5 item 3's shape-based filtering
    # (tested separately below) never applies here regardless of shape; this test
    # is purely about compilers/gcc.py's own language filtering.
    baseline_a = _baseline()
    baseline_a.resource_dominance = "memory-bound"
    baseline_b = _baseline()
    baseline_b.resource_dominance = "frontend-bound"

    candidates_a = generate_candidates(cfg, benchmark="fake_r", baseline=baseline_a, compiler=compiler)
    candidates_b = generate_candidates(cfg, benchmark="fake_r", baseline=baseline_b, compiler=compiler)

    assert {c.flag for c in candidates_a} == {"-c-flag"}
    assert {c.flag for c in candidates_a} == {c.flag for c in candidates_b}


def test_generate_candidates_passes_the_whole_baseline_through_for_m2_ranking(tmp_path):
    # Protects the orchestrator-level wiring specifically: generate_candidates()
    # must pass `baseline` itself (not just baseline.resource_dominance) as
    # candidate_flags_for_signature()'s signature argument, since M2's ranking
    # (cfm/compilers/gcc.py's own unit tests cover the ranking logic itself) needs
    # resource_dominance_pct/vectorization_density too, not just resource_dominance.
    cfg = _cfg(tmp_path)
    _write_object_pm(Path(cfg.spec_dir), "fake_r", "C")

    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({
        "schema_version": 1, "source": "test", "note": "test",
        "flags": [
            # -no-signal-flag deliberately listed *first* -- if generate_candidates()
            # regressed to passing baseline.resource_dominance alone (a bare string
            # with no vectorization_density attribute), -vector-flag would never
            # out-rank it and catalog order (this order) would show through
            # unchanged. Only a real, correctly-wired vectorization_density read
            # promotes -vector-flag ahead of it.
            {"flag": "-no-signal-flag", "languages": ["c"], "category": "misc", "risk": "safe",
             "requires": [], "conflicts": [], "notes": "", "topdown_signals": []},
            {"flag": "-vector-flag", "languages": ["c"], "category": "vectorization", "risk": "safe",
             "requires": [], "conflicts": [], "notes": "", "topdown_signals": ["vectorization-density-high"]},
        ],
    }))
    compiler = GccCompiler(catalog_path=catalog_path)

    baseline = _baseline(resource_dominance="memory-bound", vectorization_density="high")
    candidates = generate_candidates(cfg, benchmark="fake_r", baseline=baseline, compiler=compiler)

    assert [c.flag for c in candidates] == ["-vector-flag", "-no-signal-flag"]
    # And the negative check: a baseline reporting vectorization_density="low"
    # must NOT rank -vector-flag first (it's excluded by the M2.5 filter, not
    # merely un-ranked -- confirming the signature really is read, not ignored).
    low_density_baseline = _baseline(resource_dominance="memory-bound", vectorization_density="low")
    filtered = generate_candidates(cfg, benchmark="fake_r", baseline=low_density_baseline, compiler=compiler)
    assert "-vector-flag" not in {c.flag for c in filtered}


# -- _filter_implausible_candidates (M2.5 item 3) --------------------------------

def _signaled_candidate(flag, topdown_signals):
    return FlagCandidate(
        flag=flag, category="misc", risk="safe", languages=["c"], topdown_signals=topdown_signals,
    )


@pytest.mark.parametrize("resource_dominance,expect_excluded", [
    ("compute-bound", True),  # confidently contradicted -- excluded
    ("backend-bound", False),  # matches the candidate's own signal -- kept
    (None, False),  # unknown -- absence of information never excludes
])
def test_filter_excludes_resource_dominance_signal_only_on_confident_mismatch(
    resource_dominance, expect_excluded,
):
    baseline = _baseline(resource_dominance=resource_dominance)
    candidates = [_signaled_candidate("-flag", ["backend-bound"])]
    survivors = _filter_implausible_candidates(candidates, baseline)
    assert (survivors == []) is expect_excluded


@pytest.mark.parametrize("pct,expect_excluded", [
    (64.0, True),   # 777.zstd_r's real margin -- confident, exclusion applies
    (55.0, True),   # exactly at CONFIDENT_SHAPE_MIN_PCT
    (45.4, False),  # 734.vpr_r's real margin -- LTO/PGO measured +14.65% there
    (None, False),  # unknown margin never excludes
])
def test_filter_resource_dominance_exclusion_needs_a_confident_margin(pct, expect_excluded):
    baseline = _baseline(resource_dominance="memory-bound", resource_dominance_pct=pct)
    survivors = _filter_implausible_candidates(
        [_signaled_candidate("-freorder-functions", ["frontend-bound"])], baseline,
    )
    assert (survivors == []) is expect_excluded


@pytest.mark.parametrize("pct", [72.9, 55.0, 45.4, None])
def test_filter_never_excludes_lto_on_shape(pct):
    # 829.abc_s: memory-bound 72.9% excluded -flto, which then measured +2.32% (#28).
    baseline = _baseline(resource_dominance="memory-bound", resource_dominance_pct=pct)
    survivors = _filter_implausible_candidates(
        [_signaled_candidate("-flto", ["frontend-bound"]),
         _signaled_candidate("-freorder-functions", ["frontend-bound"])],
        baseline,
    )
    kept = [c.flag for c in survivors]
    assert "-flto" in kept
    assert ("-freorder-functions" in kept) is (pct is None or pct < 55.0)


def test_shape_exempt_flags_are_real_catalog_entries():
    from cfm.compilers.gcc import GccCompiler
    from cfm.orchestrator import SHAPE_EXEMPT_FLAGS

    catalog = {entry["flag"] for entry in GccCompiler()._flags()}
    assert SHAPE_EXEMPT_FLAGS <= catalog


def test_filter_memory_bound_corroborated_exclusion_needs_a_confident_margin():
    baseline = _baseline(resource_dominance="frontend-bound", resource_dominance_pct=40.6)
    survivors = _filter_implausible_candidates(
        [_signaled_candidate("-prefetch", ["memory-bound-corroborated"])], baseline,
    )
    assert [c.flag for c in survivors] == ["-prefetch"]


def test_filter_low_margin_still_applies_vectorization_density_exclusion():
    # The margin gate only covers resource_dominance; vectorization density keeps its own rule.
    baseline = _baseline(
        resource_dominance="memory-bound", resource_dominance_pct=45.2, vectorization_density="low",
    )
    survivors = _filter_implausible_candidates(
        [_signaled_candidate("-vec", ["vectorization-density-high"])], baseline,
    )
    assert survivors == []


def test_filter_excludes_vectorization_density_high_only_when_confidently_low():
    excluded = _filter_implausible_candidates(
        [_signaled_candidate("-vec", ["vectorization-density-high"])],
        _baseline(vectorization_density="low"),
    )
    kept_unknown = _filter_implausible_candidates(
        [_signaled_candidate("-vec", ["vectorization-density-high"])],
        _baseline(vectorization_density=None),
    )
    kept_high = _filter_implausible_candidates(
        [_signaled_candidate("-vec", ["vectorization-density-high"])],
        _baseline(vectorization_density="high"),
    )
    assert excluded == []
    assert [c.flag for c in kept_unknown] == ["-vec"]
    assert [c.flag for c in kept_high] == ["-vec"]


def test_filter_excludes_memory_bound_corroborated_when_resource_dominance_differs():
    baseline = _baseline(resource_dominance="compute-bound")
    survivors = _filter_implausible_candidates(
        [_signaled_candidate("-prefetch", ["memory-bound-corroborated"])], baseline,
    )
    assert survivors == []


def test_filter_never_excludes_retiring_high_narrow_margin():
    baseline = _baseline(resource_dominance="memory-bound")
    survivors = _filter_implausible_candidates(
        [_signaled_candidate("-march", ["retiring-high-narrow-margin"])], baseline,
    )
    assert [c.flag for c in survivors] == ["-march"]


def test_filter_keeps_multi_signal_candidate_if_any_signal_is_plausible():
    # -fgraphite-identity's real catalog entry: ["backend-bound", "memory-bound-corroborated"].
    # backend-bound is contradicted (resource_dominance is memory-bound), but
    # memory-bound-corroborated isn't -- keep, since not *every* signal is implausible.
    baseline = _baseline(resource_dominance="memory-bound")
    survivors = _filter_implausible_candidates(
        [_signaled_candidate("-fgraphite-identity", ["backend-bound", "memory-bound-corroborated"])],
        baseline,
    )
    assert [c.flag for c in survivors] == ["-fgraphite-identity"]


def test_filter_never_excludes_empty_signal_candidates():
    baseline = _baseline(resource_dominance="compute-bound")
    survivors = _filter_implausible_candidates([_signaled_candidate("-frecursive", [])], baseline)
    assert [c.flag for c in survivors] == ["-frecursive"]


# -- outlier re-run and baseline re-check ---------------------------------------

def test_slow_rep_indices():
    from cfm.orchestrator import _slow_rep_indices
    assert _slow_rep_indices([17.22, 17.08, 12.20]) == [2]  # 777.zstd_r trial 542's real numbers
    assert _slow_rep_indices([17.46, 17.45, 17.40]) == []
    assert _slow_rep_indices([6.33, 3.02, 4.24]) == [1, 2]  # 782.lbm_r's throttle: two slow, slowest first
    assert _slow_rep_indices([100.0, 120.0]) == [0]
    assert _slow_rep_indices([100.0]) == []


def test_confirm_reruns_a_slow_rep_and_replaces_it(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=17.15)
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-mprefer-vector-width=256"): [17.22, 17.08, 12.20, 17.15],
    })

    [outcome] = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-mprefer-vector-width=256")], workload=backends, instrumentation=backends,
    )

    assert outcome.ratios == [17.22, 17.08, 17.15]
    assert len(outcome.trial_ids) == 4  # 3 reps + 1 re-run, all persisted
    assert outcome.delta_vs_baseline_pct == pytest.approx(0.0, abs=0.5)  # not -9.6%
    conn = db.connect(cfg.db_path)
    try:
        rationales = [
            r[0] for r in conn.execute(
                "SELECT rationale FROM hypotheses WHERE trial_id = ?", (outcome.trial_ids[2],),
            )
        ]
        k = conn.execute(
            "SELECT mean_delta_pct FROM knowledge WHERE flag = '-mprefer-vector-width=256'"
        ).fetchone()
    finally:
        conn.close()
    assert any(r.startswith("slow rep excluded") for r in rationales)
    assert abs(k[0]) < 0.5  # the knowledge table no longer sees the outlier


def test_confirm_keeps_the_slow_rep_when_the_rerun_has_no_ratio(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    # Only 3 queued ratios: the re-run hits an empty queue (validate-failed, no ratio).
    backends = ScriptedBackends(ratio_sequences={("-O3", "-x"): [100.0, 101.0, 60.0]})

    [outcome] = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-x")], workload=backends, instrumentation=backends,
    )

    assert outcome.ratios == [100.0, 101.0, 60.0]
    assert len(outcome.trial_ids) == 4


def test_run_baseline_reruns_a_slow_calibration_rep(tmp_path):
    cfg = _cfg(tmp_path)
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): [999.0, 777.0, 777.0, 100.0, 70.0, 101.0, 99.0]},
    )

    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends, reference_matrix_fetch=_no_reference_matrix,
    )

    assert result.ratios == [100.0, 99.0, 101.0]
    assert len(result.trial_ids) == 7  # 1 characterization + 2 warm-up + 3 calibration + 1 re-run


def test_confirm_reruns_every_slow_rep_when_two_are_throttled(tmp_path):
    # 782.lbm_r on niwot: the same -O3 binary at 6.33 (unthrottled) and 3.02/4.24.
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()
    baseline = _baseline(mean_ratio=6.33)
    backends = ScriptedBackends(ratio_sequences={("-O3", "-x"): [6.33, 3.02, 4.24, 6.32, 6.34]})

    [outcome] = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-x")], workload=backends, instrumentation=backends,
    )

    assert outcome.ratios == [6.33, 6.32, 6.34]
    assert len(outcome.trial_ids) == 5


def test_confirm_stops_rerunning_slow_reps_at_the_cap(tmp_path):
    from cfm.orchestrator import MAX_SLOW_REP_RERUNS
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()
    baseline = _baseline(mean_ratio=100.0)
    # Every re-run comes back just as slow, so only the cap ends the loop.
    backends = ScriptedBackends(ratio_sequences={("-O3", "-x"): [100.0, 60.0, 101.0] + [60.0] * 10})

    [outcome] = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-x")], workload=backends, instrumentation=backends,
    )

    assert len(outcome.trial_ids) == 3 + MAX_SLOW_REP_RERUNS
    assert outcome.ratios == [100.0, 60.0, 101.0]


@pytest.mark.parametrize("ratio,expect_flagged", [
    (100.0, False),  # dead on the mean
    (100.4, False),  # outside a zero-width CI but under BASELINE_RECHECK_WARN_PCT
    (99.3, True),    # 0.7% low and outside the CI
])
def test_recheck_baseline_flags_only_a_real_offset(tmp_path, ratio, expect_flagged):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()
    baseline = _baseline(mean_ratio=100.0)
    backends = ScriptedBackends(ratio_sequences={("-O3",): [ratio]})

    recheck = recheck_baseline(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        workload=backends, instrumentation=backends,
    )

    assert recheck.ratio == pytest.approx(ratio)
    assert recheck.flagged is expect_flagged
    conn = db.connect(cfg.db_path)
    try:
        # Filter by prefix: run_one_trial() also records the real host's package-power reading.
        rationales = [
            r[0] for r in conn.execute(
                "SELECT rationale FROM hypotheses WHERE trial_id = ?", (recheck.trial_id,),
            )
        ]
    finally:
        conn.close()
    assert any(r.startswith("baseline re-check after Phase 4") for r in rationales)


def test_recheck_baseline_with_no_ratio_is_not_flagged(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()
    backends = ScriptedBackends(ratio_sequences={})

    recheck = recheck_baseline(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=_baseline(),
        workload=backends, instrumentation=backends,
    )

    assert recheck.ratio is None
    assert recheck.flagged is False


# -- confirm_candidates -----------------------------------------------------------

def _screened(flag, survived=True):
    return ScreeningOutcome(
        candidate=_candidate(flag), trial_id=0, ratio=105.0,
        delta_vs_baseline_pct=5.0, survived=survived, reason="test",
    )


def test_confirm_candidates_accepts_a_clear_improvement(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)  # zero-width CI at 100
    backends = ScriptedBackends(ratio_sequences={("-O3", "-good"): [109.0, 110.0, 111.0]})

    outcomes = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-good")], workload=backends, instrumentation=backends,
    )

    assert len(outcomes) == 1
    assert outcomes[0].accepted is True
    assert outcomes[0].ci.mean == pytest.approx(110.0)
    assert outcomes[0].ci.n == 3


def test_confirm_candidates_only_processes_survivors(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline()
    backends = ScriptedBackends(ratio_sequences={("-O3", "-good"): [110.0, 110.0, 110.0]})
    outcomes = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-good", survived=True), _screened("-bad", survived=False)],
        workload=backends, instrumentation=backends,
    )
    assert len(outcomes) == 1
    assert outcomes[0].flags == ["-O3", "-good"]


def test_confirm_candidates_rejects_non_overlapping_but_practically_insignificant_delta(tmp_path):
    # doc/DESIGN.md sec. 14 M2.5 item 3: non-overlapping CI alone isn't enough --
    # a zero-width CI at 100.5 (delta = +0.5%, under MIN_PRACTICAL_SIGNIFICANCE_PCT)
    # is technically non-overlapping against a zero-width CI at 100.0, but still
    # defaults to reject.
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    assert MIN_PRACTICAL_SIGNIFICANCE_PCT == 1.0  # sanity: the module default didn't drift silently
    baseline = _baseline(mean_ratio=100.0)
    backends = ScriptedBackends(ratio_sequences={("-O3", "-marginal"): [100.5, 100.5, 100.5]})
    outcomes = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-marginal")], workload=backends, instrumentation=backends,
    )
    assert outcomes[0].accepted is False

    # A delta comfortably over the threshold, same non-overlapping shape, accepts.
    backends = ScriptedBackends(ratio_sequences={("-O3", "-good"): [102.0, 102.0, 102.0]})
    outcomes = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-good")], workload=backends, instrumentation=backends,
    )
    assert outcomes[0].accepted is True


def test_confirm_candidates_rejects_when_ci_overlaps_baseline(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    # No real difference from baseline -- CIs will overlap.
    backends = ScriptedBackends(ratio_sequences={("-O3", "-meh"): [99.0, 100.0, 101.0]})
    outcomes = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-meh")], workload=backends, instrumentation=backends,
    )
    assert outcomes[0].accepted is False


def test_confirm_candidates_calls_check_regression_only_when_accepted(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()
    baseline = _baseline(mean_ratio=100.0)

    accepted_backends = ScriptedBackends(
        ratio_sequences={("-O3", "-good"): [110.0, 110.0, 110.0]},
        regression_rows=[{"metric": "ipc", "status": "within", "baseline_verdict": "PASS"}],
    )
    confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-good")], workload=accepted_backends, instrumentation=accepted_backends,
    )
    assert len(accepted_backends.check_regression_calls) == 3  # once per repetition

    rejected_backends = ScriptedBackends(ratio_sequences={("-O3", "-meh"): [100.0, 100.0, 100.0]})
    confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-meh")], workload=rejected_backends, instrumentation=rejected_backends,
    )
    assert rejected_backends.check_regression_calls == []


def test_confirm_candidates_persists_verdict_and_upserts_knowledge(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    backends = ScriptedBackends(ratio_sequences={("-O3", "-good"): [110.0, 110.0, 110.0]})
    outcomes = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-good")], workload=backends, instrumentation=backends,
    )

    conn = db.connect(cfg.db_path)
    try:
        for trial_id in outcomes[0].trial_ids:
            row = conn.execute("SELECT * FROM trials WHERE id=?", (trial_id,)).fetchone()
            assert row["verdict"] == "accept"
            assert row["delta_vs_baseline_pct"] == pytest.approx(10.0)
            assert row["ci_overlap"] == 0

        knowledge = conn.execute(
            "SELECT * FROM knowledge WHERE flag=? AND cluster_key=?", ("-good", "memory-bound"),
        ).fetchone()
        assert knowledge is not None
        assert knowledge["n_trials"] == 1
        assert knowledge["n_accepted"] == 1
        assert knowledge["mean_delta_pct"] == pytest.approx(10.0)
    finally:
        conn.close()


def test_confirm_candidates_total_failure_rejects_without_knowledge_upsert(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline()
    backends = ScriptedBackends(
        ratio_sequences={("-O3", "-broken"): []}, build_fails_for=frozenset({("-O3", "-broken")}),
    )
    outcomes = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-broken")], workload=backends, instrumentation=backends,
    )
    assert outcomes[0].accepted is False
    assert outcomes[0].ci is None

    conn = db.connect(cfg.db_path)
    try:
        knowledge = conn.execute("SELECT * FROM knowledge WHERE flag=?", ("-broken",)).fetchone()
        assert knowledge is None
    finally:
        conn.close()


# -- greedy_combine -----------------------------------------------------------------

def _confirmed(flag, delta, accepted=True):
    return ConfirmationOutcome(
        flags=[flag], trial_ids=[0], ratios=[], ci=None,
        delta_vs_baseline_pct=delta, accepted=accepted, reason="test",
    )


def test_greedy_combine_builds_a_cumulative_winning_set(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = BaselineResult(
        experiment_id=exp_id, flags=["-O3"], ratios=[100.0] * 3,
        ci=confidence_interval([100.0, 100.0, 100.0]), resource_dominance="memory-bound",
    )
    confirmed = [_confirmed("-flag-a", delta=10.0), _confirmed("-flag-b", delta=5.0)]
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-flag-a"): [110.0, 110.0, 110.0],
        # Same tuple the pair tournament's own (only possible) pair -- {-flag-a,
        # -flag-b} -- would also evaluate (baseline.flags is always included now,
        # confirmed live, 2026-08-22): with only 2 candidates total, the pair
        # tournament can never reach a combination the greedy walk didn't already
        # try, so it just finds this queue exhausted (no usable ratio) and never
        # disturbs the greedy winner. See the *_can_beat_the_greedy_winner test
        # below for a real 3-candidate synergy case where they do diverge.
        ("-O3", "-flag-a", "-flag-b"): [120.0, 120.0, 120.0],
    })

    result = greedy_combine(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, confirmed=confirmed,
        workload=backends, instrumentation=backends, rng=random.Random(0),
    )

    assert result.winning_flags == ["-O3", "-flag-a", "-flag-b"]
    assert result.winning_ci.mean == pytest.approx(120.0)
    assert len(result.steps) == 2
    assert len(result.pair_trials) == 1


def test_greedy_combine_pair_tournament_can_beat_the_greedy_winner(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = BaselineResult(
        experiment_id=exp_id, flags=["-O3"], ratios=[100.0] * 3,
        ci=confidence_interval([100.0, 100.0, 100.0]), resource_dominance="memory-bound",
    )
    # Three candidates, not two -- with only two, the pair tournament's one
    # possible pair is mechanically identical to the greedy walk's own last
    # step (baseline.flags is always included in both now, confirmed live,
    # 2026-08-22), so it can never diverge from what greedy already tried. A
    # real synergy-catching scenario needs a pair the greedy walk *never*
    # reaches -- here, greedy commits to -flag-a first (highest delta), then
    # -flag-b and -flag-c each fail to improve on top of it, but -flag-b and
    # -flag-c *together* (a combination greedy never tries, having already
    # committed to -flag-a) beat the greedy winner.
    confirmed = [
        _confirmed("-flag-a", delta=10.0),
        _confirmed("-flag-b", delta=8.0),
        _confirmed("-flag-c", delta=5.0),
    ]
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-flag-a"): [110.0, 110.0, 110.0],
        # Neither -flag-b nor -flag-c improves on top of -flag-a enough to clear
        # the bar over the current winner (110).
        ("-O3", "-flag-a", "-flag-b"): [109.0, 111.0, 110.0],
        ("-O3", "-flag-a", "-flag-c"): [109.0, 111.0, 110.0],
        # But -flag-b and -flag-c together beat both baseline and the greedy
        # winner -- exactly the synergy the pair tournament exists to catch.
        ("-O3", "-flag-b", "-flag-c"): [125.0, 125.0, 125.0],
    })

    result = greedy_combine(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, confirmed=confirmed,
        workload=backends, instrumentation=backends, rng=random.Random(0),
    )

    assert result.winning_flags == ["-O3", "-flag-b", "-flag-c"]
    assert result.winning_ci.mean == pytest.approx(125.0)


def test_greedy_combine_pair_tournament_is_bounded(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = BaselineResult(
        experiment_id=exp_id, flags=["-O3"], ratios=[100.0] * 3,
        ci=confidence_interval([100.0, 100.0, 100.0]), resource_dominance="memory-bound",
    )
    # 6 accepted candidates -> C(6,2) = 15 possible pairs, well over any reasonable
    # bound -- every trial here has no matching ratio_sequences entry (empty dict),
    # so everything reports "no usable ratio" and nothing is ever accepted; this
    # test only cares about how many pair trials were actually run.
    confirmed = [_confirmed(f"-flag-{i}", delta=float(i)) for i in range(6)]
    backends = ScriptedBackends(ratio_sequences={})

    result = greedy_combine(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, confirmed=confirmed,
        workload=backends, instrumentation=backends, max_pair_trials=3, rng=random.Random(0),
    )

    assert len(result.pair_trials) == 3
    assert result.winning_flags == baseline.flags  # nothing cleared the bar
    assert MAX_PAIR_TOURNAMENT_TRIALS == 10  # sanity: the module default didn't drift silently


# -- full pipeline (Phases 1-5 chained) ----------------------------------------
# Exercises real composition -- Phase N's actual return value feeding Phase N+1,
# not hand-constructed intermediate objects -- which is exactly what cfm mine
# (cli.py) itself does. cli.py's own argv/JSON-summary glue is covered separately
# in tests/test_cli.py with these orchestrator calls mocked; this is the reverse:
# real orchestrator composition, fake workload/instrumentation.

def test_full_pipeline_surfaces_a_genuinely_better_flag(tmp_path):
    cfg = _cfg(tmp_path)
    baseline_flags = ["-O3"]
    candidates = [_candidate("-good-flag"), _candidate("-bad-flag")]
    # Every phase now renders baseline.flags + [candidate.flag] (confirmed live,
    # 2026-08-22 -- see screen_candidates()'s own comment for why), so Phase 3's
    # screening run, Phase 4's 3 confirmation reps, *and* Phase 5's own greedy
    # step for "-good-flag" all share the identical ("-O3", "-good-flag") queue
    # key -- one queue of 1+3+3=7 entries, consumed in call order.
    backends = ScriptedBackends(ratio_sequences={
        ("-O3",): [100.0, 100.0, 100.0, 100.0],  # baseline: 1 characterization + 3 calibration
        ("-O3", "-good-flag"): [
            110.0,                # 1 screening
            111.0, 111.0, 111.0,  # 3 confirmation
            112.0, 112.0, 112.0,  # Phase 5's greedy step
        ],
        ("-O3", "-bad-flag"): [80.0],  # 1 screening only (pruned)
    })

    baseline = run_baseline(
        cfg, benchmark="fake_r", base_flags=baseline_flags, workload=backends, instrumentation=backends,
        reference_matrix_fetch=_no_reference_matrix,
    )
    screened = screen_candidates(
        cfg, experiment_id=baseline.experiment_id, benchmark="fake_r", baseline=baseline,
        candidates=candidates, workload=backends, instrumentation=backends,
    )
    confirmed = confirm_candidates(
        cfg, experiment_id=baseline.experiment_id, benchmark="fake_r", baseline=baseline,
        screened=screened, workload=backends, instrumentation=backends,
    )
    combination = greedy_combine(
        cfg, experiment_id=baseline.experiment_id, benchmark="fake_r", baseline=baseline,
        confirmed=confirmed, workload=backends, instrumentation=backends, rng=random.Random(0),
    )

    assert {o.candidate.flag for o in screened if o.survived} == {"-good-flag"}
    assert len(confirmed) == 1
    assert confirmed[0].accepted is True
    assert combination.winning_flags == ["-O3", "-good-flag"]
    assert combination.winning_ci.mean == pytest.approx(112.0)


def test_full_pipeline_reports_baseline_when_nothing_helps(tmp_path):
    cfg = _cfg(tmp_path)
    candidates = [_candidate("-bad-flag-1"), _candidate("-bad-flag-2")]
    backends = ScriptedBackends(ratio_sequences={
        ("-O3",): [100.0, 100.0, 100.0, 100.0],  # 1 characterization + 3 calibration
        ("-O3", "-bad-flag-1"): [70.0],
        ("-O3", "-bad-flag-2"): [60.0],
    })

    baseline = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"], workload=backends, instrumentation=backends,
        reference_matrix_fetch=_no_reference_matrix,
    )
    screened = screen_candidates(
        cfg, experiment_id=baseline.experiment_id, benchmark="fake_r", baseline=baseline,
        candidates=candidates, workload=backends, instrumentation=backends,
    )
    confirmed = confirm_candidates(
        cfg, experiment_id=baseline.experiment_id, benchmark="fake_r", baseline=baseline,
        screened=screened, workload=backends, instrumentation=backends,
    )
    combination = greedy_combine(
        cfg, experiment_id=baseline.experiment_id, benchmark="fake_r", baseline=baseline,
        confirmed=confirmed, workload=backends, instrumentation=backends, rng=random.Random(0),
    )

    assert all(not o.survived for o in screened)
    assert confirmed == []
    assert combination.winning_flags == baseline.flags


# -- run_pgo_multiplier (Phase 6, PGO slice) ------------------------------------

def test_run_pgo_multiplier_accepts_a_real_improvement(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", PGO_FLAG): [130.0, 130.0, 130.0],
    })

    result = run_pgo_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is True
    assert result.outcome.accepted is True
    assert result.winning_flags == ["-O3", PGO_FLAG]
    assert result.winning_ci.mean == pytest.approx(130.0)


def test_run_pgo_multiplier_rejects_when_not_better(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", PGO_FLAG): [99.0, 100.0, 101.0],  # flat -- no real improvement
    })

    result = run_pgo_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is True
    assert result.outcome.accepted is False
    assert result.winning_flags == combination.winning_flags  # unchanged -- PGO didn't win
    assert result.winning_ci is combination.winning_ci


@pytest.mark.parametrize("resource_dominance,pct", [
    # 777.zstd_r's real shape: the clearest memory-bound margin on niwot, which
    # used to skip PGO outright.
    ("memory-bound", 64.0),
    # 750.sealcrypto_r's: just above the old 55% gate, where the skip hid +10.4%.
    ("compute-bound", 55.1),
    ("memory-bound", 45.2),
    (None, None),
])
def test_run_pgo_multiplier_is_attempted_whatever_the_baseline_shape(tmp_path, resource_dominance, pct):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0, resource_dominance=resource_dominance, resource_dominance_pct=pct)
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={("-O3", PGO_FLAG): [110.0, 110.0, 110.0]})

    result = run_pgo_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is True
    assert result.skip_reason is None
    assert result.outcome.accepted is True


def test_run_pgo_multiplier_upserts_knowledge_keyed_by_pgo_flag(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0, resource_dominance="frontend-bound")
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={("-O3", PGO_FLAG): [130.0, 130.0, 130.0]})

    run_pgo_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        workload=backends, instrumentation=backends,
    )

    conn = db.connect(cfg.db_path)
    try:
        row = conn.execute(
            "SELECT * FROM knowledge WHERE flag=? AND cluster_key=?", (PGO_FLAG, "frontend-bound"),
        ).fetchone()
        assert row is not None
        assert row["n_trials"] == 1
        assert row["n_accepted"] == 1

        trial_rows = conn.execute(
            "SELECT DISTINCT phase FROM trials WHERE experiment_id=?", (exp_id,),
        ).fetchall()
        assert {r["phase"] for r in trial_rows} == {"multiplier"}
    finally:
        conn.close()
    assert combination.winning_ci is baseline.ci


# -- find_near_miss_flags / near-miss PGO variant --------------------------------

def _measured(flag, ratios, accepted=False, base_mean=100.0):
    ci = confidence_interval(ratios)
    return ConfirmationOutcome(
        flags=["-O3", flag], trial_ids=[0], ratios=ratios, ci=ci,
        delta_vs_baseline_pct=(ci.mean - base_mean) / base_mean * 100.0, accepted=accepted, reason="test",
    )


def test_find_near_miss_flags_keeps_only_ci_clear_sub_threshold_rejects():
    baseline = _baseline(mean_ratio=100.0)  # zero-width CI at 100.0
    confirmed = [
        _measured("-small", [100.4, 100.5, 100.6]),          # +0.5%, CI clear -> near miss
        _measured("-bigger", [100.8, 100.9, 101.0]),         # +0.9%, CI clear -> near miss, first
        _measured("-overlaps", [99.0, 100.5, 102.0]),        # CI overlaps baseline
        _measured("-worse", [99.0, 99.1, 99.2]),             # CI clear, but below
        _measured("-won", [105.0, 105.0, 105.1], accepted=True),
        ConfirmationOutcome(flags=["-O3", "-nobuild"], trial_ids=[0], ratios=[], ci=None,
                            delta_vs_baseline_pct=None, accepted=False, reason="test"),
    ]

    assert find_near_miss_flags(confirmed, baseline, ["-O3", "-won"]) == ["-bigger", "-small"]


def test_find_near_miss_flags_skips_a_flag_already_in_the_winning_set():
    baseline = _baseline(mean_ratio=100.0)
    confirmed = [_measured("-flto", [100.9, 101.0, 100.95])]

    assert find_near_miss_flags(confirmed, baseline, ["-O3", "-flto"]) == []


def _near_miss_pgo(tmp_path, ratio_sequences):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()
    baseline = _baseline(mean_ratio=100.0, resource_dominance="frontend-bound")
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences=ratio_sequences)
    result = run_pgo_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        near_miss_flags=["-flto"],
        workload=backends, instrumentation=backends,
    )
    return cfg, result


def test_run_pgo_multiplier_near_miss_variant_wins_when_clear_of_plain_pgo(tmp_path):
    # 727.cppcheck_r's real shape on niwot: PGO 26.72, -flto + PGO 27.42.
    cfg, result = _near_miss_pgo(tmp_path, {
        ("-O3", PGO_FLAG): [107.5, 107.6, 107.0],
        ("-O3", "-flto", PGO_FLAG): [110.4, 110.3, 110.3],
    })

    assert [o.flags for o in result.outcomes] == [["-O3", PGO_FLAG], ["-O3", "-flto", PGO_FLAG]]
    assert result.winning_flags == ["-O3", "-flto", PGO_FLAG]
    assert result.outcome is result.outcomes[1]

    # Only plain PGO's delta is PGO's alone, so only it lands in the knowledge table.
    conn = db.connect(cfg.db_path)
    try:
        row = conn.execute("SELECT n_trials FROM knowledge WHERE flag=?", (PGO_FLAG,)).fetchone()
        assert row["n_trials"] == 1
    finally:
        conn.close()


def test_run_pgo_multiplier_keeps_plain_pgo_when_the_variant_overlaps_it(tmp_path):
    _, result = _near_miss_pgo(tmp_path, {
        ("-O3", PGO_FLAG): [107.0, 108.0, 109.0],
        ("-O3", "-flto", PGO_FLAG): [107.5, 108.5, 109.5],  # higher mean, CIs overlap
    })

    assert result.outcomes[1].accepted is True
    assert result.winning_flags == ["-O3", PGO_FLAG]
    assert result.outcome is result.outcomes[0]


def test_run_pgo_multiplier_near_miss_variant_wins_when_plain_pgo_rejects(tmp_path):
    _, result = _near_miss_pgo(tmp_path, {
        ("-O3", PGO_FLAG): [99.0, 100.0, 101.0],
        ("-O3", "-flto", PGO_FLAG): [105.0, 105.1, 105.2],
    })

    assert result.outcomes[0].accepted is False
    assert result.winning_flags == ["-O3", "-flto", PGO_FLAG]


def test_run_pgo_multiplier_both_rejected_keeps_the_incoming_set(tmp_path):
    _, result = _near_miss_pgo(tmp_path, {
        ("-O3", PGO_FLAG): [95.0, 95.1, 95.2],
        ("-O3", "-flto", PGO_FLAG): [96.0, 96.1, 96.2],
    })

    assert result.attempted is True
    assert result.winning_flags == ["-O3"]
    assert result.outcome is result.outcomes[-1]


# -- run_microarch_multiplier (Phase 6, microarch slice) ------------------------

def _fake_cpu_info_dir(tmp_path, stdout: str, exit_code: int = 0) -> Path:
    """A wspy_dir containing just a fake `cpu_info` script -- reuses the same
    technique tests/test_hostinfo.py uses for that module's own direct tests.
    """
    wspy_dir = tmp_path / "wspy-unused"
    wspy_dir.mkdir(exist_ok=True)
    script = wspy_dir / "cpu_info"
    script.write_text(f"#!/bin/sh\ncat <<'EOF'\n{stdout}\nEOF\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return wspy_dir


_ZEN5_CPU_INFO_OUTPUT = "CPU information:\n\tAMD family 1a model 70\n\t   * 0 Zen5\n\t   * 1 Zen5\n"


def test_run_microarch_multiplier_accepts_march_over_baseline(tmp_path):
    cfg = _cfg(tmp_path)
    _fake_cpu_info_dir(tmp_path, _ZEN5_CPU_INFO_OUTPUT)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-march=znver5"): [115.0, 115.0, 115.0],
        ("-O3", "-mtune=znver5"): [102.0, 102.0, 102.0],  # worse than -march=, shouldn't win
    })

    result = run_microarch_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is True
    assert result.winning_flags == ["-O3", "-march=znver5"]
    assert result.winning_ci.mean == pytest.approx(115.0)
    assert len(result.outcomes) == 2  # both candidates tried, even though only one won


def test_run_microarch_multiplier_rejects_when_neither_helps(tmp_path):
    cfg = _cfg(tmp_path)
    _fake_cpu_info_dir(tmp_path, _ZEN5_CPU_INFO_OUTPUT)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-march=znver5"): [99.0, 100.0, 101.0],
        ("-O3", "-mtune=znver5"): [98.0, 99.0, 100.0],
    })

    result = run_microarch_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is True
    assert result.winning_flags == combination.winning_flags  # unchanged
    assert result.winning_ci is combination.winning_ci
    assert all(not o.accepted for o in result.outcomes)


def test_run_microarch_multiplier_skips_when_nothing_detected(tmp_path):
    # _cfg()'s own wspy_dir ("wspy-unused") has no cpu_info at all -- the
    # default, no fake binary set up here.
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={})  # must never be reached

    result = run_microarch_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is False
    assert result.outcomes == []
    assert "no confidently-detected" in result.skip_reason
    assert result.winning_flags == combination.winning_flags


def test_run_microarch_multiplier_skips_when_march_already_present(tmp_path):
    cfg = _cfg(tmp_path)
    _fake_cpu_info_dir(tmp_path, _ZEN5_CPU_INFO_OUTPUT)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    # e.g. -march=native already accepted via the ordinary Phase 2-5 per-flag path.
    combination = CombinationResult(winning_flags=["-O3", "-march=native"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={})  # must never be reached

    result = run_microarch_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is False
    assert "already" in result.skip_reason
    assert result.winning_flags == ["-O3", "-march=native"]


def test_run_microarch_multiplier_chains_off_a_prior_multiplier_result(tmp_path):
    # combination is duck-typed -- confirms this accepts run_pgo_multiplier()'s
    # own MultiplierResult (as cli.py's real chained wiring does), not just a
    # Phase 5 CombinationResult.
    from cfm.orchestrator import MultiplierResult

    cfg = _cfg(tmp_path)
    _fake_cpu_info_dir(tmp_path, _ZEN5_CPU_INFO_OUTPUT)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    prior = MultiplierResult(
        attempted=True, winning_flags=["-O3", PGO_FLAG], winning_ci=confidence_interval([130.0] * 3),
    )
    backends = ScriptedBackends(ratio_sequences={
        (("-O3", PGO_FLAG, "-march=znver5")): [150.0, 150.0, 150.0],
        (("-O3", PGO_FLAG, "-mtune=znver5")): [131.0, 131.0, 131.0],
    })

    result = run_microarch_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=prior,
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is True
    assert result.winning_flags == ["-O3", PGO_FLAG, "-march=znver5"]
    assert result.winning_ci.mean == pytest.approx(150.0)


# -- M4: split_candidates_by_known_prior / confirm_known_candidates ------------

def _known(flag, mean_delta_pct, n_accepted, n_trials=1, last_benchmark="706.stockfish_r"):
    return KnownFlag(
        flag=flag, mean_delta_pct=mean_delta_pct, n_trials=n_trials,
        n_accepted=n_accepted, last_benchmark=last_benchmark,
    )


def test_split_candidates_by_known_prior_fast_tracks_only_accepted_priors(tmp_path):
    candidates = [_candidate("-march=native"), _candidate("-fgraphite-identity"), _candidate("-new-flag")]
    known_flags = {
        "-march=native": _known("-march=native", mean_delta_pct=48.75, n_accepted=1),
        "-fgraphite-identity": _known("-fgraphite-identity", mean_delta_pct=-4.22, n_accepted=0),
        # "-new-flag" has no prior at all -- not in known_flags.
    }

    fast_tracked, remaining = split_candidates_by_known_prior(candidates, known_flags)

    assert [c.flag for c in fast_tracked] == ["-march=native"]  # only the accepted prior
    assert {c.flag for c in remaining} == {"-fgraphite-identity", "-new-flag"}  # rejected + unknown both stay


def test_split_candidates_by_known_prior_orders_fast_tracked_by_best_evidence_first(tmp_path):
    candidates = [_candidate("-flag-a"), _candidate("-flag-b")]
    known_flags = {
        "-flag-a": _known("-flag-a", mean_delta_pct=5.0, n_accepted=1),
        "-flag-b": _known("-flag-b", mean_delta_pct=40.0, n_accepted=1),
    }

    fast_tracked, remaining = split_candidates_by_known_prior(candidates, known_flags)

    assert [c.flag for c in fast_tracked] == ["-flag-b", "-flag-a"]  # 40% before 5%
    assert remaining == []


def test_split_candidates_by_known_prior_screens_a_minority_accepted_prior(tmp_path):
    # 735.gem5_r's real case: -march=native at 1 of 5 accepted, mean still +8.62%
    # (one +48% outlier). It used to be fast-tracked; now it's screened like anything else.
    candidates = [_candidate("-march=native"), _candidate("-flto")]
    known_flags = {
        "-march=native": _known("-march=native", mean_delta_pct=8.62, n_accepted=1, n_trials=5),
        "-flto": _known("-flto", mean_delta_pct=5.93, n_accepted=3, n_trials=4),
    }

    fast_tracked, remaining = split_candidates_by_known_prior(candidates, known_flags)

    assert [c.flag for c in fast_tracked] == ["-flto"]
    assert [c.flag for c in remaining] == ["-march=native"]


def test_split_candidates_by_known_prior_no_priors_leaves_everything_in_remaining(tmp_path):
    candidates = [_candidate("-a"), _candidate("-b")]
    fast_tracked, remaining = split_candidates_by_known_prior(candidates, known_flags={})
    assert fast_tracked == []
    assert [c.flag for c in remaining] == ["-a", "-b"]


def test_confirm_known_candidates_skips_screening_and_confirms_directly(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    candidates = [_candidate("-march=native")]
    # No screening-trial ratio queued at all for ("-O3", "-march=native") --
    # only a confirmation-grade queue with 3 entries. If this accidentally
    # went through screen_candidates() first, it would consume one of these
    # early and the 3rd confirmation rep would find an empty queue.
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-march=native"): [148.0, 147.0, 146.0],
    })

    outcomes = confirm_known_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        candidates=candidates, workload=backends, instrumentation=backends,
    )

    assert len(outcomes) == 1
    assert outcomes[0].flags == ["-O3", "-march=native"]
    assert outcomes[0].accepted is True
    assert len(outcomes[0].ratios) == 3  # all 3 confirmation reps consumed, none wasted on screening

    conn = db.connect(cfg.db_path)
    try:
        phases = {r["phase"] for r in conn.execute(
            "SELECT phase FROM trials WHERE experiment_id=?", (exp_id,),
        ).fetchall()}
        assert phases == {"confirmation"}  # never "screening"
    finally:
        conn.close()


# -- no-code-change guard -------------------------------------------------------

def _experiment_with_baseline_fingerprint(cfg, flags, fingerprint):
    """An experiment whose baseline trial for ``flags`` recorded ``fingerprint``,
    the way run_baseline()'s real reps would."""
    conn = db.connect(cfg.db_path)
    try:
        exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
        trial_id = db.record_trial(
            conn, experiment_id=exp_id, phase="confirmation", flags=flags,
            optimize_string=" ".join(flags), build_status="ok", ratio=100.0, code_fingerprint=fingerprint,
        )
    finally:
        conn.close()
    return exp_id, trial_id


def test_screen_candidates_skips_the_timed_run_when_the_code_is_unchanged(tmp_path):
    cfg = _cfg(tmp_path)
    exp_id, baseline_trial = _experiment_with_baseline_fingerprint(cfg, ["-O3"], "code-A")
    backends = ScriptedBackends(
        ratio_sequences={("-O3", "-noop"): [150.0], ("-O3", "-real"): [110.0]},
        code_for={("-O3", "-noop"): "code-A", ("-O3", "-real"): "code-B"},
    )

    outcomes = screen_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=_baseline(mean_ratio=100.0),
        candidates=[_candidate("-noop"), _candidate("-real")], workload=backends, instrumentation=backends,
    )

    by_flag = {o.candidate.flag: o for o in outcomes}
    assert by_flag["-noop"].unchanged is True
    assert by_flag["-noop"].survived is False
    assert by_flag["-noop"].ratio is None
    assert f"trial {baseline_trial}" in by_flag["-noop"].reason
    assert by_flag["-real"].unchanged is False and by_flag["-real"].survived is True
    assert backends.timed_runs == [("-O3", "-real")]  # -noop was built but never run

    conn = db.connect(cfg.db_path)
    try:
        row = conn.execute(
            "SELECT ratio, code_fingerprint FROM trials WHERE id=?", (by_flag["-noop"].trial_id,),
        ).fetchone()
        assert row["ratio"] is None and row["code_fingerprint"] == "code-A"
    finally:
        conn.close()


def test_screen_candidates_never_skips_without_a_fingerprint(tmp_path):
    # A backend (or binary) that can't be fingerprinted must never be treated as unchanged.
    cfg = _cfg(tmp_path)
    exp_id, _ = _experiment_with_baseline_fingerprint(cfg, ["-O3"], "code-A")
    backends = ScriptedBackends(ratio_sequences={("-O3", "-maybe"): [101.0]})

    outcomes = screen_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=_baseline(mean_ratio=100.0),
        candidates=[_candidate("-maybe")], workload=backends, instrumentation=backends,
    )

    assert outcomes[0].unchanged is False and outcomes[0].ratio == 101.0


def test_confirm_known_candidates_rejects_unchanged_code_after_one_build_without_a_knowledge_row(tmp_path):
    cfg = _cfg(tmp_path)
    exp_id, _ = _experiment_with_baseline_fingerprint(cfg, ["-O3"], "code-A")
    backends = ScriptedBackends(
        ratio_sequences={("-O3", "-noop"): [150.0, 150.0, 150.0]},
        code_for={("-O3", "-noop"): "code-A"},
    )

    outcomes = confirm_known_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=_baseline(mean_ratio=100.0),
        candidates=[_candidate("-noop")], workload=backends, instrumentation=backends,
    )

    assert outcomes[0].unchanged is True and outcomes[0].accepted is False
    assert len(outcomes[0].trial_ids) == 1 and outcomes[0].ratios == []
    assert backends.timed_runs == []
    conn = db.connect(cfg.db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0] == 0
        assert conn.execute(
            "SELECT verdict FROM trials WHERE id=?", (outcomes[0].trial_ids[0],),
        ).fetchone()[0] == "reject"
    finally:
        conn.close()


def test_greedy_combine_compares_code_against_the_running_set_not_the_baseline(tmp_path):
    # -b changes the code on its own (Phase 4 accepted it) but not on top of -a:
    # the greedy step adding it must be skipped against the running set's code.
    cfg = _cfg(tmp_path)
    exp_id, _ = _experiment_with_baseline_fingerprint(cfg, ["-O3"], "code-base")
    backends = ScriptedBackends(
        ratio_sequences={("-O3", "-a"): [120.0, 120.5, 121.0]},
        code_for={("-O3", "-a"): "code-a", ("-O3", "-a", "-b"): "code-a"},
    )
    baseline = _baseline(mean_ratio=100.0)
    confirmed = [
        ConfirmationOutcome(
            flags=["-O3", flag], trial_ids=[], ratios=[], ci=None,
            delta_vs_baseline_pct=delta, accepted=True, reason="",
        )
        for flag, delta in (("-a", 20.0), ("-b", 10.0))
    ]

    result = greedy_combine(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, confirmed=confirmed,
        workload=backends, instrumentation=backends, max_pair_trials=0,
    )

    assert result.winning_flags == ["-O3", "-a"]
    assert [s.unchanged for s in result.steps] == [False, True]
    assert ("-O3", "-a", "-b") not in backends.timed_runs


# -- vector-width deferral and multiplier ---------------------------------------

def test_defer_vector_width_candidates_holds_them_back_without_march():
    candidates = [_candidate("-flto"), _candidate("-mprefer-vector-width=256"), _candidate("-mprefer-vector-width=512")]
    deferred, remaining = defer_vector_width_candidates(candidates, ["-O3"])
    assert [c.flag for c in deferred] == ["-mprefer-vector-width=256", "-mprefer-vector-width=512"]
    assert [c.flag for c in remaining] == ["-flto"]


def test_defer_vector_width_candidates_keeps_them_when_base_already_has_march():
    candidates = [_candidate("-flto"), _candidate("-mprefer-vector-width=512")]
    deferred, remaining = defer_vector_width_candidates(candidates, ["-O3", "-march=znver5"])
    assert deferred == []
    assert [c.flag for c in remaining] == ["-flto", "-mprefer-vector-width=512"]


def test_run_vector_width_multiplier_skips_without_march_in_winning_set(tmp_path):
    cfg = _cfg(tmp_path)
    baseline = _baseline(mean_ratio=100.0)
    combination = CombinationResult(winning_flags=["-O3", "-flto"], winning_ci=baseline.ci)
    backends = ScriptedBackends(ratio_sequences={})  # any trial would hit an empty queue

    result = run_vector_width_multiplier(
        cfg, experiment_id=1, benchmark="fake_r", baseline=baseline, combination=combination,
        candidates=[_candidate("-mprefer-vector-width=512")], workload=backends, instrumentation=backends,
    )

    assert result.attempted is False
    assert "no -march=" in result.skip_reason
    assert result.winning_flags == ["-O3", "-flto"]


def test_run_vector_width_multiplier_skips_with_no_candidates(tmp_path):
    cfg = _cfg(tmp_path)
    baseline = _baseline(mean_ratio=100.0)
    combination = CombinationResult(winning_flags=["-O3", "-march=native"], winning_ci=baseline.ci)

    result = run_vector_width_multiplier(
        cfg, experiment_id=1, benchmark="fake_r", baseline=baseline, combination=combination,
        candidates=[],
    )

    assert result.attempted is False
    assert result.winning_flags == ["-O3", "-march=native"]


def test_run_vector_width_multiplier_layers_on_march_and_keeps_the_best(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    combination = CombinationResult(
        winning_flags=["-O3", "-march=native"], winning_ci=confidence_interval([110.0, 110.0, 110.0]),
    )
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-march=native", "-mprefer-vector-width=256"): [110.2, 110.1, 110.3],  # flat
        ("-O3", "-march=native", "-mprefer-vector-width=512"): [116.0, 116.0, 116.0],
    })

    result = run_vector_width_multiplier(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, combination=combination,
        candidates=[_candidate("-mprefer-vector-width=256"), _candidate("-mprefer-vector-width=512")],
        workload=backends, instrumentation=backends,
    )

    assert result.attempted is True
    assert result.winning_flags == ["-O3", "-march=native", "-mprefer-vector-width=512"]
    assert len(result.outcomes) == 2



# -- settle-based warm-up and low-power reruns (2026-10-26) ---------------------

def _power_sequence(monkeypatch, values):
    """Each run_one_trial() call takes the next reading: fake runs finish before the
    sampler's first tick, so run_one_trial() falls back to one reading after the run."""
    import cfm.agents.spec_agent as spec_agent
    queue = deque(values)
    monkeypatch.setattr(spec_agent, "read_package_power_watts", lambda: queue.popleft() if queue else None)


def test_run_baseline_warms_up_until_two_reps_agree(tmp_path):
    cfg = _cfg(tmp_path)
    # Warm-ups 120 -> 110 (8% apart) -> 101 (8%) -> 100 (1%, settled), then calibration.
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): [999.0, 120.0, 110.0, 101.0, 100.0, 100.0, 101.0, 99.0]},
    )
    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends, reference_matrix_fetch=_no_reference_matrix,
    )
    assert result.ratios == [100.0, 101.0, 99.0]
    assert len(result.trial_ids) == 8  # 1 characterization + 4 warm-up + 3 calibration


def test_run_baseline_warms_up_for_at_least_the_minimum_time(tmp_path, monkeypatch):
    import cfm.orchestrator as orchestrator
    cfg = CfmConfig.from_env(
        spec_dir=str(tmp_path / "spec"), wspy_dir=str(tmp_path / "wspy-unused"),
        output_root=str(tmp_path / "results"), db_path=str(tmp_path / "cfm.db"),
        warmup_min_seconds=100.0,
    )
    clock = iter(range(0, 10_000, 30))  # every clock read is 30 s after the last
    monkeypatch.setattr(orchestrator, "_clock", lambda: next(clock))
    # Every warm-up agrees, so only the minimum time keeps it going. The start
    # reads 0 s; after warm-ups 2, 3 and 4 the clock reads 30, 60, 90 s (short),
    # and after the 5th it reads 120 s, which ends it.
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): [999.0] + [100.0] * 5 + [100.0, 101.0, 99.0]},
    )
    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends, reference_matrix_fetch=_no_reference_matrix,
    )
    assert result.ratios == [100.0, 101.0, 99.0]
    assert len(result.trial_ids) == 9  # 1 characterization + 5 warm-up + 3 calibration


def test_run_baseline_stops_warming_up_at_the_cap(tmp_path):
    from cfm.orchestrator import BASELINE_WARMUP_MAX_REPETITIONS
    cfg = _cfg(tmp_path)
    never_settles = [100.0 + 10.0 * (i % 2) for i in range(BASELINE_WARMUP_MAX_REPETITIONS)]
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): [999.0] + never_settles + [100.0, 101.0, 99.0]},
    )
    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends, reference_matrix_fetch=_no_reference_matrix,
    )
    assert result.ratios == [100.0, 101.0, 99.0]
    assert len(result.trial_ids) == 1 + BASELINE_WARMUP_MAX_REPETITIONS + 3
    conn = db.connect(cfg.db_path)
    try:
        notes = [r["rationale"] for r in conn.execute(
            "SELECT rationale FROM hypotheses WHERE rationale LIKE 'baseline warm-up NOT settled%'")]
    finally:
        conn.close()
    assert len(notes) == 1


def test_confirm_reruns_a_low_power_rep_when_the_power_check_is_on(tmp_path, monkeypatch):
    import cfm.orchestrator as orchestrator
    cfg = CfmConfig.from_env(
        spec_dir=str(tmp_path / "spec"), wspy_dir=str(tmp_path / "wspy-unused"),
        output_root=str(tmp_path / "results"), db_path=str(tmp_path / "cfm.db"),
        power_check=True,
    )
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()
    baseline = _baseline(mean_ratio=100.0)
    baseline.power_w = 30.0
    slept = []
    monkeypatch.setattr(orchestrator, "_sleep", slept.append)
    # The second rep ran at 24 W (20% low) and read a little slow, but not 10% slow.
    _power_sequence(monkeypatch, [30.0, 24.0, 30.0, 29.5])
    backends = ScriptedBackends(ratio_sequences={("-O3", "-x"): [100.0, 95.0, 100.5, 100.2]})

    [outcome] = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-x")], workload=backends, instrumentation=backends,
    )

    assert outcome.ratios == [100.0, 100.2, 100.5]
    assert len(outcome.trial_ids) == 4
    assert slept == [orchestrator.LOW_POWER_RERUN_IDLE_S]


def test_confirm_ignores_low_power_when_the_power_check_is_off(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()
    baseline = _baseline(mean_ratio=100.0)
    baseline.power_w = 30.0
    _power_sequence(monkeypatch, [30.0, 24.0, 30.0])
    backends = ScriptedBackends(ratio_sequences={("-O3", "-x"): [100.0, 95.0, 100.5]})

    [outcome] = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-x")], workload=backends, instrumentation=backends,
    )

    assert outcome.ratios == [100.0, 95.0, 100.5]
    assert len(outcome.trial_ids) == 3


def test_run_baseline_records_the_calibration_reps_median_power(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    _power_sequence(monkeypatch, [20.0, 25.0, 26.0, 29.0, 30.0, 31.0])
    backends = ScriptedBackends(ratio_sequences={("-O3",): [999.0, 777.0, 777.0, 100.0, 101.0, 99.0]})
    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends, reference_matrix_fetch=_no_reference_matrix,
    )
    assert result.power_w == pytest.approx(30.0)
