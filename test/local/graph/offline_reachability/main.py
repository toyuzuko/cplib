from __future__ import annotations

from cplib.graph.base import Node
from cplib.graph.core import Graph
from cplib.graph.reachability import offline_reachability


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, m, q = map(int, lines[0].split())
    graph = Graph(n, is_directed=True)
    for line in lines[1:1 + m]:
        u, v = map(int, line.split())
        graph.add_edge(Node(u), Node(v))
    queries: list[tuple[Node, Node]] = []
    for line in lines[1 + m:1 + m + q]:
        s, t = map(int, line.split())
        queries.append((Node(s), Node(t)))
    answers = offline_reachability(graph, queries, block_size=32)
    return '\n'.join('1' if answer else '0' for answer in answers) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
