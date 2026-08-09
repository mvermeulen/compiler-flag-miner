"""GCC/GFortran Compiler Knowledge agent -- doc/DESIGN.md sec. 4.3.

Loads config/gcc_flag_catalog.seed.json as its flag catalog. M1 scope: candidates
are the whole applicable-language catalog, uniformly (no resource_dominance-based
filtering yet -- that's M2, see compilers/base.py's module docstring).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from ..util import catalog_flag_base, normalize_flag_base
from .base import CompilerBackend, FlagCandidate, ValidationResult

# config/gcc_flag_catalog.seed.json's default location, resolved relative to this
# package's own location (matching db.py's schema/cfm_schema.sql trick and
# config.py's vendor/wspy trick) -- not the caller's cwd.
_DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "gcc_flag_catalog.seed.json"

# SPEC's Spec/object.pm $benchlang values, confirmed against every benchmark in a
# real CPU2026 install this session (doc/DESIGN.md's M1 plan -- the whole suite only
# ever uses these 4 values): '"C"'->c, 'CXX'->cxx, 'CXX,C'->[cxx,c], 'F'->fortran.
_BENCHLANG_RE = re.compile(r"\$benchlang\s*=\s*'([^']+)'")
_BENCHLANG_TO_CATALOG = {"C": "c", "CXX": "cxx", "F": "fortran"}


def benchmark_languages(spec_dir, bench: str) -> list[str]:
    """Reads a benchmark's applicable languages straight from SPEC's own metadata
    (``benchspec/CPU/<bench>/Spec/object.pm``'s ``$benchlang`` line) rather than
    guessing from source-file extensions -- confirmed live this session that the
    illustrative language notes in config/gcc_flag_catalog.seed.json's own entries
    (e.g. "-fstack-arrays ... cactus_r" as a Fortran example) can be wrong for a
    *specific* SPEC suite: this fictional CPU2026 install's own 709.cactus_r is
    'CXX,C', not Fortran, unlike real-world CPU2017's Fortran 508.cactuBSSN_r the
    catalog note was actually referring to. Fails loudly (not a silent guess) if
    object.pm is missing, has no $benchlang line, or uses a language token this
    suite hasn't been seen to use.
    """
    object_pm = Path(spec_dir) / "benchspec" / "CPU" / bench / "Spec" / "object.pm"
    if not object_pm.exists():
        raise RuntimeError(f"no Spec/object.pm for benchmark {bench!r} at {object_pm}")
    match = _BENCHLANG_RE.search(object_pm.read_text())
    if not match:
        raise RuntimeError(f"no $benchlang line found in {object_pm}")
    tokens = match.group(1).split(",")
    try:
        return [_BENCHLANG_TO_CATALOG[t] for t in tokens]
    except KeyError as exc:
        raise RuntimeError(
            f"{object_pm}: unrecognized $benchlang token {exc.args[0]!r} in {tokens!r} -- "
            f"known tokens are {sorted(_BENCHLANG_TO_CATALOG)}"
        ) from exc


class GccCompiler(CompilerBackend):
    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = Path(catalog_path) if catalog_path else _DEFAULT_CATALOG_PATH
        self._catalog: Optional[list[dict]] = None  # loaded lazily, cached

    def _flags(self) -> list[dict]:
        if self._catalog is None:
            data = json.loads(self.catalog_path.read_text())
            self._catalog = data["flags"]
        return self._catalog

    def candidate_flags_for_signature(
        self, signature: Optional[object], languages: list[str],
    ) -> list[FlagCandidate]:
        # M1 ignores `signature` entirely -- see this module's docstring and
        # compilers/base.py's interface docstring for why that's a deliberate
        # M1-scope choice, not an oversight.
        del signature
        wanted = set(languages)
        return [
            FlagCandidate(
                flag=entry["flag"],
                category=entry["category"],
                risk=entry["risk"],
                languages=entry["languages"],
                requires=entry.get("requires", []),
                conflicts=entry.get("conflicts", []),
                notes=entry.get("notes", ""),
                topdown_signals=entry.get("topdown_signals", []),
            )
            for entry in self._flags()
            if wanted & set(entry["languages"])
        ]

    def validate_flagset(
        self, flags: list[str], gcc_version: Optional[str] = None, target: Optional[str] = None,
    ) -> ValidationResult:
        # gcc_version/target aren't used yet -- see compilers/base.py's interface
        # docstring; accepted now so a future per-version/per-target check doesn't
        # need to change every caller's call site.
        del gcc_version, target
        by_base = {catalog_flag_base(entry["flag"]): entry for entry in self._flags()}
        present_bases = {normalize_flag_base(f) for f in flags}

        problems: list[str] = []
        notes: list[str] = []
        reported_conflict_pairs: set[frozenset] = set()

        for f in flags:
            base = normalize_flag_base(f)
            entry = by_base.get(base)
            if entry is None:
                problems.append(f"{f!r} is not in the catalog (normalized base {base!r})")
                continue

            for conflict in entry.get("conflicts", []):
                conflict_base = normalize_flag_base(conflict.split()[0])
                if conflict_base in present_bases:
                    pair = frozenset({base, conflict_base})
                    if pair not in reported_conflict_pairs:
                        reported_conflict_pairs.add(pair)
                        problems.append(f"{f!r} conflicts with a flag also in this set ({conflict!r})")

            # "requires" entries are deliberately never auto-checked as "must also
            # be present in this flagset" -- doing so would be actively *wrong* for
            # an entry like -fprofile-use's "requires: -fprofile-generate (prior
            # training run)": the two are each other's *conflicts* too (a two-step
            # build/run/rebuild sub-flow, doc/DESIGN.md sec. 6 Phase 6 -- never
            # simultaneous). Surfaced as a note for a human/future agent to read,
            # not silently dropped.
            for requirement in entry.get("requires", []):
                notes.append(f"{f!r} requires: {requirement}")

        return ValidationResult(ok=not problems, problems=problems, notes=notes)

    def render_optimize_string(self, flags: list[str]) -> str:
        return " ".join(flags)
