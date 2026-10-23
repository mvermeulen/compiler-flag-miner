import shutil

import pytest

from cfm import bandwidth
from cfm.bandwidth import GATE_FRACTION, MAX_WAIT_S, PROBE_INTERVAL_S, BandwidthGate
from cfm.config import CfmConfig


def _gate(readings):
    queue = list(readings)
    sleeps = []
    gate = BandwidthGate(None, probe=lambda: queue.pop(0) if queue else None, sleep=sleeps.append)
    return gate, sleeps


def test_first_call_probes_twice_and_keeps_the_better_reading():
    gate, sleeps = _gate([22.5, 45.0])
    result = gate.wait()
    assert result.passed and result.probe_gbps == 45.0 and gate.best == 45.0
    assert sleeps == [PROBE_INTERVAL_S]


def test_waits_out_a_throttled_reading():
    gate, sleeps = _gate([45.0, 45.0, 22.5, 22.6, 45.4])
    gate.wait()
    sleeps.clear()
    result = gate.wait()
    assert result.passed
    assert result.probe_gbps == 45.4
    assert result.waited_s == 2 * PROBE_INTERVAL_S
    assert len(sleeps) == 2


def test_passes_straight_through_when_bandwidth_is_close_to_the_best():
    gate, sleeps = _gate([45.0, 45.0, 45.0 * GATE_FRACTION + 0.1])
    gate.wait()
    sleeps.clear()
    result = gate.wait()
    assert result.passed and result.waited_s == 0 and sleeps == []


def test_gives_up_after_max_wait_and_says_so():
    gate, _ = _gate([45.0, 45.0] + [20.0] * 100)
    gate.wait()
    result = gate.wait()
    assert not result.passed
    assert result.waited_s >= MAX_WAIT_S
    assert "WARNING" in result.rationale()


def test_an_unavailable_probe_never_blocks():
    gate, sleeps = _gate([])
    result = gate.wait()
    assert result.passed and result.probe_gbps is None and sleeps == []
    assert result.rationale().endswith("unavailable")


def test_config_reads_the_environment(monkeypatch):
    monkeypatch.setenv("CFM_BANDWIDTH_GATE", "1")
    assert CfmConfig.from_env().bandwidth_gate is True
    monkeypatch.setenv("CFM_BANDWIDTH_GATE", "0")
    assert CfmConfig.from_env().bandwidth_gate is False
    assert CfmConfig.from_env(bandwidth_gate=True).bandwidth_gate is True


@pytest.mark.skipif(shutil.which("gcc") is None, reason="needs gcc")
def test_probe_binary_builds_once_and_is_reused(tmp_path):
    first = bandwidth._probe_binary(tmp_path)
    assert first is not None and first.exists()
    mtime = first.stat().st_mtime_ns
    assert bandwidth._probe_binary(tmp_path) == first
    assert first.stat().st_mtime_ns == mtime
