"""Unit tests for scripts/audit_flags_from_spec_results.py's pure parsing/diff logic.

No network access, no SPEC license concerns -- tests/fixtures/spec_cpu2017_sample_gcc.cfg
is a hand-constructed synthetic config (see its header comment), not a captured real
result, and the HTML snippets below are generic markup, not scraped page content.
"""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "spec_cpu2017_sample_gcc.cfg"

# scripts/ isn't an importable package (it's plain dev tooling, like bootstrap_wspy.sh),
# so load the module directly from its file path.
_spec = importlib.util.spec_from_file_location(
    "audit_flags_from_spec_results", REPO_ROOT / "scripts" / "audit_flags_from_spec_results.py"
)
audit = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = audit
_spec.loader.exec_module(audit)


def test_extract_cfg_links_resolves_relative_and_absolute():
    html = """
    <table><tr><td>
      <a href="cpu2017-20190625-15870.html">HTML</a> |
      <a href="cpu2017-20190625-15870.cfg">Config</a>
    </td></tr><tr><td>
      <a href="/cpu2017/results/res2019q3/cpu2017-20190709-16046.cfg">Config</a>
    </td></tr></table>
    """
    links = audit.extract_cfg_links(html, "https://www.spec.org/cpu2017/results/res2019q3/")
    assert links == [
        "https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190625-15870.cfg",
        "https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190709-16046.cfg",
    ]


def test_extract_cfg_links_dedupes_and_ignores_non_cfg():
    html = """
    <a href="a.cfg">x</a> <a href="a.cfg">x again</a> <a href="a.html">not cfg</a>
    """
    links = audit.extract_cfg_links(html, "https://www.spec.org/")
    assert links == ["https://www.spec.org/a.cfg"]


def test_looks_like_cgi_bin_guard():
    assert audit._looks_like_cgi_bin("https://www.spec.org/cgi-bin/osgresults?conf=cpu2017")
    assert not audit._looks_like_cgi_bin("https://www.spec.org/cpu2017/results/res2019q3/x.cfg")


def test_looks_like_gnu_compiler_true_for_fixture():
    text = FIXTURE.read_text()
    is_gnu, ident = audit.looks_like_gnu_compiler(text)
    assert is_gnu
    assert "gcc" in ident and "gfortran" in ident


def test_looks_like_gnu_compiler_false_for_non_gnu():
    text = "CC = icc -m64\nCXX = icpc -m64\nFC = ifort -m64\n"
    is_gnu, _ident = audit.looks_like_gnu_compiler(text)
    assert not is_gnu


def test_looks_like_gnu_compiler_resolves_dollar_paren_speclang_prefix():
    # Confirmed live against a real 494-config corpus (2026-08-09): SPEC's own
    # example config template writes CC = $(SPECLANG)gcc with SPECLANG defined
    # elsewhere as a directory path -- checking the raw unresolved "$(SPECLANG)gcc"
    # string for a "gcc" suffix fails (it doesn't end in a /-delimited "gcc" until
    # resolved); 31/31 real configs written this way were wrongly rejected before
    # this fix. SPECLANG's own value below still contains an unresolved %{gcc_dir}
    # percent-brace macro (a distinct, unhandled SPEC preprocessor construct) --
    # deliberately left that way, since the rsplit("/", 1)[-1] basename check only
    # needs the text after the *last* "/" to be exactly "gcc", regardless of
    # whatever unresolved macro noise precedes it.
    text = (
        "SPECLANG = %{gcc_dir}/bin/\n"
        "CC       = $(SPECLANG)gcc     -std=c99   %{model}\n"
        "CXX      = $(SPECLANG)g++     -std=c++03 %{model}\n"
        "FC       = $(SPECLANG)gfortran           %{model}\n"
    )
    is_gnu, ident = audit.looks_like_gnu_compiler(text)
    assert is_gnu, ident


def test_looks_like_gnu_compiler_requires_all_three_roles_to_be_gnu():
    # Confirmed live against the same corpus: AOCC sets CC=clang/CXX=clang++ but
    # FC=gfortran (a real gfortran binary, AOCC-plugin-modified codegen per the
    # config's own notes_comp banner) -- any() previously let FC's "gfortran"
    # alone pass the whole config as "GNU". 463/463 real AOCC configs were wrongly
    # counted as GCC before this fix (all() now correctly rejects them on CC/CXX).
    text = "CC = clang\nCXX = clang++\nFC = gfortran\n"
    is_gnu, ident = audit.looks_like_gnu_compiler(text)
    assert not is_gnu
    assert "clang" in ident and "gfortran" in ident  # diagnostic text still shows all three


def test_looks_like_gnu_compiler_vendor_marker_overrides_gnu_looking_identity():
    # Defense-in-depth: even if CC/CXX/FC all *look* GNU by name, a config that
    # self-identifies as a known non-GNU vendor (_KNOWN_NON_GNU_VENDOR_MARKERS) is
    # still rejected -- not yet observed in the wild for a vendor whose C/C++
    # driver is literally named gcc/g++, but the all()-role check alone wouldn't
    # catch that hypothetical case.
    text = (
        "CC = gcc\nCXX = g++\nFC = gfortran\n"
        "notes_comp_025 = The AOCC Fortran Plugin version 1.2 was used\n"
    )
    is_gnu, ident = audit.looks_like_gnu_compiler(text)
    assert not is_gnu
    assert "AOCC" in ident


def test_looks_like_gnu_compiler_true_for_all_gnu_with_no_vendor_banner():
    text = "CC = gcc\nCXX = g++\nFC = gfortran\n"
    is_gnu, _ident = audit.looks_like_gnu_compiler(text)
    assert is_gnu


def test_looks_like_gnu_compiler_handles_speclang_with_no_path_separator():
    # Confirmed live: 1/494 real configs define SPECLANG = %{gcc_dir} with no
    # trailing "/bin/" (unlike the far more common template), resolving CC to
    # "%{gcc_dir}gcc ..." -- no "/" anywhere in the string at all.
    text = (
        "SPECLANG = %{gcc_dir}\n"
        "CC       = $(SPECLANG)gcc     -std=c99   %{model}\n"
        "CXX      = $(SPECLANG)g++     -std=c++03 %{model}\n"
        "FC       = $(SPECLANG)gfortran           %{model}\n"
    )
    is_gnu, ident = audit.looks_like_gnu_compiler(text)
    assert is_gnu, ident


def test_gnu_name_if_any_rejects_clang_plus_plus():
    # The exact case a naive .endswith("g++") check would get wrong.
    assert audit._gnu_name_if_any("clang++") is None
    assert audit._gnu_name_if_any("clang") is None


def test_gnu_name_if_any_accepts_target_triple_prefixed_cross_compiler():
    assert audit._gnu_name_if_any("aarch64-linux-gnu-gcc") == "gcc"
    assert audit._gnu_name_if_any("/usr/bin/g++") == "g++"
    assert audit._gnu_name_if_any("%{gcc_dir}gfortran") == "gfortran"


def test_resolve_refs_substitutes_and_flags_unresolved():
    all_vars = {"FOO": "-fbar -fbaz"}
    resolved, had_unresolved = audit.resolve_refs("$(FOO) -fqux", all_vars)
    assert resolved == "-fbar -fbaz -fqux"
    assert not had_unresolved

    resolved, had_unresolved = audit.resolve_refs("$(UNDEFINED) -fqux", all_vars)
    assert had_unresolved
    assert "-fqux" in resolved


def test_normalize_base_param_and_equals_forms():
    assert audit.normalize_base("-mbranch-cost=4") == "-mbranch-cost"
    assert audit.normalize_base("-flto") == "-flto"
    assert audit.normalize_base("--param=prefetch-latency=300") == "--param:prefetch-latency"


def test_extract_flag_tokens_against_fixture():
    text = FIXTURE.read_text()
    tokens, had_unresolved = audit.extract_flag_tokens(text)
    bases = {audit.normalize_base(t) for t in tokens}

    # Known-good flags actually present in config/gcc_flag_catalog.seed.json.
    for expected in ("-march", "-funroll-loops", "-fprefetch-loop-arrays",
                      "--param:prefetch-latency", "-flto", "-fprofile-use",
                      "-fstack-arrays", "-fno-semantic-interposition"):
        assert expected in bases, f"expected {expected!r} in {bases}"

    # Catalog gaps this fixture deliberately plants.
    for expected in ("-mtune", "-fno-plt", "-ffree-line-length-none"):
        assert expected in bases, f"expected {expected!r} in {bases}"

    # EXTRA_CFLAGS references an undefined $(SITE_SPECIFIC_FLAGS).
    assert had_unresolved
    assert not any("$(" in t for t in tokens)


def test_load_catalog_bases_covers_seed_catalog():
    bases = audit.load_catalog_bases(audit.DEFAULT_CATALOG)
    assert "-flto" in bases
    assert "-march" in bases  # from "-march=<detected-uarch>"
    assert "--param:prefetch-latency" in bases  # from "--param prefetch-latency=N"


def test_run_audit_end_to_end_against_fixture(tmp_path, monkeypatch):
    # Avoid any real network access: monkeypatch fetch_static to read the fixture
    # directly, keyed off a fake URL.
    fake_url = "https://www.spec.org/cpu2017/results/res2099q1/fake-result.cfg"

    def fake_fetch(url, cache_dir, user_agent, limiter, force_refetch=False):
        assert url == fake_url
        return FIXTURE.read_text()

    monkeypatch.setattr(audit, "fetch_static", fake_fetch)

    result = audit.run_audit(
        [fake_url], audit.DEFAULT_CATALOG, tmp_path, "test-agent/1.0",
        delay_seconds=0.0, force_refetch=False, skip_compiler_check=False,
    )

    assert result.configs_used == 1
    assert result.configs_skipped_non_gnu == 0
    assert result.configs_with_unresolved_refs == 1
    assert "-mtune" in result.new_candidates
    assert "-flto" in result.known
    assert result.examples["-mtune"] == [fake_url]

    report = audit.render_report(result, audit.DEFAULT_CATALOG)
    assert "-mtune" in report
    assert "-flto" in report


# -- ignore-list additions (confirmed live against a real all-GCC corpus) ---------

def test_is_ignored_diagnostic_and_build_speed_flags():
    for tok in ("-Wno-error", "-Wno-implicit-int", "-w", "-pipe", "-fpermissive"):
        assert audit.is_ignored(audit.normalize_base(tok), tok), tok


def test_is_ignored_linker_passthrough_z():
    # "-z muldefs" is two argv tokens; only "-z" itself is ever a candidate token
    # at all ("muldefs" doesn't start with "-", filtered by _tokenize itself).
    assert audit.is_ignored("-z", "-z")


def test_is_ignored_legacy_buildability_shims():
    for tok in (
        "-fgnu89-inline", "-fallow-argument-mismatch", "-fcommon",
        "-fconvert", "-funsigned-char",
    ):
        assert audit.is_ignored(audit.normalize_base(tok), tok), tok


def test_is_ignored_does_not_swallow_a_real_tuning_flag():
    # Sanity check the new -Wno- prefix/exact additions didn't overreach.
    assert not audit.is_ignored("-fomit-frame-pointer", "-fomit-frame-pointer")
    assert not audit.is_ignored("-mcpu", "-mcpu=native")
