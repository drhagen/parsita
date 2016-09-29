from unittest import TestCase

from parsita import *
from parsita.state import Continue, Backtrack


class StateTestCase(TestCase):
    def test_state_creation(self):
        succ = Success(40)
        self.assertEqual(succ.value, 40)
        self.assertEqual(succ, Success(40))
        self.assertEqual(str(succ), 'Success(40)')
        self.assertNotEqual(succ, Success('a'))

        fail = Failure('my message')
        self.assertEqual(fail.message, 'my message')
        self.assertEqual(fail, Failure('my message'))
        self.assertEqual(str(fail), "Failure('my message')")
        self.assertNotEqual(fail, Failure('another message'))

        self.assertNotEqual(succ, fail)

        read = SequenceReader([1, 2, 3])
        self.assertEqual(read.first, 1)
        self.assertEqual(read.rest.first, 2)
        self.assertEqual(str(read), 'Reader(1@0)')
        self.assertEqual(str(read.rest.rest.rest), 'Reader(finished)')

        read = StringReader('a b')
        self.assertEqual(read.first, 'a')
        self.assertEqual(read.rest.first, ' ')
        self.assertEqual(str(read), 'StringReader(a@0)')
        self.assertEqual(str(read.rest.rest.rest), 'StringReader(finished)')

        cont = Continue(40, read)
        self.assertEqual(cont.value, 40)
        self.assertEqual(str(cont), "Continue(40, StringReader(a@0))")

        back = Backtrack(2, lambda: 'no further')
        self.assertEqual(back.message(), 'no further')
        self.assertEqual(str(back), "Backtrack(2, 'no further')")
