from cplib.graph.base import Node
from cplib.graph import Tree


def solve(inp: str) -> str:
    lines = inp.splitlines()
    n = int(lines[0])
    parents = [] if n == 1 else list(map(int, lines[1].split()))
    colors = list(map(int, lines[2 if n > 1 else 1].split()))

    tree = Tree(n)
    for v in range(1, n):
        tree.add_edge(Node(parents[v - 1]), Node(v))
    tree.build(Node(0))

    children: list[list[int]] = [[] for _ in range(n)]
    for v in range(1, n):
        children[parents[v - 1]].append(v)

    ans = [0] * n
    for root in range(n):
        stack: list[int] = [root]
        used: set[int] = set()
        while stack:
            v = stack.pop()
            used.add(colors[v])
            stack.extend(children[v])
        ans[root] = len(used)
    return " ".join(map(str, ans)) + "\n"
