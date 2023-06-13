# Getting started

David Hagen gave an [introductory talk](https://www.youtube.com/watch?v=9JSGGSRgUcw) on Parsita at SciPy 2021. The documentation is more thorough, but the talk is useful for anyone looking for a quick walk-through.

Strictly speaking, Parsita parsers can parse any kind of sequence, `str`, `bytes`, `Sequence[Token]`, etc. As long as the arguments to the terminal parsers match the input sequence, everything will work. However, this documentation will focus exclusively on parsing `str` because parsing text is most accessible to beginners.

## Defining a parser

Parsita parsers are written inside the bodies of classes that inherit from `ParserContext`. Such classes are not meant to be instantiated. They are used purely as a kind of souped-up context manager.

The metaclass of `ParserContext` takes a `whitespace` named argument, which is a regular expression, or more commonly, a string that can be parsed into a regular expression, or less commonly, an arbitrary `Parser`. This becomes the definition of whitespace for all `Parser`s defined in this class body, making it so that whitespace as defined does not need to be explicitly captured and discarded. With the default `whitespace=None`, no whitespace is ignored. Common values for whitespace are:

* `whitespace=r'[ ]*'` to ignore spaces
* `whitespace=r'[ \t]*'` to ignore spaces and tabs
* `whitespace=r'\s*'` to ignore all whitespace including newlines

```python
from parsita import *

class NumericListParsers(ParserContext, whitespace=r'[ ]*'):
    integer_list = '[' >> repsep(reg('[+-]?[0-9]+') > int, ',') << ']'
```

Pretty much every function in Parsita returns an object with type `Parser`. Various operators, like `&` and `|`, are defined so that `Parser`s can be combined to make new, more complex, parsers, hence the name "parser combinators".

In version 1 of Parsita, `ParserContext` was split into two context classes, one with a default whitespace of `None` and the other with a default whitespace of `r'\s*'`. This was considered heavyweight, so they were combined into a single context.

## Invoking a parser

### `Parser.parse`

The only method of note on a `Parser` is the `parse` method. The `parse` method takes a `str` as as argument and returns an instance of the `Result` class, which has two subclasses `Success` and `Failure`. Note that in v2.0, these classes are reexported by Parsita, but are defined by the popular Returns package in [`returns.result`](https://returns.readthedocs.io/en/latest/pages/result.html). By using the `Result` class from Returns, Parsita's error handling can be composed with that of other libraries that use Returns. 

Instances of `Result` work especially well with pattern matching in the `match` statement introduced in Python 3.10:

```python
from parsita import *

class NumericListParsers(ParserContext, whitespace=r'[ ]*'):
    integer_list = '[' >> repsep(reg('[+-]?[0-9]+') > int, ',') << ']'

result = NumericListParsers.integer_list.parse('[1, 1, 2, 3, 5]')

match result:
    case Success(value):
        python_list = value
    case Failure(error):
        raise error
```

If working in a version of Python prior to 3.10, you can use `isinstance` directly:

```python
from parsita import *

class NumericListParsers(ParserContext, whitespace=r'[ ]*'):
    integer_list = '[' >> repsep(reg('[+-]?[0-9]+') > int, ',') << ']'

result = NumericListParsers.integer_list.parse('[1, 1, 2, 3, 5]')

if isinstance(result, Success):
    python_list = result.unwrap()
elif isinstance(result, Failure):
    raise result.failure()
```

Returns has lots of features related to the `Result` class not covered here. One of the useful features that is not a method on `Result` is `returns.pipeline.is_successful`, which may be useful for those on Python versions without pattern matching.
