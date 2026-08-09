from cfm.instrumentation.wspy import WspyInstrumentation, _to_float


def _make(tmp_path):
    return WspyInstrumentation(
        tmp_path, store_db=tmp_path / "store.db", run_index_path=tmp_path / "index.jsonl",
        hostname="testhost",
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
