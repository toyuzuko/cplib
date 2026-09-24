from __future__ import annotations

from cplib.graph.base import Node, Weight
from cplib.graph.core import CSRGraph


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, m, is_directed, is_weighted = map(int, lines[0].split())
    if is_weighted:
        edges = []
        for line in lines[1:1 + m]:
            u, v, w = map(int, line.split())
            edges.append((Node(u), Node(v), Weight(w)))
    else:
        edges = []
        for line in lines[1:1 + m]:
            u, v = map(int, line.split())
            edges.append((Node(u), Node(v)))

    graph = CSRGraph(n, edges, is_directed=bool(is_directed))
    out: list[str] = []
    for v in range(n):
        row: list[str] = [str(graph.out_degree(Node(v)))]
        for i in graph.adjacent_range(Node(v)):
            row.append(str(int(graph.to[i])))
            row.append(str(int(graph.edge_id[i])))
            row.append(str(int(graph.weight[i])))
        out.append(' '.join(row))
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
