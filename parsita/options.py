import re

from .state import StringReader, Success, Failure, Continue

# Global mutable state

default_whitespace = re.compile('\s*')
whitespace = None


def wrap_literal_with_whitespace(literal):
    from .parsers import LiteralStringParser
    return LiteralStringParser(literal, whitespace)

handle_literal = wrap_literal_with_whitespace


def default_parse():
    freeze_whitespace = whitespace

    def regex_parse(self, source: str):
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

parse_method = default_parse()


