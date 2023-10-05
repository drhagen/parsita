# Parsita

[![Build status](https://github.com/drhagen/parsita/workflows/ci/badge.svg)](https://github.com/drhagen/parsita/actions/workflows/ci.yml)
[![Code coverage](https://codecov.io/github/drhagen/parsita/coverage.svg?branch=master)](https://codecov.io/github/drhagen/parsita?branch=master)
[![Latest PyPI version](https://img.shields.io/pypi/v/parsita.svg)](https://pypi.python.org/pypi/parsita)
[![License](https://img.shields.io/pypi/l/parsita.svg)](https://github.com/drhagen/parsita/blob/master/LICENSE)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/parsita.svg)](https://pypi.python.org/pypi/parsita)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org)
[![Nox](https://img.shields.io/badge/%F0%9F%A6%8A-Nox-D85E00.svg)](https://nox.thea.codes)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://beta.ruff.rs)

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
