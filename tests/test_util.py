from cfm.util import catalog_flag_base, normalize_flag_base, parse_kv_lines


def test_parse_kv_lines_basic():
    text = "a=1\nb = 2\n# comment\n\nc=hello world\n"
    assert parse_kv_lines(text) == {"a": "1", "b": "2", "c": "hello world"}


def test_parse_kv_lines_skips_lines_without_separator():
    text = "banner line\nk=v\n"
    assert parse_kv_lines(text) == {"k": "v"}


def test_parse_kv_lines_custom_separator():
    text = "key: value\nother: thing\n"
    assert parse_kv_lines(text, sep=":") == {"key": "value", "other": "thing"}


def test_normalize_flag_base_plain_flag_unchanged():
    assert normalize_flag_base("-flto") == "-flto"


def test_normalize_flag_base_strips_equals_value():
    assert normalize_flag_base("-mbranch-cost=4") == "-mbranch-cost"


def test_normalize_flag_base_param_form():
    assert normalize_flag_base("--param=prefetch-latency=300") == "--param:prefetch-latency"


def test_catalog_flag_base_plain_and_equals_forms():
    assert catalog_flag_base("-flto") == "-flto"
    assert catalog_flag_base("-march=<detected-uarch>") == "-march"


def test_catalog_flag_base_param_form_matches_normalize_flag_base():
    # The catalog spells --param entries space-separated ("--param prefetch-latency=N"),
    # a real argv-derived token spells them "=" merged ("--param=prefetch-latency=N") --
    # both must normalize to the same base name for a candidate flag to match a
    # catalog entry.
    assert (
        catalog_flag_base("--param prefetch-latency=N")
        == normalize_flag_base("--param=prefetch-latency=300")
        == "--param:prefetch-latency"
    )
