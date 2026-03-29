__all__ = ["whitespace"]

from typing import Any

from .parsers import Parser

# Global mutable state
whitespace: Parser[Any, Any] | None = None
