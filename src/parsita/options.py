__all__ = ["whitespace"]

from typing import Any, Optional

from .parsers import Parser

# Global mutable state
whitespace: Optional[Parser[Any, Any]] = None
