# Getting started

David Hagen gave an [introductory talk](https://www.youtube.com/watch?v=9JSGGSRgUcw) on Parsita at SciPy 2021. The documentation is more thorough, but the talk is useful for anyone looking for a quick walk-through.

## Defining a parser

Parsita parsers are written inside the bodies of classes that inherit from `TextParsers`. (If you are parsing something other than a string, such a stream of tokens, there is the `GeneralParsers` class.) Such classes are not meant to be instantiated. They are used purely as a kind of souped-up context manager.

The metaclass of `TextParsers` takes a `whitespace` named argument, which is a regular expression, or more commonly, a string that can be parsed into a regular expression. This becomes the definition of whitespace for all `Parser`s defined in this class body, making it so that whitespace as defined does not need to be explicitly captured and discarded. The default value is `r'\s*'`—all whitespace including newlines. With `whitespace=None`, no whitespace is ignored.

```python
from parsita import *

class NumericListParsers(TextParsers, whitespace=r'[ ]*'):
    integer_list = '[' >> repsep(reg('(+-)?[0-9]+') > int, ',') << ']'
```

Pretty much every function in Parsita returns an object with type `Parser`. Various operators, like `&` and `|`, are defined so that `Parser`s can be combined to make new, more complex, parsers, hence the name "parser combinators".

## Invoking a parser

### `Parser.parse`

The only method of note on a `Parser` is the `parse` method. The `parse` method takes a `str` as input and returns an instance of the `Result` class, which has two subclasses `Success` and `Failure`. Note that in v2.0, these classes are not defined in Parsita, but are imported from `returns.result`.

The standard way to test if a result is a `Success` or `Failure` is to use `is_successful` from `returns.pipeline`:

```python
from returns.pipeline import is_successful
from parsita import *

class NumericListParsers(TextParsers, whitespace=r'[ ]*'):
    integer_list = '[' >> repsep(reg('(+-)?[0-9]+') > int, ',') << ']'

result = NumericListParsers.integer_list.parse('[1, 1, 2, 3, 5]')

if is_successful(result):
    python_list = result.unwrap()
else:
    raise result.failure()
```

In on Python 3.10 or later, an even better solution is to use the `match` statement:

```python
from returns.result import Success, Failure
from parsita import *

class NumericListParsers(TextParsers, whitespace=r'[ ]*'):
    integer_list = '[' >> repsep(reg('(+-)?[0-9]+') > int, ',') << ']'

result = NumericListParsers.integer_list.parse('[1, 1, 2, 3, 5]')

match result:
    case Success(value):
        python_list = value
    case Failure(error):
        raise result.failure()
```
