__all__ = ["ConversionParser", "TransformationParser"]

from typing import Callable, Generic, Optional, TypeVar

from ..state import Continue, Input, Reader, State
from ._base import Parser

Output = TypeVar("Output")
Convert = TypeVar("Convert", covariant=True)


class ConversionParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(self, parser: Parser[Input, Output], converter: Callable[[Output], Convert]):
        super().__init__()
        self.parser = parser
        self.converter = converter

    def _consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Convert]]:
        status = self.parser.consume(state, reader)

        if isinstance(status, Continue):
            return Continue(status.remainder, self.converter(status.value))
        else:
            return None

    def __repr__(self) -> str:
        return self.name_or_nothing() + f"{self.parser!r} > {self.converter.__name__}"


class TransformationParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(
        self,
        parser: Parser[Input, Output],
        transformer: Callable[[Output], Parser[Input, Convert]],
    ):
        super().__init__()
        self.parser = parser
        self.transformer = transformer

    def _consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Convert]]:
        status = self.parser.consume(state, reader)

        if isinstance(status, Continue):
            return self.transformer(status.value).consume(state, status.remainder)
        else:
            return status

    def __repr__(self) -> str:
        string = f"{self.parser.name_or_repr()} >= {self.transformer.__name__}"
        return self.name_or_nothing() + string
