import re

import pytest

from parsita import Failure, ParseError, Result, SequenceReader, StringReader, Success
from parsita.state import Continue, State


def test_state_creation():
    read = SequenceReader([1, 2, 3])
    assert read.first == 1
    assert read.rest.first == 2

    read = StringReader("a b")
    assert read.first == "a"
    assert read.rest.first == " "

    cont = Continue(read, 40)
    assert cont.value == 40


def test_parse_error_str_sequence_reader():
    err = ParseError(SequenceReader("a a", 2), ["b", "c"])
    assert str(err) == "Expected b or c but found a at index 2"


def test_parse_error_str_sequence_reader_end_of_source():
    err = ParseError(SequenceReader("a a", 3), ["b"])
    assert str(err) == "Expected b but found end of source"


def test_parse_error_str_string_reader():
    err = ParseError(StringReader("a a", 2), ["'b'", "'c'"])
    assert str(err) == "Expected 'b' or 'c' but found 'a'\nLine 1, character 3\n\na a\n  ^"


def test_parse_error_str_string_reader_end_of_source():
    err = ParseError(StringReader("a a", 3), ["'b'"])
    assert str(err) == "Expected 'b' but found end of source"


def test_register_failure_first():
    state = State()
    state.register_failure("foo", StringReader("bar baz", 0))
    assert state.expected == ["foo"]
    assert state.farthest.position == 0


def test_register_failure_at_middle():
    state = State()
    state.register_failure("foo", StringReader("bar baz", 4))
    assert state.expected == ["foo"]
    assert state.farthest.position == 4


def test_register_failure_latest():
    state = State()
    state.register_failure("foo", StringReader("bar baz", 0))
    state.register_failure("egg", StringReader("bar baz", 4))
    assert state.expected == ["egg"]
    assert state.farthest.position == 4


def test_register_failure_tied():
    state = State()
    state.register_failure("foo", StringReader("bar baz", 4))
    state.register_failure("egg", StringReader("bar baz", 4))
    assert state.expected == ["foo", "egg"]
    assert state.farthest.position == 4


def test_isinstance():
    success = Success(1)
    failure = Failure(ParseError(StringReader("bar baz", 4), ["foo"]))
    assert isinstance(success, Success)
    assert isinstance(failure, Failure)


@pytest.mark.xfail(reason="Result is a type alias and importing the concrete type would break eager annotations")
def test_isinstance_result():
    success = Success(1)
    failure = Failure(ParseError(StringReader("bar baz", 4), ["foo"]))
    assert isinstance(success, Result)
    assert isinstance(failure, Result)


def test_result_annotation():
    def foo() -> Result[int]:
        return Success(1)

    assert foo() == Success(1)


def test_current_line():
    # This test only exists to get 100% test coverage without doing a pragma: no cover on the whole current_line
    # method. Under normal operation, the for loop should never complete because the position is also on some
    # line. Here, the position has been artificially advanced beyond the length of the input.
    reader = StringReader("foo", 3)
    assert reader.current_line() is None


def test_reader_with_defective_next_token_regex():
    # With the default value of next_token_regex, a match cannot fail. However, if a fallible regex is provided to
    # a super class next_token should not crash.
    class DefectiveReader(StringReader):
        next_token_regex = re.compile(r"[A-Za-z0-9]+")

    good_position = DefectiveReader("foo_foo", 4)
    assert good_position.next_token() == "foo"

    bad_position = DefectiveReader("foo_foo", 3)
    assert bad_position.next_token() == "_"
