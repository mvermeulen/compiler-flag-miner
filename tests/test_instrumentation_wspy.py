import json

import pytest

from cfm.instrumentation.wspy import WspyInstrumentation, _count_lines, _to_float


def _make(tmp_path):
    return WspyInstrumentation(
        tmp_path, store_db=tmp_path / "store.db", run_index_path=tmp_path / "index.jsonl",
    )


def test_preflight_reports_all_missing_binaries(tmp_path):
    problems = _make(tmp_path).preflight()
    assert len(problems) == 5
    assert all("make" in p for p in problems)


def test_preflight_passes_when_binaries_present(tmp_path):
    for name in ("wspy", "wspy-run", "wspy-store", "wspy-validate", "wspy-archetype"):
        (tmp_path / name).write_text("#!/bin/sh\n")
    assert _make(tmp_path).preflight() == []


def test_preflight_reports_only_missing_binaries(tmp_path):
    (tmp_path / "wspy").write_text("#!/bin/sh\n")
    (tmp_path / "wspy-run").write_text("#!/bin/sh\n")
    problems = _make(tmp_path).preflight()
    assert len(problems) == 3
    assert not any("wspy-run not found" in p or p.startswith("wspy not found") for p in problems)


def test_to_float_handles_none_and_bad_values():
    assert _to_float(None) is None
    assert _to_float("not-a-number") is None
    assert _to_float("12.5") == 12.5


def test_count_lines_missing_file_is_zero(tmp_path):
    assert _count_lines(tmp_path / "does-not-exist.jsonl") == 0


def test_count_lines_counts_real_lines(tmp_path):
    path = tmp_path / "index.jsonl"
    path.write_text('{"a":1}\n{"a":2}\n{"a":3}\n')
    assert _count_lines(path) == 3


def test_resolve_run_identity_reads_the_newly_appended_record(tmp_path):
    # This is the fix for the bug tests/test_wspy_interface.py caught live: the
    # run_id wspy-store/wspy-archetype key on is the one *wspy itself* generated
    # and wrote to --run-index, not whatever run_id characterize() was called with.
    # rundir/profile are irrelevant on the single-new-line path (not touched until
    # more than one new record shows up), so dummy values are fine here.
    instrumentation = _make(tmp_path)
    instrumentation.run_index_path.write_text(
        json.dumps({"hostname": "otherhost", "run_id": "pre-existing-run"}) + "\n"
    )
    lines_before = _count_lines(instrumentation.run_index_path)
    with instrumentation.run_index_path.open("a") as f:
        f.write(json.dumps({"hostname": "realhost", "run_id": "20260809T000000.000-12345"}) + "\n")
    hostname, run_id = instrumentation._resolve_run_identity(tmp_path, "quick", lines_before)
    assert hostname == "realhost"
    assert run_id == "20260809T000000.000-12345"


def test_resolve_run_identity_raises_when_nothing_new_was_written(tmp_path):
    instrumentation = _make(tmp_path)
    instrumentation.run_index_path.write_text(
        json.dumps({"hostname": "otherhost", "run_id": "pre-existing-run"}) + "\n"
    )
    lines_before = _count_lines(instrumentation.run_index_path)
    with pytest.raises(RuntimeError, match="no new run-index record"):
        instrumentation._resolve_run_identity(tmp_path, "quick", lines_before)


def test_resolve_run_identity_picks_the_designated_pass_for_a_known_multi_pass_profile(tmp_path):
    # Mirrors a real deep-cpu run's shape (confirmed live, see _ARCHETYPE_PASS_NAME's
    # comment in cfm/instrumentation/wspy.py): 3 new run-index records, only one of
    # which shares its start_time with the "amdtopdown" pass's own per-pass manifest.
    instrumentation = _make(tmp_path)
    rundir = tmp_path / "cpu2026" / "706.stockfish_r" / "run1"
    rundir.mkdir(parents=True)
    (rundir / "manifest.json").write_text(json.dumps({
        "layout_version": "1.0.0",
        "passes": [
            {"name": "systemtime", "manifest": "systemtime.manifest.json", "status": "ok"},
            {"name": "counters", "manifest": "counters.manifest.json", "status": "ok"},
            {"name": "amdtopdown", "manifest": "amdtopdown.manifest.json", "status": "ok"},
        ],
    }))
    for name, start_time in (
        ("systemtime", "2026-08-09T16:41:52.036Z"),
        ("counters", "2026-08-09T16:41:54.507Z"),
        ("amdtopdown", "2026-08-09T16:42:14.157Z"),
    ):
        (rundir / f"{name}.manifest.json").write_text(
            json.dumps({"timing": {"start_time": start_time}})
        )

    instrumentation.run_index_path.write_text("")
    lines_before = _count_lines(instrumentation.run_index_path)
    with instrumentation.run_index_path.open("a") as f:
        f.write(json.dumps({
            "hostname": "h", "run_id": "20260809T164152.036-1",
            "start_time": "2026-08-09T16:41:52.036Z",
        }) + "\n")
        f.write(json.dumps({
            "hostname": "h", "run_id": "20260809T164154.507-2",
            "start_time": "2026-08-09T16:41:54.507Z",
        }) + "\n")
        f.write(json.dumps({
            "hostname": "h", "run_id": "20260809T164214.157-3",
            "start_time": "2026-08-09T16:42:14.157Z",
        }) + "\n")

    hostname, run_id = instrumentation._resolve_run_identity(rundir, "deep-cpu", lines_before)
    assert hostname == "h"
    assert run_id == "20260809T164214.157-3"  # the amdtopdown pass's run, not systemtime/counters


def test_resolve_run_identity_raises_on_unmapped_multi_pass_profile(tmp_path):
    # A multi-pass profile with no _ARCHETYPE_PASS_NAME entry (e.g. deep-cpu-intel) --
    # this must fail loudly, not guess which pass's run_id to use.
    instrumentation = _make(tmp_path)
    instrumentation.run_index_path.write_text("")
    lines_before = _count_lines(instrumentation.run_index_path)
    with instrumentation.run_index_path.open("a") as f:
        f.write(json.dumps({"hostname": "h", "run_id": "run-a"}) + "\n")
        f.write(json.dumps({"hostname": "h", "run_id": "run-b"}) + "\n")
    with pytest.raises(RuntimeError, match="deep-cpu-intel"):
        instrumentation._resolve_run_identity(tmp_path, "deep-cpu-intel", lines_before)
