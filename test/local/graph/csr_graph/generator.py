from __future__ import annotations

import random

from config import M_MAX, N_MAX, W_MAX, W_MIN


def generate_testcase() -> str:
    n = random.randint(0, N_MAX)
    m = random.randint(0, M_MAX if n else 0)
    is_directed = random.randint(0, 1)
    is_weighted = random.randint(0, 1)

    lines = [f'{n} {m} {is_directed} {is_weighted}']
    for _ in range(m):
        u = random.randrange(n)
        v = random.randrange(n)
        if is_weighted:
            w = random.randint(W_MIN, W_MAX)
            lines.append(f'{u} {v} {w}')
        else:
            lines.append(f'{u} {v}')
    return '\n'.join(lines) + '\n'
