import re

from parsita import Failure, ParseError, SequenceReader, StringReader, Success
from parsita.state import Continue, State


def test_state_creation():
    succ = Success(40)
    assert succ == Success(40)
    assert succ != Success("a")

    fail = Failure(ParseError("my message"))
    assert fail == Failure(ParseError("my message"))
    assert fail != Failure(ParseError("another message"))

    assert succ != fail

    read = SequenceReader([1, 2, 3])
    assert read.first == 1
    assert read.rest.first == 2
    assert str(read) == "Reader(1@0)"
    assert str(read.rest.rest.rest) == "Reader(finished)"

    read = StringReader("a b")
    assert read.first == "a"
    assert read.rest.first == " "
    assert str(read) == "StringReader(a@0)"
    assert str(read.rest.rest.rest) == "StringReader(finished)"

    cont = Continue(read, 40)
    assert cont.value == 40
    assert str(cont) == "Continue(remainder=StringReader(a@0), value=40)"

    error = ParseError("Expected a but found b at index 0")
    assert str(error) == "Expected a but found b at index 0"
    assert repr(error) == "ParseError('Expected a but found b at index 0')"


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
