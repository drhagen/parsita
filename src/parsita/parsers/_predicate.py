__all__ = ["PredicateParser", "pred"]

from typing import Callable, Generic

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser, wrap_literal


class PredicateParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(
        self, parser: Parser[Input, Output], predicate: Callable[[Output], bool], description: str
    ):
        super().__init__()
        self.parser = parser
        self.predicate = predicate
        self.description = description

    def consume(self, state: State[Input], reader: Reader[Input]):
        status = self.parser.cached_consume(state, reader)
        if isinstance(status, Continue):
            if self.predicate(status.value):
                return status
            else:
                state.register_failure(self.description, status.remainder)
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
        parser: ``Parser`` or literal
        predicate: A predicate for the result to satisfy
        description: Name for the predicate, to use in error reporting

    Returns:
        A ``PredicateParser``.
    """
    return PredicateParser(wrap_literal(parser), predicate, description)
