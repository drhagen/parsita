from __future__ import annotations

import re
from types import MethodType
from typing import Any, Callable, Generic, List, NoReturn, Optional, Sequence, Union

from . import options
from .state import (
    Continue,
    Convert,
    Failure,
    Input,
    Output,
    ParseError,
    Reader,
    RecursionError,
    Result,
    State,
    StringReader,
    Success,
)

# Singleton indicating that no result is yet in the memo
missing = object()


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

    def cached_consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        """Match this parser at the given location.

        This is a concrete wrapper around ``consume``. This method implements
        the left-recursive packrat algorithm:

        1. Check the memo if this parser has already operated at this location
            a. Return the result immediately if it is there
        2. Put a ``None`` in the memo for this parser at this position
        3. Invoke ``consume``
        4. Put the result in the memo for this parser at this position
        5. Return the result

        Individual parsers need to implement ``consume``, but not
        ``cached_consume``. But all combinations should invoke
        ``cached_consume`` instead of ``consume`` on their member parsers.

        Args:
            state: The mutable state of the parse
            reader: The current state of the input

        Returns:
            If the pattern matches, a ``Continue`` is returned. If the pattern
            does not match, a ``None`` is returned.
        """
        key = (self, reader.position)
        value = state.memo.get(key, missing)

        if value is not missing:
            return value

        state.memo[key] = None

        result = self.consume(state, reader)

        state.memo[key] = result

        return result

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        """Abstract method for matching this parser at the given location.

        This is the central method of every parser combinator.

        Args:
            state: The mutable state of the parse
            reader: The current state of the input

        Returns:
            If the pattern matches, a ``Continue`` is returned. If the pattern
            does not match, a ``None`` is returned.
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
            completely consumed, a ``Failure`` with a message indicating this
            is returned.
        """
        raise NotImplementedError()

    name: Optional[str] = None

    protected: bool = False

    def name_or_repr(self) -> str:
        if self.name is None:
            return self.__repr__()
        else:
            return self.name

    def name_or_nothing(self) -> Optional[str]:
        if self.name is None:
            return ""
        else:
            return self.name + " = "

    @staticmethod
    def handle_other(obj: Any) -> Parser:
        if isinstance(obj, Parser):
            return obj
        else:
            return options.handle_literal(obj)

    def __or__(self, other) -> AlternativeParser:
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

    def __ror__(self, other) -> AlternativeParser:
        other = self.handle_other(other)
        return other.__or__(self)

    def __and__(self, other) -> SequentialParser:
        other = self.handle_other(other)
        if isinstance(self, SequentialParser) and not self.protected:
            return SequentialParser(*self.parsers, other)
        else:
            return SequentialParser(self, other)

    def __rand__(self, other) -> SequentialParser:
        other = self.handle_other(other)
        return other.__and__(self)

    def __rshift__(self, other) -> DiscardLeftParser:
        other = self.handle_other(other)
        return DiscardLeftParser(self, other)

    def __rrshift__(self, other) -> DiscardLeftParser:
        other = self.handle_other(other)
        return other.__rshift__(self)

    def __lshift__(self, other) -> DiscardRightParser:
        other = self.handle_other(other)
        return DiscardRightParser(self, other)

    def __rlshift__(self, other) -> DiscardRightParser:
        other = self.handle_other(other)
        return other.__lshift__(self)

    def __gt__(self, other) -> ConversionParser:
        return ConversionParser(self, other)

    def __ge__(self, other) -> TransformationParser:
        return TransformationParser(self, other)


def completely_parse_reader(parser: Parser[Input, Output], reader: Reader[Input]) -> Result[Output]:
    """Consume reader and return Success only on complete consumption.

    This is a helper function for ``parse`` methods, which return ``Success``
    when the input is completely consumed and ``Failure`` with an appropriate
    message otherwise.

    Args:
        parser: The parser doing the consuming
        reader: The input being consumed

    Returns:
        A Returns ``Result`` containing either the successfully parsed value or
        an error from the farthest parsed point in the input.
    """
    state = State()
    status = (parser << eof).cached_consume(state, reader)

    if isinstance(status, Continue):
        return Success(status.value)
    else:
        used = set()
        unique_expected = []
        for expected in state.expected:
            if expected not in used:
                used.add(expected)
                unique_expected.append(expected)

        return Failure(ParseError(state.farthest, unique_expected))


class LiteralParser(Generic[Input], Parser[Input, Input]):
    def __init__(self, pattern: Sequence[Input]):
        super().__init__()
        self.pattern = pattern

    def consume(self, state: State, reader: Reader[Input]):
        remainder = reader
        for elem in self.pattern:
            if remainder.finished:
                state.register_failure(str(elem), remainder)
                return None
            elif elem == remainder.first:
                remainder = remainder.rest
            else:
                state.register_failure(str(elem), remainder)
                return None

        return Continue(remainder, self.pattern)

    def __repr__(self):
        return self.name_or_nothing() + repr(self.pattern)


class LiteralStringParser(Parser[str, str]):
    def __init__(self, pattern: str, whitespace: Optional[Parser[str, None]] = None):
        super().__init__()
        self.whitespace = whitespace
        self.pattern = pattern

    def consume(self, state: State, reader: StringReader):
        if self.whitespace is not None:
            status = self.whitespace.cached_consume(state, reader)
            reader = status.remainder

        if reader.source.startswith(self.pattern, reader.position):
            reader = reader.drop(len(self.pattern))

            if self.whitespace is not None:
                status = self.whitespace.cached_consume(state, reader)
                reader = status.remainder

            return Continue(reader, self.pattern)
        else:
            state.register_failure(repr(self.pattern), reader)
            return None

    def __repr__(self):
        return self.name_or_nothing() + repr(self.pattern)


def lit(literal: Sequence[Input], *literals: Sequence[Input]) -> Parser[str, str]:
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

    def consume(self, state: State, reader: Reader[Input]):
        remainder = reader
        status = self.parser.cached_consume(state, remainder)
        if isinstance(status, Continue):
            if self.predicate(status.value):
                return status
            else:
                state.register_failure(self.description, reader)
                return None
        else:
            return status

    def __repr__(self):
        return self.name_or_nothing() + f"pred({self.parser.name_or_repr()}, {self.description})"


def pred(
    parser: Parser[Input, Output], predicate: Callable[[Output], bool], description: str
) -> PredicateParser[Input, Output]:
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
    # Python lacks type of compiled regex so use str
    def __init__(self, pattern: str, whitespace: Optional[Parser[str, None]] = None):
        super().__init__()
        self.whitespace = whitespace
        self.pattern = re.compile(pattern)

    def consume(self, state: State, reader: StringReader):
        if self.whitespace is not None:
            status = self.whitespace.cached_consume(state, reader)
            reader = status.remainder

        match = self.pattern.match(reader.source, reader.position)

        if match is None:
            state.register_failure(f"r'{self.pattern.pattern}'", reader)
            return None
        else:
            value = reader.source[match.start() : match.end()]
            reader = reader.drop(len(value))

            if self.whitespace is not None:
                status = self.whitespace.cached_consume(state, reader)
                reader = status.remainder

            return Continue(reader, value)

    def __repr__(self):
        return self.name_or_nothing() + f"reg(r'{self.pattern.pattern}')"


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

    def consume(self, state: State, reader: Reader[Input]):
        status = self.parser.cached_consume(state, reader)

        if isinstance(status, Continue):
            return Continue(status.remainder, [status.value])
        else:
            return Continue(reader, [])

    def __repr__(self):
        return self.name_or_nothing() + f"opt({self.parser.name_or_repr()})"


def opt(parser: Union[Parser[Input, Output], Sequence[Input]]) -> OptionalParser[Input, Output]:
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

    def consume(self, state: State, reader: Reader[Input]):
        for parser in self.parsers:
            status = parser.cached_consume(state, reader)
            if isinstance(status, Continue):
                return status

        return None

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + " | ".join(names)


def first(
    parser: Union[Parser[Input, Output], Sequence[Input]], *parsers: Union[Parser[Input, Output], Sequence[Input]]
) -> AlternativeParser[Input, Output]:
    """Match the first of several alternative parsers.

    A ``AlternativeParser`` attempts to match each supplied parser. If a parser
    succeeds, its result is immediately returned and later parsers are not
    attempted. If all parsers fail, a failure is returned.

    Currently, the behavior of `|` matches this function. If the current
    behavior of always returning the first parser to succeed is desired, this
    function should be used instead, because a future release of Parsita will
    change the behavior of `|` to use `longest` instead.

    Args:
        *parsers: Non-empty list of ``Parser``s or literals to try
    """
    cleaned_parsers = [lit(parser_i) if isinstance(parser_i, str) else parser_i for parser_i in [parser, *parsers]]
    return AlternativeParser(*cleaned_parsers)


class LongestAlternativeParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, parser: Parser[Input, Output], *parsers: Parser[Input, Output]):
        super().__init__()
        self.parsers = (parser,) + tuple(parsers)

    def consume(self, state: State, reader: Reader[Input]):
        longest_success: Optional[Continue] = None
        for parser in self.parsers:
            status = parser.cached_consume(state, reader)
            if isinstance(status, Continue):
                if longest_success is None or status.remainder.position > longest_success.remainder.position:
                    longest_success = status

        return longest_success

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + f"longest({', '.join(names)})"


def longest(
    parser: Union[Parser[Input, Output], Sequence[Input]], *parsers: Union[Parser[Input, Output], Sequence[Input]]
) -> LongestAlternativeParser[Input, Output]:
    """Match the longest of several alternative parsers.

    A ``LongestAlternativeParser`` attempts to match all supplied parsers. If
    multiple parsers succeed, the result of the one that makes the farthest
    successful progress is returned. If all parsers fail, a failure is returned.
    If multiple alternatives succeed with the same progress, the first one is
    returned.

    Currently, the behavior of `|` matches `first`. If you desired returning the
    longest match instead of the first, use this function instead. A future
    release of Parsita will change the behavior of `|` to use `longest`.

    Args:
        *parsers: Non-empty list of ``Parser``s or literals to try
    """
    cleaned_parsers = [lit(parser_i) if isinstance(parser_i, str) else parser_i for parser_i in [parser, *parsers]]
    return LongestAlternativeParser(*cleaned_parsers)


class SequentialParser(Generic[Input], Parser[Input, List[Any]]):  # Type of this class is inexpressible
    def __init__(self, parser: Parser[Input, Any], *parsers: Parser[Input, Any]):
        super().__init__()
        self.parsers = (parser,) + tuple(parsers)

    def consume(self, state: State, reader: Reader[Input]):
        output = []
        remainder = reader

        for parser in self.parsers:
            status = parser.cached_consume(state, remainder)
            if isinstance(status, Continue):
                output.append(status.value)
                remainder = status.remainder
            else:
                return None

        return Continue(remainder, output)

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + " & ".join(names)


class DiscardLeftParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, Any], right: Parser[Input, Output]):
        super().__init__()
        self.left = left
        self.right = right

    def consume(self, state: State, reader: Reader[Input]):
        status = self.left.cached_consume(state, reader)
        if isinstance(status, Continue):
            return self.right.cached_consume(state, status.remainder)
        else:
            return None

    def __repr__(self):
        return self.name_or_nothing() + f"{self.left.name_or_repr()} >> {self.right.name_or_repr()}"


class DiscardRightParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, left: Parser[Input, Output], right: Parser[Input, Any]):
        super().__init__()
        self.left = left
        self.right = right

    def consume(self, state: State, reader: Reader[Input]):
        status1 = self.left.cached_consume(state, reader)
        if isinstance(status1, Continue):
            status2 = self.right.cached_consume(state, status1.remainder)
            if isinstance(status2, Continue):
                return Continue(status2.remainder, status1.value)
            else:
                return None
        else:
            return None

    def __repr__(self):
        return self.name_or_nothing() + f"{self.left.name_or_repr()} << {self.right.name_or_repr()}"


class RepeatedOnceParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, state: State, reader: Reader[Input]):
        status = self.parser.cached_consume(state, reader)

        if status is None:
            return None
        else:
            output = [status.value]
            remainder = status.remainder
            while True:
                status = self.parser.cached_consume(state, remainder)
                if isinstance(status, Continue):
                    if remainder.position == status.remainder.position:
                        raise RecursionError(self, remainder)

                    remainder = status.remainder
                    output.append(status.value)
                else:
                    return Continue(remainder, output)

    def __repr__(self):
        return self.name_or_nothing() + f"rep1({self.parser.name_or_repr()})"


def rep1(parser: Union[Parser[Input, Output], Sequence[Input]]) -> RepeatedOnceParser[Input, Output]:
    """Match a parser one or more times repeatedly.

    This matches ``parser`` multiple times in a row. If it matches as least
    once, it returns a list of values from each time ``parser`` matched. If it
    does not match ``parser`` at all, it fails. This parser is shorthand for
    ``rep(parser, min=1)``.

    Args:
        parser: Parser or literal
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return RepeatedOnceParser(parser)


class RepeatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], *, min: int = 0, max: Optional[int] = None):
        super().__init__()
        self.parser = parser
        self.min = min
        self.max = max

    def consume(self, state: State, reader: Reader[Input]):
        output = []
        remainder = reader

        while self.max is None or len(output) < self.max:
            status = self.parser.cached_consume(state, remainder)
            if isinstance(status, Continue):
                if remainder.position == status.remainder.position:
                    raise RecursionError(self, remainder)

                remainder = status.remainder
                output.append(status.value)
            else:
                break

        if len(output) >= self.min:
            return Continue(remainder, output)
        else:
            return None

    def __repr__(self):
        min_string = f", min={self.min}" if self.min > 0 else ""
        max_string = f", max={self.max}" if self.max is not None else ""
        return self.name_or_nothing() + f"rep({self.parser.name_or_repr()}{min_string}{max_string})"


def rep(
    parser: Union[Parser, Sequence[Input]], *, min: int = 0, max: Optional[int] = None
) -> RepeatedParser[Input, Output]:
    """Match a parser zero or more times repeatedly.

    This matches ``parser`` multiple times in a row. A list is returned
    containing the value from each match. If there are no matches, an empty list
    is returned.

    Args:
        parser: Parser or literal
        min: Nonnegative integer defining the minimum number of entries matched
            before the parser can succeed
        max: Nonnegative integer defining the maximum number of entries that
            will be matched or ``None``, meaning that there is no limit
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return RepeatedParser(parser, min=min, max=max)


class RepeatedOnceSeparatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], separator: Parser[Input, Any]):
        super().__init__()
        self.parser = parser
        self.separator = separator

    def consume(self, state: State, reader: Reader[Input]):
        status = self.parser.cached_consume(state, reader)

        if status is None:
            return None
        else:
            output = [status.value]
            remainder = status.remainder
            while True:
                # If the separator matches, but the parser does not, the remainder from the last successful parser step
                # must be used, not the remainder from any separator. That is why the parser starts from the remainder
                # on the status, but remainder is not updated until after the parser succeeds.
                status = self.separator.cached_consume(state, remainder)
                if isinstance(status, Continue):
                    status = self.parser.cached_consume(state, status.remainder)
                    if isinstance(status, Continue):
                        if remainder.position == status.remainder.position:
                            raise RecursionError(self, remainder)

                        remainder = status.remainder
                        output.append(status.value)
                    else:
                        return Continue(remainder, output)
                else:
                    return Continue(remainder, output)

    def __repr__(self):
        return self.name_or_nothing() + f"rep1sep({self.parser.name_or_repr()}, {self.separator.name_or_repr()})"


def rep1sep(
    parser: Union[Parser[Input, Output], Sequence[Input]], separator: Union[Parser[Input, Any], Sequence[Input]]
) -> RepeatedOnceSeparatedParser[Input, Output]:
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
    def __init__(
        self,
        parser: Parser[Input, Output],
        separator: Parser[Input, Any],
        *,
        min: int = 0,
        max: Optional[int] = None,
    ):
        super().__init__()
        self.parser = parser
        self.separator = separator
        self.min = min
        self.max = max

    def consume(self, state: State, reader: Reader[Input]):
        status = self.parser.cached_consume(state, reader)

        if not isinstance(status, Continue):
            output = []
            remainder = reader
        else:
            output = [status.value]
            remainder = status.remainder
            while self.max is None or len(output) < self.max:
                # If the separator matches, but the parser does not, the remainder from the last successful parser step
                # must be used, not the remainder from any separator. That is why the parser starts from the remainder
                # on the status, but remainder is not updated until after the parser succeeds.
                status = self.separator.cached_consume(state, remainder)
                if isinstance(status, Continue):
                    status = self.parser.cached_consume(state, status.remainder)
                    if isinstance(status, Continue):
                        if remainder.position == status.remainder.position:
                            raise RecursionError(self, remainder)

                        remainder = status.remainder
                        output.append(status.value)
                    else:
                        break
                else:
                    break

        if len(output) >= self.min:
            return Continue(remainder, output)
        else:
            return None

    def __repr__(self):
        min_string = f", min={self.min}" if self.min > 0 else ""
        max_string = f", max={self.max}" if self.max is not None else ""
        return (
            self.name_or_nothing()
            + f"repsep({self.parser.name_or_repr()}, {self.separator.name_or_repr()}{min_string}{max_string})"
        )


def repsep(
    parser: Union[Parser[Input, Output], Sequence[Input]],
    separator: Union[Parser[Input, Any], Sequence[Input]],
    *,
    min: int = 0,
    max: Optional[int] = None,
) -> RepeatedSeparatedParser[Input, Output]:
    """Match a parser zero or more times separated by another parser.

    This matches repeated sequences of ``parser`` separated by ``separator``. A
    list is returned containing the value from each match of ``parser``. The
    values from ``separator`` are discarded. If there are no matches, an empty
    list is returned.

    Args:
        parser: Parser or literal
        separator: Parser or literal
        min: Nonnegative integer defining the minimum number of entries matched
            before the parser can succeed
        max: Nonnegative integer defining the maximum number of entries that
            will be matched or ``None``, meaning that there is no limit
    """
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatedSeparatedParser(parser, separator, min=min, max=max)


class ConversionParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(self, parser: Parser[Input, Output], converter: Callable[[Output], Convert]):
        super().__init__()
        self.parser = parser
        self.converter = converter

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Convert]]:
        status = self.parser.cached_consume(state, reader)

        if isinstance(status, Continue):
            return Continue(status.remainder, self.converter(status.value))
        else:
            return None

    def __repr__(self):
        return self.name_or_nothing() + repr(self.parser)


class TransformationParser(Generic[Input, Output, Convert], Parser[Input, Convert]):
    def __init__(self, parser: Parser[Input, Output], transformer: Callable[[Output], Parser[Output, Convert]]):
        super().__init__()
        self.parser = parser
        self.transformer = transformer

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Convert]]:
        status = self.parser.cached_consume(state, reader)

        if isinstance(status, Continue):
            return self.transformer(status.value).cached_consume(state, status.remainder)
        else:
            return status


class DebugParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(
        self,
        parser: Parser[Input, Output],
        verbose: bool = False,
        callback: Callable[[Parser[Input, Output], Reader[Input]], None] = None,
    ):
        super().__init__()
        self.parser = parser
        self.verbose = verbose
        self.callback = callback
        self._parser_string = repr(parser)

    def consume(self, state: State, reader: Reader[Input]):
        if self.verbose:
            print(f"""Evaluating token {reader.next_token()} using parser {self._parser_string}""")

        if self.callback:
            self.callback(self.parser, reader)

        result = self.parser.cached_consume(state, reader)

        if self.verbose:
            print(f"""Result {result!r}""")

        return result

    def __repr__(self):
        return self.name_or_nothing() + f"debug({self.parser.name_or_repr()})"


def debug(
    parser: Parser[Input, Output],
    *,
    verbose: bool = False,
    callback: Optional[Callable[[Parser[Input, Output], Reader[Input]], None]] = None,
) -> DebugParser:
    """Execute debugging hooks before a parser.

    This parser is used purely for debugging purposes. From a parsing
    perspective, it behaves identically to the provided ``parser``, which makes
    ``debug`` a kind of harmless wrapper around a another parser. The
    functionality of the ``debug`` comes from providing one or more of the
    optional arguments.

    Args:
        parser: Parser or literal
        verbose: If True, causes a message to be printed containing the
            representation of ``parser`` and the next token before the
            invocation of ``parser``. After ``parser`` returns, the
            ``ParseResult`` returned is printed.
        callback: If not ``None``, is invoked immediately before ``parser`` is
            invoked. This allows the use to inspect the state of the input or
            add breakpoints before the possibly troublesome parser is invoked.
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return DebugParser(parser, verbose, callback)


class EndOfSourceParser(Generic[Input], Parser[Input, None]):
    def __init__(self):
        super().__init__()

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, None]]:
        if reader.finished:
            return Continue(reader, None)
        else:
            state.register_failure("end of source", reader)
            return None

    def __repr__(self):
        return self.name_or_nothing() + "eof"


eof = EndOfSourceParser()


class SuccessParser(Generic[Output], Parser[Any, Output]):
    def __init__(self, value: Output):
        super().__init__()
        self.value = value

    def consume(self, state: State, reader: Reader[Input]) -> Continue[Input, None]:
        return Continue(reader, self.value)

    def __repr__(self):
        return self.name_or_nothing() + f"success({self.value!r})"


def success(value: Output) -> SuccessParser[Input, Output]:
    """Always succeed in matching and return a value.

    This parser always succeeds and returns the given ``value``. No input is
    consumed. This is useful for inserting arbitrary values into complex
    parsers.

    Args:
        value: Any value
    """
    return SuccessParser(value)


class FailureParser(Generic[Input], Parser[Input, NoReturn]):
    def __init__(self, expected: str):
        super().__init__()
        self.expected = expected

    def consume(self, state: State, reader: Reader[Input]) -> None:
        state.register_failure(self.expected, reader)
        return None

    def __repr__(self):
        return self.name_or_nothing() + f"failure({self.expected!r})"


def failure(expected: str = "") -> FailureParser[Input]:
    """Always fail in matching with a given message.

    This parser always backtracks with a message that it is expecting the
    given ``expected``. This is useful for appending to parsers that are
    expected to be seen in the input, but are not valid so that a more useful
    error message can be given.

    Args:
        expected: Message to be conveyed
    """
    return FailureParser(expected)


class UntilParser(Generic[Input], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Any]):
        super().__init__()
        self.parser = parser

    def consume(self, state: State, reader: Reader[Input]):
        start_position = reader.position
        while True:
            status = self.parser.cached_consume(state, reader)

            if isinstance(status, Continue):
                break
            elif reader.finished:
                return status
            else:
                reader = reader.rest

        return Continue(reader, reader.source[start_position : reader.position])

    def __repr__(self):
        return self.name_or_nothing() + f"until({self.parser.name_or_repr()})"


def until(parser: Parser[Input, Output]) -> UntilParser:
    """Match everything until it matches the provided parser.

    This parser matches all input until it encounters a position in the input
    where the given ``parser`` succeeds.

    Args:
        parser: Parser or literal
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return UntilParser(parser)


class AnyParser(Generic[Input], Parser[Input, Input]):
    """Match any single element.

    This parser matches any single element, returning it. This is useful when it
    does not matter what is at this position or when validation is deferred to a
    later step, such as with the ``pred`` parser. This parser can only fail at
    the end of the stream.
    """

    def __init__(self):
        super().__init__()

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Input]]:
        if reader.finished:
            state.register_failure("anything", reader)
            return None
        else:
            return Continue(reader.rest, reader.first)

    def __repr__(self):
        return self.name_or_nothing() + "any1"


any1 = AnyParser()


__all__ = [
    "Parser",
    "LiteralParser",
    "LiteralStringParser",
    "lit",
    "RegexParser",
    "reg",
    "OptionalParser",
    "opt",
    "AlternativeParser",
    "first",
    "LongestAlternativeParser",
    "longest",
    "SequentialParser",
    "DiscardLeftParser",
    "DiscardRightParser",
    "RepeatedOnceParser",
    "rep1",
    "RepeatedParser",
    "rep",
    "RepeatedOnceSeparatedParser",
    "rep1sep",
    "RepeatedSeparatedParser",
    "repsep",
    "ConversionParser",
    "TransformationParser",
    "DebugParser",
    "debug",
    "EndOfSourceParser",
    "eof",
    "SuccessParser",
    "success",
    "FailureParser",
    "failure",
    "PredicateParser",
    "pred",
    "UntilParser",
    "until",
    "AnyParser",
    "any1",
    "completely_parse_reader",
]
