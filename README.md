# Parsita
The executable grammar of parsers combinators made available in the executable pseudocode of Python.

### Motivation
Parsita is a parser combinator library written in Python. Parser combinators provide an easy way to define a grammar using code so that the grammar itself effectively parses the source. They are not the fastest to parse, but they are the easiest to write. The science of parser combinators is best left to [others](http://www.codecommit.com/blog/scala/the-magic-behind-parser-combinators), so I will demonstrate only the syntax of Parsita.

Like all good parser combinator libraries, this one abuses operators to provide a clean grammar-like syntax. The `__or__` method is defined so that `|` tests between two alternatives. The `__and__` method is defined so that `&` tests two parsers in sequence. Other operators are used as well.

In a techinque that I think is new to Python, Parsita uses metaclass magic to allow for forward declarations of values. This is important for parser combinators because grammars are often recursive or mutually recursive, means that some components must be used in the definition of others before they themselves are defined.

#### Motivating example
Below is a complete parser of [JSON](https://tools.ietf.org/html/rfc7159). It could have be shorter if I chose to cheat with Python's `eval`, but I wanted to show the full power of Parsita:

```Python
from parsita import *

json_whitespace = r'[ \t\n\r]*'

class JsonStringParsers(TextParsers, whitespace=None):
    quote = lit(r'\"') > (lambda _: '"')
    reverse_solidus = lit(r'\\') > (lambda _: '\\')
    solidus = lit(r'\/') > (lambda _: '/')
    backspace = lit(r'\b') > (lambda _: '\b')
    form_feed = lit(r'\f') > (lambda _: '\f')
    line_feed = lit(r'\n') > (lambda _: '\n')
    carriage_return = lit(r'\r') > (lambda _: '\r')
    tab = lit(r'\t') > (lambda _: '\t')
    uni = reg(r'\\u([0-9a-fA-F]{4})') > (lambda x: chr(int(x.group(1), 16)))

    escaped = (quote | reverse_solidus | solidus | backspace | form_feed
               | line_feed | carriage_return | tab | uni)
    unescaped = reg(r'[\u0020-\u0021\u0023-\u005B\u005D-\U0010FFFF]+')

    string = '"' >> rep(escaped | unescaped) << '"' > ''.join


class JsonParsers(TextParsers, whitespace=json_whitespace):
    number = reg(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?')

    false = lit('false') > (lambda _: False)
    true = lit('true') > (lambda _: True)
    null = lit('null') > (lambda _: None)

    string = json_whitespace >> JsonStringParsers.string

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
        '{"__class__" : "Rectangle", "location" : {"x":-1.3,"y":-4.5}, "height" : 2.0, "width" : 4.0}'
    ]

    for string in strings:
        print('source: {}\nvalue: {}'.format(string, JsonParsers.value.parse(string)))
```

## Tutorial
There is a lot of generic parsing machinary under the hood. Parser combinators have a rich science behind them. If you know all about that and want to do advanced parsing, by all means pop open the source hood and install some nitro. However, most users will want the basic interface, which is described below.

```Python
from parsita import *
```

### Metaclass magic

`GeneralParsers` and `TextParsers` are two classes that are imported that are just wrappers around a couple of metaclasses. They are not meant to be instatiated. They are meant to be inherited from and their class bodies used to define a grammar. I am going to call these classes "contexts" to reflect their intended usage.

```Python
class MyParsers(TextParsers):
    ...
```

If you are parsing strings (and you almost certainly are), use `TextParser` not the other one. If you know what it means to parse things other than strings, you probably don't need this tutorial anyway. The `TextParser` ignores whitespace. By default it considers `r"\s*"` to be whitespace, but this can be configured using the `whitespace` keyword. Use `None` to disable whitespace skipping.

```Python
class MyParsers(TextParsers, whitespace=r'[ \t]*'):
    # In here, only space and tab are considered whitespace.
    # This can be useful for grammars sensitive to newlines.
    ...
```

### `lit(*literals)`: literal parser
This is the simplest parser. It matches the exact string provided and returns the string as its value. If multiple arguments are provided, it tries each one in succession, returning the first one it finds.

```Python
class HelloParsers(TextParsers):
    hello = lit('Hello World!')
assert HelloParsers.hello.parse('Hello World!') == Success('Hello World!')
assert HelloParsers.hello.parse('Goodbye') == Failure("Hello World! expected but Goodbye found")
```

In most cases, the call to `lit` is handled automatically. If a bare string is provided to the functions and operators below, it will be promoted to literal parser whenever possible. Only when an operator is between two Python types, like a string and a string `'a' | 'b'` or a string and function `'100' > int` will this "implicit conversion" not take place and you have to use `lit` (e.g. `lit('a', 'b')` and `lit('100') > int`).

### `reg(pattern)`: regular expression parser
Like `lit`, this matches a string and returns it, but the matching is done with a [regular expression](https://docs.python.org/3/library/re.html).

```Python
class IntegerParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+')
assert IntegerParsers.integer.parse('-128') == Success('-128')
```

### `parser > function`: conversion parser
Conversion parsers don't change how the text is parsed�they change the value returned. Every parser returns a value when it succeeds. The function supplied must take a single argument (that value) and returns a new value. This is how text is converted to other objects and simpler objects built into larger ones. In accordance with Python's operator precedence, `>` is the operator in Parsita with the loosest binding.

```Python
class IntegerParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
assert IntegerParsers.integer.parse(-128) == Success(-128)
```

### `parser1 | parser2`: alternative parser
This tries to match `parser1`. If it fails, it then tries to match `parser2`. If both fail, it returns the failure message from whichever one got farther. Either side can be a bare string, not both because `'a' | 'b'` tries to call `__or__` on `str` which fails. To try alternative literals, use `lit` with multiple arguments.

```Python
class NumberParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    real = reg(r'[+-]?\d+\.\d+(e[+-]?\d+)?') | 'nan' | 'inf' > float
    number = integer | real
assert NumberParsers.number.parse('4.0000') == Success(4.0)
```

### `parser1 & parser2`: sequential parser
All the parsers above will match at most one thing. This is the syntax for matching one parser and then another after it. If working in the `TextParsers` context, the two may be seperated by whitespace. The value returned is a list of all the values returned by each parser. If there are multiple parsers seperated by `&`, a list of the same length as the number of parsers is returned. Like `|`, either side may be a bare string, but not both. In accordance with Python's operator precedence, `&` binds more tightly than `|`.

```Python
class UrlParsers(TextParsers, whitespace=None):
    url = lit('http', 'ftp') & '://' & reg(r'[^/]+') & reg(r'.*')
assert UrlParsers.url.parse('http://drhagen.com/blog/sane-equality/') == \
    Success(['http', '://', 'drhagen.com', '/blog/sane_equality/'])
```

### `parser1 >> parser2` and `parser1 << parser2`: discard left and right parsers
The discard left and discard right parser match the exact same text as `parser1 & parser2`, but rather than return a list of values from both, the left value in `>>` and the right value in `<<` is discarded so that only the remaining value is returned. A memonic to help remember which is which is to imagine the symbols as open mouths eating the parser to be discarded.

```Python
class PointParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    point = '(' >> integer << ',' & integer << ')'
assert PointParsers.point.parse('(4, 3)') == Success([4, 3])
```

In accordance with Python's operator precedence, these bind more tightly than any other operators including `&` or `|`, meaning that `<<` and `>>` discard only the immediate parser.

* Incorrect: `entry = key << ':' >> value`
* Correct: `entry = key << ':' & value`
* Also correct: `entry = key & ':' >> value`
* Incorrect: `hostname = lit('http', 'ftp') & '://' >> reg(r'[^/]+') << reg(r'.*')`
* Correct: `hostname = lit('http', 'ftp') >> '://' >> reg(r'[^/]+') << reg(r'.*')`
* Better: `hostname = (lit('http', 'ftp') & '://') >> reg(r'[^/]+') << reg(r'.*')`

### `opt(parser)`: optional parser
An optional parser tries to match its argument. If the argument succeeds, it returns a list of length one with the successful value as its only element. If the argument fails, then `opt` succeeds anyway, but returns an empty list and consuming no input.

```Python
class DeclarationParsers(TextParsers):
    id = reg(r'[A-Za-z_][A-Za-z0-9_]+')
    declaration = id & opt(':' >> id)
assert DeclarationParsers.declaration.parse('x: int') == Success(['x', ['int']])
```

### `rep(parser)` and `rep1(parser)`: repeated parsers
A repeated parser matches repeated instances of its parser argument. It returns a list with each element being the value of one match. `rep1` only succeeds if at least one match is found. `rep` always succeeds, returning an empty list if no matches are found.

```Python
class SummationParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    summation = integer & rep('+' >> integer) > lambda x: sum([x[0]] + x[1])
assert SummationParsers.summation.parse('1 + 1 + 2 + 3 + 5') == Success(12)
```

### `repsep(parser, separator)` and `rep1sep(parser, separator)`: repeated separated parsers
A repeated separated parser matches `parser` seperated by `separator`, returning a list of the values returned by `parser` and discarding the value of `separator`. `rep1sep` only succeeds if at least one match is found. `repsep` always succeeds, returning an empty list if no matches are found.

```Python
class ListParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    my_list = '[' >> repsep(integer, ',') << ']'
assert ListParsers.my_list.parse('[1,2,3]') == [1, 2, 3]
```
