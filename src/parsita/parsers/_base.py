from __future__ import annotations

__all__ = ["Parser", "wrap_literal"]

from abc import abstractmethod
from typing import Any, Callable, Generic, Optional, Sequence, TypeVar, Union, overload

from .. import options
from ..state import (
    Continue,
    Failure,
    Input,
    Output,
    ParseError,
    Reader,
    Result,
    SequenceReader,
    State,
    StringReader,
    Success,
)

OtherOutput = TypeVar("OtherOutput")

# Singleton indicating that no result is yet in the memo
# Use Ellipsis instead of object() to avoid mypy errors
missing = ...


@overload
def wrap_literal(obj: Sequence[Input]) -> Parser[Input, Sequence[Input]]: ...


@overload
def wrap_literal(obj: Parser[Input, Output]) -> Parser[Input, Output]: ...


def wrap_literal(
    obj: Union[Parser[Input, Output], Sequence[Input]],
) -> Union[Parser[Input, Output], Parser[Input, Sequence[Input]]]:
    from ._literal import LiteralParser

    if isinstance(obj, Parser):
        return obj
    else:
        return LiteralParser(obj, options.whitespace)


class Parser(Generic[Input, Output]):
    """Abstract base class for all parser combinators.

    Inheritors of this class must:

    1. Implement the ``_consume`` method
    2. Implement the ``__repr__`` method

    Attributes:
        protected (bool): The metaclasses set this flag to true whenever a
            parser is assigned to a name. Operators that flatten the parsers
            they receive (``__or__`` and ``__and__``) will not flatten parsers
            with a ``True`` value here. This is most important for ``__and__``
            because there is no other way to tell that these two should be
            different:

            ```
            abc = a & b & c  # returns [a, b, c]
            ```
            ```
            temp = a & b
            abc = temp & c  # returns [[a, b], c]
            ```

            The fundamental limitation is that python does not handle linked
            lists well or have unpacking that would let one unpack abc as
            [temp, c].
        name (Optional[str]): A name used by ``__str__`` and ``__repr__``.
            It is set by the context classes when a parser is assigned to a
            name.
    """

    def consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        """Match this parser at the given location.

        This is a concrete wrapper around ``consume``. This method implements
        the left-recursive packrat algorithm:

        1. Check the memo if this parser has already operated at this location
            a. Return the result immediately if it is there
        2. Put a ``None`` in the memo for this parser at this position
        3. Invoke ``consume``
        4. Put the result in the memo for this parser at this position
        5. Return the result

        Individual parsers need to implement ``_consume``, but not ``consume``.
        But all combinations should invoke ``consume`` instead of ``_consume``
        on their member parsers.

        Args:
            state: The mutable state of the parse
            reader: The current state of the input

        Returns:
            If the pattern matches, a ``Continue`` is returned. If the pattern
            does not match, a ``None`` is returned.
        """
        key = (self, reader.position)
        value = state.memo.get(key, missing)

        if value is not missing:
            return value

        state.memo[key] = None

        result = self._consume(state, reader)

        state.memo[key] = result

        return result

    @abstractmethod
    def _consume(self, state: State, reader: Reader[Input]) -> Optional[Continue[Input, Output]]:
        """Abstract method for matching this parser at the given location.

        This is the central method of every parser combinator.

        Args:
            state: The mutable state of the parse
            reader: The current state of the input

        Returns:
            If the pattern matches, a ``Continue`` is returned. If the pattern
            does not match, a ``None`` is returned.
        """
        raise NotImplementedError()

    def parse(self, source: Union[Sequence[Input], Reader[Input]]) -> Result[Output]:
        """Completely parse a source.

        Args:
            source: What will be parsed.

        Returns:
            If the parser succeeded in matching and consumed the entire output,
            the value from ``Continue`` is copied to make a ``Success``. If the
            parser failed in matching, the expected patterns at the farthest
            point in the source are used to construct a ``ParseError``, which is
            then used to contruct a ``Failure``. If the parser succeeded but the
            source was not completely consumed, it returns a ``Failure`` with a
            ``ParseError`` indicating this.

        If a ``Reader`` is passed in, it is used directly. Otherwise, the source
        is converted to an appropriate ``Reader``. If the source is ``str``, a
        ``StringReader`` is used. Otherwise, a ``SequenceReader`` is used.
        """
        from ._end_of_source import eof

        if isinstance(source, Reader):
            reader = source
        elif isinstance(source, str):
            reader = StringReader(source, 0)  # type: ignore
        else:
            reader = SequenceReader(source)

        state: State = State()

        status = (self << eof).consume(state, reader)

        if isinstance(status, Continue):
            return Success(status.value)
        else:
            used = set()
            unique_expected = []
            for expected in state.expected:
                if expected not in used:
                    used.add(expected)
                    unique_expected.append(expected)

            # mypy does not understand that state.farthest cannot be None when there is a failure
            parse_error = ParseError(state.farthest, unique_expected)  # type: ignore
            return Failure(parse_error)

    name: Optional[str] = None

    protected: bool = False

    def name_or_repr(self) -> str:
        if self.name is None:
            return self.__repr__()
        else:
            return self.name

    def name_or_nothing(self) -> str:
        if self.name is None:
            return ""
        else:
            return self.name + " = "

    @overload
    def __or__(self, other: Sequence[Input]) -> Parser[Input, Union[Output, Sequence[Input]]]: ...

    @overload
    def __or__(
        self, other: Parser[Input, OtherOutput]
    ) -> Parser[Input, Union[Output, OtherOutput]]: ...

    def __or__(
        self, other: Union[Sequence[Input], Parser[Input, OtherOutput]]
    ) -> Parser[Input, object]:
        from ._alternative import LongestAlternativeParser

        narrowed_other = wrap_literal(other)
        parsers: list[Parser[Input, object]] = []
        if isinstance(self, LongestAlternativeParser) and not self.protected:
            parsers.extend(self.parsers)
        else:
            parsers.append(self)
        if isinstance(narrowed_other, LongestAlternativeParser) and not narrowed_other.protected:
            parsers.extend(narrowed_other.parsers)
        else:
            parsers.append(narrowed_other)
        return LongestAlternativeParser(*parsers)

    @overload
    def __ror__(self, other: Sequence[Input]) -> Parser[Input, Union[Sequence[Input], Output]]: ...

    @overload
    def __ror__(
        self, other: Parser[Input, OtherOutput]
    ) -> Parser[Input, Union[OtherOutput, Output]]: ...

    def __ror__(
        self, other: Union[Sequence[Input], Parser[Input, OtherOutput]]
    ) -> Parser[Input, object]:
        narrowed_other = wrap_literal(other)
        return narrowed_other.__or__(self)

    @overload
    def __and__(self, other: Sequence[Input]) -> Parser[Input, Sequence[Any]]: ...

    @overload
    def __and__(self, other: Parser[Input, OtherOutput]) -> Parser[Input, Sequence[Any]]: ...

    def __and__(
        self, other: Union[Sequence[Input], Parser[Input, OtherOutput]]
    ) -> Parser[Input, Sequence[Any]]:
        from ._sequential import SequentialParser

        narrowed_other = wrap_literal(other)
        if isinstance(self, SequentialParser) and not self.protected:  # type: ignore
            return SequentialParser(*self.parsers, narrowed_other)  # type: ignore
        else:
            return SequentialParser(self, narrowed_other)

    @overload
    def __rand__(self, other: Sequence[Input]) -> Parser[Input, Sequence[Any]]: ...

    @overload
    def __rand__(self, other: Parser[Input, OtherOutput]) -> Parser[Input, Sequence[Any]]: ...

    def __rand__(
        self, other: Union[Sequence[Input], Parser[Input, OtherOutput]]
    ) -> Parser[Input, Sequence[Any]]:
        narrowed_other = wrap_literal(other)
        return narrowed_other.__and__(self)

    @overload
    def __rshift__(self, other: Sequence[Input]) -> Parser[Input, Sequence[Input]]: ...

    @overload
    def __rshift__(self, other: Parser[Input, OtherOutput]) -> Parser[Input, OtherOutput]: ...

    def __rshift__(
        self, other: Union[Sequence[Input], Parser[Input, OtherOutput]]
    ) -> Parser[Input, object]:
        from ._sequential import DiscardLeftParser

        narrowed_other = wrap_literal(other)
        return DiscardLeftParser(self, narrowed_other)

    def __rrshift__(
        self, other: Union[Sequence[Input], Parser[Input, OtherOutput]]
    ) -> Parser[Input, Output]:
        narrowed_other = wrap_literal(other)
        return narrowed_other.__rshift__(self)

    def __lshift__(
        self, other: Union[Sequence[Input], Parser[Input, OtherOutput]]
    ) -> Parser[Input, Output]:
        from ._sequential import DiscardRightParser

        narrowed_other = wrap_literal(other)
        return DiscardRightParser(self, narrowed_other)

    @overload
    def __rlshift__(self, other: Sequence[Input]) -> Parser[Input, Sequence[Input]]: ...

    @overload
    def __rlshift__(self, other: Parser[Input, OtherOutput]) -> Parser[Input, OtherOutput]: ...

    def __rlshift__(
        self, other: Union[Sequence[Input], Parser[Input, OtherOutput]]
    ) -> Parser[Input, object]:
        narrowed_other = wrap_literal(other)
        return narrowed_other.__lshift__(self)

    def __gt__(self, other: Callable[[Output], OtherOutput]) -> Parser[Input, OtherOutput]:
        from ._conversion import ConversionParser

        return ConversionParser(self, other)

    def __ge__(
        self, other: Callable[[Output], Parser[Input, OtherOutput]]
    ) -> Parser[Input, OtherOutput]:
        from ._conversion import TransformationParser

        return TransformationParser(self, other)
