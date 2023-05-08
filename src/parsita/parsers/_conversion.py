__all__ = ["ConversionParser", "TransformationParser"]

from typing import Callable, Generic, Optional, TypeVar

from ..reader import Reader
from ..state import Continue, Input, Output, State
from ._base import Parser

Convert = TypeVar("Convert")


class ConversionParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(self, parser: Parser[Input, Output], converter: Callable[[Output], Convert]):
        super().__init__()
        self.parser = parser
        self.converter = converter

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Convert]]:
        status = self.parser.cached_consume(state, reader)

        if isinstance(status, Continue):
            return Continue(status.remainder, self.converter(status.value))
        else:
            return None

    def __repr__(self):
        return self.name_or_nothing() + repr(self.parser)


class TransformationParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(self, parser: Parser[Input, Output], transformer: Callable[[Output], Parser[Output, Convert]]):
        super().__init__()
        self.parser = parser
        self.transformer = transformer

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Convert]]:
        status = self.parser.cached_consume(state, reader)

        if isinstance(status, Continue):
            return self.transformer(status.value).cached_consume(state, status.remainder)
        else:
            return status
