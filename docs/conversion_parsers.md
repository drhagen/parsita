# Conversion parsers

## `parser > function`: conversion parser

Conversion parsers don't change how the text is parsed—they change the value returned. Every parser returns a value when it succeeds. The function supplied must take a single argument (the successful value) and returns a new value. This is how text is converted to other objects and simpler objects built into larger ones. In accordance with Python's operator precedence, `>` is the operator in Parsita with the loosest binding.

```python
from parsita import *

class IntegerParsers(TextParsers):
    integer = reg(r'[-+]?[0-9]+') > int

assert IntegerParsers.integer.parse('-128') == Success(-128)
```
