__all__ = ["UntilParser", "until"]

from typing import Any, Generic

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser, wrap_literal


class UntilParser(Generic[Input], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Any]):
        super().__init__()
        self.parser = parser

    def _consume(self, state: State[Input], reader: Reader[Input]):
        start_position = reader.position
        while True:
            status = self.parser.consume(state, reader)

            if isinstance(status, Continue):
                break
            elif reader.finished:
                return status
            else:
                reader = reader.rest

        return Continue(reader, reader.source[start_position : reader.position])

    def __repr__(self):
        return self.name_or_nothing() + f"until({self.parser.name_or_repr()})"


def until(parser: Parser[Input, Output]) -> UntilParser:
    """Match everything until it matches the provided parser.

    This parser matches all input until it encounters a position in the input
    where the given ``parser`` succeeds.

    Args:
        parser: Parser or literal
    """
    return UntilParser(wrap_literal(parser))
