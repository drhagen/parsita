import re
from typing import Generic, Sequence, TypeVar, Callable, Optional

Input = TypeVar('Input')
Output = TypeVar('Output')
Convert = TypeVar('Convert')
Left = TypeVar('Left')
Right = TypeVar('Right')


class Reader(Generic[Input]):
    first = NotImplemented
    rest = NotImplemented
    position = NotImplemented
    finished = NotImplemented

    def __repr__(self):
        if self.finished:
            return "Reader(finished)"
        else:
            return "Reader({}@{})".format(self.first, self.position)


class SequenceReader(Reader):
    def __init__(self, source: Sequence[Input], position: int = 0):
        self.source = source
        self.position = position

    @property
    def first(self):
        return self.source[self.position]

    @property
    def rest(self):
        return SequenceReader(self.source, self.position + 1)

    @property
    def finished(self):
        return self.position >= len(self.source)


class StringReader(Reader[str]):  # Python lacks character type
    def __init__(self, source: str, position: int = 0):
        self.source = source
        self.position = position

    @property
    def first(self):
        return self.source[self.position]

    @property
    def rest(self):
        return StringReader(self.source, self.position + 1)

    @property
    def finished(self):
        return self.position >= len(self.source)

    def drop(self, count):
        return StringReader(self.source, self.position + count)

    next_word_regex = re.compile(r'[\(\)\[\]\{\}\"\']|\w+|[^\w\s\(\)\[\]\{\}\"\']+|\s+')

    def next_word(self):
        match = self.next_word_regex.match(self.source, self.position)
        return self.source[match.start():match.end()]

    def __repr__(self):
        if self.finished:
            return "StringReader(finished)"
        else:
            return "StringReader({}@{})".format(self.next_word(), self.position)


class Result(Generic[Output]):
    pass


class Success(Generic[Output], Result[Output]):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if isinstance(other, Success):
            return self.value == other.value
        else:
            return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self):
        return "Success({})".format(self.value)


class Failure(Generic[Output], Result[Output]):
    def __init__(self, message: str):
        self.message = message

    def __eq__(self, other):
        if isinstance(other, Failure):
            return self.message == other.message
        else:
            return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self):
        return "Failure({})".format(self.message)


class Status(Generic[Input, Output]):
    farthest = None  # type: Optional[int]
    message = NotImplemented  # type: Callable[[], str]

    def merge(self, status: 'Status[Input, None]'):
        raise NotImplementedError()


class Continue(Generic[Input, Output], Status[Input, Output]):
    def __init__(self, value: Output, remainder: Reader[Input]):
        self.value = value
        self.remainder = remainder

    def merge(self, status: Status[Input, None]):
        if status is not None and status.farthest is not None \
                and (self.farthest is None or status.farthest >= self.farthest) \
                and status.farthest >= self.remainder.position:
            self.farthest = status.farthest
            self.message = status.message
        return self

    def __eq__(self, other):
        if isinstance(other, Continue):
            return self.value == other.value and self.remainder == other.remainder
        else:
            return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self):
        return "Continue({}, {})".format(self.value, self.remainder)


class Backtrack(Generic[Input], Status[Input, None]):
    def __init__(self, farthest: int, message: Callable[[], str]):
        self.farthest = farthest
        self.message = message

    def merge(self, status: Status[Input, None]):
        if status is not None and status.farthest is not None and \
                (self.farthest is None or status.farthest >= self.farthest):
            self.farthest = status.farthest
            self.message = status.message
        return self

    def __eq__(self, other):
        if isinstance(other, Backtrack):
            return self.farthest == other.farthest and self.message == other.message
        else:
            return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self):
        return "Backtrack({})".format(self.message())


class Stop(Generic[Input], Status[Input, None]):
    def __init__(self, message: Callable[[], str], remainder: Reader[Input]):
        self.farthest = remainder.position
        self.message = message
        self.remainder = remainder

    def merge(self, status: Status[Input, None]):
        return self

    def __eq__(self, other):
        if isinstance(other, Stop):
            return self.farthest == other.farthest and self.message == other.message
        else:
            return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self):
        return "Stop({})".format(self.message())

__all__ = ['Input', 'Output', 'Convert', 'Left', 'Right',
           'Reader', 'SequenceReader', 'StringReader',
           'Result', 'Success', 'Failure', 'Status', 'Continue', 'Backtrack', 'Stop']
