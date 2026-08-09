"""Small shared helpers with no home in a more specific module."""

from __future__ import annotations


def parse_kv_lines(text: str, sep: str = "=") -> dict[str, str]:
    """Generic ``key<sep>value``-per-line parser.

    Shared by anything reading wspy's line-oriented trace-style output
    (``wspy-archetype --run``, ``wspy-summary --trace`` -- see the real captured
    example in doc/DESIGN.md sec. 4.2/§8) and SPEC's ``.rsf`` raw-result format
    (``cfm/workloads/spec_cpu2026.py``, whose keys look like
    ``spec.cpu2026.results.706_stockfish_r.peak.ratio = 12.34``). Blank lines and
    ``#``-prefixed comments are skipped; a line with no ``sep`` is skipped rather
    than raising, since both source formats interleave the odd banner/comment line
    with real key/value data.
    """
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or sep not in line:
            continue
        key, _, value = line.partition(sep)
        result[key.strip()] = value.strip()
    return result
