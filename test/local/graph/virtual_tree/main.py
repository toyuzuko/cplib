from cplib.graph.base import Node
from cplib.graph import Tree
from cplib.graph.treequery import VirtualTreeBuilder


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ""
    n, k = map(int, lines[0].split())
    parent_line = lines[1] if n > 1 else ""
    vertex_line_index = 2 if n > 1 else 1
    vertex_line = lines[vertex_line_index] if vertex_line_index < len(lines) else ""
    parents = [] if n == 1 else list(map(int, parent_line.split()))
    vertices = [] if k == 0 else list(map(int, vertex_line.split()))

    tree = Tree(n)
    for v in range(1, n):
        tree.add_edge(Node(parents[v - 1]), Node(v))
    tree.build(Node(0))

    result = VirtualTreeBuilder(tree).build([Node(v) for v in vertices])
    nodes = sorted(map(int, result.original))
    edges: list[tuple[int, int, int]] = []
    for edge_index in range(result.tree.m):
        u, v = result.tree.edges[edge_index]
        edges.append(
            (
                int(result.original[u]),
                int(result.original[v]),
                int(result.tree.wt[edge_index]),
            )
        )
    edges.sort()

    out = [str(len(nodes))]
    out.append(" ".join(map(str, nodes)))
    out.append(str(len(edges)))
    out.extend(f"{u} {v} {w}" for u, v, w in edges)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
