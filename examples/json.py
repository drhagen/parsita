from parsita import *
from parsita.util import constant

# JSON definition according to https://tools.ietf.org/html/rfc7159


class JsonStringParsers(TextParsers, whitespace=None):
    quote = lit(r"\"") > constant('"')
    reverse_solidus = lit(r"\\") > constant("\\")
    solidus = lit(r"\/") > constant("/")
    backspace = lit(r"\b") > constant("\b")
    form_feed = lit(r"\f") > constant("\f")
    line_feed = lit(r"\n") > constant("\n")
    carriage_return = lit(r"\r") > constant("\r")
    tab = lit(r"\t") > constant("\t")
    uni = reg(r"\\u([0-9a-fA-F]{4})") > (lambda x: chr(int(x.group(1), 16)))

    escaped = quote | reverse_solidus | solidus | backspace | form_feed | line_feed | carriage_return | tab | uni
    unescaped = reg(r"[\u0020-\u0021\u0023-\u005B\u005D-\U0010FFFF]+")

    string = '"' >> rep(escaped | unescaped) << '"' > "".join


class JsonParsers(TextParsers, whitespace=r"[ \t\n\r]*"):
    number = reg(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?") > float

    false = lit("false") > constant(False)
    true = lit("true") > constant(True)
    null = lit("null") > constant(None)

    string = JsonStringParsers.string

    array = "[" >> repsep(value, ",") << "]"

    entry = string << ":" & value
    obj = "{" >> repsep(entry, ",") << "}" > dict

    value = number | false | true | null | string | array | obj


if __name__ == "__main__":
    strings = [
        '"name"',
        "-12.40e2",
        "[false, true, null]",
        '{"__class__" : "Point", "x" : 2.3, "y" : -1.6}',
        '{"__class__" : "Rectangle", "location" : {"x":-1.3,"y":-4.5}, "height" : 2.0, "width" : 4.0}',
        '{"text" : ""}',
    ]

    for string in strings:
        print("source: {}\nvalue: {}".format(string, JsonParsers.value.parse(string)))
