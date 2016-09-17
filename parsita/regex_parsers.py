import re

from . import parsers
from .parsers import ParsersMeta, Parsers, ParsersDict, Reader, Parser, DiscardLeftParser, DiscardRightParser, \
    Result, Success, Failure, Continue, Backtrack, Stop, \
    lit, opt, rep, rep1, repsep, rep1sep


class StringReader(Reader[str]):  # Python lacks character type
    def __init__(self, source: str, position: int = 0):
        self.source = source
        self.position = position

    @property
    def first(self):
        return self.source[self.position]

    @property
    def rest(self):
        return StringReader(self.source, self.position + 1)

    @property
    def finished(self):
        return self.position >= len(self.source)

    def drop(self, count):
        return StringReader(self.source, self.position + count)

    next_word_regex = re.compile(r'[\(\)\[\]\{\}\"\']|\w+|[^\w\s\(\)\[\]\{\}\"\']+|\s+')

    def next_word(self):
        match = self.next_word_regex.match(self.source, self.position)
        return self.source[match.start():match.end()]

    def __repr__(self):
        if self.finished:
            return "StringReader(finished)"
        else:
            return "StringReader({}@{})".format(self.next_word(), self.position)


class RegexParser(Parser[str, str]):
    def __init__(self, pattern: str):  # Python lacks type of compiled RegularExpression
        super().__init__()
        self.pattern = re.compile(pattern)

    def consume(self, reader: StringReader):
        match = self.pattern.match(reader.source, reader.position)

        if match is None:
            return Backtrack(reader.position,
                lambda: '{} expected but {} found at {}'.format(
                    self.pattern.pattern, reader.next_word(), reader.position))
        else:
            value = reader.source[match.start():match.end()]
            return Continue(value, reader.drop(len(value)))

    def __repr__(self):
        return "reg(r'{}')".format(self.pattern.pattern)


def reg(pattern: str):
    if _whitespace is None:
        return RegexParser(pattern)
    else:
        return IgnoreWhitespaceParser(RegexParser(pattern), _whitespace)


class LiteralStringParser(Parser[str, str]):
    def __init__(self, pattern: str):
        super().__init__()
        self.pattern = pattern

    def consume(self, reader: StringReader):
        if reader.source.startswith(self.pattern, reader.position):
            return Continue(self.pattern, reader.drop(len(self.pattern)))
        else:
            return Backtrack(reader.position,
                lambda: '{} expected but {} found at {}'.format(self.pattern, reader.next_word(), reader.position))

    def __repr__(self):
        return "'{}'".format(self.pattern)


# Global mutable state controlling the handling of whitespace during parser construction
_whitespace = None


class IgnoreWhitespaceParser(Parser[str, str]):
    def __init__(self, pattern: Parser[str, str], whitespace: RegexParser):
        super().__init__()
        self.pattern = pattern
        self.whitespace = whitespace
        self.definition = DiscardLeftParser(whitespace, pattern)

    def consume(self, reader: Reader[str]):
        return self.definition.consume(reader)

    def __repr__(self):
        return repr(self.pattern)


def wrap_literal_with_whitespace(literal):
    if _whitespace is None:
        return LiteralStringParser(literal)
    else:
        return IgnoreWhitespaceParser(LiteralStringParser(literal), _whitespace)


class RegexParsersMeta(ParsersMeta):
    @classmethod
    def __prepare__(mcs, name, bases, whitespace: str = re.compile('\s*')):
        # Store whitespace in global location so regex parsers can see it
        global _whitespace
        if isinstance(whitespace, str):
            whitespace = re.compile(whitespace)

        def regex_parse(self, source: str) -> Result[str]:
            reader = StringReader(source)
            if whitespace is None:
                result = self.consume(reader)
            else:
                result = DiscardRightParser(self, RegexParser(whitespace)).consume(reader)

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

        if whitespace is None:
            _whitespace = None
        else:
            _whitespace = RegexParser(whitespace)
        parsers._handle_literal = wrap_literal_with_whitespace
        parsers._parse_method = regex_parse

        return ParsersDict()

    def __new__(mcs, name, bases, dct, **_):
        return super().__new__(mcs, name, bases, dct)

    def __init__(cls, name, bases, dct, **_):
        super().__init__(name, bases, dct)

        # Reset global variables
        global _whitespace
        _whitespace = None
        parsers._handle_literal = parsers.wrap_literal
        parsers._parse_method = parsers.basic_parse


class RegexParsers(metaclass=RegexParsersMeta):
    pass
