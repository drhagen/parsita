import inspect
import builtins
import re

from . import options
from .parsers import Parser, RegexParser, wrap_literal, basic_parse


class ParsersDict(dict):
    def __init__(self):
        super().__init__()
        self.forward_declarations = dict()

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
            value.__name__ = key  # Used for better error messages

        super().__setitem__(key, value)


class ForwardDeclaration(Parser):
    def __init__(self):
        self._definition = None

    def __getattribute__(self, member):
        if member != '_definition' and self._definition is not None:
            return getattr(self._definition, member)
        else:
            return object.__getattribute__(self, member)

    def define(self, parser: Parser):
        self._definition = parser


def fwd():
    return ForwardDeclaration()


class ParsersMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases, **_):
        options.handle_literal = wrap_literal
        options.parse_method = basic_parse

        return ParsersDict()

    def __init__(cls, name, bases, dct, **_):
        super().__init__(name, bases, dct)

        # Resolve forward declarations, will raise
        for name, forward_declaration in dct.forward_declarations.items():
            obj = dct[name]
            if not isinstance(obj, Parser):
                obj = options.handle_literal(obj)
            forward_declaration._definition = obj

        # Reset global variables
        options.whitespace = None
        options.handle_literal = options.wrap_literal_with_whitespace
        options.parse_method = options.default_parse()


class Parsers(metaclass=ParsersMeta):
    pass


class RegexParsersMeta(ParsersMeta):
    @classmethod
    def __prepare__(mcs, name, bases, whitespace: str = options.default_whitespace):
        # Store whitespace in global location so regex parsers can see it
        if isinstance(whitespace, str):
            whitespace = re.compile(whitespace)

        if whitespace is None:
            options.whitespace = None
        else:
            options.whitespace = RegexParser(whitespace)

        options.handle_literal = options.wrap_literal_with_whitespace
        options.parse_method = options.default_parse()

        return ParsersDict()

    def __new__(mcs, name, bases, dct, **_):
        return super().__new__(mcs, name, bases, dct)


class RegexParsers(metaclass=RegexParsersMeta):
    pass
