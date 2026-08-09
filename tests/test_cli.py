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
from cfm.orchestrator import BaselineResult, CombinationResult
from cfm.stats import confidence_interval


def _fake_baseline(exp_id=1):
    return BaselineResult(
        experiment_id=exp_id, flags=["-O3"], ratios=[100.0, 100.0, 100.0],
        ci=confidence_interval([100.0, 100.0, 100.0]), resource_dominance="memory-bound",
        trial_ids=[1, 2, 3],
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
    # db.connect() is left real (a throwaway sqlite file under tmp_path) rather
    # than faked -- cli.py's mine handler still calls db.finish_experiment()
    # directly (not through orchestrator), and a real, cheap sqlite connection is
    # simpler than a fake one that has to imitate sqlite3.Connection's API.
    # baseline.experiment_id=1 doesn't correspond to a real row here (run_baseline
    # is mocked, never actually created one) -- finish_experiment()'s UPDATE
    # affecting zero rows is harmless and not what these tests are checking.

    exit_code = cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db")])
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

    # --max-trials 5, 3 already spent on baseline -> only 2 of the 4 candidates
    # should reach screen_candidates().
    exit_code = cli.main(["mine", "fake_r", "--max-trials", "5", "--db", str(tmp_path / "cfm.db")])
    assert exit_code == 0
    assert seen["candidates_len"] == 2


def test_mine_propagates_a_runtime_error_cleanly(tmp_path, monkeypatch, capsys):
    def raise_it(*a, **k):
        raise RuntimeError("baseline for 'fake_r' produced no valid ratio")

    monkeypatch.setattr(cli.orchestrator, "run_baseline", raise_it)

    exit_code = cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db")])
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

    cli.main(["mine", "fake_r", "--db", str(tmp_path / "cfm.db")])
    assert calls == [(42, "converged")]
