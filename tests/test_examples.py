import sys
from unittest import TestCase
import pytest


class ExpressionTestCase(TestCase):
    def test_expressions(self):
        from examples.expressions import ExpressionParsers

        self.assertEqual(ExpressionParsers.expr.parse('1 + 2 * (3/6)').value, 2.0)


class JsonTestCase(TestCase):
    def test_json(self):
        from examples.json import JsonParsers

        self.assertEqual(JsonParsers.obj.parse('{"a": 1, "b": [1,2,3]}').value, {'a': 1, 'b': [1, 2, 3]})


@pytest.mark.skipif(sys.version_info < (3, 7), reason='Example made for Python 3.7 and requires dataclasses')
class Positioned(TestCase):
    def test_positioned(self):
        from examples.positioned import PlusParsers, Variable, Plus

        value = PlusParsers.plus.parse('abc+xyz').or_die()
        self.assertEqual(value, Plus(Variable('abc', 0, 3), Variable('xyz', 4, 3)))
