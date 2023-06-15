import builtins
import inspect
import re
import warnings

from . import options
from .parsers import Parser, RegexParser


class ParsersDict(dict):
    def __init__(self, old_options: dict):
        super().__init__()
        self.old_options = old_options  # Holds state of options at start of definition
        self.forward_declarations = {}  # Stores forward declarations as they are discovered

    def __missing__(self, key):
        frame = inspect.currentframe()  # Should be the frame of __missing__
        while frame.f_code.co_name != "__missing__":  # pragma: no cover
            # But sometimes debuggers add frames on top of the stack; get back to `__missing__`'s frame
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
            value.protected = True  # Protects against accidental concatenation of sequential parsers
            value.name = key  # Used for better error messages

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


# The Deprecated package does not work on __init_subclass__
deprecation_text = "{} is deprecated; use ParserContext instead. -- Deprecated since 1.8.0."


class GeneralParsersMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases, **_):  # noqa: N804
        old_options = {
            "handle_literal": options.handle_literal,
            "parse_method": options.parse_method,
        }

        options.handle_literal = options.wrap_literal
        options.parse_method = options.basic_parse

        return ParsersDict(old_options)

    def __init__(cls, name, bases, dct, **_):
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

    def __call__(cls, *args, **kwargs):
        raise TypeError(
            "Parsers cannot be instantiated. They use class bodies purely as contexts for managing defaults and "
            "allowing forward declarations. Access the individual parsers as static attributes."
        )


class GeneralParsers(metaclass=GeneralParsersMeta):
    """Context for parsing general sequences.

    This is not a real class. Don't instantiate it. This is used by inheriting
    from it and defining parsers as class attributes in the body of the child
    class.

    In Parsita 2.0, this context will be removed, use ``ParserContext`` instead.
    """

    def __init_subclass__(cls, **kwargs) -> None:
        warnings.warn(DeprecationWarning(deprecation_text.format("GeneralParsers")), stacklevel=2)
        super().__init_subclass__(**kwargs)


class TextParsersMeta(GeneralParsersMeta):
    @classmethod
    def __prepare__(mcs, name, bases, whitespace: str = options.default_whitespace):  # noqa: N804
        old_options = {
            "whitespace": options.whitespace,
            "handle_literal": options.handle_literal,
            "parse_method": options.parse_method,
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
    r"""Context for parsing text.

    This is not a real class. Don't instantiate it. This is used by inheriting
    from it and defining parsers as class attributes in the body of the child
    class.

    There is a keyword argument for the metaclass ``whitespace``. This is a
    regular expression defining the whitespace to be ignored. The default is
    r"\s*".

    In Parsita 2.0, this context will be removed, use ``ParserContext`` instead.
    """

    def __init_subclass__(cls, **kwargs) -> None:
        warnings.warn(DeprecationWarning(deprecation_text.format("TextParsers")), stacklevel=3)
        super().__init_subclass__(**kwargs)


class ParserContextMeta(TextParsersMeta):
    @classmethod
    def __prepare__(mcs, name, bases, whitespace: str = None):  # noqa: N804
        return super().__prepare__(name, bases, whitespace=whitespace)


class ParserContext(metaclass=ParserContextMeta):
    """Context for parsing.

    This is not a real class. Don't instantiate it. This is used by inheriting
    from it and defining parsers as class attributes in the body of the child
    class.

    There is a keyword argument for the metaclass ``whitespace``. This is a
    regular expression defining the whitespace to be ignored. The default is
    ``None``.

    In Parsita 2.0, this will become the only context.
    """


__all__ = ["ForwardDeclaration", "fwd", "GeneralParsers", "TextParsers", "ParserContext"]
