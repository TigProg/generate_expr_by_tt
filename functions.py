from csv import reader as csv_reader

from pyeda import inter as eda
from pyeda.boolalg.expr import _LITS


def _ast_to_str(ast):
    """Recursive unfolding of AST in pseudographics"""
    if ast[0] == 'const':
        return str(ast[1])
    elif ast[0] == 'lit':
        return str(_LITS[ast[1]])
    elif ast[0] in ('and', 'or'):
        sep = ' /\\ ' if ast[0] == 'and' else ' \\/ '  # TODO: fix
        return '(' + sep.join([_ast_to_str(items) for items in ast[1:]]) + ')'
    else:
        assert False, 'some error while building the pseudo'


def _expr_to_pseudo(expr):
    """Get representation of the expression in pseudographics"""
    return _ast_to_str(expr.to_ast())


def args_to_int(args):
    """Encoding a string from truth table by integer"""
    res = 0
    for i in reversed(args):
        res = (res << 1) | int(i)
    return res


def _csv_body_to_result_cols(rows, f_count):
    """Get full truth table body"""
    n_args = len(rows[0]) - f_count
    rows = list(set(rows))  # remove duplicates

    unique_args = set(
        row[:-f_count]
        for row in rows
    )
    if len(rows) != len(unique_args):
        raise ValueError(
            'There are identical arguments with different values of functions'
        )
    args_to_values = {
        args_to_int(row[:-f_count]): row[-f_count:]
        for row in rows
    }
    if len(args_to_values) != 2 ** n_args:  # some lines are not
        for i in range(2 ** n_args):
            if i not in args_to_values:
                args_to_values[i] = ('-',) * f_count
    return [
        [args_to_values[key][i] for key in sorted(args_to_values)]
        for i in range(f_count)
    ]


def _csv_header_to_vars(row, user_f_count):
    """Get variable names"""
    if user_f_count is not None:
        if not user_f_count or user_f_count >= len(row):
            raise ValueError("Invalid value of 'function_count'")
        f_count = user_f_count
    else:
        f_count = 0
        for name in reversed(row):
            if name.startswith('result'):
                f_count += 1
            else:
                break
    if not f_count or f_count == len(row):
        raise ValueError(
            "Invalid number of col's names starting with 'result'"
        )
    return list(map(eda.exprvar, row[:-f_count])), f_count


def _csv_to_truthtables(csv_path, user_f_count):
    """Get truth table in pyeda format from csv file"""
    with open(csv_path) as file:
        csv_file = csv_reader(file)
        rows = [tuple(row) for row in csv_file]
    bool_vars, f_count = _csv_header_to_vars(rows[0], user_f_count)
    result_columns = _csv_body_to_result_cols(rows[1:], f_count)
    return [eda.truthtable(bool_vars, result) for result in result_columns]


def csv_to_expr(csv_path, *,
                simplify=True,
                function_count=None,
                return_type='pseudo'):
    """
    Reads truth table from csv files
    and outputs a tuple of generated functions

    :param csv_path: path to csv file with truth table
    :type csv_path: str
    :param simplify: flag, try to simplify if True, otherwise not try
    :type simplify: bool
    :param function_count: how many columns in csv is function result,
           if None, get column names, that starting with 'result'
           if int, skip parsing column names
    :type function_count: None | int
    :param return_type: 'expr' or 'pseudo'
    :type return_type: str
    :return: expressions like pyeda.boolalg.expr.AndOp or pseudographics
    :rtype: tuple
    """
    if return_type not in ('expr', 'pseudo'):
        raise ValueError("return_type must be 'expr' or 'pseudo'")
    tables = _csv_to_truthtables(csv_path, function_count)
    if simplify:
        results = eda.espresso_tts(*tables)
    else:
        results = tuple(eda.truthtable2expr(table) for table in tables)
    if return_type == 'expr':
        return results
    return tuple(_expr_to_pseudo(result) for result in results)


if __name__ == '__main__':
    # examples
    print(csv_to_expr('table1.csv'))
    print(csv_to_expr('table2.csv'))
    print(csv_to_expr('table2.csv', simplify=False))
    print(csv_to_expr('table2.csv', function_count=1))
    print(csv_to_expr('table3.csv', return_type='expr'))
