__all__ = ["OptionalParser", "opt"]

from typing import Generic, Sequence, Union, overload

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser, wrap_literal


class OptionalParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def _consume(self, state: State, reader: Reader[Input]) -> Continue[Input, Sequence[Output]]:
        status = self.parser.consume(state, reader)

        if isinstance(status, Continue):
            return Continue(status.remainder, [status.value])
        else:
            return Continue(reader, [])

    def __repr__(self) -> str:
        return self.name_or_nothing() + f"opt({self.parser.name_or_repr()})"


@overload
def opt(
    parser: Sequence[Input],
) -> OptionalParser[Input, Sequence[Input]]: ...


@overload
def opt(
    parser: Parser[Input, Output],
) -> OptionalParser[Input, Output]: ...


def opt(
    parser: Union[Parser[Input, Output], Sequence[Input]],
) -> OptionalParser[Input, object]:
    """Optionally match a parser.

    An ``OptionalParser`` attempts to match ``parser``. If it succeeds, it
    returns a list of length one with the value returned by the parser as the
    only element. If it fails, it returns an empty list.

    Args:
        parser: Parser or literal
    """
    return OptionalParser(wrap_literal(parser))
