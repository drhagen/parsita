from typing import Callable, TypeVar, Iterable

A = TypeVar('A')


def constant(x: A) -> Callable[..., A]:
    """Produce a function that always returns a supplied value.

    Args:
        x: Any object.

    Returns:
        A function that accepts any number of positional and keyword arguments, discards them, and returns ``x``.
    """

    def constanted(*args, **kwargs):
        return x

    return constanted


def splat(f: Callable[..., A]) -> Callable[[Iterable], A]:
    """Convert a function taking multiple arguments into a function taking a single iterable argument.

    Args:
        f: Any function

    Returns:
        A function that accepts a single iterable argument. Each element of this iterable argument is passed as an
        argument to ``f``.

    Example:
        $ def f(a, b, c):
        $     return a + b + c
        $
        $ f(1, 2, 3)  # 6
        $ g = splat(f)
        $ g([1, 2, 3])  # 6
    """

    def splatted(args):
        return f(*args)

    return splatted


def unsplat(f: Callable[[Iterable], A]) -> Callable[..., A]:
    """Convert a function taking a single iterable argument into a function taking multiple arguments.

    Args:
        f: Any function taking a single iterable argument

    Returns:
        A function that accepts multiple arguments. Each argument of this function is passed as an element of an
        iterable to ``f``.

    Example:
        $ def f(a):
        $     return a[0] + a[1] + a[2]
        $
        $ f([1, 2, 3])  # 6
        $ g = unsplat(f)
        $ g(1, 2, 3)  # 6
    """

    def unsplatted(*args):
        return f(args)

    return unsplatted


__all__ = ['constant', 'splat', 'unsplat']
