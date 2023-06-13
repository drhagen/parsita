# Miscellaneous parsers

## `pred(parser, predicate, description)`: predicate parser

A predicate parser matches `parser` and, if it succeeds, runs a test function `predicate` on the return value. If `predicate` returns `True`, the predicate parser succeeds, returning the same value; if it returns `False`, the parser fails with the message that it is expecting `description`.

```python
from parsita import *

class IntervalParsers(ParserContext, whitespace=r'[ ]*'):
    number = reg('\d+') > int
    pair = '[' >> number << ',' & number << ']'
    interval = pred(pair, lambda x: x[0] <= x[1], 'ordered pair')

assert IntervalParsers.interval.parse('[1, 2]') == Success([1, 2])
assert IntervalParsers.interval.parse('[2, 1]') != Success([2, 1])
```

## `until(parser):`: consume until parser matches

A parser that consumes input until the member parser succeeds. The input matched by the member parser is not consumed. It acts kind of like lookahead. The returned value is all consumed input.

The user should be warned that this parser is kind of slow, especially when applied directly to text. This is because, when the member parser fails, it tries again at the next character and the next character until it succeeds. Walking one character at a time can be computationally expensive.

One of the obvious uses of the `until` parser is combining it with the transformation parser in order to implement heredocs.

```python
from parsita import *

class TestParser(ParserContext, whitespace=r'\s*'):
    heredoc = reg("[A-Za-z]+") >= (lambda token: until(token) << token)

content = "EOF\nAnything at all\nEOF"
assert TestParser.heredoc.parse(content) == Success("Anything at all\n")
```

## `any1`: any one element

A parser that matches any single input element. This is not a particularly useful parser when parsing text (for which `reg(r'.')` would be more standard). But when parsing other types of input, this is useful as the first argument to `pred` when one merely wants to run the predicate on a single token. This parser can only fail at the end of the stream. Note that `any1` is not a function—it is a complete parser itself.

```python
from parsita import *

class DigitParsers(ParserContext):
    digit = pred(any1, lambda x: x['type'] == 'digit', 'a digit') > \
        (lambda x: x['payload'])

assert DigitParsers.digit.parse([{'type': 'digit', 'payload': 3}]) == \
    Success(3)
```

## `eof`: end of file

A parser than matches the end of the input stream. It is not necessary to include this on every parser. The `parse` method on every parser is successful only if it matches the entire input. The `eof` parser is only needed to indicate that the preceding parser is only valid at the end of the input. Most commonly, it is used an alternative to an end token when the end token may be omitted at the end of the input. Note that `eof` is not a function—it is a complete parser itself.

```python
from parsita import *

class OptionsParsers(ParserContext):
    option = reg(r'[A-Za-z]+') << '=' & reg(r'[A-Za-z]+') << (';' | eof)
    options = rep(option)

assert OptionsParsers.options.parse('log=warn;detail=minimal;') == \
    Success([['log', 'warn'], ['detail', 'minimal']])
assert OptionsParsers.options.parse('log=warn;detail=minimal') == \
    Success([['log', 'warn'], ['detail', 'minimal']])
```

## `fwd()`: forward declaration

This creates a forward declaration for a parser to be defined later. This function is not typically needed because forward declarations are created automatically within the class bodies of subclasses of `ParserContext`, which is the recommended way to use Parsita. This function exists so you can create a forward declaration manually because you are either working outside of the magic classes or wish to define them manually to make your IDE happier.

To use `fwd`, first assign `fwd()` to a variable, then use that variable in other combinators like any other parser, then call the `define(parser: Parser)` method on the object to provide the forward declaration with its definition. The forward declaration will now look and act like the definition provided.

```python
from parsita import *

class AddingParsers(ParserContext):
    number = reg(r'[+-]?\d+') > int
    expr = fwd()
    base = '(' >> expr << ')' | number
    expr.define(rep1sep(base, '+') > sum)

assert AddingParsers.expr.parse('2+(1+2)+3') == Success(8)
```

## `success(value)`: always succeed with value

This parser always succeeds with the given `value` of an arbitrary type while consuming no input. Its utility is limited to inserting arbitrary values into complex parsers, often as a placeholder for unimplemented code. Usually, these kinds of values are better inserted as a post processing step or with a conversion parser `>`, but for prototyping, this parser can be convenient.

```python
from parsita import *

class HostnameParsers(ParserContext):
    port = success(80)  # TODO: do not just ignore other ports
    host = rep1sep(reg('[A-Za-z0-9]+([-]+[A-Za-z0-9]+)*'), '.')
    server = host & port

assert HostnameParsers.server.parse('drhagen.com') == Success([['drhagen', 'com'], 80])
```

## `failure(expected)`: always fail with message

This parser always fails with a message that it is expecting the given string `expected`. Its utility is limited to marking sections of code as either not yet implemented or providing a better error message for common bad input. Usually, these kinds of messages are better crafted as a postprocessing step following parsing, but for prototyping, they can be inserted with this parser.

```python
from parsita import *

class HostnameParsers(ParserContext):
    # TODO: implement allowing different port
    port = lit('80') | reg('[0-9]+') & failure('no other port than 80')
    host = rep1sep(reg('[A-Za-z0-9]+([-]+[A-Za-z0-9]+)*'), '.')
    server = host << ':' & port

assert str(HostnameParsers.server.parse('drhagen.com:443').failure()) == (
    'Expected no other port than 80 but found end of source'
)
```

## `debug(parser, *, verbose=False, callback=None)`: debug a parser

This parser does not affect input or output in any way. It merely provides a verbose flag and hook to run a callback. The default for the verbose flag is `False` and the default for the callback is `None`, so by default, `debug` does absolutely nothing. If `verbose` is set to `True`, then the input location is printed before the member parser is invoked and the result is printed after the member parser has returned.

The callback has the signature `(parser: Parser[Input, Output], reader: Reader[Input]) -> None` and will be given the member parser and the reader at the current position.

As the name suggests, this is useful only for debugging purposes. The only place one can reliably put a breakpoint in a parser is in the callback of this parser. The conversion parser can be used to place breakpoints, but only after the member parser has run and only on success, making it not very useful for debugging.

```python
from decimal import Decimal

from parsita import *

def temp(parser, reader):
    # Can put a breakpoint here to inspect why the decimal parser is capturing
    # Spoiler: use `\.` instead of `.` in regexes
    pass

class NumberParsers(ParserContext):
    integer = reg(r'[-+]?[0-9]+') > int
    decimal = debug(reg(r'[-+]?[0-9]+.[0-9]+'), callback=temp) > Decimal
    scientific = reg(r'[-+]?[0-9]+e[-+]?[0-9]+') > float
    number = decimal | scientific | integer

# Assertion is broken and needs debugged 
assert isinstance(NumberParsers.number.parse('1e5').unwrap(), float)
```
