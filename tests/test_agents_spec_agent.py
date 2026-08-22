"""Unit tests for cfm/agents/spec_agent.py's dependency-injection seam -- the
actual M0 pipeline (real SPEC/wspy calls) is exercised by cfm measure, manually
and separately, per CLAUDE.md's Build & test section.
"""

from pathlib import Path

import pytest

import cfm.db as db
from cfm.agents.spec_agent import _extract_cpu_temp_c, _summarize_compiled_flags_audit, run_one_trial
from cfm.config import CfmConfig
from cfm.instrumentation.base import RunSignature
from cfm.workloads.base import BuildResult, RunResult


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


# -- _summarize_compiled_flags_audit -------------------------------------------

def test_summarize_compiled_flags_audit_reports_found_missing_and_skipped():
    dump = "GNU C17 15.2.0 -march=znver5 -mmmx ... -flto -O3 -DDIAG_MARKER\n"
    summary = _summarize_compiled_flags_audit(
        ["-flto", "-fno-semantic-interposition", "-march=native"], dump,
    )
    assert "confirmed compiled in: ['-flto']" in summary
    assert "NOT FOUND in compiled binary" in summary and "-fno-semantic-interposition" in summary
    assert "not independently checkable" in summary and "-march=native" in summary
    assert "no -O optimization level" not in summary  # -O3 is right there in the dump


def test_summarize_compiled_flags_audit_warns_when_no_optimization_level_found():
    # The real 2026-08-22 bug this generic check exists to catch: a build whose
    # flags list never included baseline's own -O3 at all. Deliberately not
    # gated on whether "flags" itself expected an -O entry -- the whole point
    # is to catch flags itself having been wrong.
    dump = "GNU C17 15.2.0 -mtune=generic -march=x86-64 -fprefetch-loop-arrays -frecord-gcc-switches\n"
    summary = _summarize_compiled_flags_audit(["-fprefetch-loop-arrays"], dump)
    assert "⚠ WARNING: no -O optimization level found" in summary


# -- audit wiring in run_one_trial() -------------------------------------------

class _FullySucceedingWorkload:
    """generate_config()/build()/run_command()/parse_result() all succeed, plus
    audit_compiled_flags() -- the full success path, needed to test that
    run_one_trial() actually calls the audit and records it, unlike
    _SucceedingWorkload above (which deliberately stops at parse_result())."""

    def __init__(self, audit_dump):
        self.audit_dump = audit_dump
        self.audit_calls = []

    def generate_config(self, bench, tune, flags):
        return Path("/fake/config.cfg")

    def build(self, bench, tune, config_path):
        return BuildResult(ok=True, log_path=Path("/fake/build.log"), raw_output="ok")

    def run_command(self, bench, tune, config_path, iterations):
        return ["fake-run"]

    def parse_result(self, bench, tune, raw_output):
        return RunResult(ok=True, validated=True, ratio=100.0, seconds=1.0, status="ok", raw_output="")

    def audit_compiled_flags(self, bench, tune):
        self.audit_calls.append((bench, tune))
        return self.audit_dump


class _FullySucceedingInstrumentation:
    def __init__(self, raw_output=""):
        self.raw_output = raw_output

    def preflight(self):
        return []

    def characterize(self, **kwargs):
        return RunSignature(wspy_run_ref="fakehost:run123", validated=True, raw_output=self.raw_output)


def test_run_one_trial_records_compiled_flags_audit_as_a_hypothesis(tmp_path):
    cfg = CfmConfig.from_env(
        db_path=str(tmp_path / "cfm.db"), output_root=str(tmp_path / "results"),
    )
    workload = _FullySucceedingWorkload(audit_dump="... -flto -O3 ...")
    result = run_one_trial(
        cfg, benchmark="fake_r", flags=["-O3", "-flto"],
        workload=workload, instrumentation=_FullySucceedingInstrumentation(),
    )
    assert workload.audit_calls == [("fake_r", "peak")]

    conn = db.connect(cfg.db_path)
    try:
        rows = conn.execute(
            "SELECT rationale FROM hypotheses WHERE trial_id=? AND rationale LIKE 'compiled-flags audit%'",
            (result["trial_id"],),
        ).fetchall()
        assert len(rows) == 1
        assert "confirmed compiled in" in rows[0][0]
    finally:
        conn.close()


def test_run_one_trial_skips_audit_when_workload_lacks_the_method(tmp_path):
    # _SucceedingWorkload (defined above) has no audit_compiled_flags() at all --
    # confirms the getattr-guarded call degrades cleanly rather than crashing,
    # for any WorkloadBackend that doesn't implement this optional method.
    cfg = CfmConfig.from_env(
        db_path=str(tmp_path / "cfm.db"), output_root=str(tmp_path / "results"),
    )
    workload = _FullySucceedingWorkload(audit_dump=None)  # audit_fn present but returns None
    result = run_one_trial(
        cfg, benchmark="fake_r", flags=["-O3"],
        workload=workload, instrumentation=_FullySucceedingInstrumentation(),
    )
    conn = db.connect(cfg.db_path)
    try:
        rows = conn.execute(
            "SELECT rationale FROM hypotheses WHERE trial_id=? AND rationale LIKE 'compiled-flags audit%'",
            (result["trial_id"],),
        ).fetchall()
        assert rows == []  # None dump -> no hypothesis recorded, no crash
    finally:
        conn.close()


# -- _extract_cpu_temp_c / per-trial thermal record ----------------------------

def test_extract_cpu_temp_c_parses_wspys_own_line():
    raw = "loadavg              1.23\ncpu temp             62.3 C\nfreq                 3800 MHz\n"
    assert _extract_cpu_temp_c(raw) == pytest.approx(62.3)


def test_extract_cpu_temp_c_returns_none_when_absent():
    # e.g. no matching hwmon sensor found, or a profile with no --system.
    assert _extract_cpu_temp_c("loadavg              1.23\nfreq                 3800 MHz\n") is None


def test_run_one_trial_records_cpu_temp_as_a_hypothesis(tmp_path):
    cfg = CfmConfig.from_env(
        db_path=str(tmp_path / "cfm.db"), output_root=str(tmp_path / "results"),
    )
    instrumentation = _FullySucceedingInstrumentation(raw_output="cpu temp             71.5 C\n")
    result = run_one_trial(
        cfg, benchmark="fake_r", flags=["-O3"],
        workload=_FullySucceedingWorkload(audit_dump=None), instrumentation=instrumentation,
    )
    assert result["cpu_temp_c"] == pytest.approx(71.5)

    conn = db.connect(cfg.db_path)
    try:
        rows = conn.execute(
            "SELECT rationale FROM hypotheses WHERE trial_id=? AND rationale LIKE 'host cpu_temp%'",
            (result["trial_id"],),
        ).fetchall()
        assert len(rows) == 1
        assert "71.5" in rows[0][0]
    finally:
        conn.close()


def test_run_one_trial_skips_cpu_temp_hypothesis_when_absent(tmp_path):
    cfg = CfmConfig.from_env(
        db_path=str(tmp_path / "cfm.db"), output_root=str(tmp_path / "results"),
    )
    result = run_one_trial(
        cfg, benchmark="fake_r", flags=["-O3"],
        workload=_FullySucceedingWorkload(audit_dump=None), instrumentation=_FullySucceedingInstrumentation(),
    )
    assert result["cpu_temp_c"] is None
    conn = db.connect(cfg.db_path)
    try:
        rows = conn.execute(
            "SELECT rationale FROM hypotheses WHERE trial_id=? AND rationale LIKE 'host cpu_temp%'",
            (result["trial_id"],),
        ).fetchall()
        assert rows == []
    finally:
        conn.close()
