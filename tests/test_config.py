from pathlib import Path

from cfm.config import CfmConfig


def test_from_env_defaults(monkeypatch):
    for name in (
        "CFM_SPEC_DIR", "CFM_SPEC_CONFIG", "CFM_WSPY_DIR", "CFM_OUTPUT_ROOT",
        "CFM_DB", "CFM_WSPY_PROFILE",
    ):
        monkeypatch.delenv(name, raising=False)
    cfg = CfmConfig.from_env()
    assert isinstance(cfg.spec_dir, Path)
    assert cfg.spec_config == "gcc_O3.cfg"
    assert cfg.wspy_profile == "quick"
    assert cfg.hostname


def test_from_env_reads_environment(monkeypatch):
    monkeypatch.setenv("CFM_SPEC_DIR", "/tmp/env-spec")
    monkeypatch.setenv("CFM_WSPY_PROFILE", "deep-cpu")
    cfg = CfmConfig.from_env()
    assert cfg.spec_dir == Path("/tmp/env-spec")
    assert cfg.wspy_profile == "deep-cpu"


def test_explicit_kwargs_win_over_environment(monkeypatch):
    monkeypatch.setenv("CFM_SPEC_DIR", "/tmp/env-spec")
    cfg = CfmConfig.from_env(spec_dir="/tmp/explicit-spec")
    assert cfg.spec_dir == Path("/tmp/explicit-spec")
