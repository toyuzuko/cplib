from __future__ import annotations

import random

from config import K_MAX, N_MAX, Q_MAX, VALUE_MAX


def generate_successors(n: int) -> list[int]:
    if n == 1:
        return [0]
    to = [random.randrange(n) for _ in range(n)]
    if random.random() < 0.5:
        cycle_len = random.randint(1, n)
        cycle = random.sample(range(n), cycle_len)
        for i, v in enumerate(cycle):
            to[v] = cycle[(i + 1) % cycle_len]
        for v in range(n):
            if v not in cycle and random.random() < 0.6:
                to[v] = random.choice(cycle)
    return to


def generate_testcase() -> str:
    n = random.randint(1, N_MAX)
    to = generate_successors(n)
    vertex_values = [random.randint(0, VALUE_MAX) for _ in range(n)]
    edge_values = [random.randint(0, VALUE_MAX) for _ in range(n)]
    queries: list[str] = []
    ops = ('J', 'G', 'PV', 'PE', 'CID', 'CLEN', 'DIST', 'ON', 'ENTRY')
    for _ in range(Q_MAX):
        op = random.choice(ops)
        v = random.randrange(n)
        if op in ('J', 'G', 'PV', 'PE'):
            k = random.randint(0, K_MAX)
            queries.append(f'{op} {v} {k}')
        else:
            queries.append(f'{op} {v}')

    lines = [f'{n} {len(queries)}']
    lines.append(' '.join(map(str, to)))
    lines.append(' '.join(map(str, vertex_values)))
    lines.append(' '.join(map(str, edge_values)))
    lines.extend(queries)
    return '\n'.join(lines) + '\n'
