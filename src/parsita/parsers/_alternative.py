__all__ = ["FirstAlternativeParser", "LongestAlternativeParser", "first", "longest"]

from typing import Generic, Optional, Sequence, Union, overload

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser, wrap_literal


class FirstAlternativeParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, parser: Parser[Input, Output], *parsers: Parser[Input, Output]):
        super().__init__()
        self.parsers = (parser, *parsers)

    def _consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        for parser in self.parsers:
            status = parser.consume(state, reader)
            if isinstance(status, Continue):
                return status

        return None

    def __repr__(self) -> str:
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + f"first({', '.join(names)})"


@overload
def first(
    parser: Union[Parser[Input, Output], Sequence[Input]],
    *parsers: Union[Parser[Input, Output], Sequence[Input]],
) -> FirstAlternativeParser[Input, Sequence[Input]]:
    # This signature is not quite right because Python has no higher-kinded
    # types to express that Output must be a subtype of Sequence[Input].
    ...


@overload
def first(
    parser: Parser[Input, Output],
    *parsers: Parser[Input, Output],
) -> FirstAlternativeParser[Input, Output]: ...


def first(
    parser: Union[Parser[Input, Output], Sequence[Input]],
    *parsers: Union[Parser[Input, Output], Sequence[Input]],
) -> FirstAlternativeParser[Input, Union[Output, Sequence[Input]]]:
    """Match the first of several alternative parsers.

    An ``AlternativeParser`` attempts to match each supplied parser. If a parser
    succeeds, its result is immediately returned and later parsers are not
    attempted. If all parsers fail, a failure is returned.

    There is a similar function ``longest`` that instead returns the result of
    the parser that makes the farthest successful progress. The ``|`` operator
    is syntactic sugar for ``longest``.

    Args:
        *parsers: Non-empty list of ``Parser``s or literals to try
    """
    cleaned_parsers = [wrap_literal(parser_i) for parser_i in [parser, *parsers]]
    return FirstAlternativeParser(*cleaned_parsers)


class LongestAlternativeParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, parser: Parser[Input, Output], *parsers: Parser[Input, Output]):
        super().__init__()
        self.parsers = (parser, *parsers)

    def _consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        longest_success: Optional[Continue[Input, Output]] = None
        for parser in self.parsers:
            status = parser.consume(state, reader)
            if isinstance(status, Continue):
                if (
                    longest_success is None
                    or status.remainder.position > longest_success.remainder.position
                ):
                    longest_success = status

        return longest_success

    def __repr__(self) -> str:
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return self.name_or_nothing() + " | ".join(names)


# This signature is not quite right because Python has no higher-kinded
# types to express that Output must be a subtype of Sequence[Input].
@overload
def longest(
    parser: Union[Parser[Input, Output], Sequence[Input]],
    *parsers: Union[Parser[Input, Output], Sequence[Input]],
) -> LongestAlternativeParser[Input, Sequence[Input]]: ...


@overload
def longest(
    parser: Parser[Input, Output],
    *parsers: Parser[Input, Output],
) -> LongestAlternativeParser[Input, Output]: ...


def longest(
    parser: Union[Parser[Input, Output], Sequence[Input]],
    *parsers: Union[Parser[Input, Output], Sequence[Input]],
) -> LongestAlternativeParser[Input, Union[Output, Sequence[Input]]]:
    """Match the longest of several alternative parsers.

    A ``LongestAlternativeParser`` attempts to match all supplied parsers. If
    multiple parsers succeed, the result of the one that makes the farthest
    successful progress is returned. If all parsers fail, a failure is returned.
    If multiple alternatives succeed with the same progress, the first one is
    returned.

    The ``|`` operator is syntactic sugar for this function.
    ``parser1 | parser2`` is equivalent to ``longest(parser1, parser2)``.

    Args:
        *parsers: Non-empty list of ``Parser``s or literals to try
    """
    cleaned_parsers = [wrap_literal(parser_i) for parser_i in [parser, *parsers]]
    return LongestAlternativeParser(*cleaned_parsers)
