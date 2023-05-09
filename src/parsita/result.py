__all__ = ["Result", "Success", "Failure"]

from typing import TYPE_CHECKING

from returns import result

from .exceptions import ParseError
from .state import Output

# Reexport Returns Result types
Result = result.Result[Output, ParseError]
Success = result.Success
Failure = result.Failure
if TYPE_CHECKING:
    # This object fails in isinstance
    # Result does too, but that cannot be fixed without breaking eager type annotations
    Failure = result.Failure[ParseError]
