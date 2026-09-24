from __future__ import annotations

import random

from config import M_MAX, N_MAX, Q_MAX


def generate_dag_edges(n: int, m: int) -> list[tuple[int, int]]:
    perm = list(range(n))
    random.shuffle(perm)
    edges: set[tuple[int, int]] = set()
    possible = n * (n - 1) // 2
    m = min(m, possible)
    while len(edges) < m:
        i = random.randrange(n)
        j = random.randrange(n)
        if i == j:
            continue
        if i > j:
            i, j = j, i
        edges.add((perm[i], perm[j]))
    return list(edges)


def generate_general_edges(n: int, m: int) -> list[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    possible = n * n
    m = min(m, possible)
    while len(edges) < m:
        edges.add((random.randrange(n), random.randrange(n)))
    return list(edges)


def generate_testcase() -> str:
    n = random.randint(1, N_MAX)
    m = random.randint(0, min(M_MAX, n * n))
    if random.random() < 0.5:
        edges = generate_dag_edges(n, m)
    else:
        edges = generate_general_edges(n, m)
    q = random.randint(1, Q_MAX)
    queries = [(random.randrange(n), random.randrange(n)) for _ in range(q)]
    lines = [f'{n} {len(edges)} {q}']
    lines.extend(f'{u} {v}' for u, v in edges)
    lines.extend(f'{u} {v}' for u, v in queries)
    return '\n'.join(lines) + '\n'
