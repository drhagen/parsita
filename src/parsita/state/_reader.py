from __future__ import annotations

__all__ = ["Reader", "SequenceReader", "StringReader", "BytesReader"]

import re
from dataclasses import dataclass
from io import StringIO
from typing import Generic, Sequence, Tuple, TypeVar

Input = TypeVar("Input")


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

    # Despite what mypy says, these cannot be converted to properties because
    # they will break the dataclass attributes of the subclasses.
    first: Input
    rest: Reader[Input]
    position: int
    finished: bool
    source: Sequence[Input]

    def drop(self, count: int) -> Reader[Input]:
        """Advance the reader by a ``count`` elements.

        Both ``SequenceReader`` and ``StringReader`` override this method with a
        more efficient implementation.
        """
        rest = self
        for _ in range(count):
            rest = rest.rest
        return rest

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


@dataclass(frozen=True)
class SequenceReader(Reader[Input]):
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
        return self.__class__(self.source, self.position + 1)

    @property
    def finished(self) -> bool:
        return self.position >= len(self.source)

    def drop(self, count: int) -> SequenceReader[Input]:
        return self.__class__(self.source, self.position + count)


@dataclass(frozen=True)
class BytesReader(SequenceReader):
    """
    A reader for bytes.
    """

    @staticmethod
    def get_printable_form_of_byte(byte: int) -> str:
        if byte < 33 or byte > 126:
            return f"{byte:02x}"
        else:
            return chr(byte)

    def get_error_feedback_for_bytes(self) -> Tuple[int, str, str]:
        # bytes are different.  since there's no newlines, we'll report the number of bytes until the error position,
        # then the three previous bytes, the error position, and then the next 10 bytes before we show the number of
        # bytes remaining in the buffer.
        #
        # everything will be printed as spaced hex, because, you know, why not?

        if not isinstance(self.source, bytes):
            raise TypeError("get_error_feedback_for_bytes can only be called on a StringReader with a bytes source")

        current_position = self.position

        prior_bytes = self.source[:current_position]
        prefix = ""
        if len(prior_bytes) > 3:
            prior_byte_count_before_3 = len(prior_bytes) - 3
            prefix = f"{prior_byte_count_before_3} Bytes …"

        immediately_prior_bytes = prior_bytes[-3:]
        printable_immediately_prior_bytes = [self.get_printable_form_of_byte(b) for b in immediately_prior_bytes]
        printable_immediately_prior_bytes_joined = " ".join(printable_immediately_prior_bytes)
        prefix = f"{prefix} {printable_immediately_prior_bytes_joined}"

        if len(self.source) == current_position:
            printable_current_byte = "<EOF>"
        else:
            current_byte = self.source[current_position]
            printable_current_byte = self.get_printable_form_of_byte(current_byte)

        following_bytes = self.source[current_position + 1 :]
        suffix = ""

        if len(following_bytes) > 10:
            following_byte_count_after_10 = len(following_bytes) - 10
            suffix = f" … {following_byte_count_after_10} Bytes"

        immediately_following_bytes = following_bytes[:10]
        printable_immediately_following_bytes = [
            self.get_printable_form_of_byte(b) for b in immediately_following_bytes
        ]
        printable_immediately_following_bytes_joined = " ".join(printable_immediately_following_bytes)
        suffix = f"{printable_immediately_following_bytes_joined}{suffix}"

        error_line = f"{prefix} {printable_current_byte} {suffix}"

        pointer_prefix = f'{" " * (len(prefix))}'
        pointer = f"{'^' * len(printable_current_byte)}"
        pointer_suffix = f'{" " * (len(suffix))}'
        pointer_line = f"{pointer_prefix} {pointer} {pointer_suffix}"

        return current_position + 1, error_line + "\n", pointer_line + "\n"

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
        current_position, error_line, pointer_line = self.get_error_feedback_for_bytes()

        expected_string = " or ".join(expected)

        if self.finished:
            message = f"Expected {expected_string} but found end of source"
        else:
            printable_next_token = self.get_printable_form_of_byte(self.next_token())
            message = f"{expected_string} at position {current_position}, but found {printable_next_token}"

        return f"{message}\n{error_line}{pointer_line}"


# Python lacks character type, so "str" will be used for both the sequence and the elements
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

    def current_line(self) -> Tuple[int, int, str, str]:
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
