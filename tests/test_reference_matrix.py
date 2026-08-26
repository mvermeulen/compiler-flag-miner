"""Unit + contract tests for cfm/reference_matrix.py (doc/DESIGN.md sec. 14 M2.5 item 2's deferred
half). Three tiers, same "skip/fail gracefully, don't assume" posture tests/test_wspy_interface.py
already uses:

1. Pure-logic tests (slugification, HTML block extraction against a real captured fixture,
   fetch_shape()'s graceful-degradation paths via a monkeypatched _find_page) -- no network, no
   vendor/wspy needed, always run.
2. Tests needing the built vendor/wspy submodule (counter_text.py import, wspy-archetype --run-guest)
   -- skipped cleanly, not failed, when it isn't built yet, matching test_wspy_interface.py exactly.
3. A real, live contract test against the actual mvermeulen.org/workload site -- skipped cleanly on
   any network failure, never a hard test-suite failure over an unrelated site/network hiccup.
"""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path

import pytest

import cfm.reference_matrix as reference_matrix
from cfm.config import CfmConfig

_FIXTURE_PAGE_HTML = (
    Path(__file__).parent / "fixtures" / "reference_matrix.706.stockfish_r.page.sample.html"
).read_text()


def _cfg(tmp_path, **kwargs):
    return CfmConfig.from_env(
        spec_dir=str(tmp_path / "spec"), wspy_dir=str(tmp_path / "wspy-unused"),
        output_root=str(tmp_path / "results"), db_path=str(tmp_path / "cfm.db"),
        **kwargs,
    )


# -- pure-logic: slugification -------------------------------------------------

def test_slugify_test_converts_dots_to_hyphens():
    assert reference_matrix._slugify_test("706.stockfish_r") == "706-stockfish_r"


def test_slugify_test_point_strips_cfg_suffix_and_lowercases():
    assert reference_matrix._slugify_test_point("gcc_O3.cfg") == "gcc_o3-base"


def test_slugify_test_point_handles_no_cfg_suffix():
    assert reference_matrix._slugify_test_point("llvm_O3") == "llvm_o3-base"


# -- pure-logic: HTML block extraction, against a real captured page ----------

def test_extract_preformatted_blocks_finds_every_block_in_real_page():
    # Real captured content (page id 1047, mvermeulen.org/workload/cpu2026/706-stockfish_r/
    # gcc_o3-base/amd-370-96gb/) -- five <pre class="wp-block-preformatted"> blocks: command line,
    # counters.txt, ibs.txt, and two process-tree dumps. Matches CLAUDE.md's own lesson (the .rsf
    # separator bug) -- a fixture copied from real output, not hand-written.
    blocks = reference_matrix._extract_preformatted_blocks(_FIXTURE_PAGE_HTML)
    assert len(blocks) == 5
    assert blocks[0].startswith("bash -c cd")  # command line
    assert blocks[1].startswith("elapsed")  # counters.txt
    assert blocks[2].startswith("ibs_sample_fetch_count")  # ibs.txt


def test_extract_preformatted_blocks_unescapes_html_entities():
    # The real command-line block HTML-escapes its shell "&&" (further backslash-escaped by the
    # command itself) as &amp;\&amp; -- confirms html.unescape() is actually applied, not just
    # regex-extracted raw.
    blocks = reference_matrix._extract_preformatted_blocks(_FIXTURE_PAGE_HTML)
    assert "&amp;" not in blocks[0]
    assert "&" in blocks[0]


# -- pure-logic: fetch_shape()'s graceful degradation, no network at all ------

def test_fetch_shape_returns_none_when_cpu2026_page_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(reference_matrix, "_find_page", lambda site_url, slug, parent: None)
    cfg = _cfg(tmp_path)
    assert reference_matrix.fetch_shape(cfg, "706.stockfish_r") is None


def test_fetch_shape_returns_none_when_no_matching_test_point(tmp_path, monkeypatch):
    # cpu2026 and the benchmark both resolve, but no <compiler>-base test point exists for it
    # (e.g. this exact tag has never been published) -- degrades to None, not an error.
    def fake_find_page(site_url, slug, parent):
        if slug == "cpu2026":
            return {"id": 1, "slug": "cpu2026"}
        if slug == "706-stockfish_r":
            return {"id": 2, "slug": "706-stockfish_r"}
        return None

    monkeypatch.setattr(reference_matrix, "_find_page", fake_find_page)
    cfg = _cfg(tmp_path)
    assert reference_matrix.fetch_shape(cfg, "706.stockfish_r") is None


def test_fetch_shape_returns_none_when_no_machines_published(tmp_path, monkeypatch):
    monkeypatch.setattr(
        reference_matrix, "_find_page",
        lambda site_url, slug, parent: {"id": 1, "slug": slug},
    )
    monkeypatch.setattr(reference_matrix, "_list_child_pages", lambda site_url, parent: [])
    cfg = _cfg(tmp_path)
    assert reference_matrix.fetch_shape(cfg, "706.stockfish_r") is None


def test_fetch_shape_tries_machines_in_sorted_order_and_skips_empty_recovery(tmp_path, monkeypatch):
    calls = []

    monkeypatch.setattr(
        reference_matrix, "_find_page",
        lambda site_url, slug, parent: {"id": 1, "slug": slug},
    )
    monkeypatch.setattr(
        reference_matrix, "_list_child_pages",
        lambda site_url, parent: [{"id": 20, "slug": "zzz-machine"}, {"id": 10, "slug": "aaa-machine"}],
    )

    def fake_recover(site_url, wspy_dir, machine_page_id):
        calls.append(machine_page_id)
        return {}  # nothing recoverable from either machine

    monkeypatch.setattr(reference_matrix, "_recover_machine_metrics", fake_recover)
    cfg = _cfg(tmp_path)
    assert reference_matrix.fetch_shape(cfg, "706.stockfish_r") is None
    # "aaa-machine" (id 10) sorts before "zzz-machine" (id 20) -- confirms deterministic
    # first-machine-sorted-by-slug ordering, not WordPress's own arbitrary listing order.
    assert calls == [10, 20]


def test_fetch_shape_returns_scorecard_with_source_machine(tmp_path, monkeypatch):
    monkeypatch.setattr(
        reference_matrix, "_find_page",
        lambda site_url, slug, parent: {"id": 1, "slug": slug},
    )
    monkeypatch.setattr(
        reference_matrix, "_list_child_pages",
        lambda site_url, parent: [{"id": 10, "slug": "amd-370-96gb"}],
    )
    monkeypatch.setattr(
        reference_matrix, "_recover_machine_metrics",
        lambda site_url, wspy_dir, machine_page_id: {"retire_pct": 40.0, "frontend_pct": 30.0},
    )
    monkeypatch.setattr(
        reference_matrix, "_score_guest_vector",
        lambda wspy_dir, guest: {"resource_dominance": "memory-bound", "confidence": "high"},
    )
    cfg = _cfg(tmp_path)
    shape = reference_matrix.fetch_shape(cfg, "706.stockfish_r")
    assert shape == {
        "resource_dominance": "memory-bound", "confidence": "high", "source_machine": "amd-370-96gb",
    }


def test_get_json_returns_none_on_network_error(monkeypatch):
    def raise_it(req, timeout):
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr(reference_matrix.urllib.request, "urlopen", raise_it)
    assert reference_matrix._get_json("https://example.invalid/wp-json/wp/v2/pages") is None


def test_score_guest_vector_coerces_numeric_percentage_fields(tmp_path, monkeypatch):
    # Fast, always-run (no real vendor/wspy binary needed) regression test for the
    # real 2026-08-26 bug: parse_kv_lines()'s own dict[str, str] return type means
    # every field wspy-archetype --run-guest prints comes back as a string unless
    # something explicitly coerces it -- resource_dominance_pct/alternative_pct are
    # the two numeric ones, invisible until a real cfm mine 707.ntest_r run did the
    # first-ever numeric comparison on resource_dominance_pct (M2's ranking code)
    # and crashed comparing a str to a float. See CLAUDE.md's traps log.
    class _FakeCompletedProcess:
        returncode = 0
        stdout = (
            "resource_dominance=compute-bound\n"
            "resource_dominance_pct=40.60\n"
            "alternative=frontend-bound\n"
            "alternative_pct=28.10\n"
            "confidence=medium\n"
        )

    monkeypatch.setattr(reference_matrix.subprocess, "run", lambda *a, **k: _FakeCompletedProcess())

    scorecard = reference_matrix._score_guest_vector(Path("unused"), {"retire_pct": 40.0})

    assert scorecard["resource_dominance"] == "compute-bound"  # untouched, still a string
    assert isinstance(scorecard["resource_dominance_pct"], float)
    assert scorecard["resource_dominance_pct"] == pytest.approx(40.60)
    assert isinstance(scorecard["alternative_pct"], float)
    assert scorecard["alternative_pct"] == pytest.approx(28.10)


# -- needs the built vendor/wspy submodule ------------------------------------

def _wspy_built() -> bool:
    wspy_dir = CfmConfig.from_env().wspy_dir
    return (wspy_dir / "wspy-archetype").exists() and (wspy_dir / "web" / "counter_text.py").exists()


@pytest.mark.skipif(not _wspy_built(), reason="vendor/wspy not built -- run scripts/bootstrap_wspy.sh first")
class TestAgainstBuiltWspy:
    def test_extracted_counters_block_classifies_as_counters(self):
        counter_text = reference_matrix._counter_text(CfmConfig.from_env().wspy_dir)
        blocks = reference_matrix._extract_preformatted_blocks(_FIXTURE_PAGE_HTML)
        assert counter_text.classify_counter_text(blocks[0]) is None  # command line
        assert counter_text.classify_counter_text(blocks[1]) == "counters"  # counters.txt
        assert counter_text.classify_counter_text(blocks[2]) == "ibs"  # ibs.txt

    def test_parsing_real_counters_block_recovers_known_metrics(self):
        counter_text = reference_matrix._counter_text(CfmConfig.from_env().wspy_dir)
        blocks = reference_matrix._extract_preformatted_blocks(_FIXTURE_PAGE_HTML)
        records = counter_text.parse_counter_text(blocks[1])
        by_name = {r["metric"]: r["value"] for r in records}
        assert by_name["elapsed"] == pytest.approx(300.749)
        assert by_name["minflt"] == pytest.approx(32805293)

    def test_score_guest_vector_scores_a_real_wspy_archetype_run(self, tmp_path):
        # A synthetic but plausible guest vector -- confirms the subprocess plumbing (temp file,
        # --run-guest, parse_kv_lines()) works against the real binary, not that any particular
        # classification comes out (that's wspy's own scoring logic, not this module's job to
        # re-verify).
        wspy_dir = CfmConfig.from_env().wspy_dir
        guest = {"retire_pct": 10.0, "frontend_pct": 15.0, "backend_pct": 60.0, "speculate_pct": 15.0}
        scorecard = reference_matrix._score_guest_vector(wspy_dir, guest)
        assert scorecard is not None
        assert "resource_dominance" in scorecard
        # Real regression check for a real caught bug (2026-08-26, CLAUDE.md's traps
        # log): parse_kv_lines()'s own return type is dict[str, str] -- everything
        # wspy-archetype --run-guest prints comes back as a string unless something
        # explicitly coerces it. This exact test previously only checked
        # "resource_dominance" in scorecard and missed that resource_dominance_pct
        # was silently a str, not a float -- invisible until a real cfm mine
        # 707.ntest_r run crashed doing a numeric comparison on it for the first
        # time (M2's ranking code). Assert the type explicitly now, against the
        # real binary, not a mock -- a mock could trivially "pass" this check
        # without proving the real subprocess output is actually coerced.
        assert isinstance(scorecard["resource_dominance_pct"], float)


# -- real, live contract test against the actual site -------------------------

def _site_reachable() -> bool:
    try:
        result = reference_matrix._get_json(
            "https://mvermeulen.org/workload/wp-json/wp/v2/pages?slug=cpu2026&parent=0"
        )
        return result is not None
    except Exception:
        return False


@pytest.mark.skipif(not _wspy_built(), reason="vendor/wspy not built -- run scripts/bootstrap_wspy.sh first")
@pytest.mark.skipif(not _site_reachable(), reason="mvermeulen.org/workload unreachable")
def test_fetch_shape_against_the_real_live_site():
    """Confirmed live, 2026-08-20: real 706.stockfish_r data exists for 3 machines
    (amd-370-64gb/amd-370-96gb/amd-395-96gb), gcc_o3-base and llvm_o3-base. No wp_cfg/credentials --
    this is the whole point (see this module's own docstring)."""
    cfg = CfmConfig.from_env()
    shape = reference_matrix.fetch_shape(cfg, "706.stockfish_r")
    assert shape is not None
    assert shape["source_machine"] in ("amd-370-64gb", "amd-370-96gb", "amd-395-96gb")
    # resource_dominance is the one axis confirmed name-aligned in counter_text.py today
    # (wspy#278 tracks vectorization_density/allocation_pressure's own gap) -- expect a real verdict,
    # not "unknown", for this specific benchmark/machine combination.
    assert shape.get("resource_dominance") not in (None, "unknown")
