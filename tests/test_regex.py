from unittest import TestCase

from parsita import *


class LiteralTestCase(TestCase):
    def test_literal(self):
        class TestParsers(TextParsers):
            hundred = lit('100') > float

        self.assertEqual(TestParsers.hundred.parse(''), Failure("Expected '100' but found end of source"))
        self.assertEqual(TestParsers.hundred.parse('100'), Success(100))
        self.assertEqual(TestParsers.hundred.parse('   100'), Success(100))
        self.assertEqual(TestParsers.hundred.parse('100    '), Success(100))
        self.assertEqual(TestParsers.hundred.parse('   100    '), Success(100))
        self.assertEqual(str(TestParsers.hundred), "hundred = '100'")

    def test_no_whitespace(self):
        class TestParsers(TextParsers, whitespace=None):
            hundred = lit('100') > float

        self.assertEqual(TestParsers.hundred.parse('100'), Success(100))
        self.assertEqual(TestParsers.hundred.parse(' 100'),
                         Failure("Expected '100' but found ' '\nLine 1, character 1\n\n 100\n^   "))
        self.assertEqual(TestParsers.hundred.parse('100 '),
                         Failure("Expected end of source but found ' '\nLine 1, character 4\n\n100 \n   ^"))
        self.assertEqual(str(TestParsers.hundred), "hundred = '100'")


class RegexTestCase(TestCase):
    def test_regex(self):
        class TestParsers(TextParsers):
            digits = reg(r'\d+') > float

        self.assertEqual(TestParsers.digits.parse('100'), Success(100))
        self.assertEqual(TestParsers.digits.parse('   100'), Success(100))
        self.assertEqual(TestParsers.digits.parse('100    '), Success(100))
        self.assertEqual(TestParsers.digits.parse('   100    '), Success(100))
        self.assertEqual(str(TestParsers.digits), r"digits = reg(r'\d+')")

    def test_no_whitespace(self):
        class TestParsers(TextParsers, whitespace=None):
            digits = reg(r'\d+') > float

        self.assertEqual(TestParsers.digits.parse('100'), Success(100))
        self.assertEqual(TestParsers.digits.parse(' 100'),
                         Failure("Expected r'\\d+' but found ' '\nLine 1, character 1\n\n 100\n^   "))
        self.assertEqual(TestParsers.digits.parse('100 '),
                         Failure("Expected end of source but found ' '\nLine 1, character 4\n\n100 \n   ^"))
        self.assertEqual(str(TestParsers.digits), r"digits = reg(r'\d+')")

    def test_custom_whitespace(self):
        class TestParsers(TextParsers, whitespace='[ ]*'):
            digits = reg(r'\d+') > float
            pair = digits & digits

        self.assertEqual(TestParsers.digits.parse('100'), Success(100))
        self.assertEqual(TestParsers.digits.parse('   100    '), Success(100))
        self.assertEqual(TestParsers.digits.parse('100\n'),
                         Failure("Expected end of source but found '\\n'\nLine 1, character 4\n\n100\n   ^"))
        self.assertEqual(TestParsers.digits.parse('100 \n'),
                         Failure("Expected end of source but found '\\n'\nLine 1, character 5\n\n100 \n    ^"))
        self.assertEqual(TestParsers.pair.parse('100 100'), Success([100, 100]))
        self.assertEqual(TestParsers.pair.parse('100\n100'),
                         Failure("Expected r'\\d+' but found '\\n'\nLine 1, character 4\n\n100\n   ^"))
        self.assertEqual(str(TestParsers.digits), r"digits = reg(r'\d+')")
        self.assertEqual(str(TestParsers.pair), 'pair = digits & digits')


class OptionalTestCase(TestCase):
    def test_optional(self):
        class TestParsers(TextParsers):
            a = reg(r'\d+') > float
            b = opt(a)

        self.assertEqual(TestParsers.b.parse(' 100 '), Success([100]))
        self.assertEqual(TestParsers.b.parse(' c '),
                         Failure("Expected r'\\d+' but found 'c'\nLine 1, character 2\n\n c \n ^ "))
        self.assertEqual(str(TestParsers.b), 'b = opt(a)')


class SequentialTestCase(TestCase):
    def test_sequential(self):
        class TestParsers(TextParsers):
            hello = lit('Hello')
            world = lit('world')
            hello_world = hello & world

        self.assertEqual(TestParsers.hello_world.parse('Hello world'), Success(['Hello', 'world']))
        self.assertEqual(TestParsers.hello_world.parse('Hello David'),
                         Failure("Expected 'world' but found 'David'\nLine 1, character 7\n\nHello David\n      ^    "))
        self.assertEqual(TestParsers.hello_world.parse('Hello'), Failure("Expected 'world' but found end of source"))

    def test_multiline(self):
        class TestParsers(TextParsers):
            hello = lit('Hello')
            world = lit('world')
            hello_world = hello & world

        self.assertEqual(TestParsers.hello_world.parse('Hello\nworld'), Success(['Hello', 'world']))
        self.assertEqual(TestParsers.hello_world.parse('Hello\nDavid'),
                         Failure("Expected 'world' but found 'David'\nLine 2, character 1\n\nDavid\n^    "))


class RepeatedTestCase(TestCase):
    def test_repeated(self):
        class TestParsers(TextParsers):
            number = reg(r'\d+') > int
            trail = '(' >> rep(number << ',') << ')' > tuple
            trail1 = '(' >> rep1(number << ',') << ')' > tuple
            notrail = '(' >> repsep(number, ',') << ')' > tuple
            notrail1 = '(' >> rep1sep(number, ',') << ')' > tuple

        self.assertEqual(TestParsers.trail.parse('(1,2,3)'),
                         Failure("Expected ',' but found ')'\nLine 1, character 7\n\n(1,2,3)\n      ^"))
        self.assertEqual(TestParsers.trail.parse('(1,2,3,)'), Success((1, 2, 3)))
        self.assertEqual(TestParsers.trail.parse('()'), Success(()))
        self.assertEqual(TestParsers.trail1.parse('(1,2,3)'),
                         Failure("Expected ',' but found ')'\nLine 1, character 7\n\n(1,2,3)\n      ^"))
        self.assertEqual(TestParsers.trail1.parse('(1,2,3,)'), Success((1, 2, 3)))
        self.assertEqual(TestParsers.trail1.parse('()'),
                         Failure("Expected r'\\d+' but found ')'\nLine 1, character 2\n\n()\n ^"))
        self.assertEqual(TestParsers.notrail.parse('(1,2,3)'), Success((1, 2, 3)))
        self.assertEqual(TestParsers.notrail.parse('(1,2,3,)'),
                         Failure("Expected r'\\d+' but found ')'\nLine 1, character 8\n\n(1,2,3,)\n       ^"))
        self.assertEqual(TestParsers.notrail.parse('()'), Success(()))
        self.assertEqual(TestParsers.notrail1.parse('(1,2,3)'), Success((1, 2, 3)))
        self.assertEqual(TestParsers.notrail1.parse('(1,2,3,)'),
                         Failure("Expected r'\\d+' but found ')'\nLine 1, character 8\n\n(1,2,3,)\n       ^"))
        self.assertEqual(TestParsers.notrail1.parse('()'),
                         Failure("Expected r'\\d+' but found ')'\nLine 1, character 2\n\n()\n ^"))


class RecursionTestCase(TestCase):
    def test_literals(self):
        class TestParsers(TextParsers):
            one = lit('1') > float
            six = lit('6') > float
            eleven = lit('11') > float

            numbers = eleven | one | six

            def make_expr(x):
                digits1, maybe_expr = x
                if maybe_expr:
                    digits2 = maybe_expr[0]
                    return digits1 + digits2
                else:
                    return digits1

            expr = numbers & opt('+' >> expr) > make_expr

        self.assertEqual(TestParsers.expr.parse('11'), Success(11))
        self.assertEqual(TestParsers.expr.parse('6 + 11'), Success(17))
        self.assertEqual(TestParsers.expr.parse('1 +6  + 6'), Success(13))

    def test_regex(self):
        class TestParsers(TextParsers, whitespace='[ ]*'):
            digits = reg(r'\d+') > float

            def make_expr(x):
                digits1, maybe_expr = x
                if maybe_expr:
                    digits2 = maybe_expr[0]
                    return digits1 + digits2
                else:
                    return digits1
            expr = digits & opt('+' >> expr) > make_expr

        self.assertEqual(TestParsers.expr.parse('34'), Success(34))
        self.assertEqual(TestParsers.expr.parse('34 + 8'), Success(42))
        self.assertEqual(TestParsers.expr.parse('1 + 2 + 3'), Success(6))
