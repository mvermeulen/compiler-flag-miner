"""Compiler Knowledge agent interface -- doc/DESIGN.md sec. 4.3 / sec. 12.

``gcc.py`` is the only implementation today; ``llvm.py``/``aocc.py`` are the future
modularity seam this interface defines, not yet implemented.

M1 scope note (doc/DESIGN.md sec. 14, superseded by M2, 2026-08-26):
``candidate_flags_for_signature`` was given its full signature (``signature``
included) from the start so M2 could later wire in real resource_dominance-based
ranking without changing this interface -- M1's own implementation ignored
``signature`` entirely and returned the whole applicable-language catalog
uniformly ("static catalog priors only"). M2 fills that in: ``gcc.py`` now scores
and reorders the catalog by how well each candidate's ``topdown_signals`` match
``signature``'s characterized shape, highest-priority first -- still every
applicable-language entry (M2 ranks, it doesn't drop anything; that's still
``cfm/orchestrator.py``'s separate ``_filter_implausible_candidates()`` job).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# resource_dominance-named topdown_signals -- config/gcc_flag_catalog.seed.json's
# real vocabulary (see its own top-level "note" field), checked directly against a
# baseline's characterized resource_dominance. Shared between orchestrator.py's
# Phase 2 filtering (_signal_is_implausible()) and gcc.py's M2 ranking
# (_signal_matches()) -- one source of truth for the vocabulary rather than two
# modules each keeping their own copy in sync by hand. "memory-bound-corroborated"
# and "vectorization-density-high" are handled as their own special cases in both
# (they key off memory_attribution/vectorization_density, not resource_dominance
# alone); "retiring-high-narrow-margin" is also its own special case (keys off
# resource_dominance_pct too, not just resource_dominance).
RESOURCE_DOMINANCE_SIGNALS = frozenset({
    "frontend-bound", "speculation-bound", "compute-bound", "backend-bound",
})


@dataclass
class FlagCandidate:
    """One flag catalog entry, filtered to a specific benchmark's applicable
    languages -- doc/DESIGN.md sec. 4.3's "flag catalog" fields, one dataclass per
    entry rather than the raw JSON dict everywhere downstream.
    """

    flag: str
    category: str
    risk: str  # 'safe' | 'needs_validation' | 'changes_fp_semantics'
    languages: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    notes: str = ""
    topdown_signals: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """``ok`` is False iff at least one *checkable* problem was found (an unknown
    flag, or two flags in the same set that conflict). ``notes`` carries anything
    this method chose not to check rather than silently ignore -- e.g. a
    catalog ``requires`` entry that's a free-text note ("-fprofile-generate (prior
    training run)") rather than a bare flag name it can look up -- so a caller can
    tell "verified fine" apart from "not checked" if it matters.
    """

    ok: bool
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class CompilerBackend:
    def candidate_flags_for_signature(
        self, signature: Optional[object], languages: list[str],
    ) -> list[FlagCandidate]:
        """Candidate flags for a benchmark whose applicable languages are
        ``languages`` (e.g. ``["cxx"]``), ranked highest-priority-first against
        ``signature``'s characterized shape (doc/DESIGN.md sec. 4.3's signature-to-
        candidate table) -- ``None`` before a baseline exists, in which case every
        candidate ranks equally (catalog order preserved). ``signature`` is duck-
        typed, not a fixed type: anything exposing ``.resource_dominance``/
        ``.resource_dominance_pct``/``.vectorization_density`` works (both
        ``instrumentation.base.RunSignature`` and ``orchestrator.BaselineResult``
        do) -- the same duck-typing precedent as Phase 6's ``CombinationResult``/
        ``MultiplierResult`` chaining, since this method only ever reads those
        three attributes, never anything type-specific.
        """
        raise NotImplementedError

    def validate_flagset(
        self, flags: list[str], gcc_version: Optional[str] = None, target: Optional[str] = None,
    ) -> ValidationResult:
        """Checks ``flags`` against the catalog before a build cycle is spent on
        them (doc/DESIGN.md sec. 4.3: "a hallucinated flag name fails loudly at
        build time and wastes a whole build+run cycle -- validated ahead of time,
        not discovered by trial-and-error"). ``gcc_version``/``target`` are accepted
        for the future per-version/per-target applicability check design leaves
        open; ``gcc.py``'s M1 implementation doesn't use them yet.
        """
        raise NotImplementedError

    def render_optimize_string(self, flags: list[str]) -> str:
        """Renders a flag list as a SPEC ``OPTIMIZE`` line value -- the same
        ``" ".join(flags)`` ``cfm/workloads/spec_cpu2026.py``'s ``generate_config``
        already does inline; callers building a flagset (the orchestrator) go
        through this method instead so that isn't duplicated a second place.
        """
        raise NotImplementedError
