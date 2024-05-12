---
icon: material/directions-fork
---

# Alternative parsers

## `parser1 | parser2`: alternative parser

This tries to match `parser1` and `parser2`. If one succeeds and the other fails, it returns the value of the one that succeeded. If both succeed, it returns the value of the one that consumed more input in order to succeed. If both fail, it returns the failure message from whichever one got farther. Either side can be a bare string, but not both because `'a' | 'b'` tries to call `__or__` on `str` which fails. To try alternative literals, use `lit` with multiple arguments.

```python
from parsita import *

class NumberParsers(ParserContext):
    integer = reg(r'[-+]?[0-9]+') > int
    real = reg(r'[+-]?\d+\.\d+(e[+-]?\d+)?') | 'nan' | 'inf' > float
    number = real | integer

assert NumberParsers.number.parse('4.0000') == Success(4.0)
```

`a | b | c` is syntactic sugar for `longest(a, b, c)`. There is similar function `first(a, b, c)` that succeeds with the value of the first option to succeed instead of the one that consumed the most input. In most parsers, the first and longest alternative parsers have the same behavior, especially if the order of the alternatives is carefully considered. In version 1 of Parsita, the `a | b` syntax constructed a `first` parser. This was changed in version 2. If the old behavior of stopping on the first success is important, construct the parser with the `first` function to recover the old behavior.

## `longest(*parsers)`: longest alternative parser

This tries to match each parser supplied. After it has tried them all, it returns the result of the one that made the most progress, that is, consumed the most input. If none of the supplied parsers succeeds, then an error is returned corresponding to the parser that got farthest. If two or more parsers are successful and are tied for making the most progress, the result of the first such parser is returned.

```python
from parsita import *

class ExpressionParsers(ParserContext):
    name = reg(r'[a-zA-Z_]+')
    function = name & '(' >> expression << ')'
    expression = longest(name, function)

assert ExpressionParsers.expression.parse('f(x)') == Success(['f', 'x'])
```

As of version 2 of Parsita, `longest` is the implementation behind the `a | b | c` syntax. It replaced `first`, which was the implementation in version 1.

## `first(*parsers)`: first alternative parser

This tries to match each parser supplied. As soon as one parser succeeds, this returns with that parser's successful value. If later parsers would have succeeded, that is irrelevant because they are not tried. If all supplied parsers fail, this fails with the longest failure.

```python
from parsita import *

class ExpressionParsers(ParserContext):
    keyword = lit('pi', 'nan', 'inf')
    name = reg(r'[a-zA-Z_]+')
    function = name & '(' >> expression << ')'
    expression = first(keyword, function, name)

assert ExpressionParsers.expression.parse('f(x)') == Success(['f', 'x'])
assert str(ExpressionParsers.expression.parse('pi(x)').failure()) == (
    "Expected end of source but found '('\n"
    "Line 1, character 3\n\n"
    "pi(x)\n"
    "  ^  "
)
# Note how the above fails because `keyword` is matched by `first` so that
# `function`, which would have matched the input, was not tried.
```

In version 1 of Parsita, this was the implementation behind the `a | b | c` syntax. As of version 2, `longest` is used instead.

## `opt(parser)`: optional parser

An optional parser tries to match its argument. If the argument succeeds, it returns a list of length one with the successful value as its only element. If the argument fails, then `opt` succeeds anyway, but returns an empty list and consumes no input.

```python
from parsita import *

class DeclarationParsers(ParserContext, whitespace=r'[ ]*'):
    id = reg(r'[A-Za-z_][A-Za-z0-9_]*')
    declaration = id & opt(':' >> id)

assert DeclarationParsers.declaration.parse('x: int') == Success(['x', ['int']])
assert DeclarationParsers.declaration.parse('x') == Success(['x', []])
```
