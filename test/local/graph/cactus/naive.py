from __future__ import annotations

from collections import deque
import heapq


def format_blocks(blocks: list[list[int]]) -> str:
    normalized = [tuple(sorted(block)) for block in blocks]
    normalized.sort()
    return '|'.join(' '.join(map(str, block)) for block in normalized)


def build_adj(n: int, edges: list[tuple[int, int, int]]):
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append((v, w, i))
        adj[v].append((u, w, i))
    return adj


def path_without_edge(adj, start: int, goal: int, banned: int):
    parent = {start: (-1, -1)}
    q = deque([start])
    while q:
        v = q.popleft()
        if v == goal:
            break
        for u, _, e in adj[v]:
            if e == banned or u in parent:
                continue
            parent[u] = (v, e)
            q.append(u)
    if goal not in parent:
        return None
    vertices = [goal]
    edge_ids: list[int] = []
    v = goal
    while v != start:
        p, e = parent[v]
        vertices.append(p)
        edge_ids.append(e)
        v = p
    vertices.reverse()
    return vertices, edge_ids


def decompose(n: int, edges: list[tuple[int, int, int]]):
    adj = build_adj(n, edges)
    bridge = [False] * len(edges)
    cycle_by_key: dict[tuple[int, ...], set[int]] = {}
    for e, (u, v, _) in enumerate(edges):
        path = path_without_edge(adj, u, v, e)
        if path is None:
            bridge[e] = True
            continue
        vertices, edge_ids = path
        key = tuple(sorted(vertices))
        cycle_by_key.setdefault(key, set()).update(edge_ids + [e])

    blocks: list[list[int]] = []
    edge_block = [-1] * len(edges)
    cycle_blocks: list[set[int]] = []
    for key, edge_ids in sorted(cycle_by_key.items()):
        block = len(blocks)
        blocks.append(list(key))
        cycle_blocks.append(set(edge_ids))
        for e in edge_ids:
            edge_block[e] = block
    for e, (u, v, _) in enumerate(edges):
        if bridge[e]:
            edge_block[e] = len(blocks)
            blocks.append([u, v])
    vertex_blocks = [[] for _ in range(n)]
    for block, vertices in enumerate(blocks):
        for v in vertices:
            vertex_blocks[v].append(block)
    return adj, blocks, edge_block, cycle_blocks, vertex_blocks


def is_articulation(n: int, adj, v: int) -> bool:
    starts = [u for u in range(n) if u != v]
    if not starts:
        return False
    seen = [False] * n
    seen[v] = True
    q = deque([starts[0]])
    seen[starts[0]] = True
    while q:
        x = q.popleft()
        for u, _, _ in adj[x]:
            if not seen[u]:
                seen[u] = True
                q.append(u)
    return any(not seen[u] for u in range(n))


def cycle_distance(n: int, edges: list[tuple[int, int, int]], edge_ids: set[int], u: int, v: int, weighted: bool) -> int:
    adj = [[] for _ in range(n)]
    for e in edge_ids:
        a, b, w = edges[e]
        cost = w if weighted else 1
        adj[a].append((b, cost))
        adj[b].append((a, cost))
    dist = [10 ** 18] * n
    dist[u] = 0
    heap = [(0, u)]
    while heap:
        d, x = heapq.heappop(heap)
        if d != dist[x]:
            continue
        if x == v:
            return d
        for y, cost in adj[x]:
            if d + cost < dist[y]:
                dist[y] = d + cost
                heapq.heappush(heap, (dist[y], y))
    raise AssertionError('unreachable')


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, m, q = map(int, lines[0].split())
    edges = [tuple(map(int, line.split())) for line in lines[1:1 + m]]
    adj, blocks, edge_block, cycle_blocks, vertex_blocks = decompose(n, edges)
    cycle_vertices = set()
    for block, edge_ids in enumerate(cycle_blocks):
        for e in edge_ids:
            cycle_vertices.add(edges[e][0])
            cycle_vertices.add(edges[e][1])
    out: list[str] = []
    for line in lines[1 + m:1 + m + q]:
        parts = line.split()
        op = parts[0]
        if op == 'BV':
            out.append(format_blocks([blocks[block] for block in vertex_blocks[int(parts[1])]]))
        elif op == 'BE':
            out.append(format_blocks([blocks[edge_block[int(parts[1])]]]))
        elif op == 'ART':
            out.append(str(int(is_articulation(n, adj, int(parts[1])))))
        elif op == 'ON':
            out.append(str(int(int(parts[1]) in cycle_vertices)))
        elif op == 'SAME':
            u = int(parts[1])
            v = int(parts[2])
            out.append(str(int(bool(set(vertex_blocks[u]) & set(vertex_blocks[v])))))
        else:
            u = int(parts[1])
            v = int(parts[2])
            common = set(vertex_blocks[u]) & set(vertex_blocks[v])
            block = next(b for b in common if b < len(cycle_blocks))
            unweighted = cycle_distance(n, edges, cycle_blocks[block], u, v, False)
            weighted = cycle_distance(n, edges, cycle_blocks[block], u, v, True)
            out.append(f'{unweighted} {weighted}')
    return '\n'.join(out) + '\n'
