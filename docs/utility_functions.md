# Utility functions

There are several utility functions, `constant`, `splat`, and `unsplat`. They are mostly useful when used with the conversion parser (`>`). These utility functions are not exported by `from parsita import *` and must be imported from `parsita.util`.

## `constant(value)`: create a function that always returns the same value

The function `constant(value: A) -> Callable[..., A]` accepts any single value and returns a function. The function takes any number of arguments of any types and returns `value`. It is useful for defining parsers (usually of a particular literal) that evaluate to a particular value.

```python
from parsita import *
from parsita.util import constant

class BooleanParsers(ParserContext):
    true = lit('true') > constant(True)
    false = lit('false') > constant(False)
    boolean = true | false

assert BooleanParsers.boolean.parse('false') == Success(False)
```

## `splat(function)`: convert a function of many arguments to take only one list argument

The function `splat(function: Callable[Tuple[*B], A]) -> Callable[Tuple[Tuple[*B]], A]` has a complicated type signature, but does a simple thing. It takes a single function that takes multiple arguments and converts it to a function that takes only one argument, which is a list of all original arguments. It is particularly useful for passing a list of results from a sequential parser `&` to a function that takes each element as an separate argument. By applying `splat` to the function, it now takes the single list that is returned by the sequential parser.

```python
from collections import namedtuple
from parsita import *
from parsita.util import splat

Url = namedtuple('Url', ['host', 'port', 'path'])

class UrlParsers(ParserContext):
    host = reg(r'[A-Za-z0-9.]+')
    port = reg(r'[0-9]+') > int
    path = reg(r'[-._~A-Za-z0-9/]*')
    url = 'https://' >> host << ':' & port & path > splat(Url)
assert UrlParsers.url.parse('https://drhagen.com:443/blog/') == \
    Success(Url('drhagen.com', 443, '/blog/'))
```

## `unsplat(function)`: convert a function of one list argument to take many arguments

The function `unsplat(function: Callable[Tuple[Tuple[*B]], A]) -> Callable[Tuple[*B], A]` does the opposite of `splat`. It takes a single function that takes a single argument that is a list and converts it to a function that takes multiple arguments, each of which was an element of the original list. It is not very useful for writing parsers because the conversion parser always calls its converter function with a single argument, but is included here to complement `splat`.

```python
from parsita.util import splat, unsplat

def sum_args(*x):
    return sum(x)

def sum_list(x):
    return sum(x)

splatted_sum_args = splat(sum_args)
unsplatted_sum_list = unsplat(sum_list)

assert unsplatted_sum_list(2, 3, 5) == sum_args(2, 3, 5)
assert splatted_sum_args([2, 3, 5]) == sum_list([2, 3, 5])
```
