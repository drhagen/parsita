import re
from unittest import TestCase

from parsita import *
from parsita.state import Backtrack, Continue


class StateTestCase(TestCase):
    def test_state_creation(self):
        succ = Success(40)
        self.assertEqual(succ.value, 40)
        self.assertEqual(succ, Success(40))
        self.assertEqual(str(succ), "Success(40)")
        self.assertNotEqual(succ, Success("a"))

        fail = Failure("my message")
        self.assertEqual(fail.message, "my message")
        self.assertEqual(fail, Failure("my message"))
        self.assertEqual(str(fail), "Failure('my message')")
        self.assertNotEqual(fail, Failure("another message"))

        self.assertNotEqual(succ, fail)

        read = SequenceReader([1, 2, 3])
        self.assertEqual(read.first, 1)
        self.assertEqual(read.rest.first, 2)
        self.assertEqual(str(read), "Reader(1@0)")
        self.assertEqual(str(read.rest.rest.rest), "Reader(finished)")

        read = StringReader("a b")
        self.assertEqual(read.first, "a")
        self.assertEqual(read.rest.first, " ")
        self.assertEqual(str(read), "StringReader(a@0)")
        self.assertEqual(str(read.rest.rest.rest), "StringReader(finished)")

        cont = Continue(read, 40)
        self.assertEqual(cont.value, 40)
        self.assertEqual(str(cont), "Continue(40, StringReader(a@0))")

        back = Backtrack(read, lambda: "no further")
        self.assertEqual(back.expected[0](), "no further")
        self.assertEqual(str(back), "Backtrack(StringReader(a@0), ['no further'])")

        error = ParseError("Expected a but found b at index 0")
        self.assertEqual(str(error), "Expected a but found b at index 0")
        self.assertEqual(repr(error), "ParseError('Expected a but found b at index 0')")

    def test_current_line(self):
        # This test only exists to get 100% test coverage without doing a pragma: no cover on the whole current_line
        # method. Under normal operation, the for loop should never complete because the position is also on some
        # line. Here, the position has been artificially advanced beyond the length of the input.
        reader = StringReader("foo", 3)
        self.assertEqual(reader.current_line(), None)

    def test_reader_with_defective_next_token_regex(self):
        # With the default value of next_token_regex, a match cannot fail. However, if a fallible regex is provided to
        # a super class next_token should not crash.
        class DefectiveReader(StringReader):
            next_token_regex = re.compile(r"[A-Za-z0-9]+")

        good_position = DefectiveReader("foo_foo", 4)
        self.assertEqual(good_position.next_token(), "foo")

        bad_position = DefectiveReader("foo_foo", 3)
        self.assertEqual(bad_position.next_token(), "_")
