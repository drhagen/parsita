from parsita import TextParsers, lit, Failure, Success
from parsita.parsers import debug
from parsita.util import *


def test_constant():
    a = constant(1)

    assert a(2) == 1
    assert a("hello", 2) == 1
    assert a("hello", 2, key=None) == 1


def test_splat():
    def f(a, b, c):
        return a + b + c

    assert f(1, 2, 3) == 6

    g = splat(f)
    args = [1, 2, 3]
    assert g(args) == 6


def test_unsplat():
    def f(a):
        return a[0] + a[1] + a[2]

    args = [1, 2, 3]
    assert f(args) == 6

    g = unsplat(f)
    assert g(1, 2, 3) == 6


def test_debug():
    result = False

    def debug_cb(parser, reader):
        nonlocal result
        remainder = reader.source[reader.position:]
        result = remainder == '45'
        result &= isinstance(parser.parse(remainder), Failure)
        result &= isinstance(parser.parse('345'), Success)

    class TestParsers(TextParsers):
        a = lit('123')
        b = lit('345')
        c = a & debug(b, debug_callback=debug_cb)

    TestParsers.c.parse('12345')
    assert result
