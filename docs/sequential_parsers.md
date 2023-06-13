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

## `parser1 >> parser2` and `parser1 << parser2`: discard left and right parsers

The discard left and discard right parser match the exact same text as `parser1 & parser2`, but rather than return a list of values from both, the left value in `>>` and the right value in `<<` is discarded so that only the remaining value is returned. A mnemonic to help remember which is which is to imagine the symbols as open mouths eating the parser to be discarded.

```python
from parsita import *

class PointParsers(ParserContext, whitespace=r'[ ]*'):
    integer = reg(r'[-+]?[0-9]+') > int
    point = '(' >> integer << ',' & integer << ')'

assert PointParsers.point.parse('(4, 3)') == Success([4, 3])
```
