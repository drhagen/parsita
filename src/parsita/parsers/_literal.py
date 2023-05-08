__all__ = ["LiteralParser", "LiteralStringParser", "lit"]

from typing import Generic, Optional, Sequence

from .. import options
from ..reader import Reader, StringReader
from ..state import Continue, Input, State
from ._base import Parser


class LiteralParser(Generic[Input], Parser[Input, Input]):
    def __init__(self, pattern: Sequence[Input]):
        super().__init__()
        self.pattern = pattern

    def consume(self, state: State, reader: Reader[Input]):
        remainder = reader
        for elem in self.pattern:
            if remainder.finished:
                state.register_failure(str(elem), remainder)
                return None
            elif elem == remainder.first:
                remainder = remainder.rest
            else:
                state.register_failure(str(elem), remainder)
                return None

        return Continue(remainder, self.pattern)

    def __repr__(self):
        return self.name_or_nothing() + repr(self.pattern)


class LiteralStringParser(Parser[str, str]):
    def __init__(self, pattern: str, whitespace: Optional[Parser[str, None]] = None):
        super().__init__()
        self.whitespace = whitespace
        self.pattern = pattern

    def consume(self, state: State, reader: StringReader):
        if self.whitespace is not None:
            status = self.whitespace.cached_consume(state, reader)
            reader = status.remainder

        if reader.source.startswith(self.pattern, reader.position):
            reader = reader.drop(len(self.pattern))

            if self.whitespace is not None:
                status = self.whitespace.cached_consume(state, reader)
                reader = status.remainder

            return Continue(reader, self.pattern)
        else:
            state.register_failure(repr(self.pattern), reader)
            return None

    def __repr__(self):
        return self.name_or_nothing() + repr(self.pattern)


def lit(literal: Sequence[Input], *literals: Sequence[Input]) -> Parser[str, str]:
    """Match a literal sequence.

    In the `TextParsers`` context, this matches the literal string
    provided. In the ``GeneralParsers`` context, this matches a sequence of
    input.

    If multiple literals are provided, they are treated as alternatives. e.g.
    ``lit('+', '-')`` is the same as ``lit('+') | lit('-')``.

    Args:
        literal: A literal to match
        *literals: Alternative literals to match

    Returns:
        A ``LiteralParser`` in the ``GeneralContext``, a ``LiteralStringParser``
        in the ``TextParsers`` context, and an ``AlternativeParser`` if multiple
        arguments are provided.
    """
    if len(literals) > 0:
        from ._alternative import AlternativeParser

        return AlternativeParser(options.handle_literal(literal), *map(options.handle_literal, literals))
    else:
        return options.handle_literal(literal)
