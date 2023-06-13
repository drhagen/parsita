from parsita import ParserContext, lit, opt, reg, rep


class ExpressionParsers(ParserContext, whitespace=r"[ ]*"):
    number = reg(r"[+-]?\d+(\.\d+)?(e[+-]?\d+)?") > float

    base = "(" >> expr << ")" | number

    factor = base & opt("^" >> base) > (lambda x: x[0] ** x[1][0] if x[1] else x[0])

    def make_term(args):
        factor1, factors = args
        result = factor1
        for op, factor in factors:
            if op == "*":
                result = result * factor
            else:
                result = result / factor
        return result

    term = factor & rep(lit("*", "/") & factor) > make_term

    def make_expr(args):
        term1, terms = args
        result = term1
        for op, term2 in terms:
            if op == "+":
                result = result + term2
            else:
                result = result - term2
        return result

    expr = term & rep(lit("+", "-") & term) > make_expr


if __name__ == "__main__":
    expressions = ["123", "2 ^ 3", "1 + 1", "1 - 2 + 3 - 4", "3 - 4 * 2 + 10", "14 / (3.1 + 3.9)"]

    for expression in expressions:
        print("{} = {}".format(expression, ExpressionParsers.expr.parse(expression).unwrap()))
