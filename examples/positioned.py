"""User-defined positioned parser example.

This shows how a new parser can be defined outside Parsita and used in tandem
with the built-in parsers. The ``positioned`` parser updates the value
returned from an arbitrary parser with the position in the input that was
consumed by that parser.
"""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Generic

from parsita import Parser, TextParsers, reg
from parsita.util import splat
from parsita.state import Reader, Status, Continue, Input, Output


class PositionAware(Generic[Output]):
    """An object which can cooperate with the positioned parser.

    The ``positioned`` parser calls the ``set_position`` method on values it
    receives. This abstract base class marks those objects that can cooperate
    with ``positioned`` in this way and receive the input position to produce
    the final value.
    """

    @abstractmethod
    def set_position(self, start: int, length: int) -> Output:
        """Produce a new value with the position set.

        This abstract method must be implemented by subclasses of
        ``PositionAware``. It receives the position in the input that was
        consumed and returns a new value, typically an object similar to the old
        value, but with the position set. Important: the old value is not
        expected to be mutated.

        Args:
            start: The index of the first character consumed by the parser
            length: The number of characters consumed by the parser
        """
        pass


class PositionedParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, parser: Parser[Input, PositionAware[Output]]):
        super().__init__()
        self.parser = parser

    def consume(self, reader: Reader[Input]) -> Status[Input, Output]:
        start = reader.position
        status = self.parser.consume(reader)

        if isinstance(status, Continue):
            end = status.remainder.position
            return Continue(status.remainder, status.value.set_position(start, end - start)).merge(status)
        else:
            return status

    def __repr__(self):
        return self.name_or_nothing() + "positioned({})".format(self.parser.name_or_repr())


def positioned(parser: Parser[Input, PositionAware[Output]]):
    """Set the position on a PositionAware value.

    This parser matches ``parser`` and, if successful, calls ``set_position``
    on the produced value to produce a new value. The value produces by
    ``parser`` must implement the ``PositionAware`` interface so that it can
    receive the position in the input.

    Args:
        parser: Parser
    """
    return PositionedParser(parser)


# Everything below here is an example use case
@dataclass
class UnfinishedVariable(PositionAware):
    name: str

    def set_position(self, start: int, length: int):
        return Variable(self.name, start, length)


@dataclass
class Variable:
    name: str
    start: int
    length: int


@dataclass
class Plus:
    first: Variable
    second: Variable


class PlusParsers(TextParsers):
    variable = positioned(reg("[A-Za-z][A-Za-z0-9_]*") > UnfinishedVariable)
    plus = variable & "+" >> variable > splat(Plus)


if __name__ == "__main__":
    print(PlusParsers.plus.parse("abc + xyz").or_die())
