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
                    result.remainder.next_token(), result.remainder.position))
            else:
                return Failure(result.message())
        else:
            return Failure(result.message())

    return regex_parse


def basic_parse(self, source: Sequence[Input]) -> Result[Output]:
    reader = SequenceReader(source)
    result = self.consume(reader)

    if isinstance(result, Continue):
        if result.remainder.finished:
            return Success(result.value)
        elif result.farthest is None:
            return Failure('end of source expected but {} found at {}'.format(
                result.remainder.first, result.remainder.position))
        else:
            return Failure(result.message())
    else:
        return Failure(result.message())


parse_method = default_parse_method()


__all__ = ['default_whitespace', 'whitespace', 'default_handle_literal', 'wrap_literal', 'handle_literal',
           'default_parse_method', 'basic_parse', 'parse_method']
