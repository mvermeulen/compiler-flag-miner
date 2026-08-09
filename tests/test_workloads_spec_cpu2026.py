import pytest

from cfm.workloads.spec_cpu2026 import SpecCpu2026Workload


def _make_workload(tmp_path):
    spec_dir = tmp_path / "spec"
    (spec_dir / "config").mkdir(parents=True)
    return SpecCpu2026Workload(spec_dir, base_config="gcc_O3.cfg")


def test_generate_config_writes_include_and_peak_override(tmp_path):
    workload = _make_workload(tmp_path)
    config_path = workload.generate_config("706.stockfish_r", "peak", ["-O3", "-flto"])
    assert config_path.exists()
    text = config_path.read_text()
    assert "include: gcc_O3.cfg" in text
    assert "706.stockfish_r: basepeak = no" in text
    assert "706.stockfish_r=peak:" in text
    assert "OPTIMIZE = -O3 -flto" in text


def test_generate_config_is_deterministic_for_same_flags(tmp_path):
    workload = _make_workload(tmp_path)
    a = workload.generate_config("706.stockfish_r", "peak", ["-O3", "-flto"])
    b = workload.generate_config("706.stockfish_r", "peak", ["-O3", "-flto"])
    assert a == b  # same flag set -> same trial config name, safe to regenerate


def test_generate_config_rejects_base_tune(tmp_path):
    workload = _make_workload(tmp_path)
    with pytest.raises(ValueError):
        workload.generate_config("706.stockfish_r", "base", ["-O3"])


def test_run_command_shape(tmp_path):
    workload = _make_workload(tmp_path)
    config_path = workload.generate_config("706.stockfish_r", "peak", ["-O3"])
    cmd = workload.run_command("706.stockfish_r", "peak", config_path, iterations=3)
    assert cmd[0] == "bash"
    assert cmd[1] == "-c"
    inner = cmd[2]
    assert "runcpu --config" in inner
    assert config_path.stem in inner
    assert "--action=validate" in inner
    assert "--tune peak" in inner
    assert "--iterations 3" in inner
    assert "706.stockfish_r" in inner


def test_parse_result_success_extracts_ratio(tmp_path):
    workload = _make_workload(tmp_path)
    workload.result_dir.mkdir(parents=True)
    rsf_path = workload.result_dir / "CPU2026.001.intrate.rsf"
    rsf_path.write_text(
        "spec.cpu2026.results.706_stockfish_r.peak.ratio = 12.34\n"
        "spec.cpu2026.results.706_stockfish_r.peak.time_avg = 55.1\n"
        "spec.cpu2026.results.706_stockfish_r.base.ratio = 10.0\n"
    )
    raw = "...\n[runcpu validate exited 0]\nSuccess: 1x706.stockfish_r\n"
    result = workload.parse_result("706.stockfish_r", "peak", raw)
    assert result.ok
    assert result.validated
    assert result.status == "ok"
    assert result.ratio == 12.34
    assert result.seconds == 55.1


def test_parse_result_failure_on_nonzero_exit(tmp_path):
    workload = _make_workload(tmp_path)
    raw = "...\n[runcpu validate exited 1]\n"
    result = workload.parse_result("706.stockfish_r", "peak", raw)
    assert not result.ok
    assert not result.validated
    assert result.status == "validate-failed"


def test_parse_result_failure_when_bench_missing_from_success_line(tmp_path):
    workload = _make_workload(tmp_path)
    raw = "...\n[runcpu validate exited 0]\nSuccess: 1x707.ntest_r\n"
    result = workload.parse_result("706.stockfish_r", "peak", raw)
    assert not result.ok
    assert result.status == "validate-failed"


def test_parse_result_ok_but_no_rsf_found(tmp_path):
    workload = _make_workload(tmp_path)
    raw = "...\n[runcpu validate exited 0]\nSuccess: 1x706.stockfish_r\n"
    result = workload.parse_result("706.stockfish_r", "peak", raw)
    assert result.ok
    assert result.status == "ok-no-rsf"
    assert result.ratio is None
