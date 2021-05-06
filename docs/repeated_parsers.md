# Repeated parsers

## `rep(parser)` and `rep1(parser)`: repeated parsers
A repeated parser matches repeated instances of its parser argument. It returns a list with each element being the value of one match. `rep1` only succeeds if at least one match is found. `rep` always succeeds, returning an empty list if no matches are found.

```python
from parsita import *

class SummationParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    summation = integer & rep('+' >> integer) > (lambda x: sum([x[0]] + x[1]))

assert SummationParsers.summation.parse('1 + 1 + 2 + 3 + 5') == Success(12)
```

## `repsep(parser, separator)` and `rep1sep(parser, separator)`: repeated separated parsers
A repeated separated parser matches parser separated by separator, returning a list of the values returned by parser and discarding the value of separator. `rep1sep` only succeeds if at least one match is found. `repsep` always succeeds, returning an empty list if no matches are found.

```python
from parsita import *

class ListParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int
    my_list = '[' >> repsep(integer, ',') << ']'

assert ListParsers.my_list.parse('[1,2,3]') == Success([1, 2, 3])
```
