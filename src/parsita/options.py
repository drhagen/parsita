__all__ = ["whitespace"]

from .parsers import Parser
from .state import Input

# Global mutable state
whitespace: Parser[Input, Input] = None
