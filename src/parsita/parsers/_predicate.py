__all__ = ["PredicateParser", "pred"]

from typing import Callable, Generic, Optional

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser, wrap_literal


class PredicateParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(
        self, parser: Parser[Input, Output], predicate: Callable[[Output], bool], description: str
    ):
        super().__init__()
        self.parser = parser
        self.predicate = predicate
        self.description = description

    def _consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        status = self.parser.consume(state, reader)
        if isinstance(status, Continue):
            if self.predicate(status.value):
                return status
            else:
                state.register_failure(self.description, status.remainder)
                return None
        else:
            return status

    def __repr__(self) -> str:
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
