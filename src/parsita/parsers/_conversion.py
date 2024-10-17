__all__ = ["ConversionParser", "TransformationParser"]

from typing import Callable, Generic, Optional, TypeVar

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser

Convert = TypeVar("Convert")


class ConversionParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(self, parser: Parser[Input, Output], converter: Callable[[Output], Convert]):
        super().__init__()
        self.parser = parser
        self.converter = converter

    def _consume(
        self, state: State[Input], reader: Reader[Input]
    ) -> Optional[Continue[Input, Convert]]:
        status = self.parser.consume(state, reader)

        if isinstance(status, Continue):
            return Continue(status.remainder, self.converter(status.value))
        else:
            return None

    def __repr__(self):
        return self.name_or_nothing() + repr(self.parser)


class TransformationParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(
        self,
        parser: Parser[Input, Output],
        transformer: Callable[[Output], Parser[Input, Convert]],
    ):
        super().__init__()
        self.parser = parser
        self.transformer = transformer

    def _consume(
        self, state: State[Input], reader: Reader[Input]
    ) -> Optional[Continue[Input, Convert]]:
        status = self.parser.consume(state, reader)

        if isinstance(status, Continue):
            return self.transformer(status.value).consume(state, status.remainder)
        else:
            return status

    def __repr__(self) -> str:
        string = f"{self.parser.name_or_repr()} >= {self.transformer.__name__}"
        return self.name_or_nothing() + string
