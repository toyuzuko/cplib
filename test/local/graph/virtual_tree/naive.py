from cplib.graph.base import Node
from cplib.graph import Tree


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

    if not vertices:
        return "0\n\n0\n"

    in_closure = set(vertices)

    def lca(u: int, v: int) -> int:
        while tree.dep[u] > tree.dep[v]:
            u = tree.par_v[u]
        while tree.dep[v] > tree.dep[u]:
            v = tree.par_v[v]
        while u != v:
            u = tree.par_v[u]
            v = tree.par_v[v]
        return u

    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            in_closure.add(lca(vertices[i], vertices[j]))

    nodes = sorted(in_closure)
    edges: list[tuple[int, int, int]] = []
    root = min(nodes, key=lambda v: tree.dep[v])
    for v in nodes:
        if v == root:
            continue
        p = tree.par_v[v]
        while p not in in_closure:
            p = tree.par_v[p]
        edges.append((p, v, tree.dep[v] - tree.dep[p]))
    edges.sort()

    out = [str(len(nodes))]
    out.append(" ".join(map(str, nodes)))
    out.append(str(len(edges)))
    out.extend(f"{u} {v} {w}" for u, v, w in edges)
    return "\n".join(out) + "\n"
