__all__ = ["EndOfSourceParser", "eof"]

from typing import Optional, TypeVar

from ..state import Continue, Reader, State
from ._base import Parser

FunctionInput = TypeVar("FunctionInput")


class EndOfSourceParser(Parser[object, None]):
    def __init__(self) -> None:
        super().__init__()

    def _consume(
        self, state: State, reader: Reader[FunctionInput]
    ) -> Optional[Continue[FunctionInput, None]]:
        if reader.finished:
            return Continue(reader, None)
        else:
            state.register_failure("end of source", reader)
            return None

    def __repr__(self) -> str:
        return self.name_or_nothing() + "eof"


eof = EndOfSourceParser()
