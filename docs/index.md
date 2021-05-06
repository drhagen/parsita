# Parsita

Parsita is a parser combinator library written in Python. Parser combinators provide an easy way to define a grammar using code so that the grammar itself effectively parses the source. They are not the fastest at parsing, but they are the easiest to write.

Like all good parser combinator libraries, Parsita abuses operators to provide a clean grammar-like syntax. The `__or__` method is defined so that `|` tests between two alternatives. The `__and__` method is defined so that `&` tests two parsers in sequence. Other operators are used as well.

In a technique that I think is new to Python, Parsita uses metaclass magic to allow for forward declarations of values. This is important for parser combinators because grammars are often recursive or mutually recursive, meaning that some components must be used in the definition of others before they themselves are defined.

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
name = HelloWorldParsers.hello_world.parse('Hello Fred!').or_die()
# parsita.state.ParseError: Expected ',' but found 'Fred'
# Line 1, character 7

# Hello Fred!
#       ^
```
