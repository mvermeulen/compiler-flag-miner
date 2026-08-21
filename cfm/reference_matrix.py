"""External reference-matrix corpus (``mvermeulen.org/workload``) as a *characterization*-shape
source -- doc/DESIGN.md sec. 14 M2.5 item 2's deferred half.

Read-only and fully anonymous: no ``wp_cfg``/WordPress Application Password needed at all (confirmed
live, 2026-08-20, that this site's REST API serves published-page content -- including full-depth
``counters.txt`` ``<pre>`` blocks -- to unauthenticated GET requests; only *writing* via
``wspy-publish`` needs credentials). A mining host never needs to be able to log in anywhere for this
to work -- that was a hard requirement going in, not an afterthought.

Never a substitute *measurement* -- doc/DESIGN.md sec. 15's non-comparability decision holds exactly
as much here as it always has: this is purely a *shape* source (``resource_dominance``/
``vectorization_density``/``allocation_pressure``), an alternative to ``orchestrator._characterize_
baseline()``'s own local ``deep-cpu`` fallback trial, replacing ~46 minutes of real measurement with a
few read-only HTTP calls when a matching published entry already exists. The actual ratio is always
measured locally, same as before -- this module has no opinion on it at all.

Deliberately reuses ``vendor/wspy``'s own ``web/counter_text.py`` for the actual ``counters.txt``-block
parsing (imported directly from the pinned submodule, not reimplemented) -- confirmed with the user,
2026-08-20: that module is a pure, dependency-free text parser with no DB/subprocess/runtime dependency
of its own, already hand-debugged against several real edge cases (see its own module docstring and
this project's CLAUDE.md for the history). This is a deliberate, narrow exception to cfm's usual "only
integrate via stable wspy CLIs, never import wspy's internal Python" posture
(``cfm/instrumentation/wspy.py``'s docstring) -- that principle exists to avoid silently depending on
wspy's runtime/CLI *output shape* changing under us; a pinned, versioned, pure text-format parser
doesn't carry that same risk, and reimplementing ~370 lines of already-debugged parsing logic by hand
was judged the worse trade. ``wspy-archetype --run-guest`` (a real, stable, already-existing CLI) is
still the only place this module actually talks to wspy for scoring.

Everything here degrades to ``None``/``{}``/``[]`` on any failure -- no network, no matching page, a
parse that recovers nothing, ``wspy-archetype`` scoring failing -- never raises out to the caller. A
missing/failed reference-matrix lookup just means ``_characterize_baseline()`` falls through to its
existing local ``deep-cpu`` trial, exactly like "no entry exists yet" always has.

Known gap, not fixed here: ``vectorization_density``/``allocation_pressure`` currently come back
"unknown" more often than ``resource_dominance`` does, since ``float_pct``/``fault_rate`` aren't
reliably name-aligned in ``counter_text.py`` yet -- filed upstream as
https://github.com/mvermeulen/wspy/issues/278. Not a cfm-side bug; degrades gracefully (an unknown
axis is never treated as an exclusion signal by ``_filter_implausible_candidates()``).
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from .config import CfmConfig
from .util import parse_kv_lines

_REQUEST_TIMEOUT_S = 20
# Matches wspy's own MAX_WORDPRESS_RECOVERED_RUNS (wspy-testpoint) -- most-recent-first, capped so a
# machine with a long run history doesn't turn one characterization lookup into dozens of HTTP calls.
_MAX_RUN_PAGES = 20

_PREFORMATTED_RE = re.compile(
    r'<pre[^>]*class="[^"]*wp-block-preformatted[^"]*"[^>]*>(.*?)</pre>', re.DOTALL,
)

_counter_text_module = None  # lazily imported and cached -- see _counter_text()


def _counter_text(wspy_dir: Path):
    """Imports vendor/wspy's web/counter_text.py directly -- see this module's own docstring for why
    this one dependency is a deliberate exception to cfm's stable-CLI-only rule. Cached after first
    import so a repeated call in the same process doesn't keep re-inserting sys.path entries."""
    global _counter_text_module
    if _counter_text_module is not None:
        return _counter_text_module
    web_dir = str(wspy_dir / "web")
    if web_dir not in sys.path:
        sys.path.insert(0, web_dir)
    import counter_text  # the pinned vendor/wspy checkout's own web/ dir, not this package
    _counter_text_module = counter_text
    return counter_text


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "cfm-reference-matrix"})
    try:
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_S) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, OSError, ValueError):
        return None


def _find_page(site_url: str, slug: str, parent: int) -> Optional[dict]:
    """(slug, parent) lookup, anonymous -- mirrors wp_client.find_page()'s own uniqueness convention
    for WordPress Pages, minus the auth headers it always sends (confirmed live this WP install serves
    published pages to anonymous GETs regardless of whether a valid Authorization header is present).
    ``status=publish`` only (unlike wp_client's own ``status=any``) -- a mining host has no business
    surfacing a still-draft reference-matrix entry."""
    params = urllib.parse.urlencode({"slug": slug, "parent": parent, "status": "publish",
                                      "_fields": "id,slug"})
    results = _get_json(f"{site_url}/wp-json/wp/v2/pages?{params}")
    return results[0] if results else None


def _list_child_pages(site_url: str, parent: int) -> list[dict]:
    pages: list[dict] = []
    page_num = 1
    while True:
        params = urllib.parse.urlencode({
            "parent": parent, "status": "publish", "per_page": 100, "page": page_num,
            "_fields": "id,slug,date",
        })
        results = _get_json(f"{site_url}/wp-json/wp/v2/pages?{params}")
        if not results:
            break
        pages.extend(results)
        if len(results) < 100:
            break
        page_num += 1
    return pages


def _fetch_rendered_content(site_url: str, page_id: int) -> str:
    """``.rendered`` (the sanitized public HTML), not ``.raw`` -- ``.raw`` needs an explicit
    ``context=edit`` GET, which needs an authenticated ``edit_pages``-capable account. The
    ``<pre class="wp-block-preformatted">`` block text survives identically in ``.rendered`` since
    that's literally what's shown on the public page (confirmed live, 2026-08-20)."""
    params = urllib.parse.urlencode({"_fields": "content"})
    data = _get_json(f"{site_url}/wp-json/wp/v2/pages/{page_id}?{params}")
    if not data:
        return ""
    return (data.get("content") or {}).get("rendered", "")


def _extract_preformatted_blocks(raw_content: str) -> list[str]:
    return [html.unescape(m.group(1)) for m in _PREFORMATTED_RE.finditer(raw_content)]


def _slugify_test(benchmark: str) -> str:
    """706.stockfish_r -> 706-stockfish_r, matching WordPress's own sanitize_title() transform on
    however scripts/publish_cpu2026_benchmarks.py named the page (confirmed against real published
    slugs, 2026-08-20). A wrong guess here just means _find_page() returns None and the caller
    degrades to the local fallback trial -- same as "no entry exists yet"."""
    return benchmark.replace(".", "-")


def _slugify_test_point(spec_config: str) -> str:
    """cfg.spec_config (e.g. "gcc_O3.cfg") -> "gcc_o3-base". Deliberately always "-base", never
    cfm's own SPEC --tune (which is always "peak" for every cfm mining trial, doc/DESIGN.md sec. 15's
    peak-only decision) -- those are different, unrelated axes. _characterize_baseline() characterizes
    base_flags alone (typically just "-O3"), which is what the reference matrix's own "-base" test
    points represent; SPEC's peak/base *tune* is about which --config section gets a flag override,
    a mechanism cfm uses even for its "base_flags"-only baseline trial. Confirmed live, 2026-08-20:
    every cpu2026 entry published in this corpus so far is "-base" -- there is no "-peak" entry to
    match against yet regardless, so this is also just the only slug that could ever hit."""
    tag = spec_config[:-len(".cfg")] if spec_config.endswith(".cfg") else spec_config
    return f"{tag.lower()}-base"


def _recover_machine_metrics(site_url: str, wspy_dir: Path, machine_page_id: int) -> dict[str, float]:
    """{metric: mean value} across up to _MAX_RUN_PAGES most-recent runs on one already-resolved
    machine page, or {} if nothing recoverable. Mirrors wspy's own
    recover_machine_metrics_from_wordpress(), minus the per-metric n/min/max/stddev bookkeeping cfm
    doesn't need -- wspy-archetype --run-guest only ever reads a flat value per feature name."""
    run_pages = _list_child_pages(site_url, machine_page_id)
    if not run_pages:
        return {}
    run_pages = sorted(run_pages, key=lambda p: p.get("date") or "", reverse=True)[:_MAX_RUN_PAGES]

    counter_text = _counter_text(wspy_dir)
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for run_page in run_pages:
        content = _fetch_rendered_content(site_url, run_page["id"])
        if not content:
            continue
        for block_text in _extract_preformatted_blocks(content):
            # "counters" blocks only (not "ibs"/None) -- topdown/cache/fault data cfm's own signature
            # fields need, same scope collect_wordpress_archetype_scorecards() itself targets.
            if counter_text.classify_counter_text(block_text) != "counters":
                continue
            records = counter_text.parse_counter_text(block_text)
            per_run: dict[str, float] = {}
            for r in records:
                per_run.setdefault(r["metric"], r["value"])
            for r in counter_text.extract_derived_ratios(records):
                per_run[r["metric"]] = r["value"]  # derived ratios win over a line's own raw value
            for metric, value in per_run.items():
                sums[metric] = sums.get(metric, 0.0) + value
                counts[metric] = counts.get(metric, 0) + 1
    return {m: sums[m] / counts[m] for m in sums}


def _score_guest_vector(wspy_dir: Path, guest: dict[str, float]) -> Optional[dict]:
    """Shells out to `wspy-archetype --run-guest <tmpfile>` -- the one real, stable wspy CLI this
    module talks to for scoring (INVESTIGATION.md 4.3 item 23's own addition: scores a flat
    feature_name->value JSON object with no database/local run needed at all). Same key=value output
    shape cfm/instrumentation/wspy.py's own _archetype() already parses with parse_kv_lines()."""
    wspy_archetype_bin = wspy_dir / "wspy-archetype"
    fd, tmp_path_str = tempfile.mkstemp(suffix=".json", prefix="cfm-reference-matrix-guest-")
    tmp_path = Path(tmp_path_str)
    try:
        tmp_path.write_text(json.dumps(guest))
        try:
            proc = subprocess.run(
                [str(wspy_archetype_bin), "--run-guest", str(tmp_path)],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if proc.returncode != 0:
            return None
        return parse_kv_lines(proc.stdout)
    finally:
        tmp_path.unlink(missing_ok=True)


def fetch_shape(cfg: CfmConfig, benchmark: str) -> Optional[dict]:
    """Entry point: walks cpu2026 -> <benchmark> -> <compiler>-base -> (first machine, sorted) ->
    scores that machine's recovered metrics via `wspy-archetype --run-guest`. Returns a dict with
    resource_dominance/resource_dominance_pct/vectorization_density/allocation_pressure/confidence
    plus source_machine (for traceability), or None if no matching published entry exists or anything
    along the way failed -- never raises. "First machine, sorted" (not an aggregate/agreement check
    across every machine that published this benchmark) is a deliberate simplification matching
    _characterize_baseline()'s own existing "shape needs one measurement, not a 3-rep CI" philosophy
    for the local fallback; a future version could compare across machines the way
    render_archetype_section() does, but that's real added scope, not needed to start.
    """
    site_url = cfg.reference_matrix_url
    cpu2026 = _find_page(site_url, "cpu2026", 0)
    if cpu2026 is None:
        return None
    test = _find_page(site_url, _slugify_test(benchmark), cpu2026["id"])
    if test is None:
        return None
    test_point = _find_page(site_url, _slugify_test_point(cfg.spec_config), test["id"])
    if test_point is None:
        return None
    machines = _list_child_pages(site_url, test_point["id"])
    if not machines:
        return None
    machines = sorted(machines, key=lambda m: m.get("slug") or "")

    for machine in machines:
        guest = _recover_machine_metrics(site_url, cfg.wspy_dir, machine["id"])
        if not guest:
            continue
        scorecard = _score_guest_vector(cfg.wspy_dir, guest)
        if not scorecard:
            continue
        scorecard["source_machine"] = machine["slug"]
        return scorecard
    return None
