__all__ = ["Result", "Success", "Failure"]

from typing import TYPE_CHECKING, TypeVar

from returns import result

from ._exceptions import ParseError

Output = TypeVar("Output")

# Reexport Returns Result types
Result = result.Result[Output, ParseError]
Success = result.Success
Failure = result.Failure
if TYPE_CHECKING:
    # This object fails in isinstance
    # Result does too, but that cannot be fixed without breaking eager type annotations
    Failure = result.Failure[ParseError]
