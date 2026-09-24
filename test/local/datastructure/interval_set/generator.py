from __future__ import annotations

import random

from config import Q_MAX, SPAN_MAX, X_MAX, X_MIN


def random_range() -> tuple[int, int]:
    l = random.randint(X_MIN, X_MAX)
    r = l + random.randint(0, SPAN_MAX)
    return l, r


def generate_testcase() -> str:
    queries: list[str] = []
    ops = ('ADD', 'REM', 'CON', 'FIND', 'LEN', 'COV', 'GET', 'DIS', 'MEX')
    for _ in range(Q_MAX):
        op = random.choice(ops)
        if op in ('ADD', 'REM', 'DIS'):
            l, r = random_range()
            queries.append(f'{op} {l} {r}')
        elif op in ('CON', 'FIND', 'MEX'):
            queries.append(f'{op} {random.randint(X_MIN, X_MAX)}')
        elif op == 'GET':
            queries.append(f'{op} {random.randint(0, 12)}')
        else:
            queries.append(op)
    return str(len(queries)) + '\n' + '\n'.join(queries) + '\n'
