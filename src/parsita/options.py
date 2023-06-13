__all__ = ["whitespace"]

from typing import Any

from .parsers import Parser
from .state import Input

# Global mutable state
whitespace: Parser[Input, Any] = None
