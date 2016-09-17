from unittest import TestCase

from parsita import *


class LiteralTestCase(TestCase):
    def test_literals(self):
        class TestParsers(Parsers):
            a = lit('a')
            bb = lit('bb')

        self.assertEqual(TestParsers.a.parse('a'), Success('a'))
        self.assertEqual(TestParsers.bb.parse('bb'), Success('bb'))
        self.assertEqual(TestParsers.bb.parse('bbb'), Failure('end of source expected but b found at 2'))
        self.assertEqual(TestParsers.bb.parse('aa'), Failure('b expected but a found at 0'))
        self.assertEqual(str(TestParsers.a), "a = 'a'")
        self.assertEqual(str(TestParsers.bb), "bb = 'bb'")

    def test_multiple_literals(self):
        class TestParsers(Parsers):
            ab = lit('a', 'b')

        self.assertEqual(TestParsers.ab.parse('a'), Success('a'))
        self.assertEqual(TestParsers.ab.parse('b'), Success('b'))


class ForwardDeclarationTestCase(TestCase):
    def test_forward_declaration(self):
        class TestParsers(Parsers):
            a = b
            b = lit('b')

        self.assertEqual(TestParsers.a.parse('b'), Success('b'))
        self.assertEqual(TestParsers.a.parse('ab'), Failure('b expected but a found at 0'))

    def test_forward_expression(self):
        class TestParsers(Parsers):
            a = lit('a')
            ca = c | a
            da = d & a
            c = lit('c')
            d = lit('d')

        self.assertEqual(TestParsers.ca.parse('c'), Success('c'))
        self.assertEqual(TestParsers.ca.parse('a'), Success('a'))
        self.assertEqual(TestParsers.da.parse('da'), Success(['d', 'a']))
        self.assertEqual(str(TestParsers.ca), "ca = c | a")
        self.assertEqual(str(TestParsers.da), "da = d & a")

    def test_manual_forward(self):
        class TestParsers(Parsers):
            b = fwd()
            a = 'a' & b
            b.define('b' & opt(a))

        self.assertEqual(TestParsers.a.parse('ab'), Success(['a', ['b', []]]))
        self.assertEqual(TestParsers.a.parse('abab'), Success(['a', ['b', [['a', ['b', []]]]]]))

    def test_manual_forward_mutual(self):
        class TestParsers(Parsers):
            a = fwd()
            b = fwd()
            a.define('a' & b)
            b.define('b' & opt(a))

        self.assertEqual(TestParsers.a.parse('ab'), Success(['a', ['b', []]]))
        self.assertEqual(TestParsers.a.parse('abab'), Success(['a', ['b', [['a', ['b', []]]]]]))


class OptionalTestCase(TestCase):
    def test_optional(self):
        class TestParsers(Parsers):
            a = lit('a')
            b = opt(a)

        self.assertEqual(TestParsers.b.parse('a'), Success(['a']))
        self.assertEqual(TestParsers.b.parse('c'), Failure('a expected but c found at 0'))
        self.assertEqual(str(TestParsers.b), "b = opt(a)")

    def test_optional_longer(self):
        class TestParsers(Parsers):
            a = lit('ab')
            b = opt(a)

        self.assertEqual(TestParsers.b.parse('ab'), Success(['ab']))
        self.assertEqual(TestParsers.b.parse('ac'), Failure('b expected but c found at 1'))
        self.assertEqual(str(TestParsers.b), "b = opt(a)")


class AlternativeTestCase(TestCase):
    def test_alternative(self):
        class TestParsers(Parsers):
            a = lit('a')
            b = lit('b')
            c = lit('cd')
            ab = a | b
            bc = b | c

        self.assertEqual(TestParsers.ab.parse('a'), Success('a'))
        self.assertEqual(TestParsers.ab.parse('b'), Success('b'))
        self.assertEqual(TestParsers.ab.parse('c'), Failure('a expected but c found at 0'))
        self.assertEqual(TestParsers.bc.parse('cd'), Success('cd'))
        self.assertEqual(TestParsers.bc.parse('ce'), Failure('d expected but e found at 1'))
        self.assertEqual(str(TestParsers.bc), "bc = b | c")

    def test_multiple(self):
        class TestParsers(Parsers):
            a = lit('aaaa')
            b = lit('bbb')
            c = lit('cc')
            d = lit('d')
            back = a | (b | c | d)
            front = (a | b | c) | d
            both = (a | b) | c | d

        for parser in [TestParsers.back, TestParsers.front, TestParsers.both]:
            self.assertEqual(parser.parse('aaaa'), Success('aaaa'))
            self.assertEqual(parser.parse('cc'), Success('cc'))
            self.assertEqual(parser.parse('bbc'), Failure('b expected but c found at 2'))
            self.assertEqual(parser.parse('bbba'), Failure('end of source expected but a found at 3'))

        str(TestParsers.back), 'back = a | b | c | d'
        str(TestParsers.front), 'front = a | b | c | d'
        str(TestParsers.both), 'both = a | b | c | d'


class SequentialTestCase(TestCase):
    def test_sequential(self):
        class TestParsers(Parsers):
            a = lit('a')
            b = lit('b')
            c = lit('cd')
            ab = a & b
            bc = b & c
            abc = a & b & c

        self.assertEqual(TestParsers.ab.parse('ab'), Success(['a', 'b']))
        self.assertEqual(TestParsers.bc.parse('bcd'), Success(['b', 'cd']))
        self.assertEqual(TestParsers.abc.parse('abcd'), Success(['a', 'b', 'cd']))
        self.assertEqual(TestParsers.abc.parse('abc'), Failure('d expected but end of source found'))
        self.assertEqual(TestParsers.abc.parse('abf'), Failure('c expected but f found at 2'))
        self.assertEqual(str(TestParsers.abc), 'abc = a & b & c')


class DiscardTestCase(TestCase):
    def test_discard_left(self):
        class TestParsers(Parsers):
            a = lit('a')
            b = lit('b')
            ab = a >> b
            ac = a >> c
            c = lit('c')

        self.assertEqual(TestParsers.ab.parse('ab'), Success('b'))
        self.assertEqual(TestParsers.ac.parse('ac'), Success('c'))
        self.assertEqual(str(TestParsers.ac), 'ac = a >> c')

    def test_discard_right(self):
        class TestParsers(Parsers):
            a = lit('a')
            b = lit('b')
            ab = a << b
            ac = a << c
            c = lit('c')

        self.assertEqual(TestParsers.ab.parse('ab'), Success('a'))
        self.assertEqual(TestParsers.ac.parse('ac'), Success('a'))
        self.assertEqual(TestParsers.ac.parse('aa'), Failure('c expected but a found at 1'))
        self.assertEqual(str(TestParsers.ac), 'ac = a << c')


class RepeatedTestCase(TestCase):
    def test_repeated(self):
        class TestParsers(Parsers):
            bs = rep1('b')
            cs = rep('c')

        self.assertEqual(TestParsers.bs.parse('bbbb'), Success(['b', 'b', 'b', 'b']))
        self.assertEqual(TestParsers.bs.parse('b'), Success(['b']))
        self.assertEqual(TestParsers.bs.parse(''), Failure('b expected but end of source found'))
        self.assertEqual(TestParsers.bs.parse('bbbc'), Failure('b expected but c found at 3'))
        self.assertEqual(TestParsers.cs.parse('ccc'), Success(['c', 'c', 'c']))
        self.assertEqual(TestParsers.cs.parse('c'), Success(['c']))
        self.assertEqual(TestParsers.cs.parse(''), Success([]))
        self.assertEqual(TestParsers.cs.parse('cccb'), Failure('c expected but b found at 3'))

    def test_repeated_longer(self):
        class TestParsers(Parsers):
            bf = rep1('bf')
            cf = rep('cf')

        self.assertEqual(TestParsers.bf.parse('bfbf'), Success(['bf', 'bf']))
        self.assertEqual(TestParsers.bf.parse('bf'), Success(['bf']))
        self.assertEqual(TestParsers.bf.parse(''), Failure('b expected but end of source found'))
        self.assertEqual(TestParsers.bf.parse('bfbc'), Failure('f expected but c found at 3'))
        self.assertEqual(TestParsers.cf.parse('cfcfcf'), Success(['cf', 'cf', 'cf']))
        self.assertEqual(TestParsers.cf.parse('cf'), Success(['cf']))
        self.assertEqual(TestParsers.cf.parse(''), Success([]))
        self.assertEqual(TestParsers.cf.parse('cfcb'), Failure('f expected but b found at 3'))

    def test_repeated_separated(self):
        class TestParsers(Parsers):
            bs = rep1sep('b', ',')
            cs = repsep('c', ',')

        self.assertEqual(TestParsers.bs.parse('b,b,b'), Success(['b', 'b', 'b']))
        self.assertEqual(TestParsers.bs.parse('b'), Success(['b']))
        self.assertEqual(TestParsers.bs.parse(''), Failure('b expected but end of source found'))
        self.assertEqual(TestParsers.cs.parse('c,c,c'), Success(['c', 'c', 'c']))
        self.assertEqual(TestParsers.cs.parse('c'), Success(['c']))
        self.assertEqual(TestParsers.cs.parse(''), Success([]))


class ConversionTestCase(TestCase):
    def test_conversion(self):
        class TestParsers(Parsers):
            one = lit('1') > int
            two = lit('2') > int
            twelve = one & two > (lambda x: x[0]*10 + x[1])

            def make_twentyone(x):
                return x[0]*10 + x[1]
            twentyone = two & one > make_twentyone

        self.assertEqual(TestParsers.one.parse('1'), Success(1))
        self.assertEqual(TestParsers.twelve.parse('12'), Success(12))
        self.assertEqual(TestParsers.twentyone.parse('21'), Success(21))
        self.assertEqual(str(TestParsers.twelve), 'twelve = one & two')
        self.assertEqual(str(TestParsers.twentyone), 'twentyone = two & one')

    def test_recursion(self):
        class TestParsers(Parsers):
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
        self.assertEqual(TestParsers.expr.parse('6+11'), Success(17))
        self.assertEqual(TestParsers.expr.parse('1+6+6'), Success(13))


class ProtectionTestCase(TestCase):
    def test_protection(self):
        class TestParsers(Parsers):
            ab = lit('a') & lit('b')
            abc = ab & 'c'
            dab = 'd' & ab

        self.assertEqual(TestParsers.abc.parse('abc'), Success([['a', 'b'], 'c']))
        self.assertEqual(TestParsers.dab.parse('dab'), Success(['d', ['a', 'b']]))
