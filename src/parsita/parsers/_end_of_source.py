__all__ = ["EndOfSourceParser", "eof"]

from typing import Generic, Optional

from ..state import Continue, Input, Reader, State
from ._base import Parser


class EndOfSourceParser(Generic[Input], Parser[Input, None]):
    def __init__(self):
        super().__init__()

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, None]]:
        if reader.finished:
            return Continue(reader, None)
        else:
            state.register_failure("end of source", reader)
            return None

    def __repr__(self):
        return self.name_or_nothing() + "eof"


eof = EndOfSourceParser()
