from __future__ import annotations

__all__ = ["ForwardDeclaration", "ParserContext", "fwd"]

import builtins
import inspect
import re
from dataclasses import dataclass
from re import Pattern
from typing import TYPE_CHECKING, Any, Generic, NoReturn, Optional, Union, no_type_check

from . import options
from .parsers import LiteralParser, Parser, RegexParser
from .state import Continue, Input, Output, Reader, State

missing: Any = object()


@dataclass(frozen=True)
class Options:
    whitespace: Optional[Parser[Any, object]] = None


class ParsersDict(dict[str, Any]):
    def __init__(self, old_options: Options):
        super().__init__()

        # Holds state of options at start of definition
        self.old_options = old_options

        # Stores forward declarations as they are discovered
        self.forward_declarations: dict[str, ForwardDeclaration[Any, Any]] = {}

    @no_type_check  # mypy cannot handle all the frame inspection
    def __missing__(self, key: str) -> ForwardDeclaration[Any, Any]:
        frame = inspect.currentframe()  # Should be the frame of __missing__
        while frame.f_code.co_name != "__missing__":  # pragma: no cover
            # But sometimes debuggers add frames on top of the stack;
            # get back to `__missing__`'s frame
            frame = frame.f_back

        class_body_frame = frame.f_back.f_back  # Frame of parser context is two frames back
        class_body_locals = class_body_frame.f_locals
        class_body_globals = class_body_frame.f_globals

        if key in self.forward_declarations:
            return self.forward_declarations[key]
        elif key in class_body_locals:
            return class_body_locals[key]
        elif key in class_body_globals:
            return class_body_globals[key]
        elif key in dir(builtins):
            return getattr(builtins, key)
        else:
            new_forward_declaration = ForwardDeclaration()
            self.forward_declarations[key] = new_forward_declaration
            return new_forward_declaration

    def __setitem__(self, key: str, value: Any) -> None:
        if isinstance(value, Parser):
            # Protects against accidental concatenation of sequential parsers
            value.protected = True

            # Used for better error messages
            value.name = key

        super().__setitem__(key, value)


class ForwardDeclaration(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self) -> None:
        self._definition: Optional[Parser[Input, Output]] = None

    def __getattribute__(self, member: str) -> Any:
        if member != "_definition" and self._definition is not None:
            return getattr(self._definition, member)
        else:
            return object.__getattribute__(self, member)

    if TYPE_CHECKING:
        # Type checkers don't know that `_consume` is implemented in `__getattribute__`

        def _consume(
            self, state: State, reader: Reader[Input]
        ) -> Optional[Continue[Input, Output]]: ...

    def define(self, parser: Parser[Input, Output]) -> None:
        self._definition = parser


def fwd() -> ForwardDeclaration[Input, Output]:
    """Manually create a forward declaration.

    Normally, forward declarations are created automatically by the contexts.
    But they can be created manually if not in a context or if the user wants
    to avoid confusing the IDE.
    """
    return ForwardDeclaration()


class ParserContextMeta(type):
    default_whitespace: Union[Parser[Any, object], Pattern[str], str, None] = None

    @classmethod
    def __prepare__(
        mcs,  # noqa: N804
        name: str,
        bases: tuple[type, ...],
        /,
        *,
        whitespace: Union[Parser[Any, object], Pattern[str], str, None] = missing,
        **kwargs: Any,
    ) -> ParsersDict:
        super().__prepare__(name, bases, **kwargs)

        if whitespace is missing:
            whitespace = mcs.default_whitespace

        if isinstance(whitespace, (str, bytes)):
            whitespace = re.compile(whitespace)

        if isinstance(whitespace, Pattern):
            whitespace = RegexParser(whitespace)

        old_options = Options(whitespace=options.whitespace)

        # Store whitespace in global location
        options.whitespace = whitespace
        return ParsersDict(old_options)

    def __init__(cls, name: str, bases: tuple[type, ...], dct: ParsersDict, /, **_: Any) -> None:
        old_options = dct.old_options

        super().__init__(name, bases, dct)

        # Resolve forward declarations, will raise if name not found
        for name, forward_declaration in dct.forward_declarations.items():
            obj = dct[name]
            if not isinstance(obj, Parser):
                obj = LiteralParser(obj, options.whitespace)
            forward_declaration._definition = obj

        # Reset global variables
        options.whitespace = old_options.whitespace

    def __new__(
        mcs: type[ParserContextMeta],  # noqa: N804
        name: str,
        bases: tuple[type, ...],
        dct: ParsersDict,
        /,
        whitespace: Union[Parser[Any, Any], Pattern[str], str, None] = missing,
    ) -> ParserContextMeta:
        return super().__new__(mcs, name, bases, dct)

    def __call__(cls, *args: object, **kwargs: object) -> NoReturn:
        raise TypeError(
            "ParserContexts cannot be instantiated. They use class bodies purely as contexts for "
            "managing defaults and allowing forward declarations. Access the individual parsers "
            "as static attributes."
        )


class ParserContext(metaclass=ParserContextMeta):
    """Context for parsing.

    This is not a real class. Don't instantiate it. This is used by inheriting
    from it and defining parsers as class attributes in the body of the child
    class.

    The parser context uses various aspects of class bodies in Python to
    perform a few kinds of magic:

    1. Assign the metaclass argument ``whitespace`` to ``options.whitespace``
       only while the class body is being executed so that it can be used by
       terminal parsers.
    2. For each class attribute that is a ``Parser``, assign the name of that
       attribute to the ``name`` attribute of the parser so that names parsers
       know their own name.
    3. For each class attribute that is a ``Parser``, set the ``protected``
       attribute of the parser to ``True`` so that parsers know when they are
       in a chain of `a | b | c` or `a & b & c` and when they are not.
    4. Create a ``ForwardDeclaration`` as a new class attribute every time a
       name is accessed that does not exist and then resolve those forward
       declarations at the end of the class body.
    """
