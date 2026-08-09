#!/usr/bin/env python3
"""Audit config/gcc_flag_catalog.seed.json against real published SPEC CPU2017 configs.

Idea: SPEC's disclosure policy requires every published result to ship a full config file
(the exact compiler command lines used), specifically so results can be independently
reviewed/reproduced. That's a real-world corpus of "flags people actually used to win" we
can mine to find gaps in our catalog -- things the catalog doesn't know about yet.

IMPORTANT -- why this script never talks to spec.org's search tool (osgresults):
spec.org's robots.txt disallows /cgi-bin/ wholesale, annotated "Not intended for
non-interactive use". osgresults (the results-search CGI, including its CSV-dump mode)
lives entirely under that path. This script honors that by design: it never constructs
or fetches an osgresults URL itself, and it hard-refuses (see _looks_like_cgi_bin) any
URL that happens to point under /cgi-bin/ even if one slipped into a seed file by
accident. It only ever fetches static files under /cpu2017/results/ -- config files
sit there as of-right published artifacts, not behind the disallowed query interface.

Workflow (the manual first step is deliberate -- see above):
  1. In your own browser, run the filtered search yourself, e.g. Compiler matches "gcc"
     at https://www.spec.org/cgi-bin/osgresults?conf=cpu2017 -- exactly the site's
     intended *interactive* use of that tool.
  2. Save the resulting results page(s) to disk (Ctrl+S / "Save Page As", HTML only is
     fine). Quarterly results index pages under https://www.spec.org/cpu2017/results/
     work as seeds too, if you'd rather sweep a range of quarters wholesale instead of
     using the search filter.
  3. Run this script with --seed pointing at the saved file(s). It extracts every
     ``*.cfg`` link, fetches each one exactly once (cached locally -- re-runs never
     re-fetch), honors spec.org's own declared Crawl-delay (10s, see robots.txt) between
     real network requests, double-checks each fetched config actually names a GNU
     compiler (CC/CXX/FC) before using it, extracts the optimization-flag tokens, and
     diffs the result against config/gcc_flag_catalog.seed.json.

Fetched files are cached under --cache-dir, which is intentionally outside git (see
.gitignore) -- CLAUDE.md's "never commit SPEC-licensed content" rule covers other
parties' published result/config files same as it covers benchmark source; only the
*derived* report (the flag list, the diff against our own catalog) is a generated
artifact this project owns and can commit.

This is a best-effort line-oriented scanner for SPEC's cfg format (see
cpu2017/Docs/config.html for the real grammar), not a full implementation of its
%if/%define preprocessor -- it resolves simple $(VAR) substitutions but does not
evaluate conditional blocks. Good enough to surface catalog-gap candidates for human
(or the Compiler Knowledge agent's own validate_flagset, cfm/compilers/gcc.py) review;
not a guarantee that every resolved flag is exactly what a given trial's peak build
used. Flag-name normalization (normalize_flag_base/catalog_flag_base) lives in
cfm/util.py, shared with cfm/compilers/gcc.py rather than duplicated here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
# Runnable standalone (`python3 scripts/audit_flags_from_spec_results.py`, no `pip
# install -e .` needed first) by making sure the local `cfm` package resolves even
# when this script's own directory -- not the repo root -- is what Python put on
# sys.path. A no-op when cfm is already importable (e.g. the dev venv).
sys.path.insert(0, str(REPO_ROOT))
from cfm.util import normalize_flag_base as normalize_base  # noqa: E402
from cfm.util import catalog_flag_base as _catalog_base  # noqa: E402

DEFAULT_CATALOG = REPO_ROOT / "config" / "gcc_flag_catalog.seed.json"
DEFAULT_CACHE_DIR = REPO_ROOT / ".cache" / "spec_flag_audit"

# Matches spec.org/robots.txt's own declared "Crawl-delay: 10" -- this script only ever
# fetches from the static (crawlable) part of the site, but there's no reason to be
# faster than the site itself asks bots to be.
DEFAULT_DELAY_SECONDS = 10.0
DEFAULT_USER_AGENT = (
    "cfm-flag-audit/0.1 "
    "(+https://github.com/mvermeulen/compiler-flag-miner; contact: mevermeulen@gmail.com)"
)

# SPEC cfg variable names that carry compiler flags. Deliberately broad (anything ending
# in OPTIMIZE/PORTABILITY/FLAGS, plus the three compiler-invocation vars) so it survives
# suite-specific variants like EXTRA_COPTIMIZE or FPPFLAGS without a name-by-name allowlist.
_FLAG_VAR_RE = re.compile(r"^(CC|CXX|FC|[A-Z0-9_]*(?:OPTIMIZE|PORTABILITY|FLAGS))$")

# Any NAME = VALUE line, used to build the substitution table for $(NAME) refs elsewhere
# in the same file (SPEC configs commonly factor shared flags into a helper var like
# FAST_NO_STATIC and reference it from COPTIMIZE/FOPTIMIZE).
_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
_DEFINE_RE = re.compile(r"^\s*%define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.*?)\s*$")
_VARREF_RE = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)")

# Flags that are real argv tokens but not the kind of tuning knob this audit cares about:
# language-standard/ABI selection, preprocessor defines, linker/include/lib plumbing, and
# the baseline optimization level (every result sets one; not itself a candidate to mine).
_IGNORE_EXACT = {
    "-m64", "-m32", "-pthread", "-static", "-no-pie", "-fPIC", "-fPIE", "-shared",
    "-O0", "-O1", "-O2", "-O3", "-Os", "-Og", "-g",
}
_IGNORE_PREFIXES = ("-D", "-I", "-L", "-l", "-o", "-std=", "-V", "--version")


def _looks_like_cgi_bin(url: str) -> bool:
    """Guard rail: this script must never fetch anything under /cgi-bin/ (see module
    docstring) -- checked at fetch time regardless of where a URL came from."""
    return urlparse(url).path.startswith("/cgi-bin/")


def extract_cfg_links(html: str, base_url: str) -> list[str]:
    """Pull every ``*.cfg`` href out of a saved SPEC results page and resolve it against
    base_url. Works for both a saved osgresults results page (which emits absolute hrefs)
    and a saved quarterly results-index page (which emits hrefs relative to that quarter's
    own directory) -- pass that page's own URL as base_url in the latter case."""
    links = []
    seen = set()
    for href in re.findall(r'href="([^"]+\.cfg)"', html):
        url = urljoin(base_url, href)
        if url not in seen:
            seen.add(url)
            links.append(url)
    return links


def looks_like_gnu_compiler(cfg_text: str) -> tuple[bool, str]:
    """Cross-check that a fetched config actually used gcc/g++/gfortran, rather than
    trusting the search filter (or a hand-curated seed page) blindly -- catches things
    like a GCC-compatible-frontend compiler whose --version banner mentions gcc but whose
    CC/CXX/FC lines invoke something else entirely."""
    idents = []
    for var in ("CC", "CXX", "FC"):
        m = re.search(rf"^\s*{var}\s*=\s*(.+)$", cfg_text, re.MULTILINE)
        if m:
            idents.append(m.group(1).strip())
    joined = " | ".join(idents) if idents else "(no CC/CXX/FC found)"
    gnu_names = ("gcc", "g++", "gfortran")
    is_gnu = any(
        ident.split()[0].rsplit("/", 1)[-1] in gnu_names for ident in idents if ident.split()
    )
    return is_gnu, joined


def _join_continuations(text: str) -> str:
    """SPEC cfg lines can continue with a trailing backslash; join them before scanning."""
    return re.sub(r"\\\s*\n", " ", text)


def _strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.split("\n"))


def parse_all_vars(cfg_text: str) -> dict[str, str]:
    """Collect every NAME = VALUE / %define NAME VALUE assignment in the file, last
    definition wins. Used only to resolve $(NAME) references inside flag-bearing
    variables -- not an attempt to evaluate %if/%ifdef branches correctly."""
    text = _strip_comments(_join_continuations(cfg_text))
    all_vars: dict[str, str] = {}
    for line in text.split("\n"):
        m = _DEFINE_RE.match(line) or _ASSIGN_RE.match(line)
        if m:
            all_vars[m.group(1)] = m.group(2)
    return all_vars


def resolve_refs(value: str, all_vars: dict[str, str], max_passes: int = 8) -> tuple[str, bool]:
    """Best-effort $(NAME) substitution. Returns (resolved_value, had_unresolved_ref)."""
    for _ in range(max_passes):
        new_value, count = _VARREF_RE.subn(lambda m: all_vars.get(m.group(1), m.group(0)), value)
        if new_value == value:
            break
        value = new_value
    had_unresolved = bool(_VARREF_RE.search(value))
    return value, had_unresolved


def _tokenize(value: str) -> list[str]:
    tokens = re.findall(r'"[^"]*"|\'[^\']*\'|\S+', value)
    tokens = [t.strip("\"'") for t in tokens]
    # Merge "--param NAME=VALUE" (two argv tokens) into one comparable unit.
    merged = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--param" and i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
            merged.append(f"--param={tokens[i + 1]}")
            i += 2
        else:
            merged.append(tok)
            i += 1
    return [t for t in merged if t.startswith("-") and "$(" not in t]


def extract_flag_tokens(cfg_text: str) -> tuple[list[str], bool]:
    """Return (flag_tokens, had_any_unresolved_ref) for every flag-bearing variable in
    the file."""
    text = _strip_comments(_join_continuations(cfg_text))
    all_vars = parse_all_vars(cfg_text)
    tokens: list[str] = []
    had_unresolved = False
    for line in text.split("\n"):
        m = _ASSIGN_RE.match(line)
        if not m or not _FLAG_VAR_RE.match(m.group(1)):
            continue
        resolved, unresolved = resolve_refs(m.group(2), all_vars)
        had_unresolved = had_unresolved or unresolved
        tokens.extend(_tokenize(resolved))
    return tokens, had_unresolved


def is_ignored(base: str, token: str) -> bool:
    if token in _IGNORE_EXACT:
        return True
    return any(token.startswith(p) for p in _IGNORE_PREFIXES)


def load_catalog_bases(catalog_path: Path) -> set[str]:
    data = json.loads(catalog_path.read_text())
    return {_catalog_base(entry["flag"]) for entry in data["flags"]}


class RateLimiter:
    """Enforces a minimum gap between real network requests -- never applies to cache hits."""

    def __init__(self, delay_seconds: float):
        self.delay_seconds = delay_seconds
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        remaining = self.delay_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last = time.monotonic()


def cache_path_for_url(cache_dir: Path, url: str) -> Path:
    parsed = urlparse(url)
    # e.g. cpu2017/results/res2019q3/cpu2017-20190625-15870.cfg -- mirror the site's own
    # path layout under the cache dir so files are easy to inspect/dedupe by hand too.
    return cache_dir / parsed.path.lstrip("/")


def fetch_static(url: str, cache_dir: Path, user_agent: str, limiter: RateLimiter,
                  force_refetch: bool = False) -> str:
    if _looks_like_cgi_bin(url):
        raise ValueError(f"refusing to fetch a /cgi-bin/ URL (see module docstring): {url}")
    cache_path = cache_path_for_url(cache_dir, url)
    if cache_path.exists() and not force_refetch:
        return cache_path.read_text(errors="replace")
    limiter.wait()
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text)
    return text


@dataclass
class AuditResult:
    known: Counter = field(default_factory=Counter)
    ignored: Counter = field(default_factory=Counter)
    new_candidates: Counter = field(default_factory=Counter)
    examples: dict = field(default_factory=dict)  # base -> [source_url, ...] (first few)
    configs_used: int = 0
    configs_skipped_non_gnu: int = 0
    configs_with_unresolved_refs: int = 0
    fetch_failures: list = field(default_factory=list)  # [(url, error_str)]


def run_audit(cfg_urls: list[str], catalog_path: Path, cache_dir: Path, user_agent: str,
              delay_seconds: float, force_refetch: bool, skip_compiler_check: bool) -> AuditResult:
    catalog_bases = load_catalog_bases(catalog_path)
    limiter = RateLimiter(delay_seconds)
    result = AuditResult()

    for url in cfg_urls:
        try:
            text = fetch_static(url, cache_dir, user_agent, limiter, force_refetch)
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            result.fetch_failures.append((url, str(exc)))
            continue

        if not skip_compiler_check:
            is_gnu, _ident = looks_like_gnu_compiler(text)
            if not is_gnu:
                result.configs_skipped_non_gnu += 1
                continue

        tokens, had_unresolved = extract_flag_tokens(text)
        if had_unresolved:
            result.configs_with_unresolved_refs += 1
        result.configs_used += 1

        for tok in set(tokens):  # count each distinct flag once per config, not per line
            base = normalize_base(tok)
            if is_ignored(base, tok):
                result.ignored[base] += 1
            elif base in catalog_bases:
                result.known[base] += 1
            else:
                result.new_candidates[base] += 1
                result.examples.setdefault(base, []).append(url)

    return result


def render_report(result: AuditResult, catalog_path: Path) -> str:
    lines = [
        "# SPEC CPU2017 GCC flag audit",
        "",
        f"Catalog checked: `{catalog_path}`",
        "",
        f"- Configs used (GNU-compiler, successfully parsed): {result.configs_used}",
        f"- Configs skipped (compiler wasn't gcc/g++/gfortran): {result.configs_skipped_non_gnu}",
        f"- Configs with at least one unresolved `$(VAR)` reference: "
        f"{result.configs_with_unresolved_refs} (best-effort scanner -- see script docstring)",
        f"- Fetch failures: {len(result.fetch_failures)}",
        "",
        "## New candidates (flags seen in the wild, not in the catalog)",
        "",
        "| Flag | Seen in N configs | Example source |",
        "|---|---|---|",
    ]
    for base, count in result.new_candidates.most_common():
        example = result.examples[base][0]
        lines.append(f"| `{base}` | {count} | {example} |")
    if not result.new_candidates:
        lines.append("| _(none -- catalog covers everything seen)_ | | |")

    lines += [
        "",
        "## Already known (catalog coverage confirmed against real usage)",
        "",
        ", ".join(f"`{b}` ({c})" for b, c in result.known.most_common()) or "_(none)_",
        "",
        "## Ignored (language/ABI/linker plumbing, not tuning knobs)",
        "",
        ", ".join(f"`{b}` ({c})" for b, c in result.ignored.most_common()) or "_(none)_",
    ]
    if result.fetch_failures:
        lines += ["", "## Fetch failures", ""]
        lines += [f"- {url}: {err}" for url, err in result.fetch_failures]
    return "\n".join(lines) + "\n"


def parse_seed_arg(raw: str) -> tuple[Path, str]:
    if "::" in raw:
        path_str, base_url = raw.split("::", 1)
    else:
        path_str, base_url = raw, "https://www.spec.org/"
    return Path(path_str), base_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--seed", action="append", required=True, metavar="PATH[::BASE_URL]",
        help="Locally saved SPEC results HTML page (osgresults search results, or a "
             "quarterly results-index page). Repeatable. BASE_URL defaults to "
             "https://www.spec.org/ (correct for osgresults pages' absolute hrefs); "
             "pass the page's own URL explicitly for a quarterly index page, whose .cfg "
             "hrefs are relative to that quarter's own directory.",
    )
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS,
                         help="Minimum seconds between real network requests (default: "
                              "matches spec.org/robots.txt's own Crawl-delay).")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--limit", type=int, default=None,
                         help="Fetch at most N configs (for a quick trial run).")
    parser.add_argument("--force-refetch", action="store_true")
    parser.add_argument("--skip-compiler-check", action="store_true",
                         help="Skip the CC/CXX/FC gcc/g++/gfortran cross-check.")
    parser.add_argument("--dry-run", action="store_true",
                         help="Only extract and count .cfg links, fetch nothing.")
    parser.add_argument("--report", type=Path, default=None,
                         help="Write the Markdown report here (and a sibling .json with "
                              "the same stem). Default: print Markdown to stdout.")
    args = parser.parse_args(argv)

    all_urls: list[str] = []
    seen = set()
    for raw in args.seed:
        path, base_url = parse_seed_arg(raw)
        html = path.read_text(errors="replace")
        for url in extract_cfg_links(html, base_url):
            if _looks_like_cgi_bin(url):
                print(f"warning: skipping /cgi-bin/ URL found in {path}: {url}", file=sys.stderr)
                continue
            if url not in seen:
                seen.add(url)
                all_urls.append(url)

    print(f"Found {len(all_urls)} unique config URL(s) across {len(args.seed)} seed file(s).",
          file=sys.stderr)
    if args.limit is not None:
        all_urls = all_urls[: args.limit]

    if args.dry_run:
        for url in all_urls:
            print(url)
        return 0

    result = run_audit(
        all_urls, args.catalog, args.cache_dir, args.user_agent, args.delay,
        args.force_refetch, args.skip_compiler_check,
    )
    report = render_report(result, args.catalog)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report)
        json_path = args.report.with_suffix(".json")
        json_path.write_text(json.dumps({
            "known": dict(result.known),
            "ignored": dict(result.ignored),
            "new_candidates": dict(result.new_candidates),
            "examples": result.examples,
            "configs_used": result.configs_used,
            "configs_skipped_non_gnu": result.configs_skipped_non_gnu,
            "configs_with_unresolved_refs": result.configs_with_unresolved_refs,
            "fetch_failures": result.fetch_failures,
        }, indent=2))
        print(f"Wrote {args.report} and {json_path}", file=sys.stderr)
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
