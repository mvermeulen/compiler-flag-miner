"""cfm/workloads/phoronix.py against a fake PTS user directory holding a small,
coremark-shaped test profile. The toy really is compiled with the trial's CFLAGS
and really runs, so these check what reaches the compiler and what comes back
out of $LOG_FILE, not just the strings this module renders.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from cfm import reference_matrix
from cfm.config import CfmConfig
from cfm.workloads import workload_for
from cfm.workloads.phoronix import (
    COREMARK_ITERATIONS, CRAFTY_SERIAL_NODES, TSCP_NODES, TSCP_PV, TSCP_RUNS, PhoronixWorkload,
    _crafty_valid, _himeno_valid, _template_regex, _tscp_valid,
)
from cfm.workloads import phoronix
from cfm.workloads.spec_cpu2026 import SpecCpu2026Workload

BENCH = "pts/coremark-9.9.9"

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="needs gcc")

# Prints a different score on each run (a counter file in the cwd), and a
# CoreMark-style failure when built with -DBROKEN.
TOY_C = r"""
#include <stdio.h>
int main(int argc, char **argv) {
    int n = 0;
    FILE *f = fopen("count", "r");
    if (f) { if (fscanf(f, "%d", &n) != 1) n = 0; fclose(f); }
    f = fopen("count", "w"); fprintf(f, "%d\n", n + 1); fclose(f);
    printf("CoreMark Size    : 666\n");
    printf("Iterations       : %s\n", argc > 4 ? argv[4] : "auto");
    printf("Iterations/Sec   : %d.5\n", 1000 + 10 * n);
#ifdef BROKEN
    printf("ERROR! list crc 0x0000 - should be 0xe714\nErrors detected\n");
#else
    printf("Correct operation validated. See README.md for run and reporting rules.\n");
#endif
    return 0;
}
"""

# Laid out like the real profile: the binary in coremark-master/, run by a
# wrapper script that passes no arguments.
INSTALL_SH = """#!/bin/sh
mkdir -p coremark-master
gcc $CFLAGS -o coremark-master/coremark.exe toy.c
echo $? > ~/install-exit-status
cd ~
echo "#!/bin/sh
cd coremark-master
./coremark.exe > \\$LOG_FILE 2>&1
echo \\$? > ~/test-exit-status" > coremark
chmod +x coremark
"""

TEST_DEFINITION = """<?xml version="1.0"?>
<PhoronixTestSuite>
  <TestInformation>
    <Title>Coremark</Title>
    <Proportion>{proportion}</Proportion>
    <TimesToRun>3</TimesToRun>
  </TestInformation>
  {settings}
</PhoronixTestSuite>
"""

RESULTS_DEFINITION = """<?xml version="1.0"?>
<PhoronixTestSuite>
  <ResultsParser>
    <OutputTemplate>Iterations/Sec   : #_RESULT_#</OutputTemplate>
  </ResultsParser>
</PhoronixTestSuite>
"""

DOWNLOADS = """<?xml version="1.0"?>
<PhoronixTestSuite>
  <Downloads>
    <Package><FileName>toy.c</FileName></Package>
  </Downloads>
</PhoronixTestSuite>
"""


def make_pts_home(root: Path, bench: str = BENCH, proportion: str = "HIB", settings: str = "",
                  installed: bool = True, install_sh: str = INSTALL_SH, toy_c: str = TOY_C,
                  results_definition: str = RESULTS_DEFINITION) -> Path:
    pts_home = root / "pts-home"
    profile = pts_home / "test-profiles" / bench
    profile.mkdir(parents=True)
    (profile / "install.sh").write_text(install_sh)
    (profile / "test-definition.xml").write_text(
        TEST_DEFINITION.format(proportion=proportion, settings=settings)
    )
    (profile / "results-definition.xml").write_text(results_definition)
    (profile / "downloads.xml").write_text(DOWNLOADS)
    if installed:
        install = pts_home / "installed-tests" / bench
        install.mkdir(parents=True)
        (install / "toy.c").write_text(toy_c)
    return pts_home


@pytest.fixture
def workload(tmp_path):
    return PhoronixWorkload(make_pts_home(tmp_path), tmp_path / "results", cpu_count=lambda: 4)


def build(workload, flags):
    config = workload.generate_config(BENCH, "peak", flags)
    return config, workload.build(BENCH, "peak", config)


def measure(workload, config, iterations):
    argv = workload.run_command(BENCH, "peak", config, iterations=iterations)
    subprocess.run(argv, check=True)
    return workload.parse_result(BENCH, "peak", "")


def test_build_run_and_parse_take_the_median_score(workload):
    config, result = build(workload, ["-O2"])
    assert result.ok, result.raw_output
    run = measure(workload, config, iterations=3)
    assert run.ok and run.validated and run.status == "ok"
    assert run.ratio == 1010.5  # scores 1000.5, 1010.5, 1020.5
    assert len(run.result_files) == 3


def test_relative_output_root_works(tmp_path, monkeypatch):
    # cfg.output_root defaults to a relative "results"; install.sh cds around with
    # HOME pointing into it, so a relative path broke the first real build.
    pts_home = make_pts_home(tmp_path)
    monkeypatch.chdir(tmp_path)
    workload = PhoronixWorkload(pts_home, "results", cpu_count=lambda: 4)
    config, result = build(workload, ["-O2"])
    assert result.ok, result.raw_output
    monkeypatch.chdir("/")
    assert measure(workload, config, iterations=1).ok


def test_coremark_runs_a_fixed_iteration_count(workload):
    # The wrapper script would let coremark size its own run; the override
    # passes an explicit count instead (COREMARK_ITERATIONS).
    config, _ = build(workload, ["-O2"])
    run = measure(workload, config, iterations=1)
    assert run.ok
    assert f"Iterations       : {COREMARK_ITERATIONS}" in run.result_files[0].read_text()


def test_flags_reach_the_compiled_binary(workload):
    _, result = build(workload, ["-O2", "-fno-inline"])
    assert result.ok, result.raw_output
    dump = workload.audit_compiled_flags(BENCH, "peak")
    assert dump is not None
    assert "-O2" in dump and "-fno-inline" in dump


def test_rebuild_starts_from_a_clean_directory(workload):
    config, _ = build(workload, ["-O2"])
    measure(workload, config, iterations=1)
    config, result = build(workload, ["-O2"])
    assert result.ok
    # The counter file from the earlier run is gone, so scoring starts over.
    assert measure(workload, config, iterations=1).ratio == 1000.5


def test_failed_output_check_is_validate_failed(workload):
    config, result = build(workload, ["-O2", "-DBROKEN"])
    assert result.ok
    run = measure(workload, config, iterations=1)
    assert not run.ok and run.status == "validate-failed" and run.ratio is None


def test_compile_error_is_a_failed_build(workload):
    _, result = build(workload, ["-O2", "-fthis-flag-does-not-exist"])
    assert not result.ok
    assert "this-flag-does-not-exist" in result.raw_output


def test_pgo_builds_instrumented_trains_then_rebuilds_with_the_profile(workload, tmp_path):
    config, result = build(workload, ["-O2", "-fprofile-use"])
    assert result.ok, result.raw_output
    assert "PGO training run (ok)" in result.raw_output
    [profile_dir] = (tmp_path / "results" / "phoronix" / "coremark-9.9.9" / "pgo-profile").iterdir()
    assert list(profile_dir.glob("*.gcda"))
    dump = workload.audit_compiled_flags(BENCH, "peak")
    assert f"-fprofile-use={profile_dir}" in dump
    assert "-fprofile-generate" not in dump
    assert measure(workload, config, iterations=1).ok


def test_code_fingerprint_ignores_recorded_switches_but_sees_code_changes(workload):
    build(workload, ["-O2"])
    first = workload.code_fingerprint(BENCH, "peak")
    build(workload, ["-O2", "-DUNUSED_MACRO"])  # different switches, same code
    same = workload.code_fingerprint(BENCH, "peak")
    build(workload, ["-O2", "-DBROKEN"])
    different = workload.code_fingerprint(BENCH, "peak")
    assert first is not None
    assert first == same
    assert first != different


def test_benchmark_languages_from_built_sources(workload):
    with pytest.raises(RuntimeError, match="built yet"):
        workload.benchmark_languages(BENCH)
    build(workload, ["-O2"])
    assert workload.benchmark_languages(BENCH) == ["c"]


@pytest.mark.parametrize("kwargs, reason", [
    ({"bench": "pts/othertest-1.0.0"}, "no output validator"),
    ({"proportion": "LIB"}, "only higher-is-better"),
    ({"settings": "<TestSettings><Option><Identifier>x</Identifier></Option></TestSettings>"},
     "options menus"),
    ({"installed": False}, "phoronix-test-suite install"),
])
def test_unsupported_profiles_are_refused_before_building(tmp_path, kwargs, reason):
    bench = kwargs.pop("bench", BENCH)
    workload = PhoronixWorkload(make_pts_home(tmp_path, bench=bench, **kwargs), tmp_path / "results")
    with pytest.raises(RuntimeError, match=reason):
        workload.generate_config(bench, "peak", ["-O2"])


def test_template_regex_handles_glued_and_other_placeholders():
    assert _template_regex("Iterations/Sec   : #_RESULT_#").search(
        "Iterations/Sec   : 352281.825460").group(1) == "352281.825460"
    assert _template_regex("#_RESULT_#ms in #_TEST_# total").search(
        "x 12.5ms in foo total").group(1) == "12.5"


def test_workload_for_routes_by_benchmark_name(tmp_path):
    cfg = CfmConfig.from_env(spec_dir=str(tmp_path), pts_home=str(tmp_path / "pts"))
    assert isinstance(workload_for(cfg, "pts/coremark-1.0.1"), PhoronixWorkload)
    assert isinstance(workload_for(cfg, "706.stockfish_r"), SpecCpu2026Workload)


def test_reference_matrix_skips_phoronix_benchmarks_without_a_network_call(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("should not be called")
    monkeypatch.setattr(reference_matrix, "_find_page", no_network)
    cfg = CfmConfig.from_env(spec_dir=str(tmp_path))
    assert reference_matrix.fetch_shape(cfg, "pts/coremark-1.0.1") is None


def test_template_regex_ignores_tokens_after_the_result():
    # TSCP's template carries a sample "(Score: ...)" that differs on every run.
    pattern = _template_regex("Nodes per second: #_RESULT_# (Score: 1.034)")
    assert pattern.search("Nodes per second: 2514968 (Score: 10.342)").group(1) == "2514968"


# Shaped like PTS's tscp profile: CFLAGS_OVERRIDE, else "$CFLAGS -O3 -march=native".
TSCP_BENCH = "pts/tscp-9.9.9"
TSCP_INSTALL_SH = """#!/bin/sh
mkdir -p tscp181
if [ "X$CFLAGS_OVERRIDE" = "X" ]
then
          CFLAGS="$CFLAGS -O3 -march=native"
else
          CFLAGS="$CFLAGS_OVERRIDE"
fi
gcc $CFLAGS -o tscp181/tscp toy.c
echo $? > ~/install-exit-status
cd ~
echo "#!/bin/sh
cd tscp181/
./tscp \\$@ > \\$LOG_FILE 2>&1
echo \\$? > ~/test-exit-status" > tscp
chmod +x tscp
"""

# Prints TSCP's benchmark tail; the score climbs by 10 per run (a counter file),
# so a log of TSCP_RUNS runs averages to a known value.
TSCP_TOY_C = r"""
#include <stdio.h>
int main(void) {
    int n = 0, i;
    FILE *f = fopen("count", "r");
    if (f) { if (fscanf(f, "%d", &n) != 1) n = 0; fclose(f); }
    f = fopen("count", "w"); fprintf(f, "%d\n", n + 1); fclose(f);
    for (i = 0; i < 3; ++i)
        printf("  5     NODES     26  PV\nTime: 219 ms\n");
    printf("\nNodes: NODES\nBest time: 219 ms\n");
    printf("Nodes per second: %d (Score: 10.342)\n", 1000 + 10 * n);
    return 0;
}
""".replace("NODES", str(TSCP_NODES)).replace("PV", TSCP_PV)

TSCP_RESULTS_DEFINITION = RESULTS_DEFINITION.replace(
    "Iterations/Sec   : #_RESULT_#", "Nodes per second: #_RESULT_# (Score: 1.034)",
)


@pytest.fixture
def tscp_workload(tmp_path):
    pts_home = make_pts_home(
        tmp_path, bench=TSCP_BENCH, install_sh=TSCP_INSTALL_SH, toy_c=TSCP_TOY_C,
        results_definition=TSCP_RESULTS_DEFINITION,
    )
    return PhoronixWorkload(pts_home, tmp_path / "results", cpu_count=lambda: 4, cpu_lister=lambda: [0])


def test_cflags_override_replaces_the_profiles_own_flags(tscp_workload):
    config = tscp_workload.generate_config(TSCP_BENCH, "peak", ["-O1"])
    assert tscp_workload.build(TSCP_BENCH, "peak", config).ok
    dump = tscp_workload.audit_compiled_flags(TSCP_BENCH, "peak")
    assert "-O1" in dump
    assert "-march=native" not in dump and "-O3" not in dump


@pytest.mark.skipif(shutil.which("taskset") is None, reason="needs taskset")
def test_tscp_runs_pinned_and_averages_the_runs_in_a_log(tscp_workload):
    config = tscp_workload.generate_config(TSCP_BENCH, "peak", ["-O2"])
    assert tscp_workload.build(TSCP_BENCH, "peak", config).ok
    argv = tscp_workload.run_command(TSCP_BENCH, "peak", config, iterations=1)
    assert "taskset -c 0 ./tscp" in argv[-1]  # only CPU 0 listed, so CPU 0
    subprocess.run(argv, check=True)
    run = tscp_workload.parse_result(TSCP_BENCH, "peak", "")
    assert run.ok and run.validated
    # Scores 1000, 1010, ..., 1000 + 10 * (TSCP_RUNS - 1).
    assert run.ratio == pytest.approx(1000 + 5 * (TSCP_RUNS - 1))


def test_pinned_cpu_avoids_cpu_0_when_there_is_a_choice(tmp_path):
    workload = PhoronixWorkload(tmp_path, tmp_path / "results", cpu_lister=lambda: [0, 2, 4])
    assert workload._pinned_cpu() == 2


def test_tscp_validator():
    run = f"  5     {TSCP_NODES}     26  {TSCP_PV}\n" * 3 + (
        f"\nNodes: {TSCP_NODES}\nBest time: 219 ms\nNodes per second: 2514968 (Score: 10.342)\n"
    )
    assert _tscp_valid(run * 2)
    assert not _tscp_valid(run.replace(f"Nodes: {TSCP_NODES}", "Nodes: 550777"))
    assert not _tscp_valid(run.replace(TSCP_PV, "c2a4 d6c7 g2d5 e6d5 a1b1"))
    assert not _tscp_valid(run.replace("Nodes per second: 2514968 (Score: 10.342)", "(invalid)"))
    assert not _tscp_valid("")


def test_downloads_for_other_platforms_are_not_required(tmp_path):
    pts_home = make_pts_home(tmp_path)
    (pts_home / "test-profiles" / BENCH / "downloads.xml").write_text(DOWNLOADS.replace(
        "<Package><FileName>toy.c</FileName></Package>",
        "<Package><FileName>toy.c</FileName><PlatformSpecific>Linux, BSD</PlatformSpecific></Package>"
        "<Package><FileName>toy.exe.zip</FileName><PlatformSpecific>Windows</PlatformSpecific></Package>",
    ))
    workload = PhoronixWorkload(pts_home, tmp_path / "results")
    assert workload.profile(BENCH).downloads == ("toy.c",)


def test_crafty_validator_checks_only_the_serial_total():
    serial = f"Running serial benchmark. . .\nTotal nodes: {CRAFTY_SERIAL_NODES}\nRaw nodes per second: 12949126\n"
    smp = "Running SMP benchmark (2 threads)...\nTotal nodes: 193502643\nRaw nodes per second: 12840255\n"
    assert _crafty_valid(serial + smp)
    assert not _crafty_valid(serial.replace(str(CRAFTY_SERIAL_NODES), "191258592") + smp)
    assert not _crafty_valid(smp)


def test_build_override_replaces_install_sh(workload, monkeypatch):
    # The profile's install.sh would compile with $CFLAGS; this override ignores
    # it and adds a marker instead, so the audit shows which script ran.
    monkeypatch.setitem(phoronix._BUILD_OVERRIDES, "coremark", INSTALL_SH.replace(
        "gcc $CFLAGS", "gcc -O1 -fno-plt -frecord-gcc-switches",
    ))
    config, result = build(workload, ["-O2"])
    assert result.ok, result.raw_output
    dump = workload.audit_compiled_flags(BENCH, "peak")
    assert "-fno-plt" in dump and "-O2" not in dump


def test_first_score_only_ignores_later_scores(workload, monkeypatch):
    # The toy prints a running score; run it twice into one log.
    monkeypatch.setitem(
        phoronix._RUN_OVERRIDES, "coremark",
        'cd coremark-master && { ./coremark.exe; ./coremark.exe; } > "$LOG_FILE" 2>&1',
    )
    config, _ = build(workload, ["-O2"])
    assert measure(workload, config, iterations=1).ratio == 1005.5  # mean of 1000.5 and 1010.5
    monkeypatch.setattr(phoronix, "_FIRST_SCORE_ONLY", frozenset({"coremark"}))
    assert measure(workload, config, iterations=1).ratio == 1020.5  # third run's, not the fourth's


def test_pgo_trains_once_per_flagset_and_reuses_the_profile(workload):
    _, first = build(workload, ["-O2", "-fprofile-use"])
    assert first.ok and "PGO training run (ok)" in first.raw_output
    fingerprint = workload.code_fingerprint(BENCH, "peak")

    _, again = build(workload, ["-O2", "-fprofile-use"])
    assert again.ok
    assert "PGO training run" not in again.raw_output
    assert "reusing the profile" in again.raw_output
    assert workload.code_fingerprint(BENCH, "peak") == fingerprint

    # Different flags get their own profile.
    _, other = build(workload, ["-O1", "-fprofile-use"])
    assert other.ok and "PGO training run (ok)" in other.raw_output


def test_workload_for_keeps_one_phoronix_backend_so_pgo_profiles_are_reused(tmp_path):
    # run_one_trial() calls workload_for() on every trial; PGO profile reuse only
    # works if those calls share one backend.
    cfg = CfmConfig.from_env(
        spec_dir=str(tmp_path / "spec"), pts_home=str(make_pts_home(tmp_path)),
        output_root=str(tmp_path / "results"),
    )
    first = workload_for(cfg, BENCH)
    assert workload_for(cfg, BENCH) is first
    _, built = build(first, ["-O2", "-fprofile-use"])
    assert "PGO training run (ok)" in built.raw_output
    _, rebuilt = build(workload_for(cfg, BENCH), ["-O2", "-fprofile-use"])
    assert "reusing the profile" in rebuilt.raw_output


HIMENO_LOG = """ MFLOPS: 7552.172875 time(s): 0.006282 {rehearsal}

 Loop executed for 28653 times
 Gosa : {final} 
 MFLOPS measured : 7591.768531\tcpu : 59.686449
"""


@pytest.mark.parametrize("rehearsal, final, ok", [
    ("3.288628e-03", "0.000000e+00", True),
    ("3.288662e-03", "0.000000e+00", True),   # -ffast-math -march=native on erie
    ("3.300000e-03", "0.000000e+00", False),  # off by 0.3%
    ("3.288628e-03", "nan", False),
    ("3.288628e-03", "1.000000e+00", False),  # residual grew
])
def test_himeno_validator(rehearsal, final, ok):
    assert _himeno_valid(HIMENO_LOG.format(rehearsal=rehearsal, final=final)) is ok
    assert not _himeno_valid("")


def test_himeno_template_reads_the_measured_line():
    pattern = _template_regex(" MFLOPS measured : #_RESULT_#\tcpu : 59.868463")
    text = HIMENO_LOG.format(rehearsal="3.288628e-03", final="0.000000e+00")
    assert pattern.findall(text) == ["7591.768531"]
