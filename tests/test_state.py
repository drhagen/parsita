from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
from returns import result

from parsita import Failure, ParseError, SequenceReader, StringReader, Success
from parsita.state import Backtrack, Continue, Reader


def test_state_creation():
    succ = Success(40)
    assert succ.value == 40
    assert succ == Success(40)
    assert str(succ) == "Success(40)"
    assert succ != Success("a")

    fail = Failure("my message")
    assert fail.message == "my message"
    assert fail == Failure("my message")
    assert str(fail) == "Failure('my message')"
    assert fail != Failure("another message")

    error_fail = Failure(ParseError("my message"))
    assert fail == error_fail
    assert ParseError("my message") != 1

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
    assert str(cont) == "Continue(40, StringReader(a@0))"

    back = Backtrack(read, lambda: "no further")
    assert back.expected[0]() == "no further"
    assert str(back) == "Backtrack(StringReader(a@0), ['no further'])"

    error = ParseError("Expected a but found b at index 0")
    assert str(error) == "Expected a but found b at index 0"
    assert repr(error) == "ParseError('Expected a but found b at index 0')"


def test_unwrap():
    assert Success(40).unwrap() == 40
    with pytest.raises(result.UnwrapFailedError):
        Failure("my message").unwrap()


def test_equal_to_returns_result():
    assert Success(40) == result.Success(40)
    assert result.Success(40) == Success(40)
    assert Success(40) != result.Success(41)
    assert Failure("my message") == result.Failure(ParseError("my message"))
    assert result.Failure(ParseError("my message")) == Failure("my message")
    assert Failure("my message") != result.Failure(ParseError("another message"))


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


def test_reader_drop():
    # Neither StringReader nor SequenceReader use the base implementation of
    # drop, so this test is for that in case someone extends Reader.

    @dataclass(frozen=True)
    class BytesReader(Reader):
        source: bytes
        position: int = 0

        @property
        def first(self) -> int:
            return self.source[self.position]

        @property
        def rest(self) -> BytesReader:
            return BytesReader(self.source, self.position + 1)

        @property
        def finished(self) -> bool:
            return self.position >= len(self.source)

    assert BytesReader(b"foo").drop(0) == BytesReader(b"foo", 0)
    assert BytesReader(b"foo").drop(2) == BytesReader(b"foo", 2)
    assert BytesReader(b"foo").drop(1).drop(2) == BytesReader(b"foo", 3)
