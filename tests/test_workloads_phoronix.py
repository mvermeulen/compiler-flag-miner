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
from cfm.workloads.phoronix import PhoronixWorkload, _template_regex
from cfm.workloads.spec_cpu2026 import SpecCpu2026Workload

BENCH = "pts/coremark-9.9.9"

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="needs gcc")

# Prints a different score on each run (a counter file in the cwd), and a
# CoreMark-style failure when built with -DBROKEN.
TOY_C = r"""
#include <stdio.h>
int main(void) {
    int n = 0;
    FILE *f = fopen("count", "r");
    if (f) { if (fscanf(f, "%d", &n) != 1) n = 0; fclose(f); }
    f = fopen("count", "w"); fprintf(f, "%d\n", n + 1); fclose(f);
    printf("CoreMark Size    : 666\n");
    printf("Iterations/Sec   : %d.5\n", 1000 + 10 * n);
#ifdef BROKEN
    printf("ERROR! list crc 0x0000 - should be 0xe714\nErrors detected\n");
#else
    printf("Correct operation validated. See README.md for run and reporting rules.\n");
#endif
    return 0;
}
"""

INSTALL_SH = """#!/bin/sh
gcc $CFLAGS -o toy.bin toy.c
echo $? > ~/install-exit-status
cd ~
echo "#!/bin/sh
./toy.bin > \\$LOG_FILE 2>&1
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
                  installed: bool = True) -> Path:
    pts_home = root / "pts-home"
    profile = pts_home / "test-profiles" / bench
    profile.mkdir(parents=True)
    (profile / "install.sh").write_text(INSTALL_SH)
    (profile / "test-definition.xml").write_text(
        TEST_DEFINITION.format(proportion=proportion, settings=settings)
    )
    (profile / "results-definition.xml").write_text(RESULTS_DEFINITION)
    (profile / "downloads.xml").write_text(DOWNLOADS)
    if installed:
        install = pts_home / "installed-tests" / bench
        install.mkdir(parents=True)
        (install / "toy.c").write_text(TOY_C)
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
    profile_dir = tmp_path / "results" / "phoronix" / "coremark-9.9.9" / "pgo-profile"
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
