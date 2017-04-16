from parsita import *

# JSON definition according to https://tools.ietf.org/html/rfc7159

json_whitespace = r'[ \t\n\r]*'


class JsonStringParsers(TextParsers, whitespace=None):
    quote = lit(r'\"') > (lambda _: '"')
    reverse_solidus = lit(r'\\') > (lambda _: '\\')
    solidus = lit(r'\/') > (lambda _: '/')
    backspace = lit(r'\b') > (lambda _: '\b')
    form_feed = lit(r'\f') > (lambda _: '\f')
    line_feed = lit(r'\n') > (lambda _: '\n')
    carriage_return = lit(r'\r') > (lambda _: '\r')
    tab = lit(r'\t') > (lambda _: '\t')
    uni = reg(r'\\u([0-9a-fA-F]{4})') > (lambda x: chr(int(x.group(1), 16)))

    escaped = (quote | reverse_solidus | solidus | backspace | form_feed |
               line_feed | carriage_return | tab | uni)
    unescaped = reg(r'[\u0020-\u0021\u0023-\u005B\u005D-\U0010FFFF]+')

    string = '"' >> rep(escaped | unescaped) << '"' > ''.join


class JsonParsers(TextParsers, whitespace=json_whitespace):
    number = reg(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?') > float

    false = lit('false') > (lambda _: False)
    true = lit('true') > (lambda _: True)
    null = lit('null') > (lambda _: None)

    string = reg(json_whitespace) >> JsonStringParsers.string

    array = '[' >> repsep(value, ',') << ']'

    entry = string << ':' & value
    obj = '{' >> repsep(entry, ',') << '}' > dict

    value = number | false | true | null | string | array | obj


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
