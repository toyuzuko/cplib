from __future__ import annotations

import random

from config import N_MAX, Q_MAX, VALUE_EXTRA, VALUE_MIN


def generate_testcase() -> str:
    n = random.randint(0, N_MAX)
    q = random.randint(1, Q_MAX)
    value_max = n + VALUE_EXTRA
    arr = [random.randint(VALUE_MIN, value_max) for _ in range(n)]

    lines = [f'{n} {q}']
    lines.append(' '.join(map(str, arr)))
    for _ in range(q):
        l = random.randint(0, n)
        r = random.randint(l, n)
        lines.append(f'{l} {r}')
    return '\n'.join(lines) + '\n'
