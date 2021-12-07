# Repeated parsers

## `rep(parser, min=0, max=inf)` and `rep1(parser)`: repeated parsers
A repeated parser matches repeated instances of its parser argument. It returns a list with each element being the value of one match. `rep` only succeeds if it matches at least `min` times and will only consume up to `max` matches. `rep1` is syntactic sugar for `min=1`. If `min=0`, then `rep` always succeeds, returning an empty list if no matches are found.

```python
from parsita import *

class SummationParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    summation = integer & rep('+' >> integer) > (lambda x: sum([x[0]] + x[1]))

assert SummationParsers.summation.parse('1 + 1 + 2 + 3 + 5') == Success(12)
```

## `repsep(parser, separator, min=0, max=inf)` and `rep1sep(parser, separator)`: repeated separated parsers
A repeated separated parser matches parser separated by separator, returning a list of the values returned by parser and discarding the value of separator. `repsep` only succeeds if it matches at least `min` times and will only consume up to `max` matches. `rep1sep` is syntactic sugar for `min=1`. If `min=0`, then `repsep` always succeeds, returning an empty list if no matches are found.

```python
from parsita import *

class ListParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    my_list = '[' >> repsep(integer, ',') << ']'

assert ListParsers.my_list.parse('[1,2,3]') == Success([1, 2, 3])
```
