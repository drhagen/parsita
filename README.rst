Parsita
=======

.. image:: https://travis-ci.org/drhagen/parsita.svg
   :target: https://travis-ci.org/drhagen/parsita
.. image:: https://codecov.io/github/drhagen/parsita/coverage.svg
   :target: https://codecov.io/github/drhagen/parsita
.. image:: https://img.shields.io/pypi/v/parsita.svg
   :target: https://pypi.python.org/pypi/parsita
.. image:: https://img.shields.io/pypi/pyversions/parsita.svg
   :target: https://pypi.python.org/pypi/parsita

The executable grammar of parsers combinators made available in the executable pseudocode of Python.

Motivation
----------

Parsita is a parser combinator library written in Python. Parser combinators provide an easy way to define a grammar using code so that the grammar itself effectively parses the source. They are not the fastest to parse, but they are the easiest to write. The science of parser combinators is best left to `others <http://www.codecommit.com/blog/scala/the-magic-behind-parser-combinators>`__, so I will demonstrate only the syntax of Parsita.

Like all good parser combinator libraries, this one abuses operators to provide a clean grammar-like syntax. The ``__or__`` method is defined so that ``|`` tests between two alternatives. The ``__and__`` method is defined so that ``&`` tests two parsers in sequence. Other operators are used as well.

In a technique that I think is new to Python, Parsita uses metaclass magic to allow for forward declarations of values. This is important for parser combinators because grammars are often recursive or mutually recursive, meaning that some components must be used in the definition of others before they themselves are defined.

Motivating example
^^^^^^^^^^^^^^^^^^

Below is a complete parser of `JSON <https://tools.ietf.org/html/rfc7159>`__. It could have be shorter if I chose to cheat with Python's ``eval``, but I wanted to show the full power of Parsita:

.. code:: python

    from parsita import *
    from parsita.util import constant

    class JsonStringParsers(TextParsers, whitespace=None):
        quote = lit(r'\"') > constant('"')
        reverse_solidus = lit(r'\\') > constant('\\')
        solidus = lit(r'\/') > constant('/')
        backspace = lit(r'\b') > constant('\b')
        form_feed = lit(r'\f') > constant('\f')
        line_feed = lit(r'\n') > constant('\n')
        carriage_return = lit(r'\r') > constant('\r')
        tab = lit(r'\t') > constant('\t')
        uni = reg(r'\\u([0-9a-fA-F]{4})') > (lambda x: chr(int(x.group(1), 16)))

        escaped = (quote | reverse_solidus | solidus | backspace | form_feed
                  | line_feed | carriage_return | tab | uni)
        unescaped = reg(r'[\u0020-\u0021\u0023-\u005B\u005D-\U0010FFFF]+')

        string = '"' >> rep(escaped | unescaped) << '"' > ''.join


    class JsonParsers(TextParsers, whitespace=r'[ \t\n\r]*'):
        number = reg(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?') > float

        false = lit('false') > constant(False)
        true = lit('true') > constant(True)
        null = lit('null') > constant(None)

        string = JsonStringParsers.string

        array = '[' >> repsep(value, ',') << ']'

        entry = string << ':' & value
        obj = '{' >> repsep(entry, ',') << '}' > dict

        value = number | false | true | null | string | array | obj

    if __name__ == '__main__':
        strings = [
            '"name"',
            '-12.40e2',
            '[false, true, null]',
            '{"__class__" : "Point", "x" : 2.3, "y" : -1.6}',
            '{"__class__" : "Rectangle", "location" : {"x":-1.3,"y":-4.5}, "height" : 2.0, "width" : 4.0}',
        ]

        for string in strings:
            print('source: {}\nvalue: {}'.format(string, JsonParsers.value.parse(string)))

Tutorial
--------

The recommended means of installation is with ``pip`` from PyPI.

.. code:: bash

    pip install parsita

There is a lot of generic parsing machinery under the hood. Parser combinators have a rich science behind them. If you know all about that and want to do advanced parsing, by all means pop open the source hood and install some nitro. However, most users will want the basic interface, which is described below.

.. code:: python

    from parsita import *

Metaclass magic
^^^^^^^^^^^^^^^

``GeneralParsers`` and ``TextParsers`` are two classes that are imported that are just wrappers around a couple of metaclasses. They are not meant to be instantiated. They are meant to be inherited from and their class bodies used to define a grammar. I am going to call these classes "contexts" to reflect their intended usage.

.. code:: python

    class MyParsers(TextParsers):
        ...

If you are parsing strings (and you almost certainly are), use ``TextParsers`` not the other one. If you know what it means to parse things other than strings, you probably don't need this tutorial anyway. ``TextParsers`` ignores whitespace. By default it considers ``r"\s*"`` to be whitespace, but this can be configured using the ``whitespace`` keyword. Use ``None`` to disable whitespace skipping.

.. code:: python

    class MyParsers(TextParsers, whitespace=r'[ \t]*'):
        # In here, only space and tab are considered whitespace.
        # This can be useful for grammars sensitive to newlines.
        ...

``lit(*literals)``: literal parser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the simplest parser. It matches the exact string provided and returns the string as its value. If multiple arguments are provided, it tries each one in succession, returning the first one it finds.

.. code:: python

    class HelloParsers(TextParsers):
        hello = lit('Hello World!')
    assert HelloParsers.hello.parse('Hello World!') == Success('Hello World!')
    assert isinstance(HelloParsers.hello.parse('Goodbye'), Failure)

In most cases, the call to ``lit`` is handled automatically. If a bare string is provided to the functions and operators below, it will be promoted to literal parser whenever possible. Only when an operator is between two Python types, like a string and a string ``'a' | 'b'`` or a string and function ``'100' > int`` will this "implicit conversion" not take place and you have to use ``lit`` (e.g. ``lit('a', 'b')`` and ``lit('100') > int``).

``reg(pattern)``: regular expression parser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Like ``lit``, this matches a string and returns it, but the matching is done with a `regular expression <https://docs.python.org/3/library/re.html>`__.

.. code:: python

    class IntegerParsers(TextParsers):
        integer = reg(r'[-+]?[0-9]+')
    assert IntegerParsers.integer.parse('-128') == Success('-128')

``parser > function``: conversion parser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Conversion parsers don't change how the text is parsed—they change the value returned. Every parser returns a value when it succeeds. The function supplied must take a single argument (that value) and returns a new value. This is how text is converted to other objects and simpler objects built into larger ones. In accordance with Python's operator precedence, ``>`` is the operator in Parsita with the loosest binding.

.. code:: python

    class IntegerParsers(TextParsers):
        integer = reg(r'[-+]?[0-9]+') > int
    assert IntegerParsers.integer.parse('-128') == Success(-128)

``parser1 | parser2``: alternative parser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This tries to match ``parser1``. If it fails, it then tries to match ``parser2``. If both fail, it returns the failure message from whichever one got farther. Either side can be a bare string, not both because ``'a' | 'b'`` tries to call ``__or__`` on ``str`` which fails. To try alternative literals, use ``lit`` with multiple arguments.

.. code:: python

    class NumberParsers(TextParsers):
        integer = reg(r'[-+]?[0-9]+') > int
        real = reg(r'[+-]?\d+\.\d+(e[+-]?\d+)?') | 'nan' | 'inf' > float
        number = real | integer
    assert NumberParsers.number.parse('4.0000') == Success(4.0)

``parser1 & parser2``: sequential parser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All the parsers above will match at most one thing. This is the syntax for matching one parser and then another after it. If working in the ``TextParsers`` context, the two may be separated by whitespace. The value returned is a list of all the values returned by each parser. If there are multiple parsers separated by ``&``, a list of the same length as the number of parsers is returned. Like ``|``, either side may be a bare string, but not both. In accordance with Python's operator precedence, ``&`` binds more tightly than ``|``.

.. code:: python

    class UrlParsers(TextParsers, whitespace=None):
        url = lit('http', 'ftp') & '://' & reg(r'[^/]+') & reg(r'.*')
    assert UrlParsers.url.parse('http://drhagen.com/blog/sane-equality/') == \
        Success(['http', '://', 'drhagen.com', '/blog/sane-equality/'])

``parser1 >> parser2`` and ``parser1 << parser2``: discard left and right parsers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The discard left and discard right parser match the exact same text as ``parser1 & parser2``, but rather than return a list of values from both, the left value in ``>>`` and the right value in ``<<`` is discarded so that only the remaining value is returned. A mnemonic to help remember which is which is to imagine the symbols as open mouths eating the parser to be discarded.

.. code:: python

    class PointParsers(TextParsers):
        integer = reg(r'[-+]?[0-9]+') > int
        point = '(' >> integer << ',' & integer << ')'
    assert PointParsers.point.parse('(4, 3)') == Success([4, 3])

In accordance with Python's operator precedence, these bind more tightly than any other operators including ``&`` or ``|``, meaning that ``<<`` and ``>>`` discard only the immediate parser.

-  Incorrect: ``entry = key << ':' >> value``
-  Correct: ``entry = key << ':' & value``
-  Also correct: ``entry = key & ':' >> value``
-  Incorrect: ``hostname = lit('http', 'ftp') & '://' >> reg(r'[^/]+') << reg(r'.*')``
-  Correct: ``hostname = lit('http', 'ftp') >> '://' >> reg(r'[^/]+') << reg(r'.*')``
-  Also correct: ``hostname = (lit('http', 'ftp') & '://') >> reg(r'[^/]+') << reg(r'.*')``

``opt(parser)``: optional parser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An optional parser tries to match its argument. If the argument succeeds, it returns a list of length one with the successful value as its only element. If the argument fails, then ``opt`` succeeds anyway, but returns an empty list and consumes no input.

.. code:: python

    class DeclarationParsers(TextParsers):
        id = reg(r'[A-Za-z_][A-Za-z0-9_]*')
        declaration = id & opt(':' >> id)
    assert DeclarationParsers.declaration.parse('x: int') == Success(['x', ['int']])
    assert DeclarationParsers.declaration.parse('x') == Success(['x', []])

``rep(parser)`` and ``rep1(parser)``: repeated parsers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A repeated parser matches repeated instances of its parser argument. It returns a list with each element being the value of one match. ``rep1`` only succeeds if at least one match is found. ``rep`` always succeeds, returning an empty list if no matches are found.

.. code:: python

    class SummationParsers(TextParsers):
        integer = reg(r'[-+]?[0-9]+') > int
        summation = integer & rep('+' >> integer) > (lambda x: sum([x[0]] + x[1]))
    assert SummationParsers.summation.parse('1 + 1 + 2 + 3 + 5') == Success(12)

``repsep(parser, separator)`` and ``rep1sep(parser, separator)``: repeated separated parsers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A repeated separated parser matches ``parser`` separated by ``separator``, returning a list of the values returned by ``parser`` and discarding the value of ``separator``. ``rep1sep`` only succeeds if at least one match is found. ``repsep`` always succeeds, returning an empty list if no matches are found.

.. code:: python

    class ListParsers(TextParsers):
        integer = reg(r'[-+]?[0-9]+') > int
        my_list = '[' >> repsep(integer, ',') << ']'
    assert ListParsers.my_list.parse('[1,2,3]') == Success([1, 2, 3])

``pred(parser, predicate, description)``: predicate parser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A predicate parser matches ``parser`` and, if it succeeds, runs a test function ``predicate`` on the return value. If ``predicate`` returns ``True``, the predicate parser succeeds, returning the same value; if it returns ``False``, the parser fails with the message that it is expecting ``description``.

.. code:: python

    class IntervalParsers(TextParsers):
        number = reg('\d+') > int
        pair = '[' >> number << ',' & number << ']'
        interval = pred(pair, lambda x: x[0] <= x[1], 'ordered pair')
    assert IntervalParsers.interval.parse('[1, 2]') == Success([1, 2])
    assert IntervalParsers.interval.parse('[2, 1]') != Success([2, 1])

``any1``: any one element
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A parser that matches any single input element. This is not a particularly useful parser in the context of parsing text (for which ``reg(r'.')`` would be more standard). But in the ``GeneralParsers`` context, this is useful as the first argument to ``pred`` when one merely wants to run the predicate on a single token. This parser can only fail at the end of the stream. Note that ``any1`` is not a function—it is a complete parser itself.

.. code:: python

    class DigitParsers(GeneralParsers):
        digit = pred(any1, lambda x: x['type'] == 'digit', 'a digit') > \
            (lambda x: x['payload'])
    assert DigitParsers.digit.parse([{'type': 'digit', 'payload': 3}]) == \
        Success(3)

``eof``: end of file
^^^^^^^^^^^^^^^^^^^^

A parser than matches the end of the input stream. It is not necessary to include this on every parser. The ``parse`` method on every parser is successful if it matches the entire input. The ``eof`` parser is only needed to indicate that the preceding parser is only valid at the end of the input. Most commonly, it is used an alternative to an end token when the end token may be omitted at the end of the input. Note that ``eof`` is not a function—it is a complete parser itself.

.. code:: python

    class OptionsParsers(TextParsers):
        option = reg(r'[A-Za-z]+') << '=' & reg(r'[A-Za-z]+') << (';' | eof)
        options = rep(option)
    assert OptionsParsers.options.parse('log=warn;detail=minimal;') == \
        Success([['log', 'warn'], ['detail', 'minimal']])
    assert OptionsParsers.options.parse('log=warn;detail=minimal') == \
        Success([['log', 'warn'], ['detail', 'minimal']])

``fwd()``: forward declaration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This creates a forward declaration for a parser to be defined later. This function is not typically needed because forward declarations are created automatically within the class bodies of subclasses of ``TextParsers`` and ``GeneralParsers``, which is the recommended way to use Parsita. This function exists so you can create a forward declaration manually because you are either working outside of the magic classes or wish to define them manually to make your IDE happier.

To use ``fwd``, first assign ``fwd()`` to a variable, then use that variable in other combinators like any other parser, then call the ``define(parser: Parser)`` method on the object to provide the forward declaration with its definition. The forward declaration will now look and act like the definition provided.

.. code:: python

    class AddingParsers(TextParsers):
        number = reg(r'[+-]?\d+') > int
        expr = fwd()
        base = '(' >> expr << ')' | number
        expr.define(rep1sep(base, '+') > sum)
    assert AddingParsers.expr.parse('2+(1+2)+3') == Success(8)

``success(value)``: always succeed with value
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This parser always succeeds with the given ``value`` of an arbitrary type while consuming no input. Its utility is limited to inserting arbitrary values into complex parsers, often as a placeholder for unimplemented code. Usually, these kinds of values are better inserted as a post processing step or with a conversion parser ``>``, but for prototyping, this parser can be convenient.

.. code:: python

    class HostnameParsers(TextParsers, whitespace=None):
        port = success(80)  # TODO: do not just ignore other ports
        host = rep1sep(reg('[A-Za-z0-9]+([-]+[A-Za-z0-9]+)*'), '.')
        server = host & port
    assert HostnameParsers.server.parse('drhagen.com') == Success([['drhagen', 'com'], 80])

``failure(expected)``: always fail with message
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This parser always fails with a message that it is expecting the given string ``expected``. Its utility is limited to marking sections of code as either not yet implemented or providing a better error message for common bad input. Usually, these kinds of messages are better crafted as a processing step following parsing, but for prototyping, they can be inserted with this parser.

.. code:: python

    class HostnameParsers(TextParsers, whitespace=None):
        # TODO: implement allowing different port
        port = lit('80') | reg('[0-9]+') & failure('no other port than 80')
        host = rep1sep(reg('[A-Za-z0-9]+([-]+[A-Za-z0-9]+)*'), '.')
        server = host << ':' & port
    assert HostnameParsers.server.parse('drhagen.com:443') == \
        Failure('Expected no other port than 80 but found end of source')

Utilities
^^^^^^^^^

There are several utility functions, ``constant``, ``splat``, and ``unsplat``. They are mostly useful when used with the conversion parser (``>``).

``constant(value)``: create a function that always returns the same value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The function ``constant(value: A) -> Callable[..., A]`` accepts any single value returns a function. The function takes any number of arguments of any types and returns ``value``. It is useful for defining parsers (usually of a particular literal) that evaluate to a particular value.

.. code:: python

    from parsita import *
    from parsita.util import constant

    class BooleanParsers(TextParsers, whitespace=None):
        true = lit('true') > constant(True)
        false = lit('false') > constant(False)
        boolean = true | false
    assert BooleanParsers.boolean.parse('false') == Success(False)

``splat(function)``: convert a function of many arguments to take only one list argument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The function ``splat(function: Callable[Tuple[*B], A]) -> Callable[Tuple[Tuple[*B]], A]`` has a complicated type signature, but does a simple thing. It takes a single function that takes multiple arguments and converts it to a function that takes only one argument, which is a list of all original arguments. It is particularly useful for passing a list of results from a sequential parser ``&`` to a function that takes each element as an separate argument. By applying ``splat`` to the function, it now takes the single list that is returned by the sequential parser.

.. code:: python

    from collections import namedtuple
    from parsita import *
    from parsita.util import splat

    Url = namedtuple('Url', ['host', 'port', 'path'])

    class UrlParsers(TextParsers, whitespace=None):
        host = reg(r'[A-Za-z0-9.]+')
        port = reg(r'[0-9]+') > int
        path = reg(r'[-._~A-Za-z0-9/]*')
        url = 'https://' >> host << ':' & port & path > splat(Url)
    assert UrlParsers.url.parse('https://drhagen.com:443/blog/') == \
        Success(Url('drhagen.com', 443, '/blog/'))

``unsplat(function)``: convert a function of one list argument to take many arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The function ``unsplat(function: Callable[Tuple[Tuple[*B]], A]) -> Callable[Tuple[*B], A]`` does the opposite of ``splat``. It takes a single function that takes a single argument that is a list and converts it to a function that takes multiple arguments, each of which was an element of the original list. It is not very useful for writing parsers because the conversion parser always calls its converter function with a single argument, but is included here to complement ``splat``.

.. code:: python

    from parsita.util import splat, unsplat

    def sum_args(*x):
        return sum(x)

    def sum_list(x):
        return sum(x)

    splatted_sum_args = splat(sum_args)
    unsplatted_sum_list = unsplat(sum_list)

    assert unsplatted_sum_list(2, 3, 5) == sum_args(2, 3, 5)
    assert splatted_sum_args([2, 3, 5]) == sum_list([2, 3, 5])
