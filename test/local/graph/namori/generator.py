from __future__ import annotations

import random
from collections import deque

from config import N_MAX, N_MIN, Q_MAX, WEIGHT_MAX


def cycle_vertices(n: int, edges: list[tuple[int, int, int]]) -> list[int]:
    adj = [[] for _ in range(n)]
    deg = [0] * n
    for u, v, _ in edges:
        adj[u].append(v)
        adj[v].append(u)
        deg[u] += 1
        deg[v] += 1
    removed = [False] * n
    q = deque(v for v in range(n) if deg[v] == 1)
    while q:
        v = q.popleft()
        removed[v] = True
        for u in adj[v]:
            if removed[u]:
                continue
            deg[u] -= 1
            if deg[u] == 1:
                q.append(u)
    return [v for v in range(n) if not removed[v]]


def generate_testcase() -> str:
    n = random.randint(N_MIN, N_MAX)
    edges: list[tuple[int, int, int]] = []
    used: set[tuple[int, int]] = set()
    for v in range(1, n):
        p = random.randrange(v)
        w = random.randint(1, WEIGHT_MAX)
        edges.append((p, v, w))
        used.add((min(p, v), max(p, v)))

    candidates = [(u, v) for u in range(n) for v in range(u + 1, n) if (u, v) not in used]
    u, v = random.choice(candidates)
    edges.append((u, v, random.randint(1, WEIGHT_MAX)))
    cyc = cycle_vertices(n, edges)

    queries: list[str] = []
    ops = ('ON', 'ROOT', 'DIST', 'SUB', 'SAME', 'ANC', 'LCA', 'SEG', 'ESEG', 'D', 'WD', 'PL', 'WPL', 'CD', 'WCD')
    for _ in range(Q_MAX):
        op = random.choice(ops)
        if op in ('ON', 'ROOT', 'DIST', 'SUB'):
            queries.append(f'{op} {random.randrange(n)}')
        elif op in ('CD', 'WCD'):
            a, b = random.sample(cyc, 2) if len(cyc) >= 2 else (cyc[0], cyc[0])
            queries.append(f'{op} {a} {b}')
        else:
            a = random.randrange(n)
            b = random.randrange(n)
            queries.append(f'{op} {a} {b}')

    lines = [f'{n} {len(queries)}']
    lines.extend(f'{u} {v} {w}' for u, v, w in edges)
    lines.extend(queries)
    return '\n'.join(lines) + '\n'
