from __future__ import annotations

import random

from config import CYCLE_LEN_MAX, N_MAX, Q_MAX, WEIGHT_MAX


def generate_graph() -> tuple[int, list[tuple[int, int, int]], list[list[int]]]:
    n = 1
    edges: list[tuple[int, int, int]] = []
    cycles: list[list[int]] = []

    first_len = random.randint(3, min(CYCLE_LEN_MAX, N_MAX))
    cycle = list(range(first_len))
    for i in range(first_len):
        u = cycle[i]
        v = cycle[(i + 1) % first_len]
        edges.append((u, v, random.randint(1, WEIGHT_MAX)))
    cycles.append(cycle)
    n = first_len

    while n < N_MAX and random.random() < 0.8:
        anchor = random.randrange(n)
        if random.random() < 0.45 or n + 2 > N_MAX:
            edges.append((anchor, n, random.randint(1, WEIGHT_MAX)))
            n += 1
        else:
            length = random.randint(3, min(CYCLE_LEN_MAX, N_MAX - n + 1))
            added = list(range(n, n + length - 1))
            cyc = [anchor] + added
            edges.append((anchor, added[0], random.randint(1, WEIGHT_MAX)))
            for i in range(len(added) - 1):
                edges.append((added[i], added[i + 1], random.randint(1, WEIGHT_MAX)))
            edges.append((added[-1], anchor, random.randint(1, WEIGHT_MAX)))
            cycles.append(cyc)
            n += length - 1
    return n, edges, cycles


def generate_testcase() -> str:
    n, edges, cycles = generate_graph()
    queries: list[str] = []
    ops = ('BV', 'BE', 'ART', 'ON', 'SAME', 'CYC')
    for _ in range(Q_MAX):
        op = random.choice(ops)
        if op in ('BV', 'ART', 'ON'):
            queries.append(f'{op} {random.randrange(n)}')
        elif op == 'BE':
            queries.append(f'{op} {random.randrange(len(edges))}')
        elif op == 'CYC':
            cycle = random.choice(cycles)
            u, v = random.sample(cycle, 2)
            queries.append(f'{op} {u} {v}')
        else:
            u = random.randrange(n)
            v = random.randrange(n)
            queries.append(f'{op} {u} {v}')

    lines = [f'{n} {len(edges)} {len(queries)}']
    lines.extend(f'{u} {v} {w}' for u, v, w in edges)
    lines.extend(queries)
    return '\n'.join(lines) + '\n'
