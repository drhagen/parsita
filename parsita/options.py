import re
from typing import Any, Sequence

from .state import Input, Output, SequenceReader, StringReader, Result, Success, Failure, Continue

# Global mutable state

default_whitespace = re.compile(r'\s*')
whitespace = None


# PyCharm does not understand type hint on handle_literal, so this signature is more general
def default_handle_literal(literal: Any):
    from .parsers import LiteralStringParser
    return LiteralStringParser(literal, whitespace)


def wrap_literal(literal: Input):
    from .parsers import LiteralParser
    return LiteralParser(literal)


handle_literal = default_handle_literal


def default_parse_method(self, source: str) -> Result[Output]:
    from .parsers import eof

    reader = StringReader(source)
    result = (self << eof).consume(reader)

    if isinstance(result, Continue):
         return Success(result.value)
    else:
        return Failure(result.farthest.expected_error(' or '.join(map(lambda x: x(), result.expected))))


def basic_parse(self, source: Sequence[Input]) -> Result[Output]:
    from .parsers import eof

    reader = SequenceReader(source)
    result = (self << eof).consume(reader)

    if isinstance(result, Continue):
        return Success(result.value)
    else:
        return Failure(result.farthest.expected_error(' or '.join(map(lambda x: x(), result.expected))))


parse_method = default_parse_method

__all__ = ['default_whitespace', 'whitespace', 'default_handle_literal', 'wrap_literal', 'handle_literal',
           'default_parse_method', 'basic_parse', 'parse_method']
