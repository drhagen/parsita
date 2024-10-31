from __future__ import annotations

__all__ = ["ParseError", "RecursionError"]

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ._reader import Reader

if TYPE_CHECKING:
    from ..parsers import Parser


@dataclass(frozen=True)
class ParseError(Exception):
    """Parsing failure.

    The container for the error of failed parsing.
    """

    farthest: Reader[Any]
    expected: list[str]

    def __str__(self) -> str:
        return self.farthest.expected_error(self.expected)


@dataclass(frozen=True)
class RecursionError(Exception):
    """Recursion failure.

    Error for when repeated parsers fail to consume input.
    """

    parser: Parser[Any, Any]
    context: Reader[Any]

    def __str__(self) -> str:
        return self.context.recursion_error(repr(self.parser))
