__all__ = [
    "default_whitespace",
    "whitespace",
    "default_handle_literal",
    "wrap_literal",
    "handle_literal",
    "default_parse_method",
    "basic_parse",
    "parse_method",
]
import re
from typing import Any, Sequence, Union

from .state import Input, Output, Reader, Result, SequenceReader, StringReader

# Global mutable state

default_whitespace = re.compile(r"\s*")
whitespace = None


# PyCharm does not understand type hint on handle_literal, so this signature is more general
def default_handle_literal(literal: Any):
    from .parsers import LiteralStringParser

    return LiteralStringParser(literal, whitespace)


def wrap_literal(literal: Sequence[Input]):
    from .parsers import LiteralParser

    return LiteralParser(literal)


handle_literal = default_handle_literal


def default_parse_method(self, source: str) -> Result[Output]:
    from .parsers import completely_parse_reader

    reader = StringReader(source)

    return completely_parse_reader(self, reader)


def basic_parse(self, source: Union[Sequence[Input], Reader, bytes]) -> Result[Output]:
    from .parsers import completely_parse_reader

    if isinstance(source, Reader):
        reader = source
    elif isinstance(source, bytes):
        from parsita.state import BytesReader

        reader = BytesReader(source)
    else:
        reader = SequenceReader(source)

    return completely_parse_reader(self, reader)


parse_method = default_parse_method
