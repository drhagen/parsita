from unittest import TestCase


class ExpressionTestCase(TestCase):
    def test_expressions(self):
        from examples.expressions import ExpressionParsers

        self.assertEqual(ExpressionParsers.expr.parse('1 + 2 * (3/6)').value, 2.0)


class JsonTestCase(TestCase):
    def test_json(self):
        from examples.json import JsonParsers

        self.assertEqual(JsonParsers.obj.parse('{"a": 1, "b": [1,2,3]}').value, {'a': 1, 'b': [1, 2, 3]})
