from __future__ import annotations

import re
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional, Sequence, Tuple, TypeVar

if TYPE_CHECKING:
    from .parsers import Parser

Input = TypeVar("Input")
Output = TypeVar("Output")
Convert = TypeVar("Convert")


class State:
    def __init__(self):
        self.farthest: Optional[Reader[Any]] = None
        self.expected: List[str] = []
        self.memo: Dict[Tuple[Parser[Any, Any], int], Optional[Continue[Any, Any]]] = {}

    def register_failure(self, expected: str, reader: Reader[Any]):
        if self.farthest is None or self.farthest.position < reader.position:
            self.expected.clear()
            self.expected.append(expected)
            self.farthest = reader
        elif self.farthest.position == reader.position:
            self.expected.append(expected)


class Reader(Generic[Input]):
    """Abstract base class for readers.

    A ``Reader`` is an immutable object holding the state of parsing.

    Attributes:
        first (Input): The element at the current position.
        rest (Reader[Input]): A ``Reader`` at the next position.
        position (int): How many characters into the source the parsing has
            gone.
        finished (bool): Indicates if the source is at the end. It is an error
            to access ``first`` or ``rest`` if ``finished`` is ``True``.
        source (Sequence[Input]): The full source being read.
    """

    first: Input
    rest: Reader[Input]
    position: int
    finished: bool
    source: Sequence[Input]

    def next_token(self):
        return self.first

    def expected_error(self, expected: Sequence[str]) -> str:
        """Generate a basic error to include the current state.

        A parser can supply only a representation of what it is expecting to
        this method and the reader will provide the context, including the index
        to the error.

        Args:
            expected: A list of representations of what the parser is currently
                expecting

        Returns:
            A full error message
        """
        expected_string = " or ".join(expected)

        if self.finished:
            return f"Expected {expected_string} but found end of source"
        else:
            return f"Expected {expected_string} but found {self.next_token()} at index {self.position}"

    def recursion_error(self, repeated_parser: str):
        """Generate an error to indicate that infinite recursion was encountered.

        A parser can supply a representation of itself to this method and the
        reader will supply the context, including the location where the
        parser stalled.

        Args:
            repeated_parser: A representation of the repeated parser

        Returns:
            A full error message
        """

        if self.finished:
            return (
                f"Infinite recursion detected in {repeated_parser}; empty string was matched and will be matched "
                "forever at end of source"
            )
        else:
            return (
                f"Infinite recursion detected in {repeated_parser}; empty string was matched and will be matched "
                f"forever at index {self.position} before {self.next_token()}"
            )

    def __repr__(self):
        if self.finished:
            return "Reader(finished)"
        else:
            return f"Reader({self.first}@{self.position})"


class SequenceReader(Reader[Input]):
    """A reader for sequences that should not be sliced.

    Python makes a copy when a sequence is sliced. This reader avoids making
    that copy by keeping one copy of source, passing it to the new reader when
    calling rest and using position to determine where in the source the reader
    should read from.

    Attributes:
        source (Sequence[Input]): What will be parsed.
    """

    def __init__(self, source: Sequence[Input], position: int = 0):
        self.source = source
        self.position = position

    @property
    def first(self) -> Input:
        return self.source[self.position]

    @property
    def rest(self) -> SequenceReader[Input]:
        return SequenceReader(self.source, self.position + 1)

    @property
    def finished(self) -> bool:
        return self.position >= len(self.source)


# Python lacks character type, so "str" will be used for both the sequence and the elements
class StringReader(Reader[str]):
    """A reader for strings.

    Python's regular expressions and string operations only work on strings,
    not abstract "readers". This class defines the source as a string so that
    regular expressions (and string literals) can safely and efficiently work
    directly on the source using the position to determine where to start.

    Attributes:
        source (str): What will be parsed.
    """

    def __init__(self, source: str, position: int = 0):
        self.source = source
        self.position = position

    @property
    def first(self) -> str:
        return self.source[self.position]

    @property
    def rest(self) -> StringReader:
        return StringReader(self.source, self.position + 1)

    @property
    def finished(self) -> bool:
        return self.position >= len(self.source)

    def drop(self, count: int) -> StringReader:
        return StringReader(self.source, self.position + count)

    next_token_regex = re.compile(r"[\(\)\[\]\{\}\"\']|\w+|[^\w\s\(\)\[\]\{\}\"\']+|\s+")

    def next_token(self) -> str:
        match = self.next_token_regex.match(self.source, self.position)
        if match is None:
            return self.source[self.position]
        else:
            return self.source[match.start() : match.end()]

    def current_line(self):
        characters_consumed = 0
        for line_index, line in enumerate(StringIO(self.source)):
            if characters_consumed + len(line) > self.position:
                # The line with the error has been found
                character_index = self.position - characters_consumed

                # This creates a line like this '        ^                  '
                pointer = (" " * character_index) + "^" + (" " * (len(line) - character_index - 1))

                # This adds a newline to line in case it is the end of the file
                if line[-1] != "\n":
                    line = line + "\n"

                # Add one to indexes to account for 0-indexes
                return line_index + 1, character_index + 1, line, pointer
            else:
                characters_consumed += len(line)

    def expected_error(self, expected: str) -> str:
        """Generate a basic error to include the current state.

        A parser can supply only a representation of what it is expecting to
        this method and the reader will provide the context, including the line
        and character positions.

        Args:
            expected: A representation of what the parser is currently expecting

        Returns:
            A full error message
        """
        expected_string = " or ".join(expected)

        if self.finished:
            return super().expected_error(expected)
        else:
            line_index, character_index, line, pointer = self.current_line()

            return (
                f"Expected {expected_string} but found {self.next_token()!r}\n"
                f"Line {line_index}, character {character_index}\n\n{line}{pointer}"
            )

    def recursion_error(self, repeated_parser: str):
        """Generate an error to indicate that infinite recursion was encountered.

        A parser can supply a representation of itself to this method and the
        reader will supply the context, including the location where the
        parser stalled.

        Args:
            repeated_parser: A representation of the repeated parser

        Returns:
            A full error message
        """
        if self.finished:
            return super().recursion_error(repeated_parser)
        else:
            line_index, character_index, line, pointer = self.current_line()

            return (
                f"Infinite recursion detected in {repeated_parser}; empty string was matched and will be matched "
                f"forever\nLine {line_index}, character {character_index}\n\n{line}{pointer}"
            )

    def __repr__(self):
        if self.finished:
            return "StringReader(finished)"
        else:
            return f"StringReader({self.next_token()}@{self.position})"


class ParseError(Exception):
    """Parsing failure.

    The container for the error of failed parsing.

    Attributes:
        message (str): A human-readable error message
    """

    def __init__(self, message: str):
        self.message = message

    def __eq__(self, other):
        if not isinstance(other, ParseError):
            return NotImplemented
        else:
            return self.message == other.message

    def __str__(self):
        return self.message

    def __repr__(self):
        return f"ParseError({self.message!r})"


@dataclass(frozen=True)
class Continue(Generic[Input, Output]):
    remainder: Reader[Input]
    value: Output


__all__ = [
    "Input",
    "Output",
    "Convert",
    "State",
    "Reader",
    "SequenceReader",
    "StringReader",
    "ParseError",
    "Continue",
]
