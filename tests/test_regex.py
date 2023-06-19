import pytest

from parsita import (
    Failure,
    ParseError,
    ParserContext,
    RecursionError,
    StringReader,
    Success,
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
    class TestParsers(ParserContext, whitespace="[ ]*"):
        hundred = lit("100") > float

    assert TestParsers.hundred.parse("") == Failure(ParseError(StringReader("", 0), ["'100'"]))
    assert TestParsers.hundred.parse("100") == Success(100)
    assert TestParsers.hundred.parse("   100") == Success(100)
    assert TestParsers.hundred.parse("100    ") == Success(100)
    assert TestParsers.hundred.parse("   100    ") == Success(100)
    assert str(TestParsers.hundred) == "hundred = '100'"


def test_literal_no_whitespace():
    class TestParsers(ParserContext):
        hundred = lit("100") > float

    assert TestParsers.hundred.parse("100") == Success(100)
    assert TestParsers.hundred.parse(" 100") == Failure(ParseError(StringReader(" 100", 0), ["'100'"]))
    assert TestParsers.hundred.parse("100 ") == Failure(ParseError(StringReader("100 ", 3), ["end of source"]))
    assert str(TestParsers.hundred) == "hundred = '100'"


def test_literal_multiple():
    class TestParsers(ParserContext):
        keyword = lit("in", "int")

    assert TestParsers.keyword.parse("int") == Success("int")


def test_pred_interval():
    class TestParsers(ParserContext, whitespace="[ ]*"):
        number = reg(r"\d+") > int
        pair = "[" >> number << "," & number << "]"
        interval = pred(pair, lambda x: x[0] <= x[1], "ordered pair")

    assert TestParsers.interval.parse("[1, 2]") == Success([1, 2])
    assert TestParsers.interval.parse("[2, 1]") == Failure(ParseError(StringReader("[2, 1]", 6), ["ordered pair"]))
    assert TestParsers.pair.parse("[1,a]") == TestParsers.interval.parse("[1,a]")


def test_pred_static_expression():
    def is_static(expression):
        if isinstance(expression, str):
            return False
        if isinstance(expression, int):
            return True
        elif isinstance(expression, list):
            return all(is_static(e) for e in expression)

    class PredParsers(ParserContext):
        name = reg(r"[a-zA-Z]+")
        integer = reg(r"[0-9]+") > int
        function = name >> "(" >> repsep(expression, ",") << ")"
        expression = function | name | integer
        static_expression = pred(expression, is_static, "static expression")

    assert PredParsers.static_expression.parse("1") == Success(1)
    assert PredParsers.static_expression.parse("f(2,1)") == Success([2, 1])
    assert PredParsers.static_expression.parse("a") == Failure(
        ParseError(StringReader("a", 1), ["'('", "static expression"])
    )
    assert PredParsers.static_expression.parse("f(a,1)") == Failure(
        ParseError(StringReader("f(a,1)", 6), ["static expression"])
    )
    assert PredParsers.static_expression.parse("f(2,1") == Failure(ParseError(StringReader("f(2,1", 5), ["','", "')'"]))


def test_regex():
    class TestParsers(ParserContext, whitespace="[ ]*"):
        digits = reg(r"\d+")

    assert TestParsers.digits.parse("100") == Success("100")
    assert TestParsers.digits.parse("   100") == Success("100")
    assert TestParsers.digits.parse("100    ") == Success("100")
    assert TestParsers.digits.parse("   100    ") == Success("100")
    assert str(TestParsers.digits) == r"digits = reg(r'\d+')"


def test_regex_no_whitespace():
    class TestParsers(ParserContext):
        digits = reg(r"\d+") > float

    assert TestParsers.digits.parse("100") == Success(100)
    assert TestParsers.digits.parse(" 100") == Failure(ParseError(StringReader(" 100", 0), [r"r'\d+'"]))
    assert TestParsers.digits.parse("100 ") == Failure(ParseError(StringReader("100 ", 3), ["end of source"]))
    assert str(TestParsers.digits) == r"digits = reg(r'\d+')"


def test_regex_custom_whitespace():
    class TestParsers(ParserContext, whitespace="[ ]*"):
        digits = reg(r"\d+") > float
        pair = digits & digits

    assert TestParsers.digits.parse("100") == Success(100)
    assert TestParsers.digits.parse("   100    ") == Success(100)
    assert TestParsers.digits.parse("100\n") == Failure(ParseError(StringReader("100\n", 3), ["end of source"]))
    assert TestParsers.digits.parse("100 \n") == Failure(ParseError(StringReader("100 \n", 4), ["end of source"]))
    assert TestParsers.pair.parse("100 100") == Success([100, 100])
    assert TestParsers.pair.parse("100\n100") == Failure(ParseError(StringReader("100\n100", 3), [r"r'\d+'"]))
    assert str(TestParsers.digits) == r"digits = reg(r'\d+')"
    assert str(TestParsers.pair) == "pair = digits & digits"


def test_optional():
    class TestParsers(ParserContext, whitespace="[ ]*"):
        a = reg(r"\d+") > float
        b = opt(a)

    assert TestParsers.b.parse(" 100 ") == Success([100])
    assert TestParsers.b.parse(" c ") == Failure(ParseError(StringReader(" c ", 1), [r"r'\d+'"]))
    assert str(TestParsers.b) == "b = opt(a)"


def test_multiple_messages():
    class TestParsers(ParserContext):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = function | index | name

    assert TestParsers.any.parse("var") == Success("var")
    assert TestParsers.any.parse("var[a]") == Success(["var", "a"])
    assert TestParsers.any.parse("var(a)") == Success(["var", "a"])
    assert TestParsers.any.parse("func{var}") == Failure(
        ParseError(StringReader("func{var}", 4), ["'('", "'['", "end of source"])
    )
    assert TestParsers.any.parse("func[var") == Failure(ParseError(StringReader("func[var", 8), ["']'"]))


def test_alternative_longest():
    class TestParsers(ParserContext):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = name | function | index

    assert TestParsers.any.parse("var(arg)") == Success(["var", "arg"])
    assert TestParsers.any.parse("func{var}") == Failure(
        ParseError(StringReader("func{var}", 4), ["'('", "'['", "end of source"])
    )


def test_first_function():
    class TestParsers(ParserContext):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = first(name, function, index)

    assert TestParsers.any.parse("var") == Success("var")
    assert TestParsers.any.parse("var(arg)") == Failure(ParseError(StringReader("var(arg)", 3), ["end of source"]))
    assert TestParsers.any.parse("") == Failure(ParseError(StringReader("", 0), ["r'[a-z]+'"]))


def test_longest_function():
    class TestParsers(ParserContext):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = longest(name, function, index)

    assert TestParsers.any.parse("var(arg)") == Success(["var", "arg"])
    assert TestParsers.any.parse("func{var}") == Failure(
        ParseError(StringReader("func{var}", 4), ["'('", "'['", "end of source"])
    )


def test_longest_function_shortest_later():
    class TestParsers(ParserContext):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = longest(function, index, name)

    assert TestParsers.any.parse("var(arg)") == Success(["var", "arg"])


def test_longest_function_all_failures():
    class TestParsers(ParserContext):
        name = reg("[a-z]+")
        function = name & "(" >> name << ")"
        index = name & "[" >> name << "]"
        any = longest(function, index)

    assert TestParsers.any.parse("func{var}") == Failure(ParseError(StringReader("func{var}", 4), ["'('", "'['"]))


def test_sequential():
    class TestParsers(ParserContext, whitespace="[ ]*"):
        hello = lit("Hello")
        world = lit("world")
        hello_world = hello & world

    assert TestParsers.hello_world.parse("Hello world") == Success(["Hello", "world"])
    assert TestParsers.hello_world.parse("Hello David") == Failure(
        ParseError(StringReader("Hello David", 6), ["'world'"])
    )
    assert TestParsers.hello_world.parse("Hello") == Failure(ParseError(StringReader("Hello", 5), ["'world'"]))


def test_multiline():
    class TestParsers(ParserContext, whitespace=r"\s*"):
        hello = lit("Hello")
        world = lit("world")
        hello_world = hello & world

    assert TestParsers.hello_world.parse("Hello\nworld") == Success(["Hello", "world"])
    assert TestParsers.hello_world.parse("Hello\nDavid") == Failure(
        ParseError(StringReader("Hello\nDavid", 6), ["'world'"])
    )


def test_repeated():
    class TestParsers(ParserContext):
        number = reg(r"\d+") > int
        trail = "(" >> rep(number << ",") << ")" > tuple
        trail1 = "(" >> rep1(number << ",") << ")" > tuple
        notrail = "(" >> repsep(number, ",") << ")" > tuple
        notrail1 = "(" >> rep1sep(number, ",") << ")" > tuple

    assert TestParsers.trail.parse("(1,2,3)") == Failure(ParseError(StringReader("(1,2,3)", 6), ["','"]))

    assert TestParsers.trail.parse("(1,2,3,)") == Success((1, 2, 3))
    assert TestParsers.trail.parse("()") == Success(())
    assert TestParsers.trail1.parse("(1,2,3)") == Failure(ParseError(StringReader("(1,2,3)", 6), ["','"]))
    assert TestParsers.trail1.parse("(1,2,3,)") == Success((1, 2, 3))
    assert TestParsers.trail1.parse("()") == Failure(ParseError(StringReader("()", 1), [r"r'\d+'"]))
    assert TestParsers.notrail.parse("(1,2,3)") == Success((1, 2, 3))
    assert TestParsers.notrail.parse("(1,2,3,)") == Failure(ParseError(StringReader("(1,2,3,)", 7), [r"r'\d+'"]))
    assert TestParsers.notrail.parse("()") == Success(())
    assert TestParsers.notrail1.parse("(1,2,3)") == Success((1, 2, 3))
    assert TestParsers.notrail1.parse("(1,2,3,)") == Failure(ParseError(StringReader("(1,2,3,)", 7), [r"r'\d+'"]))
    assert TestParsers.notrail1.parse("()") == Failure(ParseError(StringReader("()", 1), [r"r'\d+'"]))


def test_transformation_as_fallible_conversion():
    class Percent:
        def __init__(self, number: int):
            self.number = number

        def __eq__(self, other):
            if isinstance(other, Percent):
                return self.number == other.number
            else:
                return NotImplemented

    class TestParsers(ParserContext):
        def to_percent(number: int):
            if not 0 <= number <= 100:
                return failure("a number between 0 and 100")
            else:
                return success(Percent(number))

        percent = (reg(r"[0-9]+") > int) >= to_percent

    assert TestParsers.percent.parse("50") == Success(Percent(50))
    assert TestParsers.percent.parse("150") == Failure(
        ParseError(StringReader("150", 3), ["a number between 0 and 100"])
    )
    assert TestParsers.percent.parse("a") == Failure(ParseError(StringReader("a", 0), ["r'[0-9]+'"]))


def test_transformation_as_parameterized_parser():
    class NumberParsers(ParserContext, whitespace="[ ]*"):
        def select_parser(type: str):
            if type == "int":
                return reg(r"[0-9]+") > int
            elif type == "decimal":
                return reg(r"[0-9]+\.[0-9]+") > float

        type = lit("int", "decimal")
        number = type >= select_parser

    assert NumberParsers.number.parse("int 5") == Success(5)
    assert NumberParsers.number.parse("decimal 5") == Failure(
        ParseError(StringReader("decimal 5", 8), [r"r'[0-9]+\.[0-9]+'"])
    )


def test_transformation_error_propogation():
    class AssignmentsParser(ParserContext, whitespace="[ ]*"):
        def assignments_to_map(assignments):
            names_found = set()
            output = {}
            for name, value in assignments:
                if name in names_found:
                    return failure(f"{name!r} to be found only once")
                names_found.add(name)
                output[name] = value

            return success(output)

        name = reg(r"[a-z]+")
        value = reg(r"[0-9]+") > int
        assignment = name << "=" & value
        assignments = repsep(assignment, ",") >= assignments_to_map

    assert AssignmentsParser.assignments.parse("a = 5, b = 4") == Success({"a": 5, "b": 4})
    assert AssignmentsParser.assignments.parse("a = 5, b = 4, a = 3") == Failure(
        ParseError(StringReader("a = 5, b = 4, a = 3", 19), ["','", "'a' to be found only once"])
    )
    assert AssignmentsParser.assignments.parse("a = 5, b = , c = 8") == Failure(
        ParseError(StringReader("a = 5, b = , c = 8", 11), ["r'[0-9]+'"])
    )


def test_debug_callback():
    result = False

    def callback(parser, reader):
        nonlocal result
        remainder = reader.source[reader.position :]
        result = remainder == "45"
        result &= isinstance(parser.parse(remainder), Failure)
        result &= isinstance(parser.parse("345"), Success)

    class TestParsers(ParserContext):
        a = lit("123")
        b = lit("345")
        c = a & debug(b, callback=callback)

    TestParsers.c.parse("12345")
    assert result
    assert str(TestParsers.c) == "c = a & debug(b)"


def test_debug_verbose(capsys):
    class TestParsers(ParserContext):
        a = lit("123")
        c = a & debug("345", verbose=True)

    TestParsers.c.parse("12345")

    captured = capsys.readouterr()
    assert "Evaluating" in captured.out
    assert "Result" in captured.out


def test_until_parser():
    block_start = "Ambiguous Content:"
    block_stop = ":End Content"

    class TestParser(ParserContext):
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
    assert result_3 == Failure(
        ParseError(StringReader(no_termination_content, len(no_termination_content)), ["':End Content'"])
    )

    assert str(TestParser.ambiguous) == "ambiguous = ambiguous_start >> until(ambiguous_end) << ambiguous_end"


def test_heredoc():
    class TestParser(ParserContext, whitespace=r"\s*"):
        heredoc = reg("[A-Za-z]+") >= (lambda token: until(token) << token)

    content = "EOF\nAnything at all\nEOF"
    result = TestParser.heredoc.parse(content)
    assert result == Success("Anything at all\n")


def test_recursion_literals():
    class TestParsers(ParserContext, whitespace="[ ]*"):
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
    class TestParsers(ParserContext, whitespace="[ ]*"):
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
    class TestParsers(ParserContext, whitespace=r"\s*"):
        bad_rep = rep(opt("foo"))
        bad_rep1 = rep1(opt("foo"))
        bad_repsep = repsep(opt("foo"), opt(","))
        bad_rep1sep = rep1sep(opt("foo"), opt(","))

    # Recursion happens in middle of stream
    for parser in (TestParsers.bad_rep, TestParsers.bad_rep1, TestParsers.bad_repsep, TestParsers.bad_rep1sep):
        text = "foo foo foo bar\nfoo foo foo"
        with pytest.raises(RecursionError) as actual:
            parser.parse(text)
        assert actual.value == RecursionError(parser, StringReader(text, 12))
        assert str(actual.value) == (
            f"Infinite recursion detected in {parser!r}; "
            f"empty string was matched and will be matched forever\n"
            "Line 1, character 13\n"
            "\n"
            "foo foo foo bar\n"
            "            ^   "
        )

    # Recursion happens at end of stream
    for parser in (TestParsers.bad_rep, TestParsers.bad_rep1, TestParsers.bad_repsep, TestParsers.bad_rep1sep):
        text = "foo foo foo\nfoo foo foo"
        with pytest.raises(RecursionError) as actual:
            parser.parse(text)
        assert actual.value == RecursionError(parser, StringReader(text, 23))
        assert str(actual.value) == (
            f"Infinite recursion detected in {parser!r}; "
            f"empty string was matched and will be matched forever at end of source"
        )


def test_protection():
    class TestParsers(ParserContext, whitespace="[ ]*"):
        end_aa = "aa" << eof
        b = lit("b")
        bba = rep(b | end_aa)

    assert TestParsers.bba.parse("b b aa") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("b b aa  ") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("  b b aa") == Success(["b", "b", "aa"])
    assert TestParsers.bba.parse("aa b") == Failure(ParseError(StringReader("aa b", 3), ["end of source"]))
    assert str(TestParsers.end_aa) == "end_aa = 'aa' << eof"


def test_failures_with_duplicate_tokens():
    # If two alternatives have the same starting token, the failure message should not contain duplicates.
    class ParallelParsers(ParserContext):
        plus_one = lit("+") >> lit("1")
        plus_two = lit("+") >> lit("2")
        alt = plus_one | plus_two

    assert ParallelParsers.alt.parse("-1") == Failure(ParseError(StringReader("-1", 0), ["'+'"]))


def test_nested_class():
    class TestOuter(ParserContext, whitespace="[ ]*"):
        start = "%%"

        class TestInner(ParserContext):
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
    class TestOuter(ParserContext, whitespace="[ ]*"):
        start = "%%"

        class TestInner(ParserContext):
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
