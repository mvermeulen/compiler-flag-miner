"""Unit tests for cfm/hostinfo.py's detect_microarch_flags(). Fakes a
`cpu_info`-shaped script at various tmp_path locations rather than depending
on the real vendor/wspy binary being built -- plus one real-binary contract
test at the bottom, skipped cleanly when vendor/wspy isn't built (matching
tests/test_wspy_interface.py's own posture).
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from cfm.hostinfo import detect_microarch_flags


def _fake_cpu_info(tmp_path, stdout: str, exit_code: int = 0) -> Path:
    script = tmp_path / "cpu_info"
    script.write_text(f"#!/bin/sh\ncat <<'EOF'\n{stdout}\nEOF\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return tmp_path


def test_detect_microarch_flags_maps_zen5(tmp_path):
    wspy_dir = _fake_cpu_info(tmp_path, "CPU information:\n\tAMD family 1a model 70\n\t   * 0 Zen5\n\t   * 1 Zen5\n")
    assert detect_microarch_flags(wspy_dir) == ["-march=znver5", "-mtune=znver5"]


def test_detect_microarch_flags_maps_zen5c(tmp_path):
    wspy_dir = _fake_cpu_info(tmp_path, "CPU information:\n\tAMD family 1a model 70\n\t   * 0 Zen5c\n")
    assert detect_microarch_flags(wspy_dir) == ["-march=znver5", "-mtune=znver5"]


def test_detect_microarch_flags_never_guesses_bare_zen(tmp_path):
    # wspy's own cpu_info.c has no per-generation Zen1-4 label -- bare "Zen"
    # is genuinely ambiguous (could be any of several real generations), so
    # this must never be guessed at, unlike Zen5/Zen5c above.
    wspy_dir = _fake_cpu_info(tmp_path, "CPU information:\n\tAMD family 17 model 1\n\t   * 0 Zen\n")
    assert detect_microarch_flags(wspy_dir) == []


def test_detect_microarch_flags_skips_unmapped_vendor(tmp_path):
    wspy_dir = _fake_cpu_info(tmp_path, "CPU information:\n\tIntel family 6 model 165\n\t   * 0 Core\n")
    assert detect_microarch_flags(wspy_dir) == []


def test_detect_microarch_flags_skips_mixed_labels(tmp_path):
    # A genuinely hybrid host -- available cores disagree, so nothing is
    # confidently detectable without guessing which label should win.
    wspy_dir = _fake_cpu_info(
        tmp_path, "CPU information:\n\tAMD family 1a model 70\n\t   * 0 Zen5\n\t   * 1 Zen5c\n",
    )
    assert detect_microarch_flags(wspy_dir) == []


def test_detect_microarch_flags_ignores_unavailable_cores(tmp_path):
    # An offline/disabled core (' ' marker, not '*') must not count.
    wspy_dir = _fake_cpu_info(tmp_path, "CPU information:\n\tAMD family 1a model 70\n\t   * 0 Zen5\n\t     1 Zen5c\n")
    assert detect_microarch_flags(wspy_dir) == ["-march=znver5", "-mtune=znver5"]


def test_detect_microarch_flags_returns_empty_when_binary_missing(tmp_path):
    assert detect_microarch_flags(tmp_path / "no-such-wspy-dir") == []


def test_detect_microarch_flags_returns_empty_on_nonzero_exit(tmp_path):
    wspy_dir = _fake_cpu_info(tmp_path, "some partial output", exit_code=1)
    assert detect_microarch_flags(wspy_dir) == []


def test_detect_microarch_flags_returns_empty_on_no_cores_parsed(tmp_path):
    wspy_dir = _fake_cpu_info(tmp_path, "CPU information:\nUnknown CPU\n")
    assert detect_microarch_flags(wspy_dir) == []


# -- Real-binary contract test, skipped cleanly if vendor/wspy isn't built ----

_REAL_WSPY_DIR = Path(__file__).parent.parent / "vendor" / "wspy"


@pytest.mark.skipif(
    not (_REAL_WSPY_DIR / "cpu_info").exists(),
    reason="vendor/wspy not built yet (./scripts/bootstrap_wspy.sh)",
)
def test_detect_microarch_flags_against_the_real_binary():
    # Not asserting a specific value -- this contract test just confirms the
    # real cpu_info binary's actual output shape still parses into either a
    # well-formed two-flag list or a clean empty skip, on whatever host this
    # happens to run on, never a crash.
    result = detect_microarch_flags(_REAL_WSPY_DIR)
    assert result == [] or (
        len(result) == 2
        and result[0].startswith("-march=")
        and result[1].startswith("-mtune=")
    )
