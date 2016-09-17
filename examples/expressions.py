from parsita.regex_parsers import *


class ExpressionParsers(RegexParsers):
    number = reg(r'[+-]?(\d)+(\.\d+)?(e[+-]?\d+)?') > float

    base = '(' >> expr << ')' | number

    factor = base & opt('^' >> base) > (lambda x: x[0] ** x[1][0] if x[1] else x[0])

    def make_term(x):
        factor1, maybe_factor = x
        if maybe_factor:
            op, factor2 = maybe_factor[0]
            if op == '*':
                return factor1 * factor2
            else:
                return factor1 / factor2
        else:
            return factor1
    term = factor & opt(lit('*', '/') & factor) > make_term

    def make_expr(x):
        term1, maybe_term = x
        if maybe_term:
            op, term2 = maybe_term[0]
            if op == '+':
                return term1 + term2
            else:
                return term1 - term2
        else:
            return term1
    expr = term & opt(lit('+', '-') & term) > make_expr

if __name__ == '__main__':
    expressions = ['123', '2 ^ 3', '1 + 1', '14 / (3.1 + 3.9)']

    for expression in expressions:
        print('{} = {}'.format(expression, ExpressionParsers.expr.parse(expression).value))
