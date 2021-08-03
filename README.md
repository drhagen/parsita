# Parsita

[![Build status][build-image]][build-link]
[![Code coverage][coverage-image]][coverage-link]
[![Latest PyPI version][pypi-image]][pypi-link]
[![Supported Python versions][python-versions-image]][python-versions-link]

> The executable grammar of parsers combinators made available in the executable pseudocode of Python.

Parsita is a parser combinator library written in Python. Parser combinators provide an easy way to define a grammar using code so that the grammar itself effectively parses the source. They are not the fastest at parsing, but they are the easiest to write.

Like all good parser combinator libraries, Parsita abuses operators to provide a clean grammar-like syntax. The `__or__` method is defined so that `|` tests between two alternatives. The `__and__` method is defined so that `&` tests two parsers in sequence. Other operators are used as well.

In a technique that I think is new to Python, Parsita uses metaclass magic to allow for forward declarations of values. This is important for parser combinators because grammars are often recursive or mutually recursive, meaning that some components must be used in the definition of others before they themselves are defined.

See the [Documentation](https://parsita.drhagen.com) for the full user guide.

## Installation

The recommended means of installation is with `pip` from PyPI.

```shell
pip install parsita
```

## Hello world

The following is a very basic parser for extracting the name from a `Hello, {name}!` string.

```python
from parsita import *

class HelloWorldParsers(TextParsers, whitespace=r'[ ]*'):
    hello_world = lit('Hello') >> ',' >> reg(r'[A-Z][a-z]*') << '!'

# A successful parse produces the parsed value
name = HelloWorldParsers.hello_world.parse('Hello, David!').or_die()
assert name == 'David'

# A parsing failure produces a useful error message
name = HelloWorldParsers.hello_world.parse('Hello David!').or_die()
# parsita.state.ParseError: Expected ',' but found 'David'
# Line 1, character 7
#
# Hello David!
#       ^
```

[build-image]: https://github.com/drhagen/parsita/workflows/python/badge.svg?branch=master&event=push
[build-link]: https://github.com/drhagen/parsita/actions?query=branch%3Amaster+event%3Apush
[coverage-image]: https://codecov.io/github/drhagen/parsita/coverage.svg?branch=master
[coverage-link]: https://codecov.io/github/drhagen/parsita?branch=master
[pypi-image]: https://img.shields.io/pypi/v/parsita.svg
[pypi-link]: https://pypi.python.org/pypi/parsita
[python-versions-image]: https://img.shields.io/pypi/pyversions/parsita.svg
[python-versions-link]: https://pypi.python.org/pypi/parsita
