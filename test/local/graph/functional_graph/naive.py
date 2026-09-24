from __future__ import annotations

from collections import deque


def build_structure(to: list[int]) -> tuple[list[int], list[int], list[int], list[bool], list[int]]:
    n = len(to)
    indeg = [0] * n
    rev: list[list[int]] = [[] for _ in range(n)]
    for v, u in enumerate(to):
        indeg[u] += 1
        rev[u].append(v)

    removed = [False] * n
    q = deque(v for v in range(n) if indeg[v] == 0)
    while q:
        v = q.popleft()
        removed[v] = True
        u = to[v]
        indeg[u] -= 1
        if indeg[u] == 0:
            q.append(u)

    on_cycle = [not removed[v] for v in range(n)]
    cycle_id = [-1] * n
    cycle_length = [0] * n
    dist_to_cycle = [-1] * n
    cycle_entry = [-1] * n
    cycles: list[list[int]] = []

    for v in range(n):
        if not on_cycle[v] or cycle_id[v] != -1:
            continue
        cycle: list[int] = []
        u = v
        cid = len(cycles)
        while cycle_id[u] == -1:
            cycle_id[u] = cid
            cycle.append(u)
            u = to[u]
        cycles.append(cycle)
        for node in cycle:
            cycle_length[node] = len(cycle)
            dist_to_cycle[node] = 0
            cycle_entry[node] = node

    q = deque(v for v in range(n) if dist_to_cycle[v] == 0)
    while q:
        v = q.popleft()
        for u in rev[v]:
            if dist_to_cycle[u] != -1:
                continue
            dist_to_cycle[u] = dist_to_cycle[v] + 1
            cycle_id[u] = cycle_id[v]
            cycle_length[u] = cycle_length[v]
            cycle_entry[u] = cycle_entry[v]
            q.append(u)

    return cycle_id, cycle_length, dist_to_cycle, on_cycle, cycle_entry


def jump(to: list[int], v: int, k: int) -> int:
    for _ in range(k):
        v = to[v]
    return v


def prod(to: list[int], values: list[int], v: int, k: int) -> int:
    total = 0
    for _ in range(k):
        total += values[v]
        v = to[v]
    return total


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    to = list(map(int, lines[1].split()))
    vertex_values = list(map(int, lines[2].split()))
    edge_values = list(map(int, lines[3].split()))
    cycle_id, cycle_length, dist_to_cycle, on_cycle, cycle_entry = build_structure(to)
    out: list[str] = []
    for line in lines[4:4 + q]:
        parts = line.split()
        op = parts[0]
        v = int(parts[1])
        if op in ('J', 'G'):
            out.append(str(jump(to, v, int(parts[2]))))
        elif op == 'PV':
            out.append(str(prod(to, vertex_values, v, int(parts[2]))))
        elif op == 'PE':
            out.append(str(prod(to, edge_values, v, int(parts[2]))))
        elif op == 'CID':
            out.append(str(cycle_id[v]))
        elif op == 'CLEN':
            out.append(str(cycle_length[v]))
        elif op == 'DIST':
            out.append(str(dist_to_cycle[v]))
        elif op == 'ON':
            out.append(str(int(on_cycle[v])))
        else:
            out.append(str(cycle_entry[v]))
    assert len(to) == n
    return '\n'.join(out) + '\n'
