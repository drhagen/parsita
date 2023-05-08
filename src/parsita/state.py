from __future__ import annotations

__all__ = ["Input", "Output", "State", "Continue"]

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional, Tuple, TypeVar

from .reader import Reader

if TYPE_CHECKING:
    from .parsers import Parser

Input = TypeVar("Input")
Output = TypeVar("Output")


class State:
    def __init__(self):
        self.farthest: Optional[Reader[Any]] = None
        self.expected: List[str] = []
        self.memo: Dict[Tuple[Parser[Any, Any], int], Optional[Continue[Any, Any]]] = {}

    def register_failure(self, expected: str, reader: Reader[Any]):
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
