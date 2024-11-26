__all__ = ["FailureParser", "SuccessParser", "failure", "success"]

from typing import Generic, NoReturn, TypeVar

from ..state import Continue, Output, Reader, State
from ._base import Parser

FunctionInput = TypeVar("FunctionInput")
FunctionOutput = TypeVar("FunctionOutput")


class SuccessParser(Generic[Output], Parser[object, Output]):
    def __init__(self, value: Output):
        super().__init__()
        self.value = value

    def _consume(
        self, state: State, reader: Reader[FunctionInput]
    ) -> Continue[FunctionInput, Output]:
        return Continue(reader, self.value)

    def __repr__(self) -> str:
        return self.name_or_nothing() + f"success({self.value!r})"


def success(value: FunctionOutput) -> SuccessParser[FunctionOutput]:
    """Always succeed in matching and return a value.

    This parser always succeeds and returns the given ``value``. No input is
    consumed. This is useful for inserting arbitrary values into complex
    parsers.

    Args:
        value: Any value
    """
    return SuccessParser(value)


class FailureParser(Parser[object, NoReturn]):
    def __init__(self, expected: str):
        super().__init__()
        self.expected = expected

    def _consume(self, state: State, reader: Reader[object]) -> None:
        state.register_failure(self.expected, reader)
        return None

    def __repr__(self) -> str:
        return self.name_or_nothing() + f"failure({self.expected!r})"


def failure(expected: str = "") -> FailureParser:
    """Always fail in matching with a given message.

    This parser always backtracks with a message that it is expecting the
    given ``expected``. This is useful for appending to parsers that are
    expected to be seen in the input, but are not valid so that a more useful
    error message can be given.

    Args:
        expected: Message to be conveyed
    """
    return FailureParser(expected)
