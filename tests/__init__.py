from typing import Any, Dict

from parsita import Failure, Success


def nest_string(source: Any):
    if not isinstance(source, str):
        source = str(source)
    result = ''
    tab_depth = 0
    for char in source:
        if char in {'(', '['}:
            result += '\n'
            tab_depth += 1
            result += '--' * tab_depth
            result += char
        elif char in {')', ']'}:

            result += '\n'
            result += '--' * tab_depth
            result += char
            tab_depth -= 1
        else:
            result += char
    return result


def collect_parsing_expectations(expectations: Dict[str, Any], parser):
    """

    :param expectations:
    :param parser:
    :return: yields actual then expected, then the input as strings
    """
    for (input, expected_outcome) in expectations.items():
        actual_result = parser.parse(input)

        if expected_outcome is Failure:
            assert type(actual_result) is Failure
            continue
        if type(actual_result) == Failure:
            breakpoint()
            pass
        assert type(actual_result) == Success

        actual_result_str = nest_string(actual_result)
        expected_str = nest_string(Success(expected_outcome))
        yield \
            f"{input}\n---\n{actual_result_str}", \
            f"{input}\n---\n{expected_str}", input