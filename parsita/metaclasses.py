import inspect
import builtins
import re

from . import options
from .parsers import Parser, RegexParser


class ParsersDict(dict):
    def __init__(self, old_options: dict):
        super().__init__()
        self.old_options = old_options  # Holds state of options at start of definition
        self.forward_declarations = dict()  # Stores forward declarations as they are discovered

    def __missing__(self, key):
        class_body_globals = inspect.currentframe().f_back.f_globals
        if key in class_body_globals:
            return class_body_globals[key]
        elif key in dir(builtins):
            return getattr(builtins, key)
        elif key in self.forward_declarations:
            return self.forward_declarations[key]
        else:
            new_forward_declaration = ForwardDeclaration()
            self.forward_declarations[key] = new_forward_declaration
            return new_forward_declaration

    def __setitem__(self, key, value):
        if isinstance(value, Parser):
            value.protected = True  # Protects against accidental concatenation of sequential parsers
            value.name = key  # Used for better error messages

        super().__setitem__(key, value)


class ForwardDeclaration(Parser):
    def __init__(self):
        self._definition = None

    def __getattribute__(self, member):
        if member != '_definition' and self._definition is not None:
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


class GeneralParsersMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases, **_):  # noqa: N804
        old_options = {
            'handle_literal': options.handle_literal,
            'parse_method': options.parse_method,
        }

        options.handle_literal = options.wrap_literal
        options.parse_method = options.basic_parse

        return ParsersDict(old_options)

    def __init__(cls, name, bases, dct, **_):  # noqa: N805
        old_options = dct.old_options

        super().__init__(name, bases, dct)

        # Resolve forward declarations, will raise if name not found
        for name, forward_declaration in dct.forward_declarations.items():
            obj = dct[name]
            if not isinstance(obj, Parser):
                obj = options.handle_literal(obj)
            forward_declaration._definition = obj

        # Reset global variables
        for key, value in old_options.items():
            setattr(options, key, value)


class GeneralParsers(metaclass=GeneralParsersMeta):
    """Context for parsing general sequences.

    This is not a real class. Don't instantiate it. This is used by inheriting
    from it and defining parsers as class attributes in the body of the child
    class.
    """
    pass


class TextParsersMeta(GeneralParsersMeta):
    @classmethod
    def __prepare__(mcs, name, bases, whitespace: str = options.default_whitespace):  # noqa: N804
        old_options = {
            'whitespace': options.whitespace,
            'handle_literal': options.handle_literal,
            'parse_method': options.parse_method,
        }

        # Store whitespace in global location so regex parsers can see it
        if isinstance(whitespace, str):
            whitespace = re.compile(whitespace)

        if whitespace is None:
            options.whitespace = None
        else:
            options.whitespace = RegexParser(whitespace)

        options.handle_literal = options.default_handle_literal
        options.parse_method = options.default_parse_method

        return ParsersDict(old_options)

    def __new__(mcs, name, bases, dct, **_):  # noqa: N804
        return super().__new__(mcs, name, bases, dct)


class TextParsers(metaclass=TextParsersMeta):
    """Context for parsing text.

    This is not a real class. Don't instantiate it. This is used by inheriting
    from it and defining parsers as class attributes in the body of the child
    class.

    There is a keyword argument for the metaclass ``whitespace``. This is a
    regular expression defining the whitespace to be ignored. The default is
    r"\s*".
    """
    pass


__all__ = ['ForwardDeclaration', 'fwd', 'GeneralParsers', 'TextParsers']
