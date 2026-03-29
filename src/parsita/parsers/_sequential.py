__all__ = ["DiscardLeftParser", "DiscardRightParser", "SequentialParser", "seq"]

from typing import Any, Generic, Optional, Sequence, Union

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser, wrap_literal


# Type of this class is inexpressible
class SequentialParser(Generic[Input], Parser[Input, Sequence[Any]]):
    def __init__(self, *parsers: Parser[Input, Any]):
        super().__init__()
        self.parsers = parsers

    def _consume(
        self, state: State, reader: Reader[Input]
    ) -> Optional[Continue[Input, Sequence[Any]]]:
        output = []
        remainder = reader

        for parser in self.parsers:
            status = parser.consume(state, remainder)
            if isinstance(status, Continue):
                output.append(status.value)
                remainder = status.remainder
            else:
                return None

        return Continue(remainder, output)

    def __repr__(self) -> str:
        if len(self.parsers) == 0:
            return self.name_or_nothing() + "seq()"
        else:
            names = []
            for parser in self.parsers:
                names.append(parser.name_or_repr())

            return self.name_or_nothing() + " & ".join(names)


class DiscardLeftParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, object], right: Parser[Input, Output]):
        super().__init__()
        self.left = left
        self.right = right

    def _consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        status = self.left.consume(state, reader)
        if isinstance(status, Continue):
            return self.right.consume(state, status.remainder)
        else:
            return None

    def __repr__(self) -> str:
        string = f"{self.left.name_or_repr()} >> {self.right.name_or_repr()}"
        return self.name_or_nothing() + string


class DiscardRightParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, Output], right: Parser[Input, object]):
        super().__init__()
        self.left = left
        self.right = right

    def _consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        status1 = self.left.consume(state, reader)
        if isinstance(status1, Continue):
            status2 = self.right.consume(state, status1.remainder)
            if isinstance(status2, Continue):
                return Continue(status2.remainder, status1.value)
            else:
                return None
        else:
            return None

    def __repr__(self) -> str:
        string = f"{self.left.name_or_repr()} << {self.right.name_or_repr()}"
        return self.name_or_nothing() + string


def seq(
    *parsers: Union[Parser[Input, Any], Sequence[Input]],
) -> SequentialParser[Input]:
    """Match a sequence of parsers, returning a list of all results.

    A ``SequentialParser`` matches each parser in order and returns a list of
    all the values returned by each parser.

    This function is syntactic sugar for the ``&`` operator.
    ``parser1 & parser2`` is equivalent to ``seq(parser1, parser2)``, except
    that the ``&`` operator performs a bit of magic to flatten nested
    ``SequentialParser``s such as ``parser1 & parser2 & parser3`` into
    ``seq(parser1, parser2, parser3)`` instead of
    ``seq(seq(parser1, parser2), parser3)`` as might be expected from the
    Python operator precedence rules.

    Args:
        *parsers: ``Parser``s or literals to match in order
    """
    cleaned_parsers = [wrap_literal(parser_i) for parser_i in parsers]
    return SequentialParser(*cleaned_parsers)
