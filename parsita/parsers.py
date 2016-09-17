import re
from typing import Generic, Sequence, Union, Callable
from types import MethodType

from . import options
from .state import *


def wrap_literal(literal):
    return LiteralParser(literal)


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


class Parser(Generic[Input, Output]):
    def __init__(self):
        self.parse = MethodType(options.parse_method, self)

    def consume(self, reader: Reader[Input]):
        raise NotImplementedError()

    def parse(self, source: Sequence[Input]) -> Result[Output]:
        raise NotImplementedError()

    __name__ = None

    protected = False

    def name_or_repr(self):
        if self.__name__ is None:
            return self.__repr__()
        else:
            return self.__name__

    def name_or_nothing(self):
        if self.__name__ is None:
            return ''
        else:
            return self.__name__ + ' = '

    @classmethod
    def handle_other(cls, obj):
        if isinstance(obj, Parser):
            return obj
        else:
            return options.handle_literal(obj)

    def __or__(self, other) -> 'AlternativeParser':
        other = self.handle_other(other)
        parsers = []
        if isinstance(self, AlternativeParser) and not self.protected:
            parsers.extend(self.parsers)
        else:
            parsers.append(self)
        if isinstance(other, AlternativeParser) and not other.protected:
            parsers.extend(other.parsers)
        else:
            parsers.append(other)
        return AlternativeParser(*parsers)

    def __ror__(self, other) -> 'AlternativeParser':
        other = self.handle_other(other)
        return other.__or__(self)

    def __and__(self, other) -> 'SequentialParser':
        other = self.handle_other(other)
        if isinstance(self, SequentialParser) and not self.protected:
            return SequentialParser(*self.parsers, other)
        else:
            return SequentialParser(self, other)

    def __rand__(self, other) -> 'SequentialParser':
        other = self.handle_other(other)
        return other.__and__(self)

    def __rshift__(self, other) -> 'DiscardLeftParser':
        other = self.handle_other(other)
        return DiscardLeftParser(self, other)

    def __rrshift__(self, other) -> 'DiscardLeftParser':
        other = self.handle_other(other)
        return other.__rshift__(self)

    def __lshift__(self, other) -> 'DiscardRightParser':
        other = self.handle_other(other)
        return DiscardRightParser(self, other)

    def __rlshift__(self, other) -> 'DiscardRightParser':
        other = self.handle_other(other)
        return other.__rshift__(self)

    def __gt__(self, other) -> 'ConversionParser':
        return ConversionParser(self, other)


class LiteralParser(Generic[Input], Parser[Input, Input]):
    def __init__(self, pattern: Sequence[Input]):
        super().__init__()
        self.pattern = pattern

    def consume(self, reader: Reader[Input]):
        remainder = reader
        for elem in self.pattern:
            if remainder.finished:
                return Backtrack(remainder.position, lambda: '{} expected but end of source found'.format(elem))
            elif elem == remainder.first:
                remainder = remainder.rest
            else:
                return Backtrack(remainder.position,
                        lambda: '{} expected but {} found at {}'.format(elem, remainder.first, remainder.position))

        return Continue(self.pattern, remainder)

    def __repr__(self):
        return self.name_or_nothing() + repr(self.pattern)


class LiteralStringParser(Parser[str, str]):
    def __init__(self, pattern: str, whitespace: Parser[str, None] = None):
        super().__init__()
        self.whitespace = whitespace
        self.pattern = pattern

    def consume(self, reader: StringReader):
        if self.whitespace is not None:
            status = self.whitespace.consume(reader)
            reader = status.remainder

        if reader.source.startswith(self.pattern, reader.position):
            return Continue(self.pattern, reader.drop(len(self.pattern)))
        else:
            return Backtrack(reader.position,
                lambda: '{} expected but {} found at {}'.format(self.pattern, reader.next_word(), reader.position))

    def __repr__(self):
        return "'{}'".format(self.pattern)


def lit(lit1, *lits):
    if len(lits) > 0:
        return AlternativeParser(options.handle_literal(lit1), *map(options.handle_literal, lits))
    else:
        return options.handle_literal(lit1)


class RegexParser(Parser[str, str]):
    def __init__(self, pattern: str, whitespace: Parser[str, None] = None):  # Python lacks type of compiled RegularExpression
        super().__init__()
        self.whitespace = whitespace
        self.pattern = re.compile(pattern)

    def consume(self, reader: StringReader):
        if self.whitespace is not None:
            status = self.whitespace.consume(reader)
            reader = status.remainder

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
    return RegexParser(pattern, options.whitespace)


class OptionalParser(Generic[Input, Output], Parser[Input, Union[Output, None]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, reader: Reader[Input]) -> Status[Input, Sequence[Output]]:
        status = self.parser.consume(reader)

        if isinstance(status, Continue):
            return Continue([status.value], status.remainder).merge(status)
        elif isinstance(status, Stop):
            return status
        else:
            return Continue([], reader).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + "opt({})".format(self.parser.name_or_repr())


def opt(parser):
    if isinstance(parser, str):
        parser = lit(parser)
    return OptionalParser(parser)


class AlternativeParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, parser: Parser[Input, Output], *parsers: Sequence[Parser[Input, Output]]):
        super().__init__()
        self.parsers = (parser,) + tuple(parsers)

    def consume(self, reader: Reader[Input]):
        best_failure = None
        for parser in self.parsers:
            status = parser.consume(reader)
            if isinstance(status, Continue):
                return status.merge(best_failure)
            elif isinstance(status, Stop):
                return status
            else:
                best_failure = status.merge(best_failure)

        return best_failure

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + " | ".join(names)


class SequentialParser(Generic[Input], Parser[Input, None]):  # Type of this class is inexpressible
    def __init__(self, parser: Parser[Input, None], *parsers: Sequence[Parser[Input, None]]):
        super().__init__()
        self.parsers = (parser,) + tuple(parsers)

    def consume(self, reader: Reader[Input]):
        output = []
        status = None
        remainder = reader

        for parser in self.parsers:
            status = parser.consume(remainder).merge(status)
            if isinstance(status, Continue):
                output.append(status.value)
                remainder = status.remainder
            else:
                return status

        return Continue(output, remainder).merge(status)

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + " & ".join(names)


class DiscardLeftParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, None], right: Parser[Input, None]):
        super().__init__()
        self.left = left
        self.right = right

    def consume(self, reader: Reader[Input]):
        status = self.left.consume(reader)
        if isinstance(status, Continue):
            return self.right.consume(status.remainder).merge(status)
        else:
            return status

    def __repr__(self):
        return self.name_or_nothing() + "{} >> {}".format(self.left.name_or_repr(), self.right.name_or_repr())


class DiscardRightParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, None], right: Parser[Input, None]):
        super().__init__()
        self.left = left
        self.right = right

    def consume(self, reader: Reader[Input]):
        status1 = self.left.consume(reader)
        if isinstance(status1, Continue):
            status2 = self.right.consume(status1.remainder).merge(status1)
            if isinstance(status2, Continue):
                return Continue(status1.value, status2.remainder).merge(status2)
            else:
                return status2
        else:
            return status1

    def __repr__(self):
        return self.name_or_nothing() + "{} << {}".format(self.left.name_or_repr(), self.right.name_or_repr())


class RepeatedOnceParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)

        if not isinstance(status, Continue):
            return status
        else:
            output = [status.value]
            remainder = status.remainder
            while True:
                status = self.parser.consume(remainder).merge(status)
                if isinstance(status, Continue):
                    remainder = status.remainder
                    output.append(status.value)
                elif isinstance(status, Stop):
                    return status
                else:
                    return Continue(output, remainder).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + "rep1({})".format(self.parser.name_or_repr())


def rep1(parser):
    if isinstance(parser, str):
        parser = lit(parser)
    return RepeatedOnceParser(parser)


class RepeatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, reader: Reader[Input]):
        output = []
        status = None
        remainder = reader

        while True:
            status = self.parser.consume(remainder).merge(status)
            if isinstance(status, Continue):
                remainder = status.remainder
                output.append(status.value)
            elif isinstance(status, Stop):
                return status
            else:
                return Continue(output, remainder).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + "rep({})".format(self.parser.name_or_repr())


def rep(parser):
    if isinstance(parser, str):
        parser = lit(parser)
    return RepeatedParser(parser)


class RepeatedOnceSeperatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], separator: Parser[Input, Output]):
        super().__init__()
        parser.protected = True
        self.parser = parser
        self.separator = separator

        definition = parser & rep(separator >> parser) > (lambda x: [x[0]] + x[1])
        self.consume = definition.consume

    def __repr__(self):
        return self.name_or_nothing() + "rep1sep({}, {})".format(self.parser.name_or_repr(),
                                                                 self.separator.name_or_repr())


def rep1sep(parser, separator):
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatedOnceSeperatedParser(parser, separator)


class RepeatedSeperatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], separator: Parser[Input, Output]):
        super().__init__()
        parser.protected = True
        self.parser = parser
        self.separator = separator

        self.definition = opt(rep1sep(parser, separator)) > (lambda x: x[0] if x else [])
        self.consume = self.definition.consume

    def __repr__(self):
        return self.name_or_nothing() + "repsep({}, {})".format(self.parser.name_or_repr(),
                                                                self.separator.name_or_repr())


def repsep(parser, separator):
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatedSeperatedParser(parser, separator)


class ConversionParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(self, parser: Parser[Input, Output], converter: Callable[[Output], Convert]):
        super().__init__()
        self.parser = parser
        self.converter = converter

    def consume(self, reader: Reader[Input]) -> Status[Input, Convert]:
        status = self.parser.consume(reader)

        if isinstance(status, Continue):
            return Continue(self.converter(status.value), status.remainder).merge(status)
        else:
            return status

    def __repr__(self):
        return self.name_or_nothing() + repr(self.parser)
