from parsita.util import constant, splat, unsplat


def test_constant():
    a = constant(1)

    assert a(2) == 1
    assert a("hello", 2) == 1
    assert a("hello", 2, key=None) == 1


def test_splat():
    def f(a: int, b: int, c: int) -> int:
        return a + b + c

    assert f(1, 2, 3) == 6

    g = splat(f)
    args = (1, 2, 3)
    assert g(args) == 6


def test_unsplat():
    def f(a: tuple[int, int, int]) -> int:
        return a[0] + a[1] + a[2]

    args = (1, 2, 3)
    assert f(args) == 6

    g = unsplat(f)
    assert g(1, 2, 3) == 6
