# Miscellaneous parsers

## `pred(parser, predicate, description)`: predicate parser
A predicate parser matches `parser` and, if it succeeds, runs a test function `predicate` on the return value. If `predicate` returns `True`, the predicate parser succeeds, returning the same value; if it returns `False`, the parser fails with the message that it is expecting `description`.

```python
from parsita import *

class IntervalParsers(TextParsers):
    number = reg('\d+') > int
    pair = '[' >> number << ',' & number << ']'
    interval = pred(pair, lambda x: x[0] <= x[1], 'ordered pair')

assert IntervalParsers.interval.parse('[1, 2]') == Success([1, 2])
assert IntervalParsers.interval.parse('[2, 1]') != Success([2, 1])
```

## `any1`: any one element

A parser that matches any single input element. This is not a particularly useful parser in the context of parsing text (for which `reg(r'.')` would be more standard). But in the `GeneralParsers` context, this is useful as the first argument to `pred` when one merely wants to run the predicate on a single token. This parser can only fail at the end of the stream. Note that `any1` is not a function—it is a complete parser itself.

```python
from parsita import *

class DigitParsers(GeneralParsers):
    digit = pred(any1, lambda x: x['type'] == 'digit', 'a digit') > \
        (lambda x: x['payload'])

assert DigitParsers.digit.parse([{'type': 'digit', 'payload': 3}]) == \
    Success(3)
```

## `eof`: end of file
A parser than matches the end of the input stream. It is not necessary to include this on every parser. The `parse` method on every parser is successful only if it matches the entire input. The `eof` parser is only needed to indicate that the preceding parser is only valid at the end of the input. Most commonly, it is used an alternative to an end token when the end token may be omitted at the end of the input. Note that `eof` is not a function—it is a complete parser itself.

```python
from parsita import *

class OptionsParsers(TextParsers):
    option = reg(r'[A-Za-z]+') << '=' & reg(r'[A-Za-z]+') << (';' | eof)
    options = rep(option)

assert OptionsParsers.options.parse('log=warn;detail=minimal;') == \
    Success([['log', 'warn'], ['detail', 'minimal']])
assert OptionsParsers.options.parse('log=warn;detail=minimal') == \
    Success([['log', 'warn'], ['detail', 'minimal']])
```

## `fwd()`: forward declaration

This creates a forward declaration for a parser to be defined later. This function is not typically needed because forward declarations are created automatically within the class bodies of subclasses of `TextParsers` and `GeneralParsers`, which is the recommended way to use Parsita. This function exists so you can create a forward declaration manually because you are either working outside of the magic classes or wish to define them manually to make your IDE happier.

To use `fwd`, first assign `fwd()` to a variable, then use that variable in other combinators like any other parser, then call the `define(parser: Parser)` method on the object to provide the forward declaration with its definition. The forward declaration will now look and act like the definition provided.

```python
from parsita import *

class AddingParsers(TextParsers):
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

class HostnameParsers(TextParsers, whitespace=None):
    port = success(80)  # TODO: do not just ignore other ports
    host = rep1sep(reg('[A-Za-z0-9]+([-]+[A-Za-z0-9]+)*'), '.')
    server = host & port

assert HostnameParsers.server.parse('drhagen.com') == Success([['drhagen', 'com'], 80])
```

## `failure(expected)`: always fail with message
This parser always fails with a message that it is expecting the given string `expected`. Its utility is limited to marking sections of code as either not yet implemented or providing a better error message for common bad input. Usually, these kinds of messages are better crafted as a processing step following parsing, but for prototyping, they can be inserted with this parser.

```python
from parsita import *

class HostnameParsers(TextParsers, whitespace=None):
    # TODO: implement allowing different port
    port = lit('80') | reg('[0-9]+') & failure('no other port than 80')
    host = rep1sep(reg('[A-Za-z0-9]+([-]+[A-Za-z0-9]+)*'), '.')
    server = host << ':' & port

assert HostnameParsers.server.parse('drhagen.com:443') == \
    Failure('Expected no other port than 80 but found end of source')
```