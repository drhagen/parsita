# Parsita

![PyPI downloads](https://img.shields.io/pypi/dm/parsita)
[![Build status](https://github.com/drhagen/parsita/workflows/CI/badge.svg)](https://github.com/drhagen/parsita/actions/workflows/ci.yml)
[![Code coverage](https://codecov.io/github/drhagen/parsita/coverage.svg?branch=master)](https://codecov.io/github/drhagen/parsita?branch=master)
[![Latest PyPI version](https://img.shields.io/pypi/v/parsita.svg)](https://pypi.python.org/pypi/parsita)
[![License](https://img.shields.io/pypi/l/parsita.svg)](https://github.com/drhagen/parsita/blob/master/LICENSE)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/parsita.svg)](https://pypi.python.org/pypi/parsita)

> The executable grammar of parser combinators made available in the executable pseudocode of Python.

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

class HelloWorldParsers(ParserContext, whitespace=r'[ ]*'):
    hello_world = lit('Hello') >> ',' >> reg(r'[A-Z][a-z]*') << '!'

# A successful parse produces the parsed value
name = HelloWorldParsers.hello_world.parse('Hello, David!').unwrap()
assert name == 'David'

# A parsing failure produces a useful error message
name = HelloWorldParsers.hello_world.parse('Hello David!').unwrap()
# parsita.state.ParseError: Expected ',' but found 'David'
# Line 1, character 7
#
# Hello David!
#       ^
```
