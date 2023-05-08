__all__ = ["SequentialParser", "DiscardLeftParser", "DiscardRightParser"]

from typing import Any, Generic, List

from ..reader import Reader
from ..state import Continue, Input, Output, State
from ._base import Parser


class SequentialParser(Generic[Input], Parser[Input, List[Any]]):  # Type of this class is inexpressible
    def __init__(self, parser: Parser[Input, Any], *parsers: Parser[Input, Any]):
        super().__init__()
        self.parsers = (parser,) + tuple(parsers)

    def consume(self, state: State, reader: Reader[Input]):
        output = []
        remainder = reader

        for parser in self.parsers:
            status = parser.cached_consume(state, remainder)
            if isinstance(status, Continue):
                output.append(status.value)
                remainder = status.remainder
            else:
                return None

        return Continue(remainder, output)

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + " & ".join(names)


class DiscardLeftParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, Any], right: Parser[Input, Output]):
        super().__init__()
        self.left = left
        self.right = right

    def consume(self, state: State, reader: Reader[Input]):
        status = self.left.cached_consume(state, reader)
        if isinstance(status, Continue):
            return self.right.cached_consume(state, status.remainder)
        else:
            return None

    def __repr__(self):
        return self.name_or_nothing() + f"{self.left.name_or_repr()} >> {self.right.name_or_repr()}"


class DiscardRightParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, Output], right: Parser[Input, Any]):
        super().__init__()
        self.left = left
        self.right = right

    def consume(self, state: State, reader: Reader[Input]):
        status1 = self.left.cached_consume(state, reader)
        if isinstance(status1, Continue):
            status2 = self.right.cached_consume(state, status1.remainder)
            if isinstance(status2, Continue):
                return Continue(status2.remainder, status1.value)
            else:
                return None
        else:
            return None

    def __repr__(self):
        return self.name_or_nothing() + f"{self.left.name_or_repr()} << {self.right.name_or_repr()}"
