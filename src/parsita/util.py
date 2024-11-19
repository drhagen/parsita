from __future__ import annotations

__all__ = ["constant", "splat", "unsplat"]

from typing import TYPE_CHECKING, Any, Callable, Sequence

if TYPE_CHECKING:
    # ParamSpec was introduced in Python 3.10
    # TypeVarTuple and Unpack were introduced in Python 3.11
    from typing import ParamSpec, TypeVar, TypeVarTuple, Unpack

    A = TypeVar("A")
    P = ParamSpec("P")
    Ts = TypeVarTuple("Ts")


def constant(x: A) -> Callable[P, A]:
    """Produce a function that always returns a supplied value.

    Args:
        x: Any object.

    Returns:
        A function that accepts any number of positional and keyword arguments,
        discards them, and returns ``x``.
    """

    def constanted(*args: P.args, **kwargs: P.kwargs) -> A:
        return x

    return constanted


# This signature cannot be expressed narrowly because SequenceParser does not return a tuple
def splat(f: Callable[[Unpack[Ts]], A], /) -> Callable[[Sequence[Any]], A]:
    """Convert a function of multiple arguments into a function of a single iterable argument.

    Args:
        f: Any function

    Returns:
        A function that accepts a single iterable argument. Each element of this
        iterable argument is passed as an argument to ``f``.

    Example:
        $ def f(a, b, c):
        $     return a + b + c
        $
        $ f(1, 2, 3)  # 6
        $ g = splat(f)
        $ g([1, 2, 3])  # 6
    """

    def splatted(args: Sequence[Any], /) -> A:
        return f(*args)

    return splatted


def unsplat(f: Callable[[tuple[Unpack[Ts]]], A]) -> Callable[..., A]:
    """Convert a function of a single iterable argument into a function of multiple arguments.

    Args:
        f: Any function taking a single iterable argument

    Returns:
        A function that accepts multiple arguments. Each argument of this
        function is passed as an element of an iterable to ``f``.

    Example:
        $ def f(a):
        $     return a[0] + a[1] + a[2]
        $
        $ f([1, 2, 3])  # 6
        $ g = unsplat(f)
        $ g(1, 2, 3)  # 6
    """

    def unsplatted(*args: Unpack[Ts]) -> A:
        return f(args)

    return unsplatted
