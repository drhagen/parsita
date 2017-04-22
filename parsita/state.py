import re
from typing import Generic, Sequence, TypeVar, Callable, Optional  # noqa: F401

Input = TypeVar('Input')
Output = TypeVar('Output')
Convert = TypeVar('Convert')


class Reader(Generic[Input]):
    """Abstract base class for readers.

    A ``Reader`` is an immutable object holding the state of parsing.

    Attributes:
        first (Input): The element at the current position.
        rest (Sequence[Input]): A ``Reader`` at the next position.
        position (int): How many characters into the source the parsing has
            gone.
        finished (bool): Indicates if the source is at the end. It is an error
            to access ``first`` or ``rest`` if ``finished`` is ``True``.
    """
    first = NotImplemented  # type: Input
    rest = NotImplemented  # type: Reader[Input]
    position = NotImplemented  # type: int
    finished = NotImplemented  # type: bool

    def next_token(self):
        return self.first

    def __repr__(self):
        if self.finished:
            return 'Reader(finished)'
        else:
            return 'Reader({}@{})'.format(self.first, self.position)


class SequenceReader(Reader):
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
    def rest(self) -> 'SequenceReader[Input]':
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
    def rest(self) -> 'StringReader[str]':
        return StringReader(self.source, self.position + 1)

    @property
    def finished(self) -> bool:
        return self.position >= len(self.source)

    def drop(self, count: int) -> 'StringReader[Input]':
        return StringReader(self.source, self.position + count)

    next_token_regex = re.compile(r'[\(\)\[\]\{\}\"\']|\w+|[^\w\s\(\)\[\]\{\}\"\']+|\s+')

    def next_token(self) -> str:
        match = self.next_token_regex.match(self.source, self.position)
        return self.source[match.start():match.end()]

    def __repr__(self):
        if self.finished:
            return 'StringReader(finished)'
        else:
            return 'StringReader({}@{})'.format(self.next_token(), self.position)


class Result(Generic[Output]):
    """Abstract algebraic base class for ``Success`` and ``Failure``.

    The class of all values returned from Parser.parse.
    """
    def or_die(self):
        raise NotImplementedError()


class Success(Generic[Output], Result[Output]):
    """Parsing succeeded.

    Returned from Parser.parse when the parser matched the source entirely.

    Attributes:
        value (Output): The value returned from the parser.
    """
    def __init__(self, value: Output):
        self.value = value

    def or_die(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, Success):
            return self.value == other.value
        else:
            return NotImplemented

    def __repr__(self):
        return 'Success({})'.format(repr(self.value))


class Failure(Generic[Output], Result[Output]):
    """Parsing failed.

    Returned from Parser.parse when the parser did not match the source or the
    source was not completely consumed.

    Attributes:
        message (str): A human-readable error from the farthest point reached
            during parsing.
    """
    def __init__(self, message: str):
        self.message = message

    def or_die(self):
        raise ValueError(self.message)

    def __eq__(self, other):
        if isinstance(other, Failure):
            return self.message == other.message
        else:
            return NotImplemented

    def __repr__(self):
        return 'Failure({})'.format(repr(self.message))


class Status(Generic[Input, Output]):
    farthest = None  # type: Optional[int]
    message = NotImplemented  # type: Callable[[], str]

    def merge(self, status: 'Status[Input, Output]'):
        raise NotImplementedError()


class Continue(Generic[Input, Output], Status[Input, Output]):
    def __init__(self, value: Output, remainder: Reader[Input]):
        self.value = value
        self.remainder = remainder

    def merge(self, status: Status[Input, Output]):
        if (status is not None and status.farthest is not None and
                (self.farthest is None or status.farthest >= self.farthest) and
                status.farthest >= self.remainder.position):
            self.farthest = status.farthest
            self.message = status.message
        return self

    def __repr__(self):
        return 'Continue({}, {})'.format(repr(self.value), repr(self.remainder))


class Backtrack(Generic[Input], Status[Input, None]):
    def __init__(self, farthest: int, message: Callable[[], str]):
        self.farthest = farthest
        self.message = message

    def merge(self, status: Status[Input, None]):
        if (status is not None and status.farthest is not None and
                (self.farthest is None or status.farthest >= self.farthest)):
            self.farthest = status.farthest
            self.message = status.message
        return self

    def __repr__(self):
        return 'Backtrack({}, {})'.format(repr(self.farthest), repr(self.message()))


__all__ = ['Input', 'Output', 'Convert',
           'Reader', 'SequenceReader', 'StringReader',
           'Result', 'Success', 'Failure', 'Status', 'Continue', 'Backtrack']
