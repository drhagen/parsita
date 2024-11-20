__all__ = ["RegexParser", "reg"]

import re
from typing import Any, Generic, Optional, TypeVar, Union, no_type_check

from .. import options
from ..state import Continue, State, StringReader
from ._base import Parser

StringType = TypeVar("StringType", str, bytes)


# The Element type is str for str and int for bytes, but there is no way to
# express that in Python.
class RegexParser(Generic[StringType], Parser[Any, StringType]):
    def __init__(
        self,
        pattern: re.Pattern[StringType],
        whitespace: Optional[Parser[StringType, object]] = None,
    ):
        super().__init__()
        self.pattern: re.Pattern[StringType] = pattern
        self.whitespace: Optional[Parser[StringType, object]] = whitespace

    # RegexParser is special in that is assumes StringReader is the only
    # possible reader for strings and bytes. This is technically unsound.
    @no_type_check
    def _consume(
        self,
        state: State,
        reader: StringReader,
    ) -> Optional[Continue[StringType, StringType]]:
        if self.whitespace is not None:
            status = self.whitespace.consume(state, reader)
            reader = status.remainder

        match = self.pattern.match(reader.source, reader.position)

        if match is None:
            state.register_failure(f"r'{self.pattern.pattern}'", reader)
            return None
        else:
            value = reader.source[match.start() : match.end()]
            reader = reader.drop(len(value))

            if self.whitespace is not None:
                status = self.whitespace.consume(state, reader)
                reader = status.remainder

            return Continue(reader, value)

    def __repr__(self) -> str:
        return self.name_or_nothing() + f"reg({self.pattern.pattern!r})"


def reg(pattern: Union[re.Pattern[StringType], StringType]) -> RegexParser[StringType]:
    """Match with a regular expression.

    This matches the text with a regular expression. The regular expressions is
    treated as greedy. Backtracking in the parser combinators does not flow into
    regular expression backtracking.

    Args:
        pattern: str, bytes, or python regular expression.
    """
    return RegexParser(re.compile(pattern), options.whitespace)
