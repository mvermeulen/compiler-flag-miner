"""Unit tests for cfm/agents/spec_agent.py's dependency-injection seam -- the
actual M0 pipeline (real SPEC/wspy calls) is exercised by cfm measure, manually
and separately, per CLAUDE.md's Build & test section.
"""

from pathlib import Path

import pytest

import cfm.db as db
from cfm.agents.spec_agent import run_one_trial
from cfm.config import CfmConfig
from cfm.workloads.base import BuildResult


def test_run_one_trial_defaults_to_real_backends_and_fails_preflight_cleanly(tmp_path):
    # workload/instrumentation both omitted -- must fall back to the real
    # SpecCpu2026Workload/WspyInstrumentation (cfm/orchestrator.py's tests cover
    # the injected-fakes path instead). No real vendor/wspy at this fake wspy_dir,
    # so preflight() must fail loudly and specifically, same as before this PR's
    # DI change -- confirms the default-construction path wasn't broken by it.
    cfg = CfmConfig.from_env(
        wspy_dir=str(tmp_path / "no-such-wspy"), db_path=str(tmp_path / "cfm.db"),
        output_root=str(tmp_path / "results"),
    )
    with pytest.raises(RuntimeError, match="preflight"):
        run_one_trial(cfg, benchmark="fake_r", flags=["-O3"])


class _CrashingInstrumentation:
    """Simulates an unexpected crash mid-trial (not a build/validate *failure*,
    which is its own normal recorded outcome) -- e.g. a wspy subprocess blowing
    up unexpectedly.
    """

    def preflight(self):
        return []

    def characterize(self, **kwargs):
        raise RuntimeError("simulated wspy crash")


class _SucceedingWorkload:
    def generate_config(self, bench, tune, flags):
        return Path("/fake/config.cfg")

    def build(self, bench, tune, config_path):
        return BuildResult(ok=True, log_path=Path("/fake/build.log"), raw_output="ok")

    def run_command(self, bench, tune, config_path, iterations):
        return ["fake-run"]

    def parse_result(self, bench, tune, raw_output):
        raise AssertionError("must not be reached -- characterize() raises first")


def test_run_one_trial_marks_experiment_failed_on_unexpected_exception(tmp_path):
    # This is the gap CLAUDE.md's Non-obvious traps log (2026-08-20 entry)
    # flagged: an unhandled exception mid-trial used to leave the experiment
    # stuck at status='running' forever, since every orchestrator phase lets
    # such an exception propagate straight out to `cfm mine`'s CLI with no
    # per-candidate catch.
    cfg = CfmConfig.from_env(
        db_path=str(tmp_path / "cfm.db"), output_root=str(tmp_path / "results"),
    )
    with pytest.raises(RuntimeError, match="simulated wspy crash"):
        run_one_trial(
            cfg, benchmark="fake_r", flags=["-O3"],
            workload=_SucceedingWorkload(), instrumentation=_CrashingInstrumentation(),
        )

    conn = db.connect(cfg.db_path)
    try:
        cur = conn.execute(
            "SELECT status FROM experiments WHERE benchmark=? ORDER BY id DESC LIMIT 1",
            ("fake_r",),
        )
        assert cur.fetchone()[0] == "failed"
    finally:
        conn.close()
