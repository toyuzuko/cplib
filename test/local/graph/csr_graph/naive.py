from __future__ import annotations


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, m, is_directed, is_weighted = map(int, lines[0].split())
    graph: list[list[tuple[int, int, int]]] = [[] for _ in range(n)]
    for i, line in enumerate(lines[1:1 + m]):
        if is_weighted:
            u, v, w = map(int, line.split())
        else:
            u, v = map(int, line.split())
            w = 1
        graph[u].append((v, i, w))
        if not is_directed:
            graph[v].append((u, i, w))

    out: list[str] = []
    for edges in graph:
        row = [str(len(edges))]
        for v, edge_id, weight in edges:
            row.append(str(v))
            row.append(str(edge_id))
            row.append(str(weight))
        out.append(' '.join(row))
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
