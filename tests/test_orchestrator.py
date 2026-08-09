"""Unit tests for cfm/orchestrator.py's Phase 1 (baseline)/2 (candidates)/3
(screening) logic -- entirely against fake WorkloadBackend/InstrumentationBackend
implementations (ScriptedBackends below), no real SPEC/wspy calls, matching every
other test tier's "no real runcpu/wspy" posture (CLAUDE.md's Build & test section).
"""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path

import pytest

import cfm.db as db
from cfm.compilers.base import FlagCandidate
from cfm.compilers.gcc import GccCompiler
from cfm.config import CfmConfig
from cfm.instrumentation.base import InstrumentationBackend, RunSignature
from cfm.orchestrator import (
    MAX_PAIR_TOURNAMENT_TRIALS,
    BaselineResult,
    ConfirmationOutcome,
    ScreeningOutcome,
    confirm_candidates,
    generate_candidates,
    greedy_combine,
    run_baseline,
    screen_candidates,
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
        build_fails_for: frozenset = frozenset(),
        regression_rows: list = None,
    ):
        self._queues = {k: deque(v) for k, v in ratio_sequences.items()}
        self.resource_dominance = resource_dominance
        self._rd_sequence = deque(resource_dominance_sequence) if resource_dominance_sequence else None
        self.build_fails_for = build_fails_for
        self._current_flags = None
        self.regression_rows = regression_rows if regression_rows is not None else []
        self.check_regression_calls: list[str] = []

    # -- WorkloadBackend --
    def generate_config(self, bench, tune, flags):
        self._current_flags = tuple(flags)
        return Path("/fake/config.cfg")

    def build(self, bench, tune, config_path):
        if self._current_flags in self.build_fails_for:
            return BuildResult(ok=False, log_path=Path("/fake/build.log"), raw_output="fake build failure")
        return BuildResult(ok=True, log_path=Path("/fake/build.log"), raw_output="ok")

    def run_command(self, bench, tune, config_path, iterations):
        return ["fake-run"]

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
            memory_attribution="corroborated", metrics={}, raw_output="",
        )

    def check_regression(self, wspy_run_ref):
        self.check_regression_calls.append(wspy_run_ref)
        return self.regression_rows


def _cfg(tmp_path):
    return CfmConfig.from_env(
        spec_dir=str(tmp_path / "spec"), wspy_dir=str(tmp_path / "wspy-unused"),
        output_root=str(tmp_path / "results"), db_path=str(tmp_path / "cfm.db"),
    )


# -- run_baseline -------------------------------------------------------------

def test_run_baseline_computes_ci_over_repeated_trials(tmp_path):
    cfg = _cfg(tmp_path)
    backends = ScriptedBackends(ratio_sequences={("-O3",): [100.0, 102.0, 98.0]})

    result = run_baseline(
        cfg, benchmark="fake_r", base_flags=["-O3"],
        workload=backends, instrumentation=backends,
    )

    assert isinstance(result, BaselineResult)
    assert result.ratios == [100.0, 102.0, 98.0]
    assert result.ci.n == 3
    assert result.ci.mean == pytest.approx(100.0)
    assert result.ci.verdict == "PASS"
    assert result.resource_dominance == "memory-bound"
    assert len(result.trial_ids) == 3

    conn = db.connect(cfg.db_path)
    try:
        exp = db.get_experiment(conn, result.experiment_id)
        assert exp["baseline_run_ref"] is not None
        assert exp["baseline_run_ref"].startswith("fakehost:")
        assert exp["status"] == "running"  # set_baseline_run_ref must not finish it
        trials = db.list_trials_by_phase(conn, result.experiment_id, "confirmation")
        assert len(trials) == 3
    finally:
        conn.close()


def test_run_baseline_warns_on_disagreeing_resource_dominance(tmp_path, capsys):
    cfg = _cfg(tmp_path)
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): [100.0, 100.0, 100.0]},
        resource_dominance_sequence=["memory-bound", "compute-bound", "memory-bound"],
    )
    run_baseline(cfg, benchmark="fake_r", base_flags=["-O3"], workload=backends, instrumentation=backends)
    assert "disagreed" in capsys.readouterr().out


def test_run_baseline_raises_when_every_repetition_fails_to_build(tmp_path):
    cfg = _cfg(tmp_path)
    backends = ScriptedBackends(
        ratio_sequences={("-O3",): []}, build_fails_for=frozenset({("-O3",)}),
    )
    with pytest.raises(RuntimeError, match="fake_r"):
        run_baseline(cfg, benchmark="fake_r", base_flags=["-O3"], workload=backends, instrumentation=backends)


# -- screen_candidates ----------------------------------------------------------

def _baseline(mean_ratio=100.0):
    ci = confidence_interval([mean_ratio, mean_ratio, mean_ratio])
    return BaselineResult(
        experiment_id=1, flags=["-O3"], ratios=[mean_ratio] * 3, ci=ci,
        resource_dominance="memory-bound", trial_ids=[1, 2, 3],
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
        ("-good",): [110.0],      # +10% -- clearly better, survives
        ("-bad",): [80.0],        # -20% -- clearly worse, pruned
        ("-marginal",): [96.0],   # -4% -- within the 5% prune bar, survives
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


def test_screen_candidates_build_failure_does_not_survive(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline()
    candidates = [_candidate("-broken")]
    backends = ScriptedBackends(
        ratio_sequences={("-broken",): []}, build_fails_for=frozenset({("-broken",)}),
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
    backends = ScriptedBackends(ratio_sequences={("-good",): [110.0]})
    outcomes = screen_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        candidates=candidates, workload=backends, instrumentation=backends,
    )

    conn = db.connect(cfg.db_path)
    try:
        row = conn.execute(
            "SELECT * FROM hypotheses WHERE trial_id=?", (outcomes[0].trial_id,)
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


def test_generate_candidates_filters_by_language_and_ignores_signature(tmp_path):
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

    # Same call, two different (fabricated) baseline signatures -- M1 must ignore
    # resource_dominance entirely and return the same result either way.
    baseline_a = _baseline()
    baseline_a.resource_dominance = "memory-bound"
    baseline_b = _baseline()
    baseline_b.resource_dominance = "frontend-bound"

    candidates_a = generate_candidates(cfg, benchmark="fake_r", baseline=baseline_a, compiler=compiler)
    candidates_b = generate_candidates(cfg, benchmark="fake_r", baseline=baseline_b, compiler=compiler)

    assert {c.flag for c in candidates_a} == {"-c-flag"}
    assert {c.flag for c in candidates_a} == {c.flag for c in candidates_b}


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
    backends = ScriptedBackends(ratio_sequences={("-good",): [109.0, 110.0, 111.0]})

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
    backends = ScriptedBackends(ratio_sequences={("-good",): [110.0, 110.0, 110.0]})
    outcomes = confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-good", survived=True), _screened("-bad", survived=False)],
        workload=backends, instrumentation=backends,
    )
    assert len(outcomes) == 1
    assert outcomes[0].flags == ["-good"]


def test_confirm_candidates_rejects_when_ci_overlaps_baseline(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    exp_id = db.create_experiment(conn, benchmark="fake_r", hostname="h", compiler="gcc")
    conn.close()

    baseline = _baseline(mean_ratio=100.0)
    # No real difference from baseline -- CIs will overlap.
    backends = ScriptedBackends(ratio_sequences={("-meh",): [99.0, 100.0, 101.0]})
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
        ratio_sequences={("-good",): [110.0, 110.0, 110.0]},
        regression_rows=[{"metric": "ipc", "status": "within", "baseline_verdict": "PASS"}],
    )
    confirm_candidates(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline,
        screened=[_screened("-good")], workload=accepted_backends, instrumentation=accepted_backends,
    )
    assert len(accepted_backends.check_regression_calls) == 3  # once per repetition

    rejected_backends = ScriptedBackends(ratio_sequences={("-meh",): [100.0, 100.0, 100.0]})
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
    backends = ScriptedBackends(ratio_sequences={("-good",): [110.0, 110.0, 110.0]})
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
        ratio_sequences={("-broken",): []}, build_fails_for=frozenset({("-broken",)}),
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
        ("-O3", "-flag-a", "-flag-b"): [120.0, 120.0, 120.0],
        ("-flag-a", "-flag-b"): [108.0, 108.0, 108.0],  # pair alone -- worse than the greedy winner
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
    confirmed = [_confirmed("-flag-a", delta=10.0), _confirmed("-flag-b", delta=8.0)]
    backends = ScriptedBackends(ratio_sequences={
        ("-O3", "-flag-a"): [110.0, 110.0, 110.0],
        # Adding -flag-b on top of -flag-a doesn't clear the bar over the current
        # winner (110) -- an interaction effect the greedy walk can't see past.
        ("-O3", "-flag-a", "-flag-b"): [109.0, 111.0, 110.0],
        # But -flag-a and -flag-b *together* (without -O3's baseline flags) beat
        # both baseline and the greedy winner -- exactly the synergy the pair
        # tournament exists to catch.
        ("-flag-a", "-flag-b"): [125.0, 125.0, 125.0],
    })

    result = greedy_combine(
        cfg, experiment_id=exp_id, benchmark="fake_r", baseline=baseline, confirmed=confirmed,
        workload=backends, instrumentation=backends, rng=random.Random(0),
    )

    assert result.winning_flags == ["-flag-a", "-flag-b"]
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
