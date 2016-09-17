from ast import literal_eval
from parsita import *

# JSON definition according to https://tools.ietf.org/html/rfc7159


class JsonStringParsers(RegexParsers, whitespace=None):
    quote = lit(r'\"') > (lambda _: '"')
    reverse_solidus = lit(r'\\') > (lambda _: '\\')
    solidus = lit(r'\/') > (lambda _: '/')
    backspace = lit(r'\b') > (lambda _: '\b')
    form_feed = lit(r'\f') > (lambda _: '\f')
    line_feed = lit(r'\n') > (lambda _: '\n')
    carriage_return = lit(r'\r') > (lambda _: '\r')
    tab = lit(r'\t') > (lambda _: '\t')
    unicode = reg(r'\\u[0-9a-fA-F]{4}') > literal_eval

    escaped = (quote | reverse_solidus | solidus | backspace | form_feed
               | line_feed | carriage_return | tab | unicode)
    unescaped = reg(r'[\u0020-\u0021\u0023-\u005B\u005D-\U0010FFFF]+')

    string = '"' >> rep(escaped | unescaped) << '"' > ''.join


class JsonParsers(RegexParsers, whitespace=r'[ \t\n\r]*'):
    number = reg(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?')

    false = lit('false') > (lambda _: False)
    true = lit('true') > (lambda _: True)
    null = lit('null') > (lambda _: None)

    string = reg(r'[ \t\n\r]*') >> JsonStringParsers.string

    array = '[' >> repsep(value, ',') << ']'

    entry = string << ':' & value
    object = '{' >> repsep(entry, ',') << '}' > dict

    value = number | false | true | null | string | array | object

if __name__ == '__main__':
    strings = [
        '"name"',
        '-12.40e2',
        '[false, true, null]',
        '{"__class__" : "Point", "x" : 2.3, "y" : -1.6}',
        '{"__class__" : "Rectangle", "location" : {"x":-1.3,"y":-4.5}, "height" : 2.0, "width" : 4.0}',
        '{"text" : ""}'
    ]

    for string in strings:
        print('source: {}\nvalue: {}'.format(string, JsonParsers.value.parse(string)))
