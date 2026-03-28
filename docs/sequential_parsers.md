---
icon: material/plus
---

# Sequential parser

## `parser1 & parser2`: sequential parser

All the previous parsers will match at most one thing. This is the syntax for matching one parser and then another after it. If working in a `ParserContext`, the two may be separated by whitespace. The value returned is a list of all the values returned by each parser. If there are multiple parsers separated by `&`, a list of the same length as the number of parsers is returned. Like `|`, either side may be a bare string, but not both. In accordance with Python's operator precedence, `&` binds more tightly than `|`.

```python
from parsita import *

class UrlParsers(ParserContext):
    url = lit('http', 'ftp') & '://' & reg(r'[^/]+') & reg(r'.*')

assert UrlParsers.url.parse('http://drhagen.com/blog/sane-equality/') == \
    Success(['http', '://', 'drhagen.com', '/blog/sane-equality/'])
```

## `seq(*parsers)`: sequential parser

`seq` is the explicit function form of `&`. It takes any number of parsers and matches them in order, returning a list of all their values.

Unlike `&`, `seq` never flattens nested `SequentialParser`s. With `&`, an unprotected `SequentialParser` on the left side is extended, so `(a & b) & c` produces a 3-element list `[a, b, c]`, while `a & (b & c)` produces a 2-element list `[a, [b, c]]`. With `seq`, each argument is always one element of the result, so `seq(a & b, c)` always produces a 2-element list `[[a, b], c]`.

```python
from parsita import *

class CidrParsers(ParserContext):
    octet = reg(r'\d{1,3}') > int
    ip = seq(octet << '.', octet << '.', octet << '.', octet)
    prefix = reg(r'\d{1,2}') > int
    cidr = seq(ip << '/', prefix)

assert CidrParsers.cidr.parse('192.168.1.0/24') == Success([[192, 168, 1, 0], 24])
```

## `parser1 >> parser2` and `parser1 << parser2`: discard left and right parsers

The discard left and discard right parser match the exact same text as `parser1 & parser2`, but rather than return a list of values from both, the left value in `>>` and the right value in `<<` is discarded so that only the remaining value is returned. A mnemonic to help remember which is which is to imagine the symbols as open mouths eating the parser to be discarded.

```python
from parsita import *

class PointParsers(ParserContext, whitespace=r'[ ]*'):
    integer = reg(r'[-+]?[0-9]+') > int
    point = '(' >> integer << ',' & integer << ')'

assert PointParsers.point.parse('(4, 3)') == Success([4, 3])
```
