__all__ = ["RepeatedOnceSeparatedParser", "RepeatedSeparatedParser", "rep1sep", "repsep"]

from typing import Generic, Optional, Sequence, Union, overload

from ..state import Continue, Input, Output, Reader, RecursionError, State
from ._base import Parser, wrap_literal


class RepeatedSeparatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(
        self,
        parser: Parser[Input, Output],
        separator: Parser[Input, object],
        *,
        min: int = 0,
        max: Optional[int] = None,
    ):
        super().__init__()
        self.parser = parser
        self.separator = separator
        self.min = min
        self.max = max

    def _consume(
        self, state: State, reader: Reader[Input]
    ) -> Optional[Continue[Input, Sequence[Output]]]:
        initial_status = self.parser.consume(state, reader)

        if not isinstance(initial_status, Continue):
            output = []
            remainder = reader
        else:
            output = [initial_status.value]
            remainder = initial_status.remainder
            while self.max is None or len(output) < self.max:
                # If the separator matches, but the parser does not, the
                # remainder from the last successful parser step must be used,
                # not the remainder from any separator. That is why the parser
                # starts from the remainder on the status, but remainder is not
                # updated until after the parser succeeds.
                separator_status = self.separator.consume(state, remainder)
                if isinstance(separator_status, Continue):
                    parser_status = self.parser.consume(state, separator_status.remainder)
                    if isinstance(parser_status, Continue):
                        if remainder.position == parser_status.remainder.position:
                            raise RecursionError(self, remainder)

                        remainder = parser_status.remainder
                        output.append(parser_status.value)
                    else:
                        break
                else:
                    break

        if len(output) >= self.min:
            return Continue(remainder, output)
        else:
            return None

    def __repr__(self) -> str:
        rep_string = self.parser.name_or_repr()
        sep_string = self.separator.name_or_repr()
        min_string = f", min={self.min}" if self.min > 0 else ""
        max_string = f", max={self.max}" if self.max is not None else ""
        string = f"repsep({rep_string}, {sep_string}{min_string}{max_string})"
        return self.name_or_nothing() + string


@overload
def repsep(
    parser: Sequence[Input],
    separator: Union[Parser[Input, object], Sequence[Input]],
    *,
    min: int = 0,
    max: Optional[int] = None,
) -> RepeatedSeparatedParser[Input, Sequence[Input]]: ...


@overload
def repsep(
    parser: Parser[Input, Output],
    separator: Union[Parser[Input, object], Sequence[Input]],
    *,
    min: int = 0,
    max: Optional[int] = None,
) -> RepeatedSeparatedParser[Input, Output]: ...


def repsep(
    parser: Union[Parser[Input, Output], Sequence[Input]],
    separator: Union[Parser[Input, object], Sequence[Input]],
    *,
    min: int = 0,
    max: Optional[int] = None,
) -> RepeatedSeparatedParser[Input, object]:
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
    return RepeatedSeparatedParser(wrap_literal(parser), wrap_literal(separator), min=min, max=max)


class RepeatedOnceSeparatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], separator: Parser[Input, object]):
        super().__init__()
        self.parser = parser
        self.separator = separator

    def _consume(
        self, state: State, reader: Reader[Input]
    ) -> Optional[Continue[Input, Sequence[Output]]]:
        initial_status = self.parser.consume(state, reader)

        if initial_status is None:
            return None
        else:
            output = [initial_status.value]
            remainder = initial_status.remainder
            while True:
                # If the separator matches, but the parser does not, the
                # remainder from the last successful parser step must be used,
                # not the remainder from any separator. That is why the parser
                # starts from the remainder on the status, but remainder is not
                # updated until after the parser succeeds.
                separator_status = self.separator.consume(state, remainder)
                if isinstance(separator_status, Continue):
                    parser_status = self.parser.consume(state, separator_status.remainder)
                    if isinstance(parser_status, Continue):
                        if remainder.position == parser_status.remainder.position:
                            raise RecursionError(self, remainder)

                        remainder = parser_status.remainder
                        output.append(parser_status.value)
                    else:
                        return Continue(remainder, output)
                else:
                    return Continue(remainder, output)

    def __repr__(self) -> str:
        string = f"rep1sep({self.parser.name_or_repr()}, {self.separator.name_or_repr()})"
        return self.name_or_nothing() + string


@overload
def rep1sep(
    parser: Sequence[Input], separator: Union[Parser[Input, object], Sequence[Input]]
) -> RepeatedOnceSeparatedParser[Input, Sequence[Input]]: ...


@overload
def rep1sep(
    parser: Parser[Input, Output], separator: Union[Parser[Input, object], Sequence[Input]]
) -> RepeatedOnceSeparatedParser[Input, Output]: ...


def rep1sep(
    parser: Union[Parser[Input, Output], Sequence[Input]],
    separator: Union[Parser[Input, object], Sequence[Input]],
) -> RepeatedOnceSeparatedParser[Input, object]:
    """Match a parser one or more times separated by another parser.

    This matches repeated sequences of ``parser`` separated by ``separator``.
    If there is at least one match, a list containing the values of the
    ``parser`` matches is returned. The values from ``separator`` are discarded.
    If it does not match ``parser`` at all, it fails.

    Args:
        parser: Parser or literal
        separator: Parser or literal
    """
    return RepeatedOnceSeparatedParser(wrap_literal(parser), wrap_literal(separator))
