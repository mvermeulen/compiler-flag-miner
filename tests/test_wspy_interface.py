"""Contract/integration tests against the real, built vendor/wspy submodule
(CLAUDE.md's "wspy dependency" section) -- these are what catch a wspy update
silently changing the CLI output shape cfm's parsers depend on, rather than cfm
just quietly getting ``None``/empty results forever after a submodule bump.

Skipped automatically (not failed) when vendor/wspy hasn't been built yet
(``scripts/bootstrap_wspy.sh``), so ``pytest -q`` still runs cleanly on a fresh
clone before that script has been run -- same "skip/fail gracefully, don't assume"
posture ``cfm/instrumentation/wspy.py``'s own ``preflight()`` takes at runtime.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess

import pytest

from cfm.config import CfmConfig
from cfm.instrumentation.wspy import WspyInstrumentation
from cfm.util import parse_kv_lines


def _wspy_dir():
    return CfmConfig.from_env().wspy_dir


def _wspy_built() -> bool:
    wspy_dir = _wspy_dir()
    return all(
        (wspy_dir / binary).exists()
        for binary in ("wspy", "wspy-run", "wspy-store", "wspy-validate", "wspy-archetype", "wspy-summary")
    )


pytestmark = pytest.mark.skipif(
    not _wspy_built(), reason="vendor/wspy not built -- run scripts/bootstrap_wspy.sh first",
)


@pytest.fixture(scope="module")
def toy_binary(tmp_path_factory):
    if shutil.which("gcc") is None:
        pytest.skip("gcc not available to build the toy workload")
    src_dir = tmp_path_factory.mktemp("toybench")
    src = src_dir / "toy_compute.c"
    # printf'ing the accumulated value is load-bearing, not decoration: without an
    # observable use of `a`, gcc -O2 dead-code-eliminates the entire loop (caught
    # live -- an earlier `return (int)(a & 0)`-only version ran in 0.002s instead of
    # ~0.2s, silently turning every topdown-dependent assertion below into a test of
    # measurement noise instead of real counter data). Same shape as wspy's own toy
    # suite in doc/NEW_WORKLOAD_COOKBOOK.md, for the same reason.
    src.write_text(
        "#include <stdio.h>\n"
        "int main(void){\n"
        "  unsigned long a = 1;\n"
        "  for (long i = 0; i < 200000000L; i++) { a = a * 2654435761UL + 1; }\n"
        "  printf(\"%lu\\n\", a);\n"
        "  return 0;\n"
        "}\n"
    )
    binary = src_dir / "toy_compute"
    subprocess.run(["gcc", "-O2", "-o", str(binary), str(src)], check=True)
    return binary


@pytest.fixture(scope="module")
def real_run(tmp_path_factory, toy_binary):
    """One real wspy-run invocation, shared read-only by every test below. wspy
    imposes a ~2s minimum per invocation (its own pre-launch counter-arming window
    -- see wspy's topdown.c), so running this once per module rather than once per
    assertion keeps this file's wall-clock cost bounded. Yields (instrumentation,
    signature) -- most tests only need the signature (see real_signature below),
    but check_regression() needs the instrumentation instance too.
    """
    output_root = tmp_path_factory.mktemp("wspy_output")
    instrumentation = WspyInstrumentation(
        _wspy_dir(),
        store_db=output_root / "store.db",
        run_index_path=output_root / "cpu2026" / "run-index.jsonl",
    )
    assert instrumentation.preflight() == []
    signature = instrumentation.characterize(
        command=[str(toy_binary)],
        suite="cfmtest",
        benchmark="toy_compute",
        # NOTE: this run_id only names the output directory -- it does NOT end up
        # in wspy_run_ref below. See _resolve_run_identity()'s docstring in
        # cfm/instrumentation/wspy.py for why (a real, live-caught distinction, not
        # an assumption): each underlying wspy process invocation generates its own
        # run_id, independent of this one.
        run_id="contract-test-run",
        profile="quick",
        output_root=output_root,
    )
    return instrumentation, signature


@pytest.fixture(scope="module")
def real_signature(real_run):
    return real_run[1]


def test_check_regression_against_a_real_run_with_no_baseline_yet(real_run):
    # Only one run exists in this module's store -- confirmed live that
    # wspy-summary --check-regression reports the CSV header with zero data rows
    # in that case (exit 0), not an error and not a "no-baseline" status per row.
    # check_regression() returns [] either way (same as the "run not found" case),
    # which is exactly right: there's nothing to report yet, not a failure. This
    # test exists to confirm the real invocation itself works end to end (right
    # binary, right flags) without raising -- the parsing logic and the
    # baseline-exists case are covered by
    # tests/test_instrumentation_wspy.py's fixture-based tests and cfm/stats.py's
    # own unit tests (known hand-computed CI values) respectively.
    instrumentation, signature = real_run
    rows = instrumentation.check_regression(signature.wspy_run_ref)
    assert rows == []


def test_wspy_run_produces_a_traceable_run_ref(real_signature):
    # wspy always records its own socket.gethostname() -- not whatever this class
    # was constructed with (there's no such override anymore, see
    # cfm/instrumentation/wspy.py) -- and its own generated run_id, not the
    # directory-naming run_id characterize() was called with. Only the shape and
    # the hostname half are asserted; the run_id half is wspy's own
    # <timestamp>-<pid> value, not something this test can predict exactly.
    hostname, _, run_id = real_signature.wspy_run_ref.partition(":")
    assert hostname == socket.gethostname()
    assert run_id  # non-empty


def test_wspy_validate_passes_on_a_normal_run(real_signature):
    # cfm/instrumentation/wspy.py's _validate() reads the run-level manifest.json's
    # passes[].manifest entries and validates each pass's own manifest file -- this
    # asserts that whole path actually worked end to end, not just that some file
    # happened to exist.
    assert real_signature.validated is True


def test_archetype_scorecard_has_the_keys_cfm_parses(real_signature):
    # These are the exact key names cfm/instrumentation/wspy.py's characterize()
    # reads off wspy-archetype --run's key=value output (util.parse_kv_lines) -- if
    # a wspy update renames/removes any of these, this test fails instead of cfm
    # silently getting None for resource_dominance forever after a submodule bump.
    # "quick" only collects ipc+system (no topdown), so "unknown"/insufficient-data
    # is the *correct* outcome here, not a gap -- resource_dominance_pct/alternative
    # are legitimately omitted by wspy-archetype entirely (not printed as an empty
    # value) when there's no topdown data to compute them from; see
    # test_wspy_archetype_reports_a_populated_scorecard_with_topdown_data below for
    # the populated-data shape.
    assert real_signature.resource_dominance in (
        "compute-bound", "frontend-bound", "memory-bound", "speculation-bound", "unknown",
    )
    assert real_signature.metrics.get("confidence") == "insufficient-data"
    assert "memory_attribution" in real_signature.metrics
    assert "vectorization_density" in real_signature.metrics
    assert "allocation_pressure" in real_signature.metrics


def test_characterize_succeeds_on_deep_cpu_with_a_populated_scorecard(tmp_path_factory, toy_binary):
    # doc/DESIGN.md sec. 6 Phase 4's confirmation stage needs the multi-pass
    # "deep-cpu" profile -- M0 didn't support that (_resolve_run_identity() raised
    # rather than guess which of deep-cpu's 3 underlying wspy runs was "the" run);
    # M1 resolves it via _ARCHETYPE_PASS_NAME (see that constant's comment in
    # cfm/instrumentation/wspy.py for the live-confirmed reasoning: it's the
    # "amdtopdown" pass, not the "counters" multipass sweep one might expect from
    # wspy-run --help's own description). This is what confirms the real fix works
    # end to end against a real multi-pass wspy-run invocation, not just the
    # synthetic fixture in tests/test_instrumentation_wspy.py.
    output_root = tmp_path_factory.mktemp("wspy_output_multipass")
    instrumentation = WspyInstrumentation(
        _wspy_dir(),
        store_db=output_root / "store.db",
        run_index_path=output_root / "cpu2026" / "run-index.jsonl",
    )
    signature = instrumentation.characterize(
        command=[str(toy_binary)], suite="cfmtest", benchmark="toy_compute",
        run_id="multipass-run", profile="deep-cpu", output_root=output_root,
    )
    assert signature.validated is True
    assert signature.resource_dominance in (
        "compute-bound", "frontend-bound", "memory-bound", "speculation-bound",
    )
    assert signature.resource_dominance_pct is not None
    hostname, _, run_id = signature.wspy_run_ref.partition(":")
    assert hostname == socket.gethostname()
    assert run_id  # non-empty, and (per the fix) not "multipass-run" itself

    # vectorization_density/allocation_pressure (RunSignature's own new fields, doc/DESIGN.md sec. 14
    # M2.5 item 1) are dedicated fields now, but confirmed live (2026-08-18) still "unknown" here --
    # NOT a plumbing gap in this project, a real one in deep-cpu.conf itself: its "counters" pass
    # carries float/fault_rate in its --passes sweep but with no --csv (same non-CSV trap as the
    # amdtopdown-vs-counters pass-selection issue above), so wspy-store never ingests them into
    # run_features regardless of which pass wspy-archetype reads from. See CLAUDE.md's "Non-obvious
    # traps" for the full writeup. This assertion exists so a future deep-cpu.conf fix (upstream) makes
    # this test fail loudly with a real value instead of the gap silently going unnoticed.
    assert signature.vectorization_density == "unknown"
    assert signature.allocation_pressure == "unknown"


def test_wspy_archetype_reports_a_populated_scorecard_with_topdown_data(tmp_path_factory, toy_binary):
    # Bypasses WspyInstrumentation entirely -- this tests wspy's own CLI contract
    # directly (raw wspy -> wspy-store -> wspy-archetype), independent of this
    # project's plumbing, to confirm resource_dominance_pct really is populated
    # (not just conditionally absent, per the test above) once topdown data exists.
    # No single-pass builtin wspy-run profile collects topdown (see `wspy-run
    # --list`'s output: every topdown-carrying profile is multi-pass), so this
    # drives one `wspy --counters=topdown` invocation directly instead.
    #
    # --csv is load-bearing, not stylistic: without it, wspy-store enriches the
    # manifest but reports "0 metric-set(s) ingested, 1 skipped" and every
    # run_features row lands `coverage=unavailable` -- wspy-store only parses
    # metric *values* out of CSV output, per its own README ("ingests CSV into
    # long/tall metric_values table"). Human-readable text output (the default, and
    # what an earlier version of this test used) enriches the manifest fields but
    # carries no metric values at all. Caught live: the earlier version asserted
    # resource_dominance was populated and got "unknown" despite --counters=topdown
    # being requested and measured.
    work_dir = tmp_path_factory.mktemp("wspy_direct_topdown")
    manifest_path = work_dir / "run.manifest.json"
    run_index_path = work_dir / "run-index.jsonl"
    subprocess.run(
        [
            str(_wspy_dir() / "wspy"), "--counters=topdown", "--csv",
            "--manifest", str(manifest_path), "--run-index", str(run_index_path),
            "-o", str(work_dir / "run.csv"), "--", str(toy_binary),
        ],
        capture_output=True, text=True, check=True,
    )
    store_db = work_dir / "store.db"
    subprocess.run(
        [str(_wspy_dir() / "wspy-store"), "--db", str(store_db), "--run-index", str(run_index_path)],
        capture_output=True, text=True, check=True,
    )
    record = json.loads(run_index_path.read_text().splitlines()[-1])
    proc = subprocess.run(
        [str(_wspy_dir() / "wspy-archetype"), "--db", str(store_db),
         "--run", f"{record['hostname']}:{record['run_id']}"],
        capture_output=True, text=True, check=True,
    )
    scorecard = parse_kv_lines(proc.stdout)
    assert scorecard["resource_dominance"] in (
        "compute-bound", "frontend-bound", "memory-bound", "speculation-bound",
    )
    assert float(scorecard["resource_dominance_pct"]) >= 0.0  # raises if missing/non-numeric


def test_wspy_run_lists_the_profiles_cfm_relies_on_by_name():
    proc = subprocess.run(
        [str(_wspy_dir() / "wspy-run"), "--list"], capture_output=True, text=True, check=True,
    )
    # cfm/config.py's CFM_WSPY_PROFILE default is "quick"; doc/DESIGN.md sec. 6
    # Phases 3/4 assume "deep-cpu" exists for the confirmation stage -- both names
    # are relied on elsewhere in this codebase, so a wspy update that renames
    # either should fail this test rather than fail silently at mine-time in M1.
    assert "quick" in proc.stdout
    assert "deep-cpu" in proc.stdout
