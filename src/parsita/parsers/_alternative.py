__all__ = ["AlternativeParser", "first", "LongestAlternativeParser", "longest"]

from typing import Generic, Optional, Sequence, Union

from ..reader import Reader
from ..state import Continue, Input, Output, State
from ._base import Parser
from ._literal import lit


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
