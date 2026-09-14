import pytest

from pystingerconniface.contenttype import ContentType


def test_simple_type() -> None:
    ct = ContentType("text/plain")

    assert ct == "text/plain"
    assert ct.parameters == {}


def test_lowercases_type_and_strips_whitespace() -> None:
    ct = ContentType(" TEXT/Plain ")

    assert ct == "text/plain"


def test_unquoted_parameter() -> None:
    ct = ContentType("text/plain; charset=utf-8")

    assert ct == "text/plain"
    assert ct.parameters == {"charset": "utf-8"}
    assert ct.charset == "utf-8"


def test_quoted_parameter_with_spaces() -> None:
    ct = ContentType('multipart/form-data; boundary="some boundary value"')

    assert ct.parameters == {"boundary": "some boundary value"}
    assert ct.boundary == "some boundary value"


def test_quoted_parameter_with_escaped_quote() -> None:
    ct = ContentType(r'text/plain; name="a \"quoted\" value"')

    assert ct.parameters == {"name": 'a "quoted" value'}


def test_multiple_parameters() -> None:
    ct = ContentType("text/plain; charset=utf-8; format=flowed")

    assert ct.parameters == {"charset": "utf-8", "format": "flowed"}


def test_parameter_keys_are_lowercased() -> None:
    ct = ContentType("text/plain; CHARSET=utf-8")

    assert ct.parameters == {"charset": "utf-8"}


def test_non_identifier_parameter_key_is_not_set_as_attribute() -> None:
    ct = ContentType("text/plain; not-an-identifier=value")

    assert ct.parameters == {"not-an-identifier": "value"}
    assert not hasattr(ct, "not_an_identifier")


def test_missing_attribute_raises_attribute_error() -> None:
    ct = ContentType("text/plain")

    with pytest.raises(AttributeError):
        _ = ct.charset


def test_empty_string_raises_value_error() -> None:
    with pytest.raises(ValueError):
        ContentType("")


def test_whitespace_only_raises_value_error() -> None:
    with pytest.raises(ValueError):
        ContentType("   ")


def test_missing_slash_raises_value_error() -> None:
    with pytest.raises(ValueError):
        ContentType("not-a-valid-type")


def test_copy_constructor_preserves_parameters() -> None:
    original = ContentType("text/plain; charset=utf-8")
    copy = ContentType(original)

    assert copy == original
    assert copy.parameters == original.parameters
    assert copy.charset == "utf-8"


def test_copy_constructor_is_independent_of_original() -> None:
    original = ContentType("text/plain; charset=utf-8")
    copy = ContentType(original)
    copy.parameters["charset"] = "ascii"

    assert original.parameters["charset"] == "utf-8"


def test_to_header_round_trips_simple_type() -> None:
    ct = ContentType("text/plain")

    assert ct.to_header() == "text/plain"


def test_to_header_includes_unquoted_parameters() -> None:
    ct = ContentType("text/plain; charset=utf-8")

    assert ct.to_header() == "text/plain; charset=utf-8"


def test_to_header_quotes_values_needing_it() -> None:
    ct = ContentType('multipart/form-data; boundary="some boundary"')

    assert ct.to_header() == 'multipart/form-data; boundary="some boundary"'


def test_to_header_escapes_quotes_in_values() -> None:
    ct = ContentType(r'text/plain; name="a \"quoted\" value"')

    assert ct.to_header() == r'text/plain; name="a \"quoted\" value"'
