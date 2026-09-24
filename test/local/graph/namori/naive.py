from __future__ import annotations

from collections import deque
import heapq


def build(n: int, edges: list[tuple[int, int, int]]):
    adj = [[] for _ in range(n)]
    deg = [0] * n
    for i, (u, v, w) in enumerate(edges):
        adj[u].append((v, w, i))
        adj[v].append((u, w, i))
        deg[u] += 1
        deg[v] += 1
    removed = [False] * n
    q = deque(v for v in range(n) if deg[v] == 1)
    while q:
        v = q.popleft()
        removed[v] = True
        for u, _, _ in adj[v]:
            if removed[u]:
                continue
            deg[u] -= 1
            if deg[u] == 1:
                q.append(u)
    on_cycle = [not removed[v] for v in range(n)]
    root = [-1] * n
    dist = [-1] * n
    weighted_dist = [0] * n
    parent = [-1] * n
    q = deque(v for v in range(n) if on_cycle[v])
    for v in q:
        root[v] = v
        dist[v] = 0
    while q:
        v = q.popleft()
        for u, w, _ in adj[v]:
            if on_cycle[u] or dist[u] != -1:
                continue
            root[u] = root[v]
            dist[u] = dist[v] + 1
            weighted_dist[u] = weighted_dist[v] + w
            parent[u] = v
            q.append(u)
    return adj, on_cycle, root, dist, weighted_dist, parent


def lca(u: int, v: int, parent: list[int], root: list[int]) -> int | None:
    if root[u] != root[v]:
        return None
    seen = set()
    x = u
    while x != -1:
        seen.add(x)
        x = parent[x]
    x = v
    while x not in seen:
        x = parent[x]
    return x


def ancestor(a: int, v: int, parent: list[int], root: list[int]) -> bool:
    if root[a] != root[v]:
        return False
    while v != -1:
        if v == a:
            return True
        v = parent[v]
    return False


def path_nodes(u: int, v: int, parent: list[int], root: list[int], edge_query: bool) -> list[int] | None:
    w = lca(u, v, parent, root)
    if w is None:
        return None
    nodes: list[int] = []
    x = u
    while x != w:
        nodes.append(x)
        x = parent[x]
    if not edge_query:
        nodes.append(w)
    stack: list[int] = []
    x = v
    while x != w:
        stack.append(x)
        x = parent[x]
    nodes.extend(reversed(stack))
    return sorted(nodes)


def cycle_arc_lengths(adj, on_cycle: list[bool], u: int, v: int) -> tuple[int, int, int, int]:
    neighbors = [(x, w) for x, w, _ in adj[u] if on_cycle[x]]
    lengths: list[tuple[int, int]] = []
    for start, w0 in neighbors:
        prev = u
        cur = start
        edges = 1
        weight = w0
        while cur != v:
            nxt = [(x, w) for x, w, _ in adj[cur] if on_cycle[x] and x != prev][0]
            prev, cur = cur, nxt[0]
            edges += 1
            weight += nxt[1]
        lengths.append((edges, weight))
    if u == v:
        return 0, 0, 0, 0
    (e0, w0), (e1, w1) = lengths
    return min(e0, e1), max(e0, e1), min(w0, w1), max(w0, w1)


def shortest(adj, start: int, goal: int, weighted: bool) -> int:
    if not weighted:
        dist = [-1] * len(adj)
        q = deque([start])
        dist[start] = 0
        while q:
            v = q.popleft()
            if v == goal:
                return dist[v]
            for u, _, _ in adj[v]:
                if dist[u] == -1:
                    dist[u] = dist[v] + 1
                    q.append(u)
        raise AssertionError('unreachable')
    dist = [10 ** 18] * len(adj)
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        d, v = heapq.heappop(heap)
        if d != dist[v]:
            continue
        if v == goal:
            return d
        for u, w, _ in adj[v]:
            if d + w < dist[u]:
                dist[u] = d + w
                heapq.heappush(heap, (dist[u], u))
    raise AssertionError('unreachable')


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    edges = [tuple(map(int, line.split())) for line in lines[1:1 + n]]
    adj, on_cycle, root, dist, weighted_dist, parent = build(n, edges)
    out: list[str] = []
    for line in lines[1 + n:1 + n + q]:
        parts = line.split()
        op = parts[0]
        if op == 'ON':
            out.append(str(int(on_cycle[int(parts[1])])))
        elif op == 'ROOT':
            out.append(str(root[int(parts[1])]))
        elif op == 'DIST':
            out.append(str(dist[int(parts[1])]))
        elif op == 'SUB':
            v = int(parts[1])
            out.append(' '.join(map(str, [u for u in range(n) if ancestor(v, u, parent, root)])))
        else:
            u = int(parts[1])
            v = int(parts[2])
            if op == 'SAME':
                out.append(str(int(root[u] == root[v])))
            elif op == 'ANC':
                out.append(str(int(ancestor(u, v, parent, root))))
            elif op == 'LCA':
                out.append(str(lca(u, v, parent, root)))
            elif op == 'SEG':
                nodes = path_nodes(u, v, parent, root, False)
                out.append('None' if nodes is None else ' '.join(map(str, nodes)))
            elif op == 'ESEG':
                nodes = path_nodes(u, v, parent, root, True)
                out.append('None' if nodes is None else ' '.join(map(str, nodes)))
            elif op == 'D':
                out.append(str(shortest(adj, u, v, False)))
            elif op == 'WD':
                out.append(str(shortest(adj, u, v, True)))
            elif op == 'CD':
                out.append(str(cycle_arc_lengths(adj, on_cycle, u, v)[0]))
            elif op == 'WCD':
                out.append(str(cycle_arc_lengths(adj, on_cycle, u, v)[2]))
            elif op == 'PL':
                if root[u] == root[v]:
                    d = shortest(adj, u, v, False)
                    out.append(f'{d} {d}')
                else:
                    c0, c1, _, _ = cycle_arc_lengths(adj, on_cycle, root[u], root[v])
                    base = dist[u] + dist[v]
                    out.append(f'{base + c0} {base + c1}')
            else:
                if root[u] == root[v]:
                    d = shortest(adj, u, v, True)
                    out.append(f'{d} {d}')
                else:
                    _, _, c0, c1 = cycle_arc_lengths(adj, on_cycle, root[u], root[v])
                    base = weighted_dist[u] + weighted_dist[v]
                    out.append(f'{base + c0} {base + c1}')
    return '\n'.join(out) + '\n'
