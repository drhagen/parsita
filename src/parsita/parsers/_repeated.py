__all__ = ["RepeatedOnceParser", "RepeatedParser", "rep", "rep1"]

from typing import Generic, Optional, Sequence, Union, overload

from ..state import Continue, Input, Output, Reader, RecursionError, State
from ._base import Parser, wrap_literal


class RepeatedOnceParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

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
                status = self.parser.consume(state, remainder)
                if isinstance(status, Continue):
                    if remainder.position == status.remainder.position:
                        raise RecursionError(self, remainder)

                    remainder = status.remainder
                    output.append(status.value)
                else:
                    return Continue(remainder, output)

    def __repr__(self) -> str:
        return self.name_or_nothing() + f"rep1({self.parser.name_or_repr()})"


@overload
def rep1(parser: Sequence[Input]) -> RepeatedOnceParser[Input, Sequence[Input]]: ...


@overload
def rep1(parser: Parser[Input, Output]) -> RepeatedOnceParser[Input, Output]: ...


def rep1(
    parser: Union[Parser[Input, Output], Sequence[Input]],
) -> RepeatedOnceParser[Input, object]:
    """Match a parser one or more times repeatedly.

    This matches ``parser`` multiple times in a row. If it matches as least
    once, it returns a list of values from each time ``parser`` matched. If it
    does not match ``parser`` at all, it fails. This parser is shorthand for
    ``rep(parser, min=1)``.

    Args:
        parser: Parser or literal
    """
    return RepeatedOnceParser(wrap_literal(parser))


class RepeatedParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], *, min: int = 0, max: Optional[int] = None):
        super().__init__()
        self.parser = parser
        self.min = min
        self.max = max

    def _consume(
        self, state: State, reader: Reader[Input]
    ) -> Optional[Continue[Input, Sequence[Output]]]:
        output: list[Output] = []
        remainder = reader

        while self.max is None or len(output) < self.max:
            status = self.parser.consume(state, remainder)
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

    def __repr__(self) -> str:
        min_string = f", min={self.min}" if self.min > 0 else ""
        max_string = f", max={self.max}" if self.max is not None else ""
        string = f"rep({self.parser.name_or_repr()}{min_string}{max_string})"
        return self.name_or_nothing() + string


@overload
def rep(
    parser: Sequence[Input],
    *,
    min: int = 0,
    max: Optional[int] = None,
) -> RepeatedParser[Input, Sequence[Input]]: ...


@overload
def rep(
    parser: Parser[Input, Output],
    *,
    min: int = 0,
    max: Optional[int] = None,
) -> RepeatedParser[Input, Output]: ...


def rep(
    parser: Union[Parser[Input, Output], Sequence[Input]],
    *,
    min: int = 0,
    max: Optional[int] = None,
) -> RepeatedParser[Input, object]:
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
    return RepeatedParser(wrap_literal(parser), min=min, max=max)
