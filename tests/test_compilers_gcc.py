import json

import pytest

from cfm.compilers.base import ValidationResult
from cfm.compilers.gcc import GccCompiler, benchmark_languages, _DEFAULT_CATALOG_PATH


def _write_catalog(path, entries):
    path.write_text(json.dumps({"schema_version": 1, "source": "test", "note": "test", "flags": entries}))


@pytest.fixture
def fixture_catalog(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, [
        {
            "flag": "-shared-flag", "languages": ["c", "cxx", "fortran"], "category": "misc",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "", "topdown_signals": [],
        },
        {
            "flag": "-c-only-flag", "languages": ["c"], "category": "misc",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "", "topdown_signals": [],
        },
        {
            "flag": "-cxx-only-flag", "languages": ["cxx"], "category": "misc",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "", "topdown_signals": [],
        },
        {
            "flag": "-fortran-only-flag", "languages": ["fortran"], "category": "gfortran-specific",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "", "topdown_signals": [],
        },
        {
            "flag": "-fprofile-generate", "languages": ["c", "cxx"], "category": "pgo",
            "risk": "needs_validation", "requires": [],
            "conflicts": ["-fprofile-use"], "notes": "", "topdown_signals": [],
        },
        {
            "flag": "-fprofile-use", "languages": ["c", "cxx"], "category": "pgo",
            "risk": "needs_validation", "requires": ["-fprofile-generate (prior training run)"],
            "conflicts": ["-fprofile-generate"], "notes": "", "topdown_signals": [],
        },
        {
            "flag": "-mbranch-cost=N", "languages": ["c", "cxx", "fortran"], "category": "target-tuning",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "", "topdown_signals": [],
        },
    ])
    return path


@pytest.fixture
def compiler(fixture_catalog):
    return GccCompiler(catalog_path=fixture_catalog)


def test_candidate_flags_filters_by_language(compiler):
    # -mbranch-cost=N is in the fixture catalog but is an unresolved template
    # placeholder (tested separately below), so it never reaches this result.
    # -fprofile-generate/-fprofile-use are category="pgo" -- excluded from this
    # ordinary per-flag list entirely (tested separately below too).
    candidates = {c.flag for c in compiler.candidate_flags_for_signature(None, ["cxx"])}
    assert candidates == {"-shared-flag", "-cxx-only-flag"}
    assert "-c-only-flag" not in candidates
    assert "-fortran-only-flag" not in candidates
    assert "-mbranch-cost=N" not in candidates


def test_candidate_flags_excludes_pgo_category(compiler):
    # -fprofile-generate/-fprofile-use are never proposed as ordinary single-flag
    # candidates -- each is meaningless tested alone (see cfm/compilers/gcc.py's
    # own comment, and doc/mining_results.714.cpython_r.2026-08-21.md's live
    # illustration of exactly why). PGO is Phase 6's own dedicated two-pass flow.
    candidates = {c.flag for c in compiler.candidate_flags_for_signature(None, ["c", "cxx"])}
    assert "-fprofile-generate" not in candidates
    assert "-fprofile-use" not in candidates


def test_candidate_flags_preserves_catalog_order_when_no_candidate_carries_signals(compiler):
    # None of fixture_catalog's entries carry topdown_signals, so every candidate
    # ranks neutrally (0) regardless of signature -- a stable sort on an all-tied
    # key preserves catalog order. Real signature-driven reordering (M2) is tested
    # separately below, against a fixture catalog whose entries actually carry
    # topdown_signals to rank on.
    with_none = compiler.candidate_flags_for_signature(None, ["fortran"])
    with_dummy = compiler.candidate_flags_for_signature(object(), ["fortran"])
    assert {c.flag for c in with_none} == {c.flag for c in with_dummy} == {"-shared-flag", "-fortran-only-flag"}


# -- unresolved template placeholders (real M1 gap, found ahead of the first real
# `cfm mine` run: a literal "-march=<detected-uarch>"/"-mbranch-cost=N" flag is
# not buildable text, GCC just rejects it outright) --------------------------------

def test_candidate_flags_resolves_detected_uarch_to_march_native(compiler):
    del compiler  # this substitution is independent of any particular catalog
    from cfm.compilers.gcc import _resolve_flag_or_none
    assert _resolve_flag_or_none("-march=<detected-uarch>") == "-march=native"


def test_candidate_flags_skips_unresolved_numeric_placeholder(compiler, capsys):
    from cfm.compilers.gcc import _resolve_flag_or_none
    assert _resolve_flag_or_none("-mbranch-cost=N") is None
    assert _resolve_flag_or_none("--param prefetch-latency=N") is None
    assert "skipping" in capsys.readouterr().out


def test_candidate_flags_passes_through_a_concrete_flag_unchanged(compiler):
    from cfm.compilers.gcc import _resolve_flag_or_none
    assert _resolve_flag_or_none("-flto") == "-flto"
    assert _resolve_flag_or_none("-mprefer-vector-width=256") == "-mprefer-vector-width=256"


def test_validate_flagset_flags_unknown_flag(compiler):
    result = compiler.validate_flagset(["-totally-made-up-flag"])
    assert isinstance(result, ValidationResult)
    assert result.ok is False
    assert any("-totally-made-up-flag" in p for p in result.problems)


def test_validate_flagset_detects_conflict(compiler):
    result = compiler.validate_flagset(["-fprofile-generate", "-fprofile-use"])
    assert result.ok is False
    assert any("conflict" in p for p in result.problems)


def test_validate_flagset_requires_is_a_note_not_a_problem(compiler):
    # -fprofile-use "requires" -fprofile-generate, but that's a prior *separate*
    # training run, not co-occurrence in the same flagset (they even conflict with
    # each other) -- so this must NOT be flagged as a problem, only noted.
    result = compiler.validate_flagset(["-fprofile-use"])
    assert result.ok is True
    assert result.problems == []
    assert any("requires" in n and "-fprofile-generate" in n for n in result.notes)


def test_validate_flagset_ok_for_a_clean_independent_flagset(compiler):
    result = compiler.validate_flagset(["-shared-flag", "-cxx-only-flag"])
    assert result.ok is True
    assert result.problems == []


def test_validate_flagset_matches_equals_value_flags_against_catalog_template(compiler):
    # "-mbranch-cost=3" (a real argv-shaped flag) must match the catalog's
    # "-mbranch-cost=N" template entry via normalize_flag_base, not fail as unknown.
    result = compiler.validate_flagset(["-mbranch-cost=3"])
    assert result.ok is True


def test_render_optimize_string_joins_with_spaces(compiler):
    assert compiler.render_optimize_string(["-O3", "-flto", "-march=native"]) == "-O3 -flto -march=native"


def test_real_seed_catalog_loads_and_is_internally_consistent():
    # Catches a future edit to config/gcc_flag_catalog.seed.json breaking the loader
    # or introducing an unresolvable conflict reference -- not a fixture, the real file.
    compiler = GccCompiler(catalog_path=_DEFAULT_CATALOG_PATH)
    candidates = compiler.candidate_flags_for_signature(None, ["c", "cxx", "fortran"])
    assert len(candidates) > 0
    assert any(c.flag == "-flto" for c in candidates)
    # Two known-compatible real catalog entries with no conflict between them.
    result = compiler.validate_flagset(["-flto", "-funroll-loops"])
    assert result.ok is True
    # A known real conflicting pair.
    result = compiler.validate_flagset(["-mprefer-vector-width=256", "-mprefer-vector-width=512"])
    assert result.ok is False


# -- M2: signature-aware ranking ------------------------------------------------
#
# doc/DESIGN.md sec. 4.3's signature-to-candidate table, made concrete: a
# candidate whose topdown_signals genuinely match the baseline's characterized
# shape should be returned before one that merely wasn't excluded. ``signature``
# is duck-typed (compilers/base.py's interface docstring) -- this stand-in only
# needs to expose the three attributes _candidate_rank() actually reads.

class _FakeSignature:
    def __init__(self, resource_dominance=None, resource_dominance_pct=None, vectorization_density=None):
        self.resource_dominance = resource_dominance
        self.resource_dominance_pct = resource_dominance_pct
        self.vectorization_density = vectorization_density


@pytest.fixture
def ranking_catalog(tmp_path):
    path = tmp_path / "ranking_catalog.json"
    _write_catalog(path, [
        {
            "flag": "-frontend-flag", "languages": ["c"], "category": "codegen-layout",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "",
            "topdown_signals": ["frontend-bound"],
        },
        {
            "flag": "-memory-flag", "languages": ["c"], "category": "memory",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "",
            "topdown_signals": ["memory-bound-corroborated"],
        },
        {
            "flag": "-vector-flag", "languages": ["c"], "category": "vectorization",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "",
            "topdown_signals": ["vectorization-density-high"],
        },
        {
            "flag": "-ofast-like-flag", "languages": ["c"], "category": "fp-semantics",
            "risk": "changes_fp_semantics", "requires": [], "conflicts": [], "notes": "",
            "topdown_signals": ["compute-bound"],
        },
        {
            "flag": "-march=<detected-uarch>", "languages": ["c"], "category": "target-tuning",
            "risk": "needs_validation", "requires": [], "conflicts": [], "notes": "",
            "topdown_signals": ["compute-bound", "retiring-high-narrow-margin"],
        },
        {
            "flag": "-no-signal-flag", "languages": ["c"], "category": "misc",
            "risk": "safe", "requires": [], "conflicts": [], "notes": "", "topdown_signals": [],
        },
    ])
    return path


@pytest.fixture
def ranking_compiler(ranking_catalog):
    return GccCompiler(catalog_path=ranking_catalog)


def test_ranking_puts_matching_frontend_bound_flag_first(ranking_compiler):
    signature = _FakeSignature(resource_dominance="frontend-bound")
    flags = [c.flag for c in ranking_compiler.candidate_flags_for_signature(signature, ["c"])]
    assert flags[0] == "-frontend-flag"
    # Everything else ties at rank 0 (no matching signal) -- catalog order preserved.
    assert flags[1:] == ["-memory-flag", "-vector-flag", "-ofast-like-flag", "-march=native", "-no-signal-flag"]


def test_ranking_puts_matching_vectorization_density_flag_first(ranking_compiler):
    signature = _FakeSignature(resource_dominance="memory-bound", vectorization_density="high")
    flags = [c.flag for c in ranking_compiler.candidate_flags_for_signature(signature, ["c"])]
    # Both -memory-flag (resource_dominance match) and -vector-flag (vectorization
    # match) rank 1 -- catalog order (memory before vector) breaks the tie.
    assert flags[:2] == ["-memory-flag", "-vector-flag"]


def test_ranking_prioritizes_march_over_other_aggressive_flags_on_a_narrow_margin(ranking_compiler):
    # The concrete case doc/DESIGN.md sec. 4.3's own table describes: compute-
    # bound, narrow margin (retiring high, no single bottleneck dominates
    # overwhelmingly) -- -march=<uarch> (2 matching signals) should outrank
    # -ofast-like-flag (1 matching signal, compute-bound only).
    signature = _FakeSignature(resource_dominance="compute-bound", resource_dominance_pct=45.0)
    flags = [c.flag for c in ranking_compiler.candidate_flags_for_signature(signature, ["c"])]
    assert flags[0] == "-march=native"
    assert flags[1] == "-ofast-like-flag"


def test_ranking_does_not_boost_march_when_margin_is_wide(ranking_compiler):
    # A confidently, dominantly compute-bound shape (pct well above the narrow-
    # margin threshold) -- -march=<uarch> and -ofast-like-flag both carry only
    # one matching signal each (compute-bound); retiring-high-narrow-margin
    # doesn't apply, so they tie and catalog order (-ofast-like-flag before
    # -march=<uarch> in this fixture) decides, not a forced march-first boost --
    # the opposite order from the narrow-margin case above, confirming the
    # boost really is margin-conditional, not unconditional.
    signature = _FakeSignature(resource_dominance="compute-bound", resource_dominance_pct=95.0)
    flags = [c.flag for c in ranking_compiler.candidate_flags_for_signature(signature, ["c"])]
    assert flags.index("-ofast-like-flag") < flags.index("-march=native")


def test_ranking_treats_unknown_baseline_as_neutral_preserving_catalog_order(ranking_compiler):
    flags = [c.flag for c in ranking_compiler.candidate_flags_for_signature(None, ["c"])]
    assert flags == [
        "-frontend-flag", "-memory-flag", "-vector-flag",
        "-ofast-like-flag", "-march=native", "-no-signal-flag",
    ]


def test_ranking_treats_narrow_margin_signal_as_neutral_when_pct_unknown(ranking_compiler):
    # A known compute-bound read with no pct at all (e.g. this benchmark's shape
    # came from a reference-matrix corpus entry or local trial that didn't supply
    # one) -- retiring-high-narrow-margin adds nothing (neither a match nor a
    # penalty), so -march=<uarch> ties with -ofast-like-flag on the plain
    # compute-bound match alone, same as the wide-margin case above.
    signature = _FakeSignature(resource_dominance="compute-bound", resource_dominance_pct=None)
    flags = [c.flag for c in ranking_compiler.candidate_flags_for_signature(signature, ["c"])]
    assert flags.index("-ofast-like-flag") < flags.index("-march=native")  # catalog order, not a boost


# -- benchmark_languages() ---------------------------------------------------------

def _write_object_pm(spec_dir, bench, benchlang):
    object_pm = spec_dir / "benchspec" / "CPU" / bench / "Spec" / "object.pm"
    object_pm.parent.mkdir(parents=True)
    object_pm.write_text(f"$benchname = '{bench}';\n$benchlang = '{benchlang}';\n$exe_base = '{bench}';\n")


@pytest.mark.parametrize("benchlang,expected", [
    ("C", ["c"]),
    ("CXX", ["cxx"]),
    ("CXX,C", ["cxx", "c"]),
    ("F", ["fortran"]),
])
def test_benchmark_languages_known_tokens(tmp_path, benchlang, expected):
    # These 4 values are the whole set confirmed against a real CPU2026 install this
    # session (706.stockfish_r/707.ntest_r/708.sqlite_r/709.cactus_r/749.fotonik3d_r).
    _write_object_pm(tmp_path, "999.fake_r", benchlang)
    assert benchmark_languages(tmp_path, "999.fake_r") == expected


def test_benchmark_languages_missing_object_pm_raises(tmp_path):
    with pytest.raises(RuntimeError, match="no Spec/object.pm"):
        benchmark_languages(tmp_path, "999.missing_r")


def test_benchmark_languages_missing_benchlang_line_raises(tmp_path):
    object_pm = tmp_path / "benchspec" / "CPU" / "999.fake_r" / "Spec" / "object.pm"
    object_pm.parent.mkdir(parents=True)
    object_pm.write_text("$benchname = '999.fake_r';\n")
    with pytest.raises(RuntimeError, match="no \\$benchlang"):
        benchmark_languages(tmp_path, "999.fake_r")


def test_benchmark_languages_unknown_token_raises(tmp_path):
    _write_object_pm(tmp_path, "999.fake_r", "RUST")
    with pytest.raises(RuntimeError, match="unrecognized \\$benchlang token"):
        benchmark_languages(tmp_path, "999.fake_r")
