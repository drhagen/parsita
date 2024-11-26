__all__ = ["Failure", "Result", "Success"]

from typing import TypeVar

from returns import result

from ._exceptions import ParseError

Output = TypeVar("Output")

# Reexport Returns Result types
# Failure and Result fail in isinstance
# Failure is replaced by plain Failure, which works at runtime
# Result is left as is because cannot be fixed without breaking eager type annotations
Result = result.Result[Output, ParseError]
Success = result.Success
Failure: type[result.Failure[ParseError]] = result.Failure[ParseError]
Failure = result.Failure
