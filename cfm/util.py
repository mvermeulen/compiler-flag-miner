"""Small shared helpers with no home in a more specific module."""

from __future__ import annotations


def normalize_flag_base(token: str) -> str:
    """Collapse a compiler flag token to the base name a
    ``config/gcc_flag_catalog.seed.json`` entry would use, e.g. ``-mbranch-cost=4``
    and the catalog's ``-mbranch-cost=N`` both normalize to ``-mbranch-cost``;
    ``--param=prefetch-latency=200`` (already merged from the two argv tokens
    ``--param``/``prefetch-latency=200``) normalizes to ``--param:prefetch-latency``
    to match the catalog's ``--param prefetch-latency=N`` entry. Shared between
    ``scripts/audit_flags_from_spec_results.py`` (matching real-world flags against
    the catalog) and ``cfm/compilers/gcc.py`` (validating a proposed flagset against
    it) -- one normalization rule, not two copies drifting apart.
    """
    if token.startswith("--param="):
        sub = token.split("=", 2)[1]
        return f"--param:{sub.split('=')[0]}"
    if "=" in token:
        return token.split("=", 1)[0]
    return token


def catalog_flag_base(flag: str) -> str:
    """Same normalization as ``normalize_flag_base``, applied to a catalog entry's
    own ``flag`` field (e.g. ``--param prefetch-latency=N`` -- space-separated, the
    catalog's own convention for a ``--param`` entry, rather than the
    ``=``-joined form a real argv token would already be merged into).
    """
    if flag.startswith("--param"):
        sub = flag.split()[1]
        return f"--param:{sub.split('=')[0]}"
    return normalize_flag_base(flag)


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
