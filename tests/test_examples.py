def test_expressions():
    from examples.expressions import ExpressionParsers

    assert ExpressionParsers.expr.parse("1 + 2 * (3/6)").or_die() == 2.0


def test_json():
    from examples.json import JsonParsers

    assert JsonParsers.obj.parse('{"a": 1, "b": [1,2,3]}').or_die(), {"a": 1, "b": [1, 2, 3]}


def test_positioned():
    from examples.positioned import Plus, PlusParsers, Variable

    value = PlusParsers.plus.parse("abc+xyz").or_die()
    assert value == Plus(Variable("abc", 0, 3), Variable("xyz", 4, 3))
