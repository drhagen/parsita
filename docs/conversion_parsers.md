# Conversion parsers

## `parser > function`: conversion parser

Conversion parsers don't change how the text is parsed—they change the value returned. Every parser returns a value when it succeeds. The function supplied must take a single argument (the successful value) and returns a new value. This is how text is converted to other objects and simpler objects built into larger ones. In accordance with Python's operator precedence, `>` is the operator in Parsita with the loosest binding.

```python
from parsita import *

class IntegerParsers(ParserContext):
    integer = reg(r'[-+]?[0-9]+') > int

assert IntegerParsers.integer.parse('-128') == Success(-128)
```

## `parser >= function`: transformation parser

Transformation parsers pass the parsed output to a function which returns a new parser. This new parser is then immediately applied to the remaining input. There are two main uses for this parser.

### Fallible conversion

The first use is as a fallible conversion parser. The conversion parser cannot tolerate failure. From the conversion parser's perspective, by the time the parsed output gets to the conversion function, parsing has already succeeded, just the output value is being changed. If the parsing needs to fail, then the transformation parser can be used. The transformer function can return a `SuccessParser` with `success` or a `FailureParser` with `failure` to declare success or failure based on its calculation.

The `TransformationParser` is basically equivalent to a `PredicateParser` followed by a `ConversionParser`. Where you would otherwise write `pred(parser, is_valid_object) > create_object`, you can write `parser >= maybe_create_object`, instead.

```python
from dataclasses import dataclass

from parsita import *

@dataclass
class Percent:
    number: int

def to_percent(number: int) -> Parser[str, Percent]:
    if not 0 <= number <= 100:
        return failure("a number between 0 and 100")
    else:
        return success(Percent(number))

class PercentParsers(ParserContext):
    percent = (reg(r"[0-9]+") > int) >= to_percent

assert PercentParsers.percent.parse('50') == Success(Percent(50))
assert isinstance(PercentParsers.percent.parse('150'), Failure)
```

In the current version of Parsita, the error messages that come from this leave something to be desired. Right now in the core of Parsita, there is no way to separately specify where in the input parsing failed or what the actual token was. The location of the failure is always the farther point that input was consumed and the actual token is always the next token from that point. That means that the error message will always mark the token after what was successfully consumed and passed to `>=` before it was converted into a failure.

### Parsers parameterized by previous input

The second use is to parse later text based on previous text. This is incredibly powerful, but in my experience, not that useful. When viewing parser combinators as a monad, this is the `bind` operation, so functional programming enthusiasts are really into it. It is only included in Parsita because it came free with the fallible conversion parser use case above.

```python
from parsita import *

def select_parser(type: str):
    if type == 'int':
        return reg(r"[0-9]+") > int
    elif type == 'decimal':
        return reg(r"[0-9]+\.[0-9]+") > float

class NumberParsers(ParserContext, whitespace=r'[ ]*'):
    type = lit('int', 'decimal')
    number = type >= select_parser

assert NumberParsers.number.parse('int 5') == Success(5)
assert isinstance(NumberParsers.number.parse('int 2.0'), Failure)
```
