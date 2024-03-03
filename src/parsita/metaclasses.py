__all__ = ["ForwardDeclaration", "fwd", "ParserContext"]

import builtins
import inspect
import re
from re import Pattern
from typing import Any, Union

from . import options
from .parsers import LiteralParser, Parser, RegexParser
from .state import Input

missing = object()


class ParsersDict(dict):
    def __init__(self, old_options: dict):
        super().__init__()
        self.old_options = old_options  # Holds state of options at start of definition
        self.forward_declarations = {}  # Stores forward declarations as they are discovered

    def __missing__(self, key):
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

    def __setitem__(self, key, value):
        if isinstance(value, Parser):
            # Protects against accidental concatenation of sequential parsers
            value.protected = True

            # Used for better error messages
            value.name = key

        super().__setitem__(key, value)


class ForwardDeclaration(Parser):
    def __init__(self):
        self._definition = None

    def __getattribute__(self, member):
        if member != "_definition" and self._definition is not None:
            return getattr(self._definition, member)
        else:
            return object.__getattribute__(self, member)

    def define(self, parser: Parser) -> None:
        self._definition = parser


def fwd() -> ForwardDeclaration:
    """Manually create a forward declaration.

    Normally, forward declarations are created automatically by the contexts.
    But they can be created manually if not in a context or if the user wants
    to avoid confusing the IDE.
    """
    return ForwardDeclaration()


class ParserContextMeta(type):
    default_whitespace: Union[Parser[Input, Any], Pattern, str, None] = None

    @classmethod
    def __prepare__(
        mcs,  # noqa: N804
        name,
        bases,
        *,
        whitespace: Union[Parser[Input, Any], Pattern, str, None] = missing,
    ):
        if whitespace is missing:
            whitespace = mcs.default_whitespace

        if isinstance(whitespace, (str, bytes)):
            whitespace = re.compile(whitespace)

        if isinstance(whitespace, Pattern):
            whitespace = RegexParser(whitespace)

        old_options = {
            "whitespace": options.whitespace,
        }

        # Store whitespace in global location
        options.whitespace = whitespace
        return ParsersDict(old_options)

    def __init__(cls, name, bases, dct, **_):
        old_options = dct.old_options

        super().__init__(name, bases, dct)

        # Resolve forward declarations, will raise if name not found
        for name, forward_declaration in dct.forward_declarations.items():
            obj = dct[name]
            if not isinstance(obj, Parser):
                obj = LiteralParser(obj, options.whitespace)
            forward_declaration._definition = obj

        # Reset global variables
        for key, value in old_options.items():
            setattr(options, key, value)

    def __new__(mcs, name, bases, dct, **_):  # noqa: N804
        return super().__new__(mcs, name, bases, dct)

    def __call__(cls, *args, **kwargs):
        raise TypeError(
            "Parsers cannot be instantiated. They use class bodies purely as contexts for "
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
