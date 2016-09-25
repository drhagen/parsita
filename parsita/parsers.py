import re
from typing import Generic, Sequence, Union, Callable
from types import MethodType

from . import options
from .state import (Input, Output, Convert, Reader, SequenceReader, StringReader,
                    Result, Success, Failure, Status, Continue, Backtrack, Stop)


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
    """Abstract base class for all parser combinators

    Inheritors of this class must:

    1. Implement the ``consume`` method
    2. Implement the ``__str__`` method
    3. Call super().__init__() in their constructor to get the parse method from
       the context.

    Attributes:
        protected (bool): The metaclasses set this flag to true whenever a
            parser is assigned to a name. Operators that flatten the parsers
            they receive (``__or__`` and ``__and__``) will not flatten parsers
            with a ``True`` value here. This is most important for ``__and__``
            because there is no other way to tell that these two should be
            different:

            ```
            abc = a & b & c  # returns [a, b, c]
            ```
            ```
            temp = a & b
            abc = temp & c  # returns [[a, b], c]
            ```

            The fundamental limitation is that python does not handle linked
            lists well or have unpacking that would let one unpack abc as
            [temp, c].
        __name__ (Optional[str]): A name used by ``__str__`` and ``__repr__``.
            It is set by the context classes when a parser is assigned to a
            name.
    """

    def __init__(self):
        self.parse = MethodType(options.parse_method, self)

    def consume(self, reader: Reader[Input]) -> Status[Input, Output]:
        """Abstract method for matching this parser at the current location

        This is the critical method of every parser combinator.

        Args:
            reader: The current state of the parser.

        Returns:
            If the pattern matches, a ``Continue`` is returned. If the pattern
            does not match, a ``Failure`` is returned. In either case, if
            multiple branches are explored, the error from the farthest point is
            merged with the returned status.
        """
        raise NotImplementedError()

    def parse(self, source: Sequence[Input]) -> Result[Output]:
        """Abstract method for completely parsing a source

        While ``parse`` is a method on every parser for convenience, it
        is really a function of the context. It is the duty of the context
        to set the correct ``Reader`` to use and to handle whitespace
        not handled by the parsers themselves. This method is pulled from the
        context when the parser is initialized.

        Args:
            source: What will be parsed.

        Returns:
            If the parser succeeded in matching and consumed the entire output,
            the value from ``Continue`` is copied to make a ``Success``. If the
            parser failed in matching, the error message is copied to a
            ``Failure``. If the parser succeeded but the source was not
            completelt consumed, a ``Failure`` with a message indicating this
            is returned.
        """
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
                                 lambda: '{} expected but {} found at {}'.format(
                                     elem, remainder.first, remainder.position))

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
                             lambda: '{} expected but {} found at {}'.format(
                                 self.pattern, reader.next_word(), reader.position))

    def __repr__(self):
        return "'{}'".format(self.pattern)


def lit(literal: Sequence[Input], *literals: Sequence[Sequence[Input]]) -> Parser:
    """Match a literal sequence

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
        return AlternativeParser(options.handle_literal(literal), *map(options.handle_literal, literals))
    else:
        return options.handle_literal(literal)


class RegexParser(Parser[str, str]):
    def __init__(self, pattern: str, whitespace: Parser[str, None] = None):  # Python lacks type of compiled regex
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


def reg(pattern: str) -> RegexParser:
    """Match with a regular expression

    This matches the text with a regular expression. The regular expressions is
    treated as greedy. Backtracking in the parser combinators does not flow into
    regular expression backtracking. This is only valid in the ``TextParsers``
    context and not in the ``GeneralParsers`` context because regular
    expressions only operate on text.

    Args:
        pattern: str or python regular expression.
    """
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
        return self.name_or_nothing() + 'opt({})'.format(self.parser.name_or_repr())


def opt(parser: Union[Parser, Sequence[Input]]) -> OptionalParser:
    """Optionally match a parser

    An ``OptionalParser`` attempts to match ``parser``. If it succeeds, it
    returns a list of length one with the value returned by the parser as the
    only element. If it fails, it returns an empty list.

    Args:
        parser: Parser or literal
    """
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

        return self.name_or_nothing() + ' | '.join(names)


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

        return self.name_or_nothing() + ' & '.join(names)


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
        return self.name_or_nothing() + '{} >> {}'.format(self.left.name_or_repr(), self.right.name_or_repr())


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
        return self.name_or_nothing() + '{} << {}'.format(self.left.name_or_repr(), self.right.name_or_repr())


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
        return self.name_or_nothing() + 'rep1({})'.format(self.parser.name_or_repr())


def rep1(parser: Union[Parser, Sequence[Input]]) -> RepeatedOnceParser:
    """Match a parser one or more times repeatedly

    This matches ``parser`` multiple times in a row. If it matches as least
    once, it returns a list of values from each time ``parser`` matched. If it
    does not match ``parser`` at all, it fails.

    Args:
        parser: Parser or literal
    """
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
        return self.name_or_nothing() + 'rep({})'.format(self.parser.name_or_repr())


def rep(parser: Union[Parser, Sequence[Input]]) -> RepeatedParser:
    """Match a parser zero or more times repeatedly

    This matches ``parser`` multiple times in a row. A list is returned
    containing the value from each match. If there are no matches, an empty list
    is returned.

    Args:
        parser: Parser or literal
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return RepeatedParser(parser)


class RepeatedOnceSeparatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], separator: Parser[Input, Output]):
        super().__init__()
        parser.protected = True
        self.parser = parser
        self.separator = separator

        definition = parser & rep(separator >> parser) > (lambda x: [x[0]] + x[1])
        self.consume = definition.consume

    def __repr__(self):
        return self.name_or_nothing() + 'rep1sep({}, {})'.format(self.parser.name_or_repr(),
                                                                 self.separator.name_or_repr())


def rep1sep(parser: Union[Parser, Sequence[Input]],
            separator: Union[Parser, Sequence[Input]]) \
        -> RepeatedOnceSeparatedParser:
    """Match a parser one or more times separated by another parser

    This matches repeated sequences of ``parser`` separated by ``separator``.
    If there is at least one match, a list containing the values of the
    ``parser`` matches is returned. The values from ``separator`` are discarded.
    If it does not match ``parser`` at all, it fails.

    Args:
        parser: Parser or literal
        separator: Parser or literal
    """
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatedOnceSeparatedParser(parser, separator)


class RepeatedSeparatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], separator: Parser[Input, Output]):
        super().__init__()
        parser.protected = True
        self.parser = parser
        self.separator = separator

        self.definition = opt(rep1sep(parser, separator)) > (lambda x: x[0] if x else [])
        self.consume = self.definition.consume

    def __repr__(self):
        return self.name_or_nothing() + 'repsep({}, {})'.format(self.parser.name_or_repr(),
                                                                self.separator.name_or_repr())


def repsep(parser: Union[Parser, Sequence[Input]],
           separator: Union[Parser, Sequence[Input]]) \
        -> RepeatedSeparatedParser:
    """Match a parser zero or more times separated by another parser

    This matches repeated sequences of ``parser`` separated by ``separator``. A
    list is returned containing the value from each match of ``parser``. The
    values from ``separator`` are discarded. If there are no matches, an empty
    list is returned.

    Args:
        parser: Parser or literal
        separator: Parser or literal
    """
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatedSeparatedParser(parser, separator)


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

__all__ = ['Parser', 'LiteralParser', 'LiteralStringParser', 'lit', 'RegexParser', 'reg', 'OptionalParser', 'opt',
           'AlternativeParser', 'SequentialParser', 'DiscardLeftParser', 'DiscardRightParser', 'RepeatedOnceParser',
           'rep1', 'RepeatedParser', 'rep', 'RepeatedOnceSeparatedParser', 'rep1sep', 'RepeatedSeparatedParser',
           'repsep', 'ConversionParser']
