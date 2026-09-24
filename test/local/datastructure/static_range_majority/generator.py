from __future__ import annotations

import random

from config import N_MAX, Q_MAX, VALUE_MAX, VALUE_MIN


def generate_testcase() -> str:
    n = random.randint(1, N_MAX)
    q = random.randint(1, Q_MAX)
    arr = [random.randint(VALUE_MIN, VALUE_MAX) for _ in range(n)]
    if random.random() < 0.4:
        value = random.randint(VALUE_MIN, VALUE_MAX)
        for i in range(n):
            if random.random() < 0.6:
                arr[i] = value

    lines = [f'{n} {q}', ' '.join(map(str, arr))]
    for _ in range(q):
        l = random.randint(0, n - 1)
        r = random.randint(l + 1, n)
        lines.append(f'{l} {r}')
    return '\n'.join(lines) + '\n'
