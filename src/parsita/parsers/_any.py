__all__ = ["AnyParser", "any1"]

from typing import Generic, Optional

from ..state import Continue, Input, Reader, State
from ._base import Parser


class AnyParser(Generic[Input], Parser[Input, Input]):
    """Match any single element.

    This parser matches any single element, returning it. This is useful when it
    does not matter what is at this position or when validation is deferred to a
    later step, such as with the ``pred`` parser. This parser can only fail at
    the end of the stream.
    """

    def __init__(self):
        super().__init__()

    def consume(
        self, state: State[Input], reader: Reader[Input]
    ) -> Optional[Continue[Input, Input]]:
        if reader.finished:
            state.register_failure("anything", reader)
            return None
        else:
            return Continue(reader.rest, reader.first)

    def __repr__(self):
        return self.name_or_nothing() + "any1"


any1 = AnyParser()
