import re
from typing import Generic, Sequence, List, Union, Callable, Optional, Any
from types import MethodType

from . import options
from .state import Input, Output, Convert, Reader, StringReader, Result, Status, Success, Failure, Continue, Backtrack


class Parser(Generic[Input, Output]):
    """Abstract base class for all parser combinators.

    Inheritors of this class must:

    1. Implement the ``consume`` method
    2. Implement the ``__repr__`` method
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
        name (Optional[str]): A name used by ``__str__`` and ``__repr__``.
            It is set by the context classes when a parser is assigned to a
            name.
    """

    def __init__(self):
        self.parse = MethodType(options.parse_method, self)

    def consume(self, reader: Reader[Input]) -> Status[Input, Output]:
        """Abstract method for matching this parser at the current location.

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
        """Abstract method for completely parsing a source.

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

    name = None  # type: Optional[str]

    protected = False  # type: bool

    def name_or_repr(self) -> str:
        if self.name is None:
            return self.__repr__()
        else:
            return self.name

    def name_or_nothing(self) -> Optional[str]:
        if self.name is None:
            return ''
        else:
            return self.name + ' = '

    @staticmethod
    def handle_other(obj: Any) -> 'Parser':
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
        return other.__lshift__(self)

    def __gt__(self, other) -> 'ConversionParser':
        return ConversionParser(self, other)


def completely_parse_reader(parser: Parser[Input, Output], reader: Reader[Input]) -> Result[Output]:
    """Consume reader and return Success only on complete consumption.

    This is a helper function for ``parse`` methods, which return ``Success``
    when the input is completely consumed and ``Failure`` with an appropriate
    message otherwise.

    Args:
        parser: The parser doing the consuming
        reader: The input being consumed

    Returns:
        A parsing ``Result``
    """
    result = (parser << eof).consume(reader)

    if isinstance(result, Continue):
        return Success(result.value)
    else:
        used = set()
        unique_expected = []
        for expected_lambda in result.expected:
            expected = expected_lambda()
            if expected not in used:
                used.add(expected)
                unique_expected.append(expected)

        return Failure(result.farthest.expected_error(' or '.join(unique_expected)))


class LiteralParser(Generic[Input], Parser[Input, Input]):
    def __init__(self, pattern: Sequence[Input]):
        super().__init__()
        self.pattern = pattern

    def consume(self, reader: Reader[Input]):
        remainder = reader
        for elem in self.pattern:
            if remainder.finished:
                return Backtrack(remainder, lambda: str(elem))
            elif elem == remainder.first:
                remainder = remainder.rest
            else:
                return Backtrack(remainder, lambda: str(elem))

        return Continue(remainder, self.pattern)

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
            reader = reader.drop(len(self.pattern))

            if self.whitespace is not None:
                status = self.whitespace.consume(reader)
                reader = status.remainder

            return Continue(reader, self.pattern)
        else:
            return Backtrack(reader, lambda: repr(self.pattern))

    def __repr__(self):
        return self.name_or_nothing() + repr(self.pattern)


def lit(literal: Sequence[Input], *literals: Sequence[Input]) -> Parser:
    """Match a literal sequence.

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


class PredicateParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output], predicate: Callable[[Output], bool], description: str):
        super().__init__()
        self.parser = parser
        self.predicate = predicate
        self.description = description

    def consume(self, reader: Reader[Input]):
        remainder = reader
        status = self.parser.consume(remainder)
        if isinstance(status, Continue):
            if self.predicate(status.value):
                return status
            else:
                return Backtrack(remainder, lambda: self.description)
        else:
            return status

    def __repr__(self):
        return self.name_or_nothing() + 'pred({}, {})'.format(repr(self.parser), self.description)


def pred(parser: Parser[Input, Output], predicate: Callable[[Output], bool],
         description: str) -> PredicateParser[Input, Output]:
    """Match ``parser``'s result if it satisfies the predicate.

    Args:
        parser: Provides the result
        predicate: A predicate for the result to satisfy
        description: Name for the predicate, to use in error reporting

    Returns:
        A ``PredicateParser``.
    """
    return PredicateParser(parser, predicate, description)


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
            return Backtrack(reader, lambda: "r'" + self.pattern.pattern + "'")
        else:
            value = reader.source[match.start():match.end()]
            reader = reader.drop(len(value))

            if self.whitespace is not None:
                status = self.whitespace.consume(reader)
                reader = status.remainder

            return Continue(reader, value)

    def __repr__(self):
        return self.name_or_nothing() + "reg(r'{}')".format(self.pattern.pattern)


def reg(pattern: str) -> RegexParser:
    """Match with a regular expression.

    This matches the text with a regular expression. The regular expressions is
    treated as greedy. Backtracking in the parser combinators does not flow into
    regular expression backtracking. This is only valid in the ``TextParsers``
    context and not in the ``GeneralParsers`` context because regular
    expressions only operate on text.

    Args:
        pattern: str or python regular expression.
    """
    return RegexParser(pattern, options.whitespace)


class OptionalParser(Generic[Input, Output], Parser[Input, List[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, reader: Reader[Input]) -> Status[Input, Sequence[Output]]:
        status = self.parser.consume(reader)

        if isinstance(status, Continue):
            return Continue(status.remainder, [status.value]).merge(status)
        else:
            return Continue(reader, []).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + 'opt({})'.format(self.parser.name_or_repr())


def opt(parser: Union[Parser, Sequence[Input]]) -> OptionalParser:
    """Optionally match a parser.

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
    def __init__(self, parser: Parser[Input, Output], *parsers: Parser[Input, Output]):
        super().__init__()
        self.parsers = (parser,) + tuple(parsers)

    def consume(self, reader: Reader[Input]):
        best_failure = None
        for parser in self.parsers:
            status = parser.consume(reader)
            if isinstance(status, Continue):
                return status.merge(best_failure)
            else:
                best_failure = status.merge(best_failure)

        return best_failure

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + ' | '.join(names)


class SequentialParser(Generic[Input], Parser[Input, List[Any]]):  # Type of this class is inexpressible
    def __init__(self, parser: Parser[Input, Any], *parsers: Parser[Input, Any]):
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

        return Continue(remainder, output).merge(status)

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + ' & '.join(names)


class DiscardLeftParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, Any], right: Parser[Input, Output]):
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
    def __init__(self, left: Parser[Input, Output], right: Parser[Input, Any]):
        super().__init__()
        self.left = left
        self.right = right

    def consume(self, reader: Reader[Input]):
        status1 = self.left.consume(reader)
        if isinstance(status1, Continue):
            status2 = self.right.consume(status1.remainder).merge(status1)
            if isinstance(status2, Continue):
                return Continue(status2.remainder, status1.value).merge(status2)
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
                    if remainder.position == status.remainder.position:
                        raise RuntimeError(remainder.recursion_error(str(self)))

                    remainder = status.remainder
                    output.append(status.value)
                else:
                    return Continue(remainder, output).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + 'rep1({})'.format(self.parser.name_or_repr())


def rep1(parser: Union[Parser, Sequence[Input]]) -> RepeatedOnceParser:
    """Match a parser one or more times repeatedly.

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
                if remainder.position == status.remainder.position:
                    raise RuntimeError(remainder.recursion_error(str(self)))

                remainder = status.remainder
                output.append(status.value)
            else:
                return Continue(remainder, output).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + 'rep({})'.format(self.parser.name_or_repr())


def rep(parser: Union[Parser, Sequence[Input]]) -> RepeatedParser:
    """Match a parser zero or more times repeatedly.

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
        self.parser = parser
        self.separator = separator

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)

        if not isinstance(status, Continue):
            return status
        else:
            output = [status.value]
            remainder = status.remainder
            while True:
                # If the separator matches, but the parser does not, the remainder from the last successful parser step
                # must be used, not the remainder from any separator. That is why the parser starts from the remainder
                # on the status, but remainder is not updated until after the parser succeeds.
                status = self.separator.consume(remainder).merge(status)
                if isinstance(status, Continue):
                    status = self.parser.consume(status.remainder).merge(status)
                    if isinstance(status, Continue):
                        if remainder.position == status.remainder.position:
                            raise RuntimeError(remainder.recursion_error(str(self)))

                        remainder = status.remainder
                        output.append(status.value)
                    else:
                        return Continue(remainder, output).merge(status)
                else:
                    return Continue(remainder, output).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + 'rep1sep({}, {})'.format(self.parser.name_or_repr(),
                                                                 self.separator.name_or_repr())


def rep1sep(parser: Union[Parser, Sequence[Input]], separator: Union[Parser, Sequence[Input]]) \
        -> RepeatedOnceSeparatedParser:
    """Match a parser one or more times separated by another parser.

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
        self.parser = parser
        self.separator = separator

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)

        if not isinstance(status, Continue):
            return Continue(reader, []).merge(status)
        else:
            output = [status.value]
            remainder = status.remainder
            while True:
                # If the separator matches, but the parser does not, the remainder from the last successful parser step
                # must be used, not the remainder from any separator. That is why the parser starts from the remainder
                # on the status, but remainder is not updated until after the parser succeeds.
                status = self.separator.consume(remainder).merge(status)
                if isinstance(status, Continue):
                    status = self.parser.consume(status.remainder).merge(status)
                    if isinstance(status, Continue):
                        if remainder.position == status.remainder.position:
                            raise RuntimeError(remainder.recursion_error(str(self)))

                        remainder = status.remainder
                        output.append(status.value)
                    else:
                        return Continue(remainder, output).merge(status)
                else:
                    return Continue(remainder, output).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + 'repsep({}, {})'.format(self.parser.name_or_repr(),
                                                                self.separator.name_or_repr())


def repsep(parser: Union[Parser, Sequence[Input]], separator: Union[Parser, Sequence[Input]]) \
        -> RepeatedSeparatedParser:
    """Match a parser zero or more times separated by another parser.

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
            return Continue(status.remainder, self.converter(status.value)).merge(status)
        else:
            return status

    def __repr__(self):
        return self.name_or_nothing() + repr(self.parser)


class EndOfSourceParser(Generic[Input], Parser[Input, None]):
    def __init__(self):
        super().__init__()

    def consume(self, reader: Reader[Input]) -> Status[Input, None]:
        if reader.finished:
            return Continue(reader, None)
        else:
            return Backtrack(reader, lambda: 'end of source')

    def __repr__(self):
        return self.name_or_nothing() + 'eof'


eof = EndOfSourceParser()


class SuccessParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, value: Output):
        super().__init__()
        self.value = value

    def consume(self, reader: Reader[Input]) -> Status[Input, None]:
        return Continue(reader, self.value)

    def __repr__(self):
        return self.name_or_nothing() + 'success({})'.format(repr(self.value))


def success(value: Any):
    """Always succeed in matching and return a value.

    This parser always succeeds and returns the given ``value``. No input is
    consumed. This is useful for inserting arbitrary values into complex
    parsers.

    Args:
        value: Any value
    """
    return SuccessParser(value)


class FailureParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, expected: str):
        super().__init__()
        self.expected = expected

    def consume(self, reader: Reader[Input]) -> Status[Input, None]:
        return Backtrack(reader, lambda: self.expected)

    def __repr__(self):
        return self.name_or_nothing() + 'failure({})'.format(repr(self.expected))


def failure(expected: str = ''):
    """Always fail in matching with a given message.

    This parser always backtracks with a message that it is expecting the
    given ``expected``. This is useful for appending to parsers that are
    expected to be seen in the input, but are not valid so that a more useful
    error message can be given.

    Args:
        expected: Message to be conveyed
    """
    return FailureParser(expected)


class AnyParser(Generic[Input], Parser[Input, Input]):
    """Match any single element.

    This parser matches any single element, returning it. This is useful when it
    does not matter what is at this position or when validation is deferred to a
    later step, such as with the ``pred`` parser. This parser can only fail at
    the end of the stream.
    """
    def __init__(self):
        super().__init__()

    def consume(self, reader: Reader[Input]) -> Status[Input, None]:
        if reader.finished:
            return Backtrack(reader, lambda: 'anything')
        else:
            return Continue(reader.rest, reader.first)

    def __repr__(self):
        return self.name_or_nothing() + 'any1'


any1 = AnyParser()


__all__ = ['Parser', 'LiteralParser', 'LiteralStringParser', 'lit', 'RegexParser', 'reg', 'OptionalParser', 'opt',
           'AlternativeParser', 'SequentialParser', 'DiscardLeftParser', 'DiscardRightParser', 'RepeatedOnceParser',
           'rep1', 'RepeatedParser', 'rep', 'RepeatedOnceSeparatedParser', 'rep1sep', 'RepeatedSeparatedParser',
           'repsep', 'ConversionParser', 'EndOfSourceParser', 'eof', 'SuccessParser', 'success', 'FailureParser',
           'failure', 'PredicateParser', 'pred', 'AnyParser', 'any1', 'completely_parse_reader']
