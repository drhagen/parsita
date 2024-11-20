__all__ = ["LiteralParser", "lit"]

from typing import Any, Generic, Optional, Sequence, TypeVar, Union, overload

from .. import options
from ..state import Continue, Element, Reader, State, StringReader
from ._base import Parser

# The bound should be Sequence[Element], but mypy doesn't support higher-kinded types.
Literal = TypeVar("Literal", bound=Sequence[Any], covariant=True)


class LiteralParser(Generic[Element, Literal], Parser[Element, Literal]):
    def __init__(self, pattern: Literal, whitespace: Optional[Parser[Element, object]] = None):
        super().__init__()
        self.pattern = pattern
        self.whitespace = whitespace

    def _consume(
        self, state: State, reader: Reader[Element]
    ) -> Optional[Continue[Element, Literal]]:
        if self.whitespace is not None:
            status = self.whitespace.consume(state, reader)
            reader = status.remainder  # type: ignore  # whitespace is infallible

        if isinstance(reader, StringReader):
            if reader.source.startswith(self.pattern, reader.position):  # type: ignore
                reader = reader.drop(len(self.pattern))  # type: ignore
            else:
                state.register_failure(repr(self.pattern), reader)
                return None
        else:
            for elem in self.pattern:
                if reader.finished:
                    state.register_failure(str(elem), reader)
                    return None
                elif elem == reader.first:
                    reader = reader.rest
                else:
                    state.register_failure(str(elem), reader)
                    return None

        if self.whitespace is not None:
            status = self.whitespace.consume(state, reader)
            reader = status.remainder  # type: ignore  # whitespace is infallible

        return Continue(reader, self.pattern)

    def __repr__(self) -> str:
        return self.name_or_nothing() + repr(self.pattern)


FunctionLiteral = TypeVar("FunctionLiteral", bound=Sequence[Any])


@overload
def lit(literal: str, *literals: str) -> Parser[str, str]: ...


@overload
def lit(literal: bytes, *literals: bytes) -> Parser[int, bytes]: ...


@overload
def lit(literal: FunctionLiteral, *literals: FunctionLiteral) -> Parser[Any, FunctionLiteral]: ...


def lit(
    literal: Union[FunctionLiteral, str, bytes], *literals: Union[FunctionLiteral, str, bytes]
) -> Parser[Element, object]:
    """Match a literal sequence.

    This parser returns successfully if the subsequence of the parsing input
    matches the literal sequence provided.

    If multiple literals are provided, they are treated as alternatives. e.g.
    ``lit('+', '-')`` is the same as ``lit('+') | lit('-')``.

    Args:
        literal: A literal to match
        *literals: Alternative literals to match

    Returns:
        A ``LiteralParser`` if a single argument is provided, and an
        ``AlternativeParser`` if multiple arguments are provided.
    """
    if len(literals) > 0:
        from ._alternative import LongestAlternativeParser

        return LongestAlternativeParser(
            LiteralParser(literal, options.whitespace),
            *(LiteralParser(literal_i, options.whitespace) for literal_i in literals),
        )
    else:
        return LiteralParser(literal, options.whitespace)
