"""Compiler Knowledge agent interface -- doc/DESIGN.md sec. 4.3 / sec. 12.

``gcc.py`` is the only implementation today; ``llvm.py``/``aocc.py`` are the future
modularity seam this interface defines, not yet implemented.

M1 scope note (doc/DESIGN.md sec. 14): ``candidate_flags_for_signature`` exists with
its full signature (``signature`` included) so M2 can wire real resource_dominance-
based filtering into ``gcc.py`` without changing this interface -- but M1's own
implementation ignores ``signature`` entirely and returns the whole
applicable-language catalog uniformly ("static catalog priors only").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


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
        ``languages`` (e.g. ``["cxx"]``), given the baseline's
        ``instrumentation.base.RunSignature`` (or ``None`` before a baseline
        exists). M1's ``gcc.py`` implementation ignores ``signature``; M2 wires in
        real resource_dominance-based filtering/ranking (doc/DESIGN.md sec. 4.3's
        signature-to-candidate table) without changing this method's shape.
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
