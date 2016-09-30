import re
from typing import Any

from .state import StringReader, Result, Success, Failure, Continue

# Global mutable state

default_whitespace = re.compile(r'\s*')
whitespace = None


# PyCharm does not understand type hint on handle_literal, so this signature is more general
def default_handle_literal(literal: Any):
    from .parsers import LiteralStringParser
    return LiteralStringParser(literal, whitespace)

handle_literal = default_handle_literal


def default_parse_method():
    freeze_whitespace = whitespace

    def regex_parse(self, source: str) -> Result:
        reader = StringReader(source)
        if freeze_whitespace is None:
            result = self.consume(reader)
        else:
            result = (self << freeze_whitespace).consume(reader)

        if isinstance(result, Continue):
            if result.remainder.finished:
                return Success(result.value)
            elif result.farthest is None:
                return Failure('end of source expected but {} found at {}'.format(
                    result.remainder.next_word(), result.remainder.position))
            else:
                return Failure(result.message())
        else:
            return Failure(result.message())

    return regex_parse

parse_method = default_parse_method()

__all__ = ['default_whitespace', 'whitespace', 'default_handle_literal', 'handle_literal', 'default_parse_method',
           'parse_method']
