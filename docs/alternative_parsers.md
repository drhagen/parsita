# Alternative parsers

## `parser1 | parser2`: alternative parser

This tries to match `parser1`. If it fails, it then tries to match `parser2`. If both fail, it returns the failure message from whichever one got farther. Either side can be a bare string, not both because `'a' | 'b'` tries to call `__or__` on `str` which fails. To try alternative literals, use `lit` with multiple arguments.

```python
from parsita import *

class NumberParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    real = reg(r'[+-]?\d+\.\d+(e[+-]?\d+)?') | 'nan' | 'inf' > float
    number = real | integer

assert NumberParsers.number.parse('4.0000') == Success(4.0)
```

## `opt(parser)`: optional parser
An optional parser tries to match its argument. If the argument succeeds, it returns a list of length one with the successful value as its only element. If the argument fails, then `opt` succeeds anyway, but returns an empty list and consumes no input.

```python
from parsita import *

class DeclarationParsers(TextParsers):
    id = reg(r'[A-Za-z_][A-Za-z0-9_]*')
    declaration = id & opt(':' >> id)

assert DeclarationParsers.declaration.parse('x: int') == Success(['x', ['int']])
assert DeclarationParsers.declaration.parse('x') == Success(['x', []])
```
