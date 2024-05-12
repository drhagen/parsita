---
icon: material/text-recognition
---

# Terminal parsers

Terminal parsers (those created by `lit` and `reg`) are the atoms of a parser, they match and extract the smallest meaningful words of the language.

You could say that they recognize the tokens of the language being parsed, but Parsita does not really have a concept of tokens, at least when `str` is the input type. Terminal parsers chew directly on the input string.

## `lit(*literals)`: literal parser

This is the simplest parser. It matches the exact string provided and returns the string as its value. If multiple arguments are provided, it tries each one in succession, returning the first one it finds.

```python
from parsita import *

class HelloParsers(ParserContext):
    hello = lit('Hello World!')

assert HelloParsers.hello.parse('Hello World!') == Success('Hello World!')
assert isinstance(HelloParsers.hello.parse('Goodbye'), Failure)
```

In most cases, the call to `lit` is handled automatically. If a bare string is provided to the functions and operators of Parsita, it will be promoted to a literal parser whenever possible. Only when an operator is between two Python types, like a string and a string `'a' | 'b'` or a string and function `'100' > int` will this "implicit conversion" not take place and you have to use `lit` (e.g. `lit('a', 'b')` and `lit('100') > int`).

## `reg(pattern)`: regular expression parser

Like `lit`, this matches a string and returns it, but the matching is done with a regular expression.

```python
from parsita import *

class IntegerParsers(ParserContext):
    integer = reg(r'[-+]?[0-9]+')

assert IntegerParsers.integer.parse('-128') == Success('-128')
```
