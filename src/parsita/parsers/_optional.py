__all__ = ["OptionalParser", "opt"]

from typing import Generic, List, Sequence, Union

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser
from ._literal import lit


class OptionalParser(Generic[Input, Output], Parser[Input, List[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, state: State, reader: Reader[Input]):
        status = self.parser.cached_consume(state, reader)

        if isinstance(status, Continue):
            return Continue(status.remainder, [status.value])
        else:
            return Continue(reader, [])

    def __repr__(self):
        return self.name_or_nothing() + f"opt({self.parser.name_or_repr()})"


def opt(parser: Union[Parser[Input, Output], Sequence[Input]]) -> OptionalParser[Input, Output]:
    """Optionally match a parser.

    An ``OptionalParser`` attempts to match ``parser``. If it succeeds, it
    returns a list of length one with the value returned by the parser as the
    only element. If it fails, it returns an empty list.

    Args:
        parser: Parser or literal
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return OptionalParser(parser)
