__all__ = ["RegexParser", "reg"]

import re
from typing import Generic, Optional, TypeVar, Union

from .. import options
from ..state import Continue, Reader, State
from ._base import Parser

StringType = TypeVar("StringType", str, bytes)


class RegexParser(Generic[StringType], Parser[StringType, StringType]):
    def __init__(self, pattern: re.Pattern, whitespace: Optional[Parser[StringType, None]] = None):
        super().__init__()
        self.pattern = pattern
        self.whitespace = whitespace

    def consume(self, state: State[StringType], reader: Reader[StringType]):
        if self.whitespace is not None:
            status = self.whitespace.cached_consume(state, reader)
            reader = status.remainder

        match = self.pattern.match(reader.source, reader.position)

        if match is None:
            state.register_failure(f"r'{self.pattern.pattern}'", reader)
            return None
        else:
            value = reader.source[match.start() : match.end()]
            reader = reader.drop(len(value))

            if self.whitespace is not None:
                status = self.whitespace.cached_consume(state, reader)
                reader = status.remainder

            return Continue(reader, value)

    def __repr__(self):
        return self.name_or_nothing() + f"reg(r'{self.pattern.pattern}')"


def reg(pattern: Union[re.Pattern, StringType]) -> RegexParser[StringType]:
    """Match with a regular expression.

    This matches the text with a regular expression. The regular expressions is
    treated as greedy. Backtracking in the parser combinators does not flow into
    regular expression backtracking.

    Args:
        pattern: str, bytes, or python regular expression.
    """
    return RegexParser(re.compile(pattern), options.whitespace)
