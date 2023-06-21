__all__ = ["DebugParser", "debug"]

from typing import Callable, Generic, Optional

from ..state import Input, Output, Reader, State
from ._base import Parser
from ._literal import lit


class DebugParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(
        self,
        parser: Parser[Input, Output],
        verbose: bool = False,
        callback: Optional[Callable[[Parser[Input, Output], Reader[Input]], None]] = None,
    ):
        super().__init__()
        self.parser = parser
        self.verbose = verbose
        self.callback = callback
        self._parser_string = repr(parser)

    def consume(self, state: State[Input], reader: Reader[Input]):
        if self.verbose:
            print(f"""Evaluating token {reader.next_token()} using parser {self._parser_string}""")

        if self.callback:
            self.callback(self.parser, reader)

        result = self.parser.cached_consume(state, reader)

        if self.verbose:
            print(f"""Result {result!r}""")

        return result

    def __repr__(self):
        return self.name_or_nothing() + f"debug({self.parser.name_or_repr()})"


def debug(
    parser: Parser[Input, Output],
    *,
    verbose: bool = False,
    callback: Optional[Callable[[Parser[Input, Output], Reader[Input]], None]] = None,
) -> DebugParser:
    """Execute debugging hooks before a parser.

    This parser is used purely for debugging purposes. From a parsing
    perspective, it behaves identically to the provided ``parser``, which makes
    ``debug`` a kind of harmless wrapper around a another parser. The
    functionality of the ``debug`` comes from providing one or more of the
    optional arguments.

    Args:
        parser: Parser or literal
        verbose: If True, causes a message to be printed containing the
            representation of ``parser`` and the next token before the
            invocation of ``parser``. After ``parser`` returns, the
            ``ParseResult`` returned is printed.
        callback: If not ``None``, is invoked immediately before ``parser`` is
            invoked. This allows the use to inspect the state of the input or
            add breakpoints before the possibly troublesome parser is invoked.
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return DebugParser(parser, verbose, callback)
