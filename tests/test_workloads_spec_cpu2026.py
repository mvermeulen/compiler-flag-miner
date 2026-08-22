import shutil
import subprocess
from pathlib import Path

import pytest

from cfm.workloads.spec_cpu2026 import SpecCpu2026Workload

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
    assert "706.stockfish_r=peak:" in text
    assert "OPTIMIZE = -O3 -flto" in text
    # `basepeak = no` MUST be scoped *inside* the "<bench>=peak:" block, not a
    # separate unscoped "<bench>: basepeak = no" line before it -- SPEC silently
    # ignores the unscoped form (confirmed live against a real runcpu build,
    # CLAUDE.md's Non-obvious traps log, 2026-08-21: every real cfm mine trial
    # before this fix actually built the *base*-tuning binary regardless of
    # which candidate flags this method rendered -- the build log's own label
    # said "peak" while silently using build_base_*/"Build successes for
    # ...(base)"). A plain substring check on "basepeak = no" being present
    # anywhere would not catch a regression back to the unscoped form -- this
    # test previously asserted the *unscoped* line verbatim as the "correct"
    # shape, which is exactly why the bug shipped undetected in the first
    # place; only checking basepeak's position relative to the section header
    # actually guards against it.
    assert "706.stockfish_r: basepeak = no" not in text
    peak_header_pos = text.index("706.stockfish_r=peak:")
    basepeak_pos = text.index("basepeak = no")
    assert basepeak_pos > peak_header_pos


def test_generate_config_always_appends_frecord_gcc_switches(tmp_path):
    # Always on -- audit_compiled_flags() below depends on every trial's binary
    # carrying a .GCC.command.line section to read back (CLAUDE.md's
    # Non-obvious traps log, 2026-08-21). Metadata-only, never affects codegen
    # or the measured ratio, so this is safe to add unconditionally.
    workload = _make_workload(tmp_path)
    config_path = workload.generate_config("706.stockfish_r", "peak", ["-O3", "-flto"])
    text = config_path.read_text()
    assert "OPTIMIZE = -O3 -flto -frecord-gcc-switches" in text


def test_generate_config_is_deterministic_for_same_flags(tmp_path):
    workload = _make_workload(tmp_path)
    a = workload.generate_config("706.stockfish_r", "peak", ["-O3", "-flto"])
    b = workload.generate_config("706.stockfish_r", "peak", ["-O3", "-flto"])
    assert a == b  # same flag set -> same trial config name, safe to regenerate


def test_audit_compiled_flags_returns_none_when_no_build_dir(tmp_path):
    workload = _make_workload(tmp_path)
    assert workload.audit_compiled_flags("706.stockfish_r", "peak") is None


def test_audit_compiled_flags_returns_none_when_no_elf_binary_present(tmp_path):
    workload = _make_workload(tmp_path)
    build_dir = workload.spec_dir / "benchspec" / "CPU" / "706.stockfish_r" / "build" / "build_peak_gcc_O3.0000"
    build_dir.mkdir(parents=True)
    (build_dir / "simple-build-stockfish-706.sh").write_text("#!/bin/sh\necho not an elf binary\n")
    assert workload.audit_compiled_flags("706.stockfish_r", "peak") is None


def test_audit_compiled_flags_finds_the_most_recent_build_dir_and_reads_it(tmp_path):
    # Real readelf, a real (tiny, locally-compiled) ELF binary with a genuine
    # .GCC.command.line section -- confirms the glob/ELF-detection/readelf
    # plumbing end to end without needing a real SPEC build. The actual
    # against-a-real-SPEC-binary confirmation is documented in CLAUDE.md's
    # Non-obvious traps log (2026-08-21), not repeated here as an automated
    # test per this project's "no real runcpu/SPEC calls in the unit tier" rule.
    if shutil.which("gcc") is None or shutil.which("readelf") is None:
        pytest.skip("gcc/readelf not available")
    workload = _make_workload(tmp_path)
    bench_dir = workload.spec_dir / "benchspec" / "CPU" / "706.stockfish_r" / "build"
    older = bench_dir / "build_peak_gcc_O3.0000"
    newer = bench_dir / "build_peak_gcc_O3.0001"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)
    (older / "toy").write_bytes(b"not a real elf, just older")
    src = newer / "toy.c"
    src.write_text("int main(void) { return 0; }\n")
    # A real compiler *switch*, not a -D define -- confirmed live, 2026-08-21:
    # -frecord-gcc-switches doesn't embed preprocessor defines, only genuine
    # command-line switches (see cfm/agents/spec_agent.py's own
    # _AUDIT_UNVERIFIABLE_LITERAL_FLAGS comment for the related -march=native
    # expansion caveat).
    subprocess.run(
        ["gcc", "-frecord-gcc-switches", "-funroll-loops", "-o", str(newer / "toy"), str(src)],
        check=True,
    )

    dump = workload.audit_compiled_flags("706.stockfish_r", "peak")
    assert dump is not None
    assert "-funroll-loops" in dump


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
    # Required, not optional -- the shipped gcc_O3.cfg's `reportable = 1` default
    # rejects any single-benchmark selection without this, regardless of
    # --iterations (confirmed live against a real runcpu invocation).
    assert "--noreportable" in inner
    assert "706.stockfish_r" in inner


def test_parse_result_success_extracts_ratio(tmp_path):
    # Shape AND separator confirmed against a real --action=validate --iterations 3
    # run of 706.stockfish_r on this host (cfm/workloads/spec_cpu2026.py's
    # _RATIO_FIELD comment, CLAUDE.md's Non-obvious traps log): one
    # "NNN.ratio"/"NNN.reported_time" block per iteration (never a bare "ratio" key
    # directly under ".peak."), and "key: value" (colon-space), not "key = value" --
    # an earlier version of this fixture used "=" and passed against the *wrong*
    # separator this test itself was also (incorrectly) assuming, which is exactly
    # why hand-rolled fixtures didn't catch the bug the real .rsf file did.
    workload = _make_workload(tmp_path)
    workload.result_dir.mkdir(parents=True)
    rsf_path = workload.result_dir / "CPU2026.001.intrate.refrate.rsf"
    rsf_path.write_text(
        "spec.cpu2026.results.706_stockfish_r.peak.000.ratio: 12.0\n"
        "spec.cpu2026.results.706_stockfish_r.peak.000.reported_time: 55.0\n"
        "spec.cpu2026.results.706_stockfish_r.base.000.ratio: 9.0\n"
    )
    raw = "...\n[runcpu validate exited 0]\nSuccess: 1x706.stockfish_r\n"
    result = workload.parse_result("706.stockfish_r", "peak", raw)
    assert result.ok
    assert result.validated
    assert result.status == "ok"
    assert result.ratio == 12.0
    assert result.seconds == 55.0


def test_parse_result_medians_across_multiple_iterations(tmp_path):
    workload = _make_workload(tmp_path)
    workload.result_dir.mkdir(parents=True)
    rsf_path = workload.result_dir / "CPU2026.001.intrate.refrate.rsf"
    rsf_path.write_text(
        "spec.cpu2026.results.706_stockfish_r.peak.000.ratio: 10.0\n"
        "spec.cpu2026.results.706_stockfish_r.peak.001.ratio: 30.0\n"
        "spec.cpu2026.results.706_stockfish_r.peak.002.ratio: 20.0\n"
    )
    raw = "...\n[runcpu validate exited 0]\nSuccess: 1x706.stockfish_r\n"
    result = workload.parse_result("706.stockfish_r", "peak", raw)
    assert result.ratio == 20.0  # median of [10, 30, 20], not the first/last block
    assert result.seconds is None  # no reported_time fields present at all


def test_parse_result_against_real_captured_rsf(tmp_path):
    # Golden-output test: tests/fixtures/706.stockfish_r.peak.sample.rsf is a real
    # excerpt from an actual SPEC CPU2026 run on this host, not another hand-written
    # guess at the format -- the two bugs the hand-written fixtures above didn't
    # catch (missing iteration-index level, wrong "=" separator) were both only
    # caught by testing against real captured output. This test is what keeps a
    # future refactor honest against the same real data.
    workload = _make_workload(tmp_path)
    workload.result_dir.mkdir(parents=True)
    shutil.copy(
        _FIXTURES_DIR / "706.stockfish_r.peak.sample.rsf",
        workload.result_dir / "CPU2026.001.intrate.refrate.rsf",
    )
    raw = "...\n[runcpu validate exited 0]\nSuccess: 1x706.stockfish_r\n"
    result = workload.parse_result("706.stockfish_r", "peak", raw)
    assert result.ok
    assert result.status == "ok"
    assert result.ratio == pytest.approx(151.206688)  # median of the 3 real iterations
    assert result.seconds == pytest.approx(266.654868)  # median reported_time


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
