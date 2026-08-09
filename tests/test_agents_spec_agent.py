"""Unit tests for cfm/agents/spec_agent.py's dependency-injection seam -- the
actual M0 pipeline (real SPEC/wspy calls) is exercised by cfm measure, manually
and separately, per CLAUDE.md's Build & test section.
"""

import pytest

from cfm.agents.spec_agent import run_one_trial
from cfm.config import CfmConfig


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
