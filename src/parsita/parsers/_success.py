__all__ = ["SuccessParser", "success", "FailureParser", "failure"]

from typing import Any, Generic, NoReturn

from ..state import Continue, Input, Output, Reader, State
from ._base import Parser


class SuccessParser(Generic[Input, Output], Parser[Any, Output]):
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
