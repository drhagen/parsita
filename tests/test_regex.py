import pytest

from parsita import (
    Failure,
    GeneralParsers,
    ParseError,
    Success,
    TextParsers,
    debug,
    eof,
    failure,
    first,
    lit,
    longest,
    opt,
    pred,
    reg,
    rep,
    rep1,
    rep1sep,
    repsep,
    success,
    until,
)


def test_literal():
    class TestParsers(TextParsers):
        hundred = lit("100") > float

    assert TestParsers.hundred.parse("") == Failure(ParseError("Expected '100' but found end of source"))
    assert TestParsers.hundred.parse("100") == Success(100)
    assert TestParsers.hundred.parse("   100") == Success(100)
    assert TestParsers.hundred.parse("100    ") == Success(100)
    assert TestParsers.hundred.parse("   100    ") == Success(100)
    assert str(TestParsers.hundred) == "hundred = '100'"


def test_literal_no_whitespace():
    class TestParsers(TextParsers, whitespace=None):
        hundred = lit("100") > float

    assert TestParsers.hundred.parse("100") == Success(100)
    assert TestParsers.hundred.parse(" 100") == Failure(ParseError(
        "Expected '100' but found ' '\nLine 1, character 1\n\n 100\n^   "
    ))
    assert TestParsers.hundred.parse("100 ") == Failure(ParseError(
        "Expected end of source but found ' '\nLine 1, character 4\n\n100 \n   ^"
    ))
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
    assert TestParsers.digits.parse(" 100") == Failure(ParseError(
        "Expected r'\\d+' but found ' '\nLine 1, character 1\n\n 100\n^   "
    ))
    assert TestParsers.digits.parse("100 ") == Failure(ParseError(
        "Expected end of source but found ' '\nLine 1, character 4\n\n100 \n   ^"
    ))
    assert str(TestParsers.digits) == r"digits = reg(r'\d+')"


def test_regex_custom_whitespace():
    class TestParsers(TextParsers, whitespace="[ ]*"):
        digits = reg(r"\d+") > float
        pair = digits & digits

    assert TestParsers.digits.parse("100") == Success(100)
    assert TestParsers.digits.parse("   100    ") == Success(100)
    assert TestParsers.digits.parse("100\n") == Failure(ParseError(
        "Expected end of source but found '\\n'\nLine 1, character 4\n\n100\n   ^"
    ))
    assert TestParsers.digits.parse("100 \n") == Failure(ParseError(
        "Expected end of source but found '\\n'\nLine 1, character 5\n\n100 \n    ^"
    ))
    assert TestParsers.pair.parse("100 100") == Success([100, 100])
    assert TestParsers.pair.parse("100\n100") == Failure(ParseError(
        "Expected r'\\d+' but found '\\n'\nLine 1, character 4\n\n100\n   ^"
    ))
    assert str(TestParsers.digits) == r"digits = reg(r'\d+')"
    assert str(TestParsers.pair) == "pair = digits & digits"


def test_optional():
    class TestParsers(TextParsers):
        a = reg(r"\d+") > float
        b = opt(a)

    assert TestParsers.b.parse(" 100 ") == Success([100])
    assert TestParsers.b.parse(" c ") == Failure(ParseError("Expected r'\\d+' but found 'c'\nLine 1, character 2\n\n c \n ^ "))
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
    assert TestParsers.any.parse("func{var}") == Failure(ParseError(
        "Expected '(' or '[' or end of source but found '{'\nLine 1, character 5\n\nfunc{var}\n    ^    "
    ))
    assert TestParsers.any.parse("func[var") == Failure(ParseError("Expected ']' but found end of source"))


def test_first_function():
    class TestParsers(TextParsers):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = first(name, function, index)

    assert TestParsers.any.parse("var(arg)") == Failure(ParseError(
        "Expected end of source but found '('\nLine 1, character 4\n\nvar(arg)\n   ^    "
    ))


def test_longest_function():
    class TestParsers(TextParsers):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = longest(name, function, index)

    assert TestParsers.any.parse("var(arg)") == Success(["var", "arg"])
    assert TestParsers.any.parse("func{var}") == Failure(ParseError(
        "Expected '(' or '[' or end of source but found '{'\n" "Line 1, character 5\n\n" "func{var}\n" "    ^    "
    ))


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

    assert TestParsers.any.parse("func{var}") == Failure(ParseError(
        "Expected '(' or '[' but found '{'\nLine 1, character 5\n\nfunc{var}\n    ^    "
    ))


def test_sequential():
    class TestParsers(TextParsers):
        hello = lit("Hello")
        world = lit("world")
        hello_world = hello & world

    assert TestParsers.hello_world.parse("Hello world") == Success(["Hello", "world"])
    assert TestParsers.hello_world.parse("Hello David") == Failure(ParseError(
        "Expected 'world' but found 'David'\nLine 1, character 7\n\nHello David\n      ^    "
    ))
    assert TestParsers.hello_world.parse("Hello") == Failure(ParseError("Expected 'world' but found end of source"))


def test_multiline():
    class TestParsers(TextParsers):
        hello = lit("Hello")
        world = lit("world")
        hello_world = hello & world

    assert TestParsers.hello_world.parse("Hello\nworld") == Success(["Hello", "world"])
    assert TestParsers.hello_world.parse("Hello\nDavid") == Failure(ParseError(
        "Expected 'world' but found 'David'\nLine 2, character 1\n\nDavid\n^    "
    ))


def test_repeated():
    class TestParsers(TextParsers):
        number = reg(r"\d+") > int
        trail = "(" >> rep(number << ",") << ")" > tuple
        trail1 = "(" >> rep1(number << ",") << ")" > tuple
        notrail = "(" >> repsep(number, ",") << ")" > tuple
        notrail1 = "(" >> rep1sep(number, ",") << ")" > tuple

    assert TestParsers.trail.parse("(1,2,3)") == Failure(ParseError(
        "Expected ',' but found ')'\nLine 1, character 7\n\n(1,2,3)\n      ^"
    ))

    assert TestParsers.trail.parse("(1,2,3,)") == Success((1, 2, 3))
    assert TestParsers.trail.parse("()") == Success(())
    assert TestParsers.trail1.parse("(1,2,3)") == Failure(ParseError(
        "Expected ',' but found ')'\nLine 1, character 7\n\n(1,2,3)\n      ^"
    ))
    assert TestParsers.trail1.parse("(1,2,3,)") == Success((1, 2, 3))
    assert TestParsers.trail1.parse("()") == Failure(ParseError("Expected r'\\d+' but found ')'\nLine 1, character 2\n\n()\n ^"))
    assert TestParsers.notrail.parse("(1,2,3)") == Success((1, 2, 3))
    assert TestParsers.notrail.parse("(1,2,3,)") == Failure(ParseError(
        "Expected r'\\d+' but found ')'\nLine 1, character 8\n\n(1,2,3,)\n       ^"
    ))
    assert TestParsers.notrail.parse("()") == Success(())
    assert TestParsers.notrail1.parse("(1,2,3)") == Success((1, 2, 3))
    assert TestParsers.notrail1.parse("(1,2,3,)") == Failure(ParseError(
        "Expected r'\\d+' but found ')'\nLine 1, character 8\n\n(1,2,3,)\n       ^"
    ))
    assert TestParsers.notrail1.parse("()") == Failure(ParseError("Expected r'\\d+' but found ')'\nLine 1, character 2\n\n()\n ^"))


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
    assert TestParsers.percent.parse("150") == Failure(ParseError("Expected a number between 0 and 100 but found end of source"))
    assert TestParsers.percent.parse("a") == Failure(ParseError("Expected r'[0-9]+' but found 'a'\nLine 1, character 1\n\na\n^"))


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
    assert NumberParsers.number.parse("decimal 5") == Failure(ParseError(
        "Expected r'[0-9]+\\.[0-9]+' but found '5'\nLine 1, character 9\n\ndecimal 5\n        ^"
    ))


def test_transformation_error_propogation():
    class AssignmentsParser(TextParsers):
        def assignments_to_map(assignments):
            names_found = set()
            output = {}
            for name, value in assignments:
                if name in names_found:
                    return failure(f"{name} to be found only once")
                names_found.add(name)
                output[name] = value

            return success(output)

        name = reg(r"[a-z]+")
        value = reg(r"[0-9]+") > int
        assignment = name << "=" & value
        assignments = repsep(assignment, ",") >= assignments_to_map

    assert AssignmentsParser.assignments.parse("a = 5, b = 4") == Success({"a": 5, "b": 4})
    assert AssignmentsParser.assignments.parse("a = 5, b = 4, a = 3") == Failure(ParseError(
        "Expected ',' or a to be found only once but found end of source"
    ))
    assert AssignmentsParser.assignments.parse("a = 5, b = , c = 8") == Failure(ParseError(
        "Expected r'[0-9]+' but found ','\nLine 1, character 12\n\na = 5, b = , c = 8\n           ^      "
    ))


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


def test_until_parser():
    block_start = "Ambiguous Content:"
    block_stop = ":End Content"

    class TestParser(TextParsers):
        ambiguous_start = lit(block_start)
        ambiguous_end = lit(block_stop)
        ambiguous = ambiguous_start >> until(ambiguous_end) << ambiguous_end

    ambiguous_content = """I'm an ambiguous block of Ambiguous Content: that has a bunch of :End Conten
    t problematic stuff in it"""
    content = f"""{block_start}{ambiguous_content}{block_stop}"""
    result = TestParser.ambiguous.parse(content)
    assert result == Success(ambiguous_content)

    empty_content = f"""{block_start}{block_stop}"""
    result_2 = TestParser.ambiguous.parse(empty_content)
    assert result_2 == Success("")

    no_termination_content = f"""{block_start}{ambiguous_content}"""
    result_3 = TestParser.ambiguous.parse(no_termination_content)
    assert result_3 == Failure(ParseError("Expected ':End Content' but found end of source"))

    assert str(TestParser.ambiguous) == "ambiguous = ambiguous_start >> until(ambiguous_end) << ambiguous_end"


def test_heredoc():
    class TestParser(TextParsers):
        heredoc = reg("[A-Za-z]+") >= (lambda token: until(token) << token)

    content = "EOF\nAnything at all\nEOF"
    result = TestParser.heredoc.parse(content)
    assert result == Success("Anything at all\n")


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


@pytest.mark.timeout(2)
def test_infinite_recursion_protection():
    class TestParsers(TextParsers):
        bad_rep = rep(opt("foo"))
        bad_rep1 = rep1(opt("foo"))
        bad_repsep = repsep(opt("foo"), opt(","))
        bad_rep1sep = rep1sep(opt("foo"), opt(","))

    # Recursion happens in middle of stream
    for parser in (TestParsers.bad_rep, TestParsers.bad_rep1, TestParsers.bad_repsep, TestParsers.bad_rep1sep):
        with pytest.raises(
            RuntimeError,
            match="Infinite recursion detected in "
            r"bad_rep1?(sep)? = rep1?(sep)?\(opt\('foo'\)(, opt\(','\))?\).*; "
            "empty string was matched and will be matched forever\n"
            "Line 1, character 13\n\nfoo foo foo bar",
        ):
            parser.parse("foo foo foo bar\nfoo foo foo")

    # Recursion happens at end of stream
    for parser in (TestParsers.bad_rep, TestParsers.bad_rep1, TestParsers.bad_repsep, TestParsers.bad_rep1sep):
        with pytest.raises(
            RuntimeError,
            match="Infinite recursion detected in "
            r"bad_rep1?(sep)? = rep1?(sep)?\(opt\('foo'\)(, opt\(','\))?\).*; "
            "empty string was matched and will be matched forever at end of source",
        ):
            parser.parse("foo foo foo\nfoo foo foo")


def test_protection():
    class TestParsers(TextParsers):
        end_aa = "aa" << eof
        b = lit("b")
        bba = rep(b | end_aa)

    assert TestParsers.bba.parse("b b aa") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("b b aa  ") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("  b b aa") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("aa b") == Failure(ParseError(
        "Expected end of source but found 'b'\nLine 1, character 4\n\naa b\n   ^"
    ))
    assert str(TestParsers.end_aa) == "end_aa = 'aa' << eof"


def test_failures_with_duplicate_tokens():
    # If two alternatives have the same starting token, the failure message should not contain duplicates.
    class ParallelParsers(TextParsers):
        plus_one = lit("+") >> lit("1")
        plus_two = lit("+") >> lit("2")
        alt = plus_one | plus_two

    assert ParallelParsers.alt.parse("-1") == Failure(ParseError("Expected '+' but found '-'\nLine 1, character 1\n\n-1\n^ "))


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
