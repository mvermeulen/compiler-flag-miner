from cfm.util import parse_kv_lines


def test_parse_kv_lines_basic():
    text = "a=1\nb = 2\n# comment\n\nc=hello world\n"
    assert parse_kv_lines(text) == {"a": "1", "b": "2", "c": "hello world"}


def test_parse_kv_lines_skips_lines_without_separator():
    text = "banner line\nk=v\n"
    assert parse_kv_lines(text) == {"k": "v"}


def test_parse_kv_lines_custom_separator():
    text = "key: value\nother: thing\n"
    assert parse_kv_lines(text, sep=":") == {"key": "value", "other": "thing"}
