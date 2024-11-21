from __future__ import annotations

__all__ = ["Reader", "SequenceReader", "StringReader"]

import re
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING, Generic, Sequence, TypeVar

Input = TypeVar("Input", covariant=True)


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

    if TYPE_CHECKING:
        # These abstract properties cannot exist at runtime or they will break the
        # dataclass subclasses

        @property
        def first(self) -> Input: ...

        @property
        def rest(self) -> Reader[Input]: ...

        @property
        def position(self) -> int: ...

        @property
        def finished(self) -> bool: ...

        @property
        def source(self) -> Sequence[Input]: ...

    def drop(self, count: int) -> Reader[Input]:
        """Advance the reader by ``count`` elements.

        Both ``SequenceReader`` and ``StringReader`` override this method with a
        more efficient implementation.
        """
        rest = self
        for _ in range(count):
            rest = rest.rest
        return rest

    def next_token(self) -> Input:
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
            return (
                f"Expected {expected_string} but found {self.next_token()} "
                f"at index {self.position}"
            )

    def recursion_error(self, repeated_parser: str) -> str:
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
                f"Infinite recursion detected in {repeated_parser}; "
                "empty string was matched and will be matched forever at end of source"
            )
        else:
            return (
                f"Infinite recursion detected in {repeated_parser}; empty string was matched "
                f"and will be matched forever at index {self.position} before {self.next_token()}"
            )


@dataclass(frozen=True)
class SequenceReader(Generic[Input], Reader[Input]):
    """A reader for sequences that should not be sliced.

    Python makes a copy when a sequence is sliced. This reader avoids making
    that copy by keeping one copy of source, passing it to the new reader when
    calling rest and using position to determine where in the source the reader
    should read from.

    Attributes:
        source (Sequence[Input]): What will be parsed
        position (int): Current position in the source
    """

    source: Sequence[Input]
    position: int = 0

    @property
    def first(self) -> Input:
        return self.source[self.position]

    @property
    def rest(self) -> SequenceReader[Input]:
        return SequenceReader(self.source, self.position + 1)

    @property
    def finished(self) -> bool:
        return self.position >= len(self.source)

    def drop(self, count: int) -> SequenceReader[Input]:
        return SequenceReader(self.source, self.position + count)


# Python lacks character type, so "str" will be used for both the sequence and
# the elements
@dataclass(frozen=True)
class StringReader(Reader[str]):
    """A reader for strings.

    Python's regular expressions and string operations only work on strings,
    not abstract "readers". This class defines the source as a string so that
    regular expressions (and string literals) can safely and efficiently work
    directly on the source using the position to determine where to start.

    Attributes:
        source (str): What will be parsed
        position (int): Current position in the source
    """

    source: str
    position: int = 0

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

    def _current_line(self) -> tuple[int, int, str, str]:
        # StringIO is not consistent in how it treats empty strings
        # and other strings not ending in newlines. Ensure that the
        # source always ends in a newline.
        # This also ensures that the loop below runs at least once
        # and that `line` always ends with a newline.
        if not self.source.endswith("\n"):
            source = self.source + "\n"
        else:
            source = self.source

        characters_consumed = 0
        for line_index, line in enumerate(StringIO(source)):  # noqa: B007
            if characters_consumed + len(line) > self.position:
                # The line with the error has been found
                character_index = self.position - characters_consumed
                break
            else:
                characters_consumed += len(line)
        else:
            # The error is at the end of the input
            # Put the pointer just beyond the last non-newline character
            character_index = len(line) - 1

        # This creates a line like this '   ^'
        pointer = " " * character_index + "^"

        # Add one to indexes to account for 0-indexes
        return line_index + 1, character_index + 1, line, pointer

    def expected_error(self, expected: Sequence[str]) -> str:
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
            next_string = "end of source"
        else:
            next_string = repr(self.next_token())

        line_index, character_index, line, pointer = self._current_line()

        return (
            f"Expected {expected_string} but found {next_string}\n"
            f"Line {line_index}, character {character_index}\n\n{line}{pointer}"
        )

    def recursion_error(self, repeated_parser: str) -> str:
        """Generate an error to indicate that infinite recursion was encountered.

        A parser can supply a representation of itself to this method and the
        reader will supply the context, including the location where the
        parser stalled.

        Args:
            repeated_parser: A representation of the repeated parser

        Returns:
            A full error message
        """
        line_index, character_index, line, pointer = self._current_line()

        return (
            f"Infinite recursion detected in {repeated_parser}; "
            "empty string was matched and will be matched forever\n"
            f"Line {line_index}, character {character_index}\n\n{line}{pointer}"
        )
