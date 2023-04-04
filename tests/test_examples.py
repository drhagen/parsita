from parsita import Success


def test_expressions():
    from examples.expressions import ExpressionParsers

    assert ExpressionParsers.expr.parse("1 + 2 * (3/6)") == Success(2.0)


def test_json():
    from examples.json import JsonParsers

    assert JsonParsers.obj.parse('{"a": 1, "b": [1,2,3]}') == Success({"a": 1, "b": [1, 2, 3]})


def test_positioned():
    from examples.positioned import Plus, PlusParsers, Variable

    assert PlusParsers.plus.parse("abc+xyz") == Success(Plus(Variable("abc", 0, 3), Variable("xyz", 4, 3)))
