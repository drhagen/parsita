__all__ = ["UntilParser", "until"]

from typing import Any, Generic, Optional, Sequence, Union

from ..state import Continue, Element, Reader, State
from ._base import Parser, wrap_literal


class UntilParser(Generic[Element], Parser[Element, Sequence[Element]]):
    def __init__(self, parser: Parser[Element, Any]):
        super().__init__()
        self.parser = parser

    def _consume(
        self, state: State, reader: Reader[Element]
    ) -> Optional[Continue[Element, Sequence[Element]]]:
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

    def __repr__(self) -> str:
        return self.name_or_nothing() + f"until({self.parser.name_or_repr()})"


def until(parser: Union[Parser[Element, object], Sequence[Element]]) -> UntilParser[Element]:
    """Match everything until it matches the provided parser.

    This parser matches all Element until it encounters a position in the Element
    where the given ``parser`` succeeds.

    Args:
        parser: Parser or literal
    """
    return UntilParser(wrap_literal(parser))
