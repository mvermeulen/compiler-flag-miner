"""Tests for cfm/cli.py's own argument/summary-building glue. Real phase
composition (does Phase 3's output correctly feed Phase 4, etc.) is
tests/test_orchestrator.py's "full pipeline" tests' job -- this file mocks every
cfm.cli.orchestrator.* call instead, since cli.py's mine handler doesn't (and
shouldn't) accept injectable backends itself; only the underlying
agents.spec_agent.run_one_trial() does (tests/test_agents_spec_agent.py,
tests/test_orchestrator.py).
"""

from __future__ import annotations

import json

import pytest

import cfm.cli as cli
from cfm.orchestrator import BaselineResult, CombinationResult, ConfirmationOutcome, MultiplierResult
from cfm.stats import confidence_interval


def _fake_baseline(exp_id=1):
    return BaselineResult(
        experiment_id=exp_id, flags=["-O3"], ratios=[100.0, 100.0, 100.0],
        ci=confidence_interval([100.0, 100.0, 100.0]), resource_dominance="memory-bound",
        trial_ids=[1, 2, 3],
    )


def _fake_pgo_not_attempted(combination):
    """Default stand-in for orchestrator.run_pgo_multiplier() in tests that
    aren't themselves about Phase 6 -- collapses straight back to combination's
    own winning flags/CI, matching a skipped-as-implausible or --skip-pgo run,
    so every pre-existing assertion about "the winning flagset" continues to
    mean Phase 5's own output unless a test opts into exercising Phase 6."""
    return MultiplierResult(
        attempted=False, winning_flags=combination.winning_flags, winning_ci=combination.winning_ci,
        skip_reason="fake: not exercising Phase 6 in this test",
    )


def _fake_microarch_not_attempted(combination):
    """Same idea as _fake_pgo_not_attempted() above, for
    orchestrator.run_microarch_multiplier() -- ``combination`` here is
    whatever run_pgo_multiplier() (or, if skipped, greedy_combine()) handed
    back, matching cli.py's own real chaining."""
    return MultiplierResult(
        attempted=False, winning_flags=combination.winning_flags, winning_ci=combination.winning_ci,
        skip_reason="fake: not exercising the microarch multiplier in this test",
    )


def test_mine_reports_a_winning_flagset(tmp_path, monkeypatch, capsys):
    baseline = _fake_baseline()
    combination = CombinationResult(
        winning_flags=["-O3", "-flto"], winning_ci=confidence_interval([110.0, 110.0, 110.0]),
    )

    monkeypatch.setattr(cli.orchestrator, "run_baseline", lambda *a, **k: baseline)
    monkeypatch.setattr(cli.orchestrator, "generate_candidates", lambda *a, **k: [])
    monkeypatch.setattr(cli.orchestrator, "screen_candidates", lambda *a, **k: [])
    monkeypatch.setattr(cli.orchestrator, "confirm_candidates", lambda *a, **k: [])
    monkeypatch.setattr(cli.orchestrator, "greedy_combine", lambda *a, **k: combination)
    monkeypatch.setattr(
        cli.orchestrator, "run_pgo_multiplier",
        lambda *a, combination, **k: _fake_pgo_not_attempted(combination),
    )
    monkeypatch.setattr(
        cli.orchestrator, "run_microarch_multiplier",
        lambda *a, combination, **k: _fake_microarch_not_attempted(combination),
    )
    # db.connect() is left real (a throwaway sqlite file under tmp_path) rather
    # than faked -- cli.py's mine handler still calls db.finish_experiment()
    # directly (not through orchestrator), and a real, cheap sqlite connection is
    # simpler than a fake one that has to imitate sqlite3.Connection's API.
    # baseline.experiment_id=1 doesn't correspond to a real row here (run_baseline
    # is mocked, never actually created one) -- finish_experiment()'s UPDATE
    # affecting zero rows is harmless and not what these tests are checking.

    exit_code = cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])
    assert exit_code == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary["winning_flags"] == ["-O3", "-flto"]
    assert summary["winning_ratio_mean"] == pytest.approx(110.0)
    assert summary["gain_vs_baseline_pct"] == pytest.approx(10.0)
    assert summary["budget_exhausted"] is False


def test_mine_max_trials_truncates_candidate_list_and_flags_budget_exhausted(tmp_path, monkeypatch):
    baseline = _fake_baseline()  # 3 baseline trial_ids already "spent"
    candidates = [object(), object(), object(), object()]  # 4 candidates, opaque is fine -- mocked below
    seen = {}

    def fake_screen(cfg, *, experiment_id, benchmark, baseline, candidates, **kwargs):
        seen["candidates_len"] = len(candidates)
        return []

    monkeypatch.setattr(cli.orchestrator, "run_baseline", lambda *a, **k: baseline)
    monkeypatch.setattr(cli.orchestrator, "generate_candidates", lambda *a, **k: candidates)
    monkeypatch.setattr(cli.orchestrator, "screen_candidates", fake_screen)
    monkeypatch.setattr(cli.orchestrator, "confirm_candidates", lambda *a, **k: [])
    monkeypatch.setattr(
        cli.orchestrator, "greedy_combine",
        lambda *a, **k: CombinationResult(winning_flags=baseline.flags, winning_ci=baseline.ci),
    )
    monkeypatch.setattr(
        cli.orchestrator, "run_pgo_multiplier",
        lambda *a, combination, **k: _fake_pgo_not_attempted(combination),
    )
    monkeypatch.setattr(
        cli.orchestrator, "run_microarch_multiplier",
        lambda *a, combination, **k: _fake_microarch_not_attempted(combination),
    )

    # --max-trials 5, 3 already spent on baseline -> only 2 of the 4 candidates
    # should reach screen_candidates().
    exit_code = cli.main(["mine", "fake_r", "--max-trials", "5", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])
    assert exit_code == 0
    assert seen["candidates_len"] == 2


def test_mine_propagates_a_runtime_error_cleanly(tmp_path, monkeypatch, capsys):
    def raise_it(*a, **k):
        raise RuntimeError("baseline for 'fake_r' produced no valid ratio")

    monkeypatch.setattr(cli.orchestrator, "run_baseline", raise_it)

    exit_code = cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])
    assert exit_code == 1
    assert "no valid ratio" in capsys.readouterr().err


class _FakeConn:
    """Stands in for db.connect()'s return value when db.finish_experiment() is
    *also* mocked (the test below) -- safe to pass around as an opaque object
    since nothing calls a real sqlite3.Connection method on it in that case.
    """

    def close(self):
        pass


def test_mine_calls_finish_experiment_with_the_right_experiment_id_and_status(tmp_path, monkeypatch):
    # Confirms cli.py's mine handler wires baseline.experiment_id and the
    # computed status through to db.finish_experiment() correctly.
    calls = []
    monkeypatch.setattr(cli.db, "connect", lambda path: _FakeConn())
    monkeypatch.setattr(cli.db, "finish_experiment", lambda conn, exp_id, status: calls.append((exp_id, status)))
    monkeypatch.setattr(cli.orchestrator, "run_baseline", lambda *a, **k: _fake_baseline(exp_id=42))
    monkeypatch.setattr(cli.orchestrator, "generate_candidates", lambda *a, **k: [])
    monkeypatch.setattr(cli.orchestrator, "screen_candidates", lambda *a, **k: [])
    monkeypatch.setattr(cli.orchestrator, "confirm_candidates", lambda *a, **k: [])
    monkeypatch.setattr(
        cli.orchestrator, "greedy_combine",
        lambda *a, **k: CombinationResult(winning_flags=["-O3"], winning_ci=confidence_interval([100.0] * 3)),
    )
    monkeypatch.setattr(
        cli.orchestrator, "run_pgo_multiplier",
        lambda *a, combination, **k: _fake_pgo_not_attempted(combination),
    )
    monkeypatch.setattr(
        cli.orchestrator, "run_microarch_multiplier",
        lambda *a, combination, **k: _fake_microarch_not_attempted(combination),
    )

    cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])
    assert calls == [(42, "converged")]


# -- Phase 6 (PGO multiplier) wiring -------------------------------------------

def _mine_common_mocks(monkeypatch, baseline, combination):
    monkeypatch.setattr(cli.orchestrator, "run_baseline", lambda *a, **k: baseline)
    monkeypatch.setattr(cli.orchestrator, "generate_candidates", lambda *a, **k: [])
    monkeypatch.setattr(cli.orchestrator, "screen_candidates", lambda *a, **k: [])
    monkeypatch.setattr(cli.orchestrator, "confirm_candidates", lambda *a, **k: [])
    monkeypatch.setattr(cli.orchestrator, "greedy_combine", lambda *a, **k: combination)
    # Default: microarch multiplier not exercised unless a test overrides this
    # itself (matches _fake_pgo_not_attempted()'s own "chains through
    # unchanged" behavior) -- most Phase 6 tests below are specifically about
    # PGO's own wiring, not microarch's.
    monkeypatch.setattr(
        cli.orchestrator, "run_microarch_multiplier",
        lambda *a, combination, **k: _fake_microarch_not_attempted(combination),
    )


def test_mine_skip_pgo_never_calls_run_pgo_multiplier(tmp_path, monkeypatch, capsys):
    baseline = _fake_baseline()
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    _mine_common_mocks(monkeypatch, baseline, combination)
    calls = []
    monkeypatch.setattr(
        cli.orchestrator, "run_pgo_multiplier", lambda *a, **k: calls.append(1) or None,
    )

    exit_code = cli.main([
        "mine", "fake_r", "--skip-pgo",
        "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock"),
    ])
    assert exit_code == 0
    assert calls == []  # never invoked at all

    summary = json.loads(capsys.readouterr().out)
    assert summary["pgo_attempted"] is False
    assert summary["pgo_skip_reason"] == "--skip-pgo"
    assert summary["winning_flags"] == combination.winning_flags  # unchanged, PGO never ran


def test_mine_pgo_accepted_becomes_the_final_winning_flagset(tmp_path, monkeypatch, capsys):
    baseline = _fake_baseline()
    combination = CombinationResult(winning_flags=["-O3", "-flto"], winning_ci=baseline.ci)
    pgo_ci = confidence_interval([130.0, 130.0, 130.0])
    pgo_result = MultiplierResult(
        attempted=True, winning_flags=["-O3", "-flto", "-fprofile-use"], winning_ci=pgo_ci,
        outcome=ConfirmationOutcome(
            flags=["-O3", "-flto", "-fprofile-use"], trial_ids=[10, 11, 12], ratios=[130.0] * 3,
            ci=pgo_ci, delta_vs_baseline_pct=30.0, accepted=True, reason="fake accept",
        ),
    )
    _mine_common_mocks(monkeypatch, baseline, combination)
    monkeypatch.setattr(cli.orchestrator, "run_pgo_multiplier", lambda *a, **k: pgo_result)

    exit_code = cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])
    assert exit_code == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary["combination_winning_flags"] == ["-O3", "-flto"]  # Phase 5's own, unmodified
    assert summary["pgo_attempted"] is True
    assert summary["pgo_accepted"] is True
    assert summary["winning_flags"] == ["-O3", "-flto", "-fprofile-use"]  # PGO's, not Phase 5's
    assert summary["winning_ratio_mean"] == pytest.approx(130.0)


def test_mine_pgo_rejected_keeps_phase5s_winning_flagset(tmp_path, monkeypatch, capsys):
    baseline = _fake_baseline()
    combination = CombinationResult(winning_flags=["-O3", "-flto"], winning_ci=baseline.ci)
    pgo_result = MultiplierResult(
        attempted=True, winning_flags=combination.winning_flags, winning_ci=combination.winning_ci,
        outcome=ConfirmationOutcome(
            flags=["-O3", "-flto", "-fprofile-use"], trial_ids=[10, 11, 12], ratios=[95.0] * 3,
            ci=confidence_interval([95.0] * 3), delta_vs_baseline_pct=-5.0,
            accepted=False, reason="fake reject",
        ),
    )
    _mine_common_mocks(monkeypatch, baseline, combination)
    monkeypatch.setattr(cli.orchestrator, "run_pgo_multiplier", lambda *a, **k: pgo_result)

    exit_code = cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])
    assert exit_code == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary["pgo_attempted"] is True
    assert summary["pgo_accepted"] is False
    assert summary["winning_flags"] == ["-O3", "-flto"]  # Phase 5's, PGO rejected


def test_mine_pgo_skipped_as_implausible(tmp_path, monkeypatch, capsys):
    baseline = _fake_baseline()
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    pgo_result = MultiplierResult(
        attempted=False, winning_flags=combination.winning_flags, winning_ci=combination.winning_ci,
        skip_reason="skipping PGO -- topdown_signals [...] implausible given baseline shape (...)",
    )
    _mine_common_mocks(monkeypatch, baseline, combination)
    monkeypatch.setattr(cli.orchestrator, "run_pgo_multiplier", lambda *a, **k: pgo_result)

    exit_code = cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])
    assert exit_code == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary["pgo_attempted"] is False
    assert "implausible" in summary["pgo_skip_reason"]
    assert summary["pgo_accepted"] is False
    assert summary["winning_flags"] == ["-O3"]


# -- Phase 6 (microarch multiplier) wiring -------------------------------------

def test_mine_skip_microarch_never_calls_run_microarch_multiplier(tmp_path, monkeypatch, capsys):
    baseline = _fake_baseline()
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    _mine_common_mocks(monkeypatch, baseline, combination)  # its own microarch default would be overridden below anyway
    monkeypatch.setattr(
        cli.orchestrator, "run_pgo_multiplier",
        lambda *a, combination, **k: _fake_pgo_not_attempted(combination),
    )
    calls = []
    monkeypatch.setattr(
        cli.orchestrator, "run_microarch_multiplier", lambda *a, **k: calls.append(1) or None,
    )

    exit_code = cli.main([
        "mine", "fake_r", "--skip-microarch",
        "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock"),
    ])
    assert exit_code == 0
    assert calls == []  # never invoked at all

    summary = json.loads(capsys.readouterr().out)
    assert summary["microarch_attempted"] is False
    assert summary["microarch_skip_reason"] == "--skip-microarch"
    assert summary["winning_flags"] == combination.winning_flags


def test_mine_microarch_accepted_becomes_the_final_winning_flagset(tmp_path, monkeypatch, capsys):
    baseline = _fake_baseline()
    combination = CombinationResult(winning_flags=["-O3", "-flto"], winning_ci=baseline.ci)
    march_ci = confidence_interval([140.0, 140.0, 140.0])
    march_result = MultiplierResult(
        attempted=True, winning_flags=["-O3", "-flto", "-march=znver5"], winning_ci=march_ci,
        outcome=ConfirmationOutcome(
            flags=["-O3", "-flto", "-march=znver5"], trial_ids=[20, 21, 22], ratios=[140.0] * 3,
            ci=march_ci, delta_vs_baseline_pct=40.0, accepted=True, reason="fake accept",
        ),
    )
    _mine_common_mocks(monkeypatch, baseline, combination)
    monkeypatch.setattr(
        cli.orchestrator, "run_pgo_multiplier",
        lambda *a, combination, **k: _fake_pgo_not_attempted(combination),
    )
    monkeypatch.setattr(cli.orchestrator, "run_microarch_multiplier", lambda *a, **k: march_result)

    exit_code = cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])
    assert exit_code == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary["combination_winning_flags"] == ["-O3", "-flto"]  # Phase 5's own, unmodified
    assert summary["microarch_attempted"] is True
    assert summary["microarch_accepted"] is True
    assert summary["winning_flags"] == ["-O3", "-flto", "-march=znver5"]
    assert summary["winning_ratio_mean"] == pytest.approx(140.0)


def test_mine_microarch_chains_off_an_accepted_pgo_result(tmp_path, monkeypatch, capsys):
    # The real cli.py wiring: microarch's own `combination` argument is
    # pgo_result when PGO was accepted, not Phase 5's own combination -- this
    # test confirms that's really what gets passed through.
    baseline = _fake_baseline()
    combination = CombinationResult(winning_flags=["-O3"], winning_ci=baseline.ci)
    pgo_ci = confidence_interval([130.0] * 3)
    pgo_result = MultiplierResult(
        attempted=True, winning_flags=["-O3", "-fprofile-use"], winning_ci=pgo_ci,
        outcome=ConfirmationOutcome(
            flags=["-O3", "-fprofile-use"], trial_ids=[10, 11, 12], ratios=[130.0] * 3,
            ci=pgo_ci, delta_vs_baseline_pct=30.0, accepted=True, reason="fake accept",
        ),
    )
    seen = {}

    def fake_microarch(cfg, *, experiment_id, benchmark, baseline, combination, **kwargs):
        seen["combination_winning_flags"] = combination.winning_flags
        return _fake_microarch_not_attempted(combination)

    _mine_common_mocks(monkeypatch, baseline, combination)
    monkeypatch.setattr(cli.orchestrator, "run_pgo_multiplier", lambda *a, **k: pgo_result)
    monkeypatch.setattr(cli.orchestrator, "run_microarch_multiplier", fake_microarch)

    cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db"), "--lock-file", str(tmp_path / "test.lock")])

    assert seen["combination_winning_flags"] == ["-O3", "-fprofile-use"]  # pgo_result's, not Phase 5's
