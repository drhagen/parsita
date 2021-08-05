from unittest import TestCase

import pytest

from parsita import *


class LiteralTestCase(TestCase):
    def test_literals(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            bb = lit("bb")

        self.assertEqual(TestParsers.a.parse("a"), Success("a"))
        self.assertEqual(TestParsers.bb.parse("bb"), Success("bb"))
        self.assertEqual(TestParsers.bb.parse("bbb"), Failure("Expected end of source but found b at index 2"))
        self.assertEqual(TestParsers.bb.parse("aa"), Failure("Expected b but found a at index 0"))
        self.assertEqual(str(TestParsers.a), "a = 'a'")
        self.assertEqual(str(TestParsers.bb), "bb = 'bb'")

    def test_multiple_literals(self):
        class TestParsers(GeneralParsers):
            ab = lit("a", "b")

        self.assertEqual(TestParsers.ab.parse("a"), Success("a"))
        self.assertEqual(TestParsers.ab.parse("b"), Success("b"))

    def test_or_die(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            bb = lit("bb")

        self.assertEqual(TestParsers.a.parse("a").or_die(), "a")
        self.assertRaisesRegex(ParseError, "Expected b but found a at index 0", TestParsers.bb.parse("aa").or_die)


class PredicateTestCase(TestCase):
    def test_predicate(self):
        class TestParsers(GeneralParsers):
            a = pred(any1, lambda x: x in ("A", "a"), "letter A")
            d = pred(any1, str.isdigit, "digit")

        self.assertEqual(TestParsers.a.parse("a"), Success("a"))
        self.assertEqual(TestParsers.a.parse("A"), Success("A"))
        self.assertEqual(TestParsers.d.parse("2"), Success("2"))
        self.assertEqual(TestParsers.d.parse("23"), Failure("Expected end of source but found 3 at index 1"))
        self.assertEqual(TestParsers.d.parse("a"), Failure("Expected digit but found a at index 0"))
        self.assertEqual(str(TestParsers.a), "a = pred(any1, letter A)")


class ForwardDeclarationTestCase(TestCase):
    def test_forward_declaration(self):
        class TestParsers(GeneralParsers):
            a = b
            b = lit("b")

        self.assertEqual(TestParsers.a.parse("b"), Success("b"))
        self.assertEqual(TestParsers.a.parse("ab"), Failure("Expected b but found a at index 0"))

    def test_forward_expression(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            ca = c | a
            da = d & a
            c = lit("c")
            d = lit("d")

        self.assertEqual(TestParsers.ca.parse("c"), Success("c"))
        self.assertEqual(TestParsers.ca.parse("a"), Success("a"))
        self.assertEqual(TestParsers.da.parse("da"), Success(["d", "a"]))
        self.assertEqual(str(TestParsers.ca), "ca = c | a")
        self.assertEqual(str(TestParsers.da), "da = d & a")

    def test_manual_forward(self):
        class TestParsers(GeneralParsers):
            b = fwd()
            a = "a" & b
            b.define("b" & opt(a))

        self.assertEqual(TestParsers.a.parse("ab"), Success(["a", ["b", []]]))
        self.assertEqual(TestParsers.a.parse("abab"), Success(["a", ["b", [["a", ["b", []]]]]]))

    def test_manual_forward_mutual(self):
        class TestParsers(GeneralParsers):
            a = fwd()
            b = fwd()
            a.define("a" & b)
            b.define("b" & opt(a))

        self.assertEqual(TestParsers.a.parse("ab"), Success(["a", ["b", []]]))
        self.assertEqual(TestParsers.a.parse("abab"), Success(["a", ["b", [["a", ["b", []]]]]]))

    def test_multiple_references(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            cora = c | a
            canda = c & a
            c = "c"

        self.assertEqual(TestParsers.cora.parse("c"), Success("c"))
        self.assertEqual(TestParsers.cora.parse("a"), Success("a"))
        self.assertEqual(TestParsers.canda.parse("ca"), Success(["c", "a"]))
        self.assertEqual(str(TestParsers.cora), "cora = 'c' | a")
        self.assertEqual(str(TestParsers.canda), "canda = 'c' & a")


class OptionalTestCase(TestCase):
    def test_optional(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            b = opt(a)

        self.assertEqual(TestParsers.b.parse("a"), Success(["a"]))
        self.assertEqual(TestParsers.b.parse("c"), Failure("Expected a or end of source but found c at index 0"))
        self.assertEqual(str(TestParsers.b), "b = opt(a)")

    def test_optional_longer(self):
        class TestParsers(GeneralParsers):
            a = lit("ab")
            b = opt(a)

        self.assertEqual(TestParsers.b.parse("ab"), Success(["ab"]))
        self.assertEqual(TestParsers.b.parse("ac"), Failure("Expected b but found c at index 1"))
        self.assertEqual(str(TestParsers.b), "b = opt(a)")

    def test_optional_literal(self):
        class TestParsers(GeneralParsers):
            b = opt("ab")

        self.assertEqual(TestParsers.b.parse("ab"), Success(["ab"]))
        self.assertEqual(TestParsers.b.parse("ac"), Failure("Expected b but found c at index 1"))
        self.assertEqual(str(TestParsers.b), "b = opt('ab')")


class AlternativeTestCase(TestCase):
    def test_alternative(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            b = lit("b")
            c = lit("cd")
            ab = a | b
            bc = b | c

        self.assertEqual(TestParsers.ab.parse("a"), Success("a"))
        self.assertEqual(TestParsers.ab.parse("b"), Success("b"))
        self.assertEqual(TestParsers.ab.parse("c"), Failure("Expected a or b but found c at index 0"))
        self.assertEqual(TestParsers.bc.parse("cd"), Success("cd"))
        self.assertEqual(TestParsers.bc.parse("ce"), Failure("Expected d but found e at index 1"))
        self.assertEqual(str(TestParsers.bc), "bc = b | c")

    def test_multiple(self):
        class TestParsers(GeneralParsers):
            a = lit("aaaa")
            b = lit("bbb")
            c = lit("cc")
            d = lit("d")
            back = a | (b | c | d)
            front = (a | b | c) | d
            both = (a | b) | c | d

        for parser in [TestParsers.back, TestParsers.front, TestParsers.both]:
            self.assertEqual(parser.parse("aaaa"), Success("aaaa"))
            self.assertEqual(parser.parse("cc"), Success("cc"))
            self.assertEqual(parser.parse("bbc"), Failure("Expected b but found c at index 2"))
            self.assertEqual(parser.parse("bbba"), Failure("Expected end of source but found a at index 3"))

        str(TestParsers.back), "back = a | b | c | d"
        str(TestParsers.front), "front = a | b | c | d"
        str(TestParsers.both), "both = a | b | c | d"

    def test_right_or(self):
        class TestParsers(GeneralParsers):
            ab = "a" | lit("b")

        self.assertEqual(TestParsers.ab.parse("a"), Success("a"))

    def test_multiple_messages_duplicate(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            ab = a & "b"
            ac = a & "c"
            either = ab | ac

        self.assertEqual(TestParsers.either.parse("cc"), Failure("Expected a but found c at index 0"))


class LongestALternativeTestCase(TestCase):
    def test_longest(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            either = longest(a, "b")

        self.assertEqual(str(TestParsers.either), "either = longest(a, 'b')")


class SequentialTestCase(TestCase):
    def test_sequential(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            b = lit("b")
            c = lit("cd")
            ab = a & b
            bc = b & c
            abc = a & b & c

        self.assertEqual(TestParsers.ab.parse("ab"), Success(["a", "b"]))
        self.assertEqual(TestParsers.bc.parse("bcd"), Success(["b", "cd"]))
        self.assertEqual(TestParsers.abc.parse("abcd"), Success(["a", "b", "cd"]))
        self.assertEqual(TestParsers.abc.parse("abc"), Failure("Expected d but found end of source"))
        self.assertEqual(TestParsers.abc.parse("abf"), Failure("Expected c but found f at index 2"))
        self.assertEqual(str(TestParsers.abc), "abc = a & b & c")


class DiscardTestCase(TestCase):
    def test_discard_left(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            b = lit("b")
            ab = a >> b
            ac = a >> c
            c = lit("c")

        self.assertEqual(TestParsers.ab.parse("ab"), Success("b"))
        self.assertEqual(TestParsers.ac.parse("ac"), Success("c"))
        self.assertEqual(str(TestParsers.ac), "ac = a >> c")

    def test_discard_right(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            b = lit("b")
            ab = a << b
            ac = a << c
            c = lit("c")

        self.assertEqual(TestParsers.ab.parse("ab"), Success("a"))
        self.assertEqual(TestParsers.ac.parse("ac"), Success("a"))
        self.assertEqual(TestParsers.ac.parse("aa"), Failure("Expected c but found a at index 1"))
        self.assertEqual(str(TestParsers.ac), "ac = a << c")

    def test_discard_bare_literals(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            b = "b"
            rshift = a >> b
            rrshift = b >> a
            lshift = a << b
            rlshift = b << a

        self.assertEqual(TestParsers.rshift.parse("ab"), Success("b"))
        self.assertEqual(TestParsers.rrshift.parse("ba"), Success("a"))
        self.assertEqual(TestParsers.lshift.parse("ab"), Success("a"))
        self.assertEqual(TestParsers.rlshift.parse("ba"), Success("b"))


class RepeatedTestCase(TestCase):
    def test_repeated(self):
        class TestParsers(GeneralParsers):
            bs = rep1("b")
            cs = rep("c")

        self.assertEqual(TestParsers.bs.parse("bbbb"), Success(["b", "b", "b", "b"]))
        self.assertEqual(TestParsers.bs.parse("b"), Success(["b"]))
        self.assertEqual(TestParsers.bs.parse(""), Failure("Expected b but found end of source"))
        self.assertEqual(TestParsers.bs.parse("bbbc"), Failure("Expected b or end of source but found c at index 3"))
        self.assertEqual(TestParsers.cs.parse("ccc"), Success(["c", "c", "c"]))
        self.assertEqual(TestParsers.cs.parse("c"), Success(["c"]))
        self.assertEqual(TestParsers.cs.parse(""), Success([]))
        self.assertEqual(TestParsers.cs.parse("cccb"), Failure("Expected c or end of source but found b at index 3"))
        self.assertEqual(str(TestParsers.bs), "bs = rep1('b')")
        self.assertEqual(str(TestParsers.cs), "cs = rep('c')")

    def test_repeated_longer(self):
        class TestParsers(GeneralParsers):
            bf = rep1("bf")
            cf = rep("cf")

        self.assertEqual(TestParsers.bf.parse("bfbf"), Success(["bf", "bf"]))
        self.assertEqual(TestParsers.bf.parse("bf"), Success(["bf"]))
        self.assertEqual(TestParsers.bf.parse(""), Failure("Expected b but found end of source"))
        self.assertEqual(TestParsers.bf.parse("bfbc"), Failure("Expected f but found c at index 3"))
        self.assertEqual(TestParsers.cf.parse("cfcfcf"), Success(["cf", "cf", "cf"]))
        self.assertEqual(TestParsers.cf.parse("cf"), Success(["cf"]))
        self.assertEqual(TestParsers.cf.parse(""), Success([]))
        self.assertEqual(TestParsers.cf.parse("cfcb"), Failure("Expected f but found b at index 3"))
        self.assertEqual(str(TestParsers.bf), "bf = rep1('bf')")
        self.assertEqual(str(TestParsers.cf), "cf = rep('cf')")

    def test_repeated_separated(self):
        class TestParsers(GeneralParsers):
            bs = rep1sep("b", ",")
            cs = repsep("c", ",")

        self.assertEqual(TestParsers.bs.parse("b,b,b"), Success(["b", "b", "b"]))
        self.assertEqual(TestParsers.bs.parse("b"), Success(["b"]))
        self.assertEqual(TestParsers.bs.parse(""), Failure("Expected b but found end of source"))
        self.assertEqual(TestParsers.cs.parse("c,c,c"), Success(["c", "c", "c"]))
        self.assertEqual(TestParsers.cs.parse("c"), Success(["c"]))
        self.assertEqual(TestParsers.cs.parse(""), Success([]))
        self.assertEqual(str(TestParsers.bs), "bs = rep1sep('b', ',')")
        self.assertEqual(str(TestParsers.cs), "cs = repsep('c', ',')")

    def test_repeated_separated_nonliteral(self):
        class TestParsers(GeneralParsers):
            bs = rep1sep("b", opt(","))
            cs = repsep("c", opt(","))

        self.assertEqual(TestParsers.bs.parse("b,bb"), Success(["b", "b", "b"]))
        self.assertEqual(TestParsers.bs.parse("b"), Success(["b"]))
        self.assertEqual(TestParsers.bs.parse(""), Failure("Expected b but found end of source"))
        self.assertEqual(TestParsers.cs.parse("cc,c"), Success(["c", "c", "c"]))
        self.assertEqual(TestParsers.cs.parse("c"), Success(["c"]))
        self.assertEqual(TestParsers.cs.parse(""), Success([]))
        self.assertEqual(str(TestParsers.bs), "bs = rep1sep('b', opt(','))")
        self.assertEqual(str(TestParsers.cs), "cs = repsep('c', opt(','))")

    @pytest.mark.timeout(2)
    def test_infinite_recursion_protection(self):
        class TestParsers(GeneralParsers):
            bad_rep = rep(opt("a"))
            bad_rep1 = rep1(opt("a"))
            bad_repsep = repsep(opt("a"), opt(":"))
            bad_rep1sep = rep1sep(opt("a"), opt(":"))

        # Recursion happens in middle of stream
        for parser in (TestParsers.bad_rep, TestParsers.bad_rep1, TestParsers.bad_repsep, TestParsers.bad_rep1sep):
            with self.assertRaisesRegex(
                RuntimeError,
                "Infinite recursion detected in "
                r"bad_rep1?(sep)? = rep1?(sep)?\(opt\('a'\)(, opt\(':'\))?\); "
                "empty string was matched and will be matched forever at index 2 before b",
            ):
                parser.parse("aab")

        # Recursion happens at end of stream
        for parser in (TestParsers.bad_rep, TestParsers.bad_rep1, TestParsers.bad_repsep, TestParsers.bad_rep1sep):
            with self.assertRaisesRegex(
                RuntimeError,
                "Infinite recursion detected in "
                r"bad_rep1?(sep)? = rep1?(sep)?\(opt\('a'\)(, opt\(':'\))?\); "
                "empty string was matched and will be matched forever at end of source",
            ):
                parser.parse("aa")


class ConversionTestCase(TestCase):
    def test_conversion(self):
        class TestParsers(GeneralParsers):
            one = lit("1") > int
            two = lit("2") > int
            twelve = one & two > (lambda x: x[0] * 10 + x[1])

            def make_twentyone(x):
                return x[0] * 10 + x[1]

            twentyone = two & one > make_twentyone

        self.assertEqual(TestParsers.one.parse("1"), Success(1))
        self.assertEqual(TestParsers.twelve.parse("12"), Success(12))
        self.assertEqual(TestParsers.twentyone.parse("21"), Success(21))
        self.assertEqual(str(TestParsers.twelve), "twelve = one & two")
        self.assertEqual(str(TestParsers.twentyone), "twentyone = two & one")

    def test_recursion(self):
        class TestParsers(GeneralParsers):
            one = lit("1") > float
            six = lit("6") > float
            eleven = lit("11") > float

            numbers = eleven | one | six

            def make_expr(x):
                digits1, maybe_expr = x
                if maybe_expr:
                    digits2 = maybe_expr[0]
                    return digits1 + digits2
                else:
                    return digits1

            expr = numbers & opt("+" >> expr) > make_expr

        self.assertEqual(TestParsers.expr.parse("11"), Success(11))
        self.assertEqual(TestParsers.expr.parse("6+11"), Success(17))
        self.assertEqual(TestParsers.expr.parse("1+6+6"), Success(13))


class ProtectionTestCase(TestCase):
    def test_protection(self):
        class TestParsers(GeneralParsers):
            ab = lit("a") & lit("b")
            abc = ab & "c"
            dab = "d" & ab

        self.assertEqual(TestParsers.abc.parse("abc"), Success([["a", "b"], "c"]))
        self.assertEqual(TestParsers.dab.parse("dab"), Success(["d", ["a", "b"]]))


class EndOfSourceTestCase(TestCase):
    def test_protection(self):
        class TestParsers(GeneralParsers):
            end_a = "a" << eof
            b = lit("b")
            bba = rep(b | end_a)

        self.assertEqual(TestParsers.bba.parse("bba"), Success(["b", "b", "a"]))
        self.assertEqual(TestParsers.bba.parse("a"), Success(["a"]))
        self.assertEqual(TestParsers.bba.parse("ab"), Failure("Expected end of source but found b at index 1"))
        self.assertEqual(str(TestParsers.end_a), "end_a = 'a' << eof")


class SuccessFailureTestCase(TestCase):
    def test_protection(self):
        class TestParsers(GeneralParsers):
            aaa = rep("a") & success(1) & rep("b")
            bbb = "aa" & failure("something else") & "bb"

        self.assertEqual(TestParsers.aaa.parse("aabb"), Success([["a", "a"], 1, ["b", "b"]]))
        self.assertEqual(TestParsers.aaa.parse(""), Success([[], 1, []]))
        self.assertEqual(TestParsers.bbb.parse("aabb"), Failure("Expected something else but found b at index 2"))
        self.assertEqual(str(TestParsers.aaa), "aaa = rep('a') & success(1) & rep('b')")
        self.assertEqual(str(TestParsers.bbb), "bbb = 'aa' & failure('something else') & 'bb'")


class AnyTestCase(TestCase):
    def test_any(self):
        class TestParsers(GeneralParsers):
            any2 = any1 & any1

        self.assertEqual(TestParsers.any2.parse("ab"), Success(["a", "b"]))
        self.assertEqual(TestParsers.any2.parse("a"), Failure("Expected anything but found end of source"))
        self.assertEqual(str(TestParsers.any2), "any2 = any1 & any1")


class OptionsResetTest(TestCase):
    def test_nested_class(self):
        class TestOuter(GeneralParsers):
            start = "%"

            class TestInner(GeneralParsers):
                inner = '"' >> rep(lit("a", "b", "c")) << '"'

            wrapped = "(" >> TestInner.inner << ")"

            outer = start >> wrapped

        self.assertEqual(TestOuter.outer.parse('%("abc")'), Success(["a", "b", "c"]))
        self.assertIsInstance(TestOuter.outer.parse('%("abc ")'), Failure)
        self.assertIsInstance(TestOuter.outer.parse(' %("abc")'), Failure)
        self.assertIsInstance(TestOuter.outer.parse('%("abc") '), Failure)


class MetaclassTest(TestCase):
    def test_disallow_instatiation(self):
        class TestParsers(GeneralParsers):
            a = lit("a")
            bb = lit("bb")

        with self.assertRaises(TypeError):
            _ = TestParsers()
