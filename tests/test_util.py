from unittest import TestCase

from parsita.util import *


class ConstantTestCase(TestCase):
    def test_constant(self):
        a = constant(1)

        self.assertEqual(a(2), 1)
        self.assertEqual(a("hello", 2), 1)
        self.assertEqual(a("hello", 2, key=None), 1)


class SplatTestCase(TestCase):
    def test_splat(self):
        def f(a, b, c):
            return a + b + c

        self.assertEqual(f(1, 2, 3), 6)

        g = splat(f)
        args = [1, 2, 3]
        self.assertEqual(g(args), 6)

    def test_unsplat(self):
        def f(a):
            return a[0] + a[1] + a[2]

        args = [1, 2, 3]
        self.assertEqual(f(args), 6)

        g = unsplat(f)
        self.assertEqual(g(1, 2, 3), 6)
