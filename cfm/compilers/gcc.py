"""GCC/GFortran Compiler Knowledge agent -- doc/DESIGN.md sec. 4.3.

Loads config/gcc_flag_catalog.seed.json as its flag catalog: every applicable-
language entry, minus any whose flag is still an unresolved template placeholder
rather than a concrete flag (see ``_resolve_flag_or_none()``), ranked
highest-priority-first against the caller's baseline shape (M2, see
``_candidate_rank()`` and ``candidate_flags_for_signature()`` below;
``compilers/base.py``'s module docstring has the M1-vs-M2 history).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from ..util import catalog_flag_base, normalize_flag_base
from .base import CompilerBackend, FlagCandidate, RESOURCE_DOMINANCE_SIGNALS, ValidationResult

# config/gcc_flag_catalog.seed.json's default location, resolved relative to this
# package's own location (matching db.py's schema/cfm_schema.sql trick and
# config.py's vendor/wspy trick) -- not the caller's cwd.
_DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "gcc_flag_catalog.seed.json"

# SPEC's Spec/object.pm $benchlang values, confirmed against every benchmark in a
# real CPU2026 install this session (doc/DESIGN.md's M1 plan -- the whole suite only
# ever uses these 4 values): '"C"'->c, 'CXX'->cxx, 'CXX,C'->[cxx,c], 'F'->fortran.
_BENCHLANG_RE = re.compile(r"\$benchlang\s*=\s*'([^']+)'")
_BENCHLANG_TO_CATALOG = {"C": "c", "CXX": "cxx", "F": "fortran"}

# A handful of config/gcc_flag_catalog.seed.json entries carry an unresolved
# template rather than a concrete, directly-buildable flag (e.g. `-march=
# <detected-uarch>`, `-mbranch-cost=N`) -- confirmed live: tried as literal text,
# GCC just rejects them outright (a wasted, uninformative build failure for every
# such candidate, not a real test of the flag). `-march=<detected-uarch>` has one
# safe, well-grounded resolution (GCC's own `-march=native` -- the exact flag M0's
# real verified run already used, CLAUDE.md's Status section) so it's substituted
# here rather than shelled out to wspy's cpu_info for the same answer. The
# remaining `=N`-style numeric-parameter placeholders (`-mbranch-cost=N`,
# `--param prefetch-latency=N`) have no single principled default value the
# catalog specifies, so those candidates are skipped entirely rather than
# fabricating one -- a real, tracked M1 gap (real parameter-sweep resolution is
# future work), not silently guessed at here.
_PLACEHOLDER_SUBSTITUTIONS = {"-march=<detected-uarch>": "-march=native"}
_UNRESOLVED_PLACEHOLDER_RE = re.compile(r"<[^>]+>|=N$")


def _resolve_flag_or_none(raw_flag: str) -> Optional[str]:
    flag = _PLACEHOLDER_SUBSTITUTIONS.get(raw_flag, raw_flag)
    if _UNRESOLVED_PLACEHOLDER_RE.search(flag):
        print(
            f"info: skipping catalog entry {raw_flag!r} -- unresolved template placeholder, "
            "not a concrete flag (see cfm/compilers/gcc.py's _PLACEHOLDER_SUBSTITUTIONS)"
        )
        return None
    return flag


# -- M2: signature-aware ranking (doc/DESIGN.md sec. 4.3/14) -------------------
#
# doc/DESIGN.md sec. 4.3's signature-to-candidate table is the spec: a candidate
# whose topdown_signals genuinely match the baseline's characterized shape should
# be tried before one that merely wasn't excluded (orchestrator.py's own
# _filter_implausible_candidates() already handles "exclude the confidently
# implausible" -- this is the separate, still-real "of what's left, try the most
# relevant first" half M1/M2.5 explicitly deferred).
#
# resource_dominance_pct (0-100, wspy-archetype's own scorecard field, threaded
# through BaselineResult since this same change) is the "margin" signal
# doc/DESIGN.md sec. 4.3's "retiring-high-narrow-margin" row needs and
# orchestrator.py's own _signal_is_implausible() explicitly said it didn't have.
# A first-cut, undocumented-elsewhere threshold, same posture as
# orchestrator.py's MIN_PRACTICAL_SIGNIFICANCE_PCT: not yet calibrated against
# real reference-matrix spread data, open to revision once that's available.
# Below this, no single topdown category dominates overwhelmingly -- "narrow
# margin," per the catalog table's own wording -- above it, the shape is
# confidently, dominantly one thing, and the "diminishing returns for aggressive
# flags, -march for the last few percent" guidance doesn't apply the same way.
_NARROW_MARGIN_MAX_PCT = 60.0


def _signal_matches(signal: str, signature) -> bool:
    """Does ``signal`` (one ``FlagCandidate.topdown_signals`` entry) genuinely,
    confidently match ``signature``'s characterized shape? Duck-typed --
    ``signature`` need only expose ``.resource_dominance``/
    ``.resource_dominance_pct``/``.vectorization_density`` (``None`` for an
    unknown/absent baseline is handled the same as everywhere else in this
    project: it never counts as a match, but it's not a penalty either --
    ``_candidate_rank()`` below just treats a non-match as neutral, same as no
    signal at all).
    """
    resource_dominance = getattr(signature, "resource_dominance", None)
    if signal == "vectorization-density-high":
        return getattr(signature, "vectorization_density", None) == "high"
    if signal == "memory-bound-corroborated":
        return resource_dominance == "memory-bound"
    if signal == "retiring-high-narrow-margin":
        # A genuine match needs a *known* pct, not just a compute-bound read --
        # unlike every other signal here, "narrow margin" is a specific extra
        # claim on top of "compute-bound," not a fallback for missing data (an
        # unknown pct means this signal simply adds nothing, it doesn't count
        # against the candidate either -- the plain "compute-bound" signal most
        # of these candidates also carry still applies on its own).
        pct = getattr(signature, "resource_dominance_pct", None)
        return resource_dominance == "compute-bound" and pct is not None and pct <= _NARROW_MARGIN_MAX_PCT
    if signal in RESOURCE_DOMINANCE_SIGNALS:
        return resource_dominance == signal
    return False


def _candidate_rank(candidate: FlagCandidate, signature) -> int:
    """Higher ranks first. The count (not just presence) of a candidate's
    ``topdown_signals`` that genuinely match ``signature`` -- not just whether
    *any* do -- specifically so ``-march=<uarch>`` (tagged both `compute-bound`
    and `retiring-high-narrow-margin`) outranks the other compute-bound-tagged-
    only flags (`-Ofast`/`-ffast-math`/`-funroll-loops`) exactly when the margin
    really is narrow -- matching doc/DESIGN.md sec. 4.3's own "low priority for
    aggressive flags; -march ... for the last few percent" guidance concretely,
    not just as prose. A candidate with no ``topdown_signals`` at all (e.g.
    gfortran-specific flags with no topdown story) ranks neutrally, same as one
    whose signals don't match anything -- absence of matching evidence is never a
    penalty, only ever the absence of a boost, matching this project's
    established "unknown/absent never counts against" posture throughout.
    """
    if not candidate.topdown_signals:
        return 0
    return sum(1 for signal in candidate.topdown_signals if _signal_matches(signal, signature))


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
        wanted = set(languages)
        candidates = []
        for entry in self._flags():
            if not (wanted & set(entry["languages"])):
                continue
            if entry["category"] == "pgo":
                # -fprofile-generate/-fprofile-use never belong in this ordinary
                # one-flag-at-a-time candidate list: each is meaningless tested
                # alone against a single OPTIMIZE line (see doc/mining_results.
                # 714.cpython_r.2026-08-21.md's live illustration of exactly
                # this -- "-fprofile-generate alone" just measures instrumentation
                # overhead, "-fprofile-use alone" has no profile to apply). PGO is
                # its own real two-pass Phase 6 multiplier (doc/DESIGN.md sec. 6),
                # driven directly by cfm/orchestrator.py's PGO-specific code path,
                # never sourced from this per-flag loop.
                continue
            flag = _resolve_flag_or_none(entry["flag"])
            if flag is None:
                continue
            candidates.append(FlagCandidate(
                flag=flag,
                category=entry["category"],
                risk=entry["risk"],
                languages=entry["languages"],
                requires=entry.get("requires", []),
                conflicts=entry.get("conflicts", []),
                notes=entry.get("notes", ""),
                topdown_signals=entry.get("topdown_signals", []),
            ))
        # M2: highest-priority-first, not raw catalog order -- stable sort, so
        # candidates that tie (including every candidate when signature is None,
        # or when nothing about it matches anything) keep the catalog's own
        # relative order rather than being shuffled for no reason.
        candidates.sort(key=lambda c: _candidate_rank(c, signature), reverse=True)
        return candidates

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

    def pgo_topdown_signals(self) -> list[str]:
        """The `-fprofile-use` catalog entry's own ``topdown_signals`` -- used by
        cfm/orchestrator.py's Phase 6 PGO multiplier to decide whether a real
        two-pass PGO trial is even worth attempting against a given baseline
        shape, reusing the exact same plausibility check Phase 2's
        `_filter_implausible_candidates()` applies to every other catalog entry.
        Phase 6 needs its own copy of this check because PGO bypasses Phase 2's
        candidate list entirely (`category == "pgo"` entries are excluded from
        `candidate_flags_for_signature()` above -- see that method's own
        comment). Returns `[]` if the catalog has no `-fprofile-use` entry at
        all (a caller should then always attempt PGO -- no signal to judge
        implausibility against, not a catalog config error worth raising on).
        """
        for entry in self._flags():
            if entry["flag"] == "-fprofile-use":
                return entry.get("topdown_signals", [])
        return []
