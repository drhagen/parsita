from __future__ import annotations

__all__ = ["Continue", "Element", "Input", "Output", "State"]

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from ._reader import Reader

if TYPE_CHECKING:
    from ..parsers import Parser

Input = TypeVar("Input", contravariant=True)
Output = TypeVar("Output", covariant=True)
Element = TypeVar("Element")


class State:
    def __init__(self) -> None:
        self.farthest: Optional[Reader[object]] = None
        self.expected: list[str] = []
        self.memo: dict[tuple[Parser[Any, Any], int], Optional[Continue[Any, Any]]] = {}

    def register_failure(self, expected: str, reader: Reader[object]) -> None:
        if self.farthest is None or self.farthest.position < reader.position:
            self.expected.clear()
            self.expected.append(expected)
            self.farthest = reader
        elif self.farthest.position == reader.position:
            self.expected.append(expected)


@dataclass(frozen=True)
class Continue(Generic[Input, Output]):
    remainder: Reader[Input]
    value: Output
