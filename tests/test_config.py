from pathlib import Path

from cfm.config import CfmConfig


def test_from_env_defaults(monkeypatch):
    for name in (
        "CFM_SPEC_DIR", "CFM_SPEC_CONFIG", "CFM_WSPY_DIR", "CFM_OUTPUT_ROOT",
        "CFM_DB", "CFM_WSPY_PROFILE", "CFM_LOCK_FILE",
    ):
        monkeypatch.delenv(name, raising=False)
    cfg = CfmConfig.from_env()
    assert isinstance(cfg.spec_dir, Path)
    assert cfg.spec_config == "gcc_O3.cfg"
    assert cfg.wspy_profile == "quick"
    assert cfg.hostname
    # Default lock_file lives alongside the SPEC install (host-wide, not
    # repo-relative) -- see cfm/lock.py's module docstring for why.
    assert cfg.lock_file == cfg.spec_dir / ".cfm-mining.lock"
    # Default wspy_dir is the pinned vendor/wspy submodule, resolved relative to the
    # repo root -- not the caller's cwd -- so `cfm` behaves the same regardless of
    # where it's invoked from.
    assert cfg.wspy_dir.name == "wspy"
    assert cfg.wspy_dir.parent.name == "vendor"
    assert (cfg.wspy_dir.parent.parent / "schema" / "cfm_schema.sql").exists()


def test_wspy_dir_env_override_wins_over_vendored_default(monkeypatch):
    monkeypatch.setenv("CFM_WSPY_DIR", "/tmp/some-other-wspy-checkout")
    cfg = CfmConfig.from_env()
    assert cfg.wspy_dir == Path("/tmp/some-other-wspy-checkout")


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


def test_lock_file_env_override_wins_over_spec_dir_default(monkeypatch):
    monkeypatch.setenv("CFM_SPEC_DIR", "/tmp/env-spec")
    monkeypatch.setenv("CFM_LOCK_FILE", "/tmp/somewhere-else.lock")
    cfg = CfmConfig.from_env()
    assert cfg.lock_file == Path("/tmp/somewhere-else.lock")


def test_lock_file_explicit_kwarg_wins_over_everything(monkeypatch):
    monkeypatch.setenv("CFM_LOCK_FILE", "/tmp/env.lock")
    cfg = CfmConfig.from_env(spec_dir="/tmp/explicit-spec", lock_file="/tmp/explicit.lock")
    assert cfg.lock_file == Path("/tmp/explicit.lock")
