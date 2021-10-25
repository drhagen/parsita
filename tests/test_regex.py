from parsita import *


def test_literal():
    class TestParsers(TextParsers):
        hundred = lit("100") > float

    assert TestParsers.hundred.parse("") == Failure("Expected '100' but found end of source")
    assert TestParsers.hundred.parse("100") == Success(100)
    assert TestParsers.hundred.parse("   100") == Success(100)
    assert TestParsers.hundred.parse("100    ") == Success(100)
    assert TestParsers.hundred.parse("   100    ") == Success(100)
    assert str(TestParsers.hundred) == "hundred = '100'"


def test_literal_no_whitespace():
    class TestParsers(TextParsers, whitespace=None):
        hundred = lit("100") > float

    assert TestParsers.hundred.parse("100") == Success(100)
    assert TestParsers.hundred.parse(" 100") == Failure(
        "Expected '100' but found ' '\nLine 1, character 1\n\n 100\n^   "
    )
    assert TestParsers.hundred.parse("100 ") == Failure(
        "Expected end of source but found ' '\nLine 1, character 4\n\n100 \n   ^"
    )
    assert str(TestParsers.hundred) == "hundred = '100'"


def test_interval():
    class TestParsers(TextParsers):
        number = reg(r"\d+") > int
        pair = "[" >> number << "," & number << "]"
        interval = pred(pair, lambda x: x[0] <= x[1], "ordered pair")

    assert TestParsers.interval.parse("[1, 2]") == Success([1, 2])
    assert isinstance(TestParsers.interval.parse("[2, 1]"), Failure)
    assert TestParsers.pair.parse("[1,a]") == TestParsers.interval.parse("[1,a]")


def test_regex():
    class TestParsers(TextParsers):
        digits = reg(r"\d+")

    assert TestParsers.digits.parse("100") == Success("100")
    assert TestParsers.digits.parse("   100") == Success("100")
    assert TestParsers.digits.parse("100    ") == Success("100")
    assert TestParsers.digits.parse("   100    ") == Success("100")
    assert str(TestParsers.digits) == r"digits = reg(r'\d+')"


def test_regex_no_whitespace():
    class TestParsers(TextParsers, whitespace=None):
        digits = reg(r"\d+") > float

    assert TestParsers.digits.parse("100") == Success(100)
    assert TestParsers.digits.parse(" 100") == Failure(
        "Expected r'\\d+' but found ' '\nLine 1, character 1\n\n 100\n^   "
    )
    assert TestParsers.digits.parse("100 ") == Failure(
        "Expected end of source but found ' '\nLine 1, character 4\n\n100 \n   ^"
    )
    assert str(TestParsers.digits) == r"digits = reg(r'\d+')"


def test_regex_custom_whitespace():
    class TestParsers(TextParsers, whitespace="[ ]*"):
        digits = reg(r"\d+") > float
        pair = digits & digits

    assert TestParsers.digits.parse("100") == Success(100)
    assert TestParsers.digits.parse("   100    ") == Success(100)
    assert TestParsers.digits.parse("100\n") == Failure(
        "Expected end of source but found '\\n'\nLine 1, character 4\n\n100\n   ^"
    )
    assert TestParsers.digits.parse("100 \n") == Failure(
        "Expected end of source but found '\\n'\nLine 1, character 5\n\n100 \n    ^"
    )
    assert TestParsers.pair.parse("100 100") == Success([100, 100])
    assert TestParsers.pair.parse("100\n100") == Failure(
        "Expected r'\\d+' but found '\\n'\nLine 1, character 4\n\n100\n   ^"
    )
    assert str(TestParsers.digits) == r"digits = reg(r'\d+')"
    assert str(TestParsers.pair) == "pair = digits & digits"


def test_optional():
    class TestParsers(TextParsers):
        a = reg(r"\d+") > float
        b = opt(a)

    assert TestParsers.b.parse(" 100 ") == Success([100])
    assert TestParsers.b.parse(" c ") == Failure("Expected r'\\d+' but found 'c'\nLine 1, character 2\n\n c \n ^ ")
    assert str(TestParsers.b) == "b = opt(a)"


def test_multiple_messages():
    class TestParsers(TextParsers):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = function | index | name

    assert TestParsers.any.parse("var") == Success("var")
    assert TestParsers.any.parse("var[a]") == Success(["var", "a"])
    assert TestParsers.any.parse("var(a)") == Success(["var", "a"])
    assert TestParsers.any.parse("func{var}") == Failure(
        "Expected '(' or '[' or end of source but found '{'\nLine 1, character 5\n\nfunc{var}\n    ^    "
    )
    assert TestParsers.any.parse("func[var") == Failure("Expected ']' but found end of source")


def test_first_function():
    class TestParsers(TextParsers):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = first(name, function, index)

    assert TestParsers.any.parse("var(arg)") == Failure(
        "Expected end of source but found '('\nLine 1, character 4\n\nvar(arg)\n   ^    "
    )


def test_longest_function():
    class TestParsers(TextParsers):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = longest(name, function, index)

    assert TestParsers.any.parse("var(arg)") == Success(["var", "arg"])
    assert TestParsers.any.parse("func{var}") == Failure(
        "Expected '(' or '[' or end of source but found '{'\n" "Line 1, character 5\n\n" "func{var}\n" "    ^    "
    )


def test_longest_function_shortest_later():
    class TestParsers(TextParsers):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = longest(function, index, name)

    assert TestParsers.any.parse("var(arg)") == Success(["var", "arg"])


def test_longest_function_all_failures():
    class TestParsers(TextParsers):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = longest(function, index)

    assert TestParsers.any.parse("func{var}") == Failure(
        "Expected '(' or '[' but found '{'\nLine 1, character 5\n\nfunc{var}\n    ^    "
    )


def test_sequential():
    class TestParsers(TextParsers):
        hello = lit("Hello")
        world = lit("world")
        hello_world = hello & world

    assert TestParsers.hello_world.parse("Hello world") == Success(["Hello", "world"])
    assert TestParsers.hello_world.parse("Hello David") == Failure(
        "Expected 'world' but found 'David'\nLine 1, character 7\n\nHello David\n      ^    "
    )
    assert TestParsers.hello_world.parse("Hello") == Failure("Expected 'world' but found end of source")


def test_multiline():
    class TestParsers(TextParsers):
        hello = lit("Hello")
        world = lit("world")
        hello_world = hello & world

    assert TestParsers.hello_world.parse("Hello\nworld") == Success(["Hello", "world"])
    assert TestParsers.hello_world.parse("Hello\nDavid") == Failure(
        "Expected 'world' but found 'David'\nLine 2, character 1\n\nDavid\n^    "
    )


def test_repeated():
    class TestParsers(TextParsers):
        number = reg(r"\d+") > int
        trail = "(" >> rep(number << ",") << ")" > tuple
        trail1 = "(" >> rep1(number << ",") << ")" > tuple
        notrail = "(" >> repsep(number, ",") << ")" > tuple
        notrail1 = "(" >> rep1sep(number, ",") << ")" > tuple

    assert TestParsers.trail.parse("(1,2,3)") == Failure(
        "Expected ',' but found ')'\nLine 1, character 7\n\n(1,2,3)\n      ^"
    )

    assert TestParsers.trail.parse("(1,2,3,)") == Success((1, 2, 3))
    assert TestParsers.trail.parse("()") == Success(())
    assert TestParsers.trail1.parse("(1,2,3)") == Failure(
        "Expected ',' but found ')'\nLine 1, character 7\n\n(1,2,3)\n      ^"
    )
    assert TestParsers.trail1.parse("(1,2,3,)") == Success((1, 2, 3))
    assert TestParsers.trail1.parse("()") == Failure("Expected r'\\d+' but found ')'\nLine 1, character 2\n\n()\n ^")
    assert TestParsers.notrail.parse("(1,2,3)") == Success((1, 2, 3))
    assert TestParsers.notrail.parse("(1,2,3,)") == Failure(
        "Expected r'\\d+' but found ')'\nLine 1, character 8\n\n(1,2,3,)\n       ^"
    )
    assert TestParsers.notrail.parse("()") == Success(())
    assert TestParsers.notrail1.parse("(1,2,3)") == Success((1, 2, 3))
    assert TestParsers.notrail1.parse("(1,2,3,)") == Failure(
        "Expected r'\\d+' but found ')'\nLine 1, character 8\n\n(1,2,3,)\n       ^"
    )
    assert TestParsers.notrail1.parse("()") == Failure("Expected r'\\d+' but found ')'\nLine 1, character 2\n\n()\n ^")


def test_transformation_as_fallible_conversion():
    class Percent:
        def __init__(self, number: int):
            self.number = number

        def __eq__(self, other):
            if isinstance(other, Percent):
                return self.number == other.number
            else:
                return NotImplemented

    class TestParsers(TextParsers):
        def to_percent(number: int):
            if not 0 <= number <= 100:
                return failure("a number between 0 and 100")
            else:
                return success(Percent(number))

        percent = (reg(r"[0-9]+") > int) >= to_percent

    assert TestParsers.percent.parse("50") == Success(Percent(50))
    assert TestParsers.percent.parse("150") == Failure("Expected a number between 0 and 100 but found end of source")
    assert TestParsers.percent.parse("a") == Failure("Expected r'[0-9]+' but found 'a'\nLine 1, character 1\n\na\n^")


def test_transformation_as_parameterized_parser():
    class NumberParsers(TextParsers):
        def select_parser(type: str):
            if type == "int":
                return reg(r"[0-9]+") > int
            elif type == "decimal":
                return reg(r"[0-9]+\.[0-9]+") > float

        type = lit("int", "decimal")
        number = type >= select_parser

    assert NumberParsers.number.parse("int 5") == Success(5)
    assert NumberParsers.number.parse("decimal 5") == Failure(
        "Expected r'[0-9]+\\.[0-9]+' but found '5'\nLine 1, character 9\n\ndecimal 5\n        ^"
    )


def test_debug_callback():
    result = False

    def callback(parser, reader):
        nonlocal result
        remainder = reader.source[reader.position :]
        result = remainder == "45"
        result &= isinstance(parser.parse(remainder), Failure)
        result &= isinstance(parser.parse("345"), Success)

    class TestParsers(TextParsers):
        a = lit("123")
        b = lit("345")
        c = a & debug(b, callback=callback)

    TestParsers.c.parse("12345")
    assert result
    assert str(TestParsers.c) == "c = a & debug(b)"


def test_debug_verbose(capsys):
    class TestParsers(TextParsers):
        a = lit("123")
        c = a & debug("345", verbose=True)

    TestParsers.c.parse("12345")

    captured = capsys.readouterr()
    assert "Evaluating" in captured.out
    assert "Result" in captured.out


def test_recursion_literals():
    class TestParsers(TextParsers):
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

    assert TestParsers.expr.parse("11") == Success(11)
    assert TestParsers.expr.parse("6 + 11") == Success(17)
    assert TestParsers.expr.parse("1 +6  + 6") == Success(13)


def test_recursion_regex():
    class TestParsers(TextParsers, whitespace="[ ]*"):
        digits = reg(r"\d+") > float

        def make_expr(x):
            digits1, maybe_expr = x
            if maybe_expr:
                digits2 = maybe_expr[0]
                return digits1 + digits2
            else:
                return digits1

        expr = digits & opt("+" >> expr) > make_expr

    assert TestParsers.expr.parse("34") == Success(34)
    assert TestParsers.expr.parse("34 + 8") == Success(42)
    assert TestParsers.expr.parse("1 + 2 + 3") == Success(6)


def test_protection():
    class TestParsers(TextParsers):
        end_aa = "aa" << eof
        b = lit("b")
        bba = rep(b | end_aa)

    assert TestParsers.bba.parse("b b aa") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("b b aa  ") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("  b b aa") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("aa b") == Failure(
        "Expected end of source but found 'b'\nLine 1, character 4\n\naa b\n   ^"
    )
    assert str(TestParsers.end_aa) == "end_aa = 'aa' << eof"


def test_nested_class():
    class TestOuter(TextParsers, whitespace="[ ]*"):
        start = "%%"

        class TestInner(TextParsers, whitespace=None):
            inner = '"' >> reg("[A-Za-z0-9]*") << '"'

        wrapped = "(" >> TestInner.inner << ")"

        outer = start >> wrapped

    assert TestOuter.outer.parse('%%("abc")') == Success("abc")
    assert TestOuter.outer.parse('%%  ("abc")') == Success("abc")
    assert TestOuter.outer.parse('%%(  "abc")') == Success("abc")
    assert TestOuter.outer.parse('%%("abc"  )') == Success("abc")
    assert isinstance(TestOuter.outer.parse('%%(" abc")'), Failure)
    assert isinstance(TestOuter.outer.parse('%%("abc ")'), Failure)
    assert TestOuter.outer.parse('   %%("abc")') == Success("abc")
    assert TestOuter.outer.parse('%%("abc")   ') == Success("abc")


def test_general_in_regex():
    class TestOuter(TextParsers, whitespace="[ ]*"):
        start = "%%"

        class TestInner(GeneralParsers):
            inner = '"' >> rep(lit("a", "b", "c")) << '"'

        wrapped = "(" >> TestInner.inner << ")"

        outer = start >> wrapped

    assert TestOuter.outer.parse('%%("abc")') == Success(["a", "b", "c"])
    assert TestOuter.outer.parse('%%  ("abc")') == Success(["a", "b", "c"])
    assert TestOuter.outer.parse('%%(  "abc")') == Success(["a", "b", "c"])
    assert TestOuter.outer.parse('%%("abc"  )') == Success(["a", "b", "c"])
    assert isinstance(TestOuter.outer.parse('%%(" abc")'), Failure)
    assert isinstance(TestOuter.outer.parse('%%("abc ")'), Failure)
    assert TestOuter.outer.parse('   %%("abc")') == Success(["a", "b", "c"])
    assert TestOuter.outer.parse('%%("abc")   ') == Success(["a", "b", "c"])
