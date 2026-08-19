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
    candidates = {c.flag for c in compiler.candidate_flags_for_signature(None, ["cxx"])}
    assert candidates == {"-shared-flag", "-cxx-only-flag", "-fprofile-generate", "-fprofile-use"}
    assert "-c-only-flag" not in candidates
    assert "-fortran-only-flag" not in candidates
    assert "-mbranch-cost=N" not in candidates


def test_candidate_flags_ignores_signature_argument(compiler):
    # M1 scope: signature is accepted but has zero effect on the result.
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
