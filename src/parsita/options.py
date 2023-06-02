__all__ = [
    "default_whitespace",
    "whitespace",
    "default_handle_literal",
    "wrap_literal",
    "handle_literal",
]
import re
from typing import Any, Sequence

from .state import Input

# Global mutable state

default_whitespace = re.compile(r"\s*")
whitespace = None


# PyCharm does not understand type hint on handle_literal, so this signature is more general
def default_handle_literal(literal: Any):
    from .parsers import LiteralStringParser

    return LiteralStringParser(literal, whitespace)


def wrap_literal(literal: Sequence[Input]):
    from .parsers import LiteralParser

    return LiteralParser(literal)


handle_literal = default_handle_literal
