__all__ = ["LiteralParser", "lit"]

from typing import Generic, Optional, Sequence

from .. import options
from ..state import Continue, Element, Reader, State, StringReader
from ._base import Parser


class LiteralParser(Generic[Element], Parser[Element, Sequence[Element]]):
    def __init__(
        self, pattern: Sequence[Element], whitespace: Optional[Parser[Element, object]] = None
    ):
        super().__init__()
        self.pattern = pattern
        self.whitespace = whitespace

    def _consume(
        self, state: State, reader: Reader[Element]
    ) -> Optional[Continue[Element, Sequence[Element]]]:
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


def lit(
    literal: Sequence[Element], *literals: Sequence[Element]
) -> Parser[Element, Sequence[Element]]:
    """Match a literal sequence.

    This parser returns successfully if the subsequence of the parsing Element
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
