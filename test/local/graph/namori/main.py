from cplib.graph.core import Graph
from cplib.graph.families import Namori


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    graph = Graph(n)
    for line in lines[1:1 + n]:
        u, v, w = map(int, line.split())
        graph.add_edge(u, v, w)
    namori = Namori(graph)
    out: list[str] = []
    for line in lines[1 + n:1 + n + q]:
        parts = line.split()
        op = parts[0]
        if op == 'ON':
            out.append(str(int(namori.is_on_cycle(int(parts[1])))))
        elif op == 'ROOT':
            out.append(str(namori.cycle_root(int(parts[1]))))
        elif op == 'DIST':
            out.append(str(namori.hops_to_cycle(int(parts[1]))))
        elif op == 'SUB':
            l, r = namori.subtree_range(int(parts[1]))
            out.append(' '.join(map(str, sorted(namori.branch_order[l:r]))))
        else:
            u = int(parts[1])
            v = int(parts[2])
            if op == 'SAME':
                out.append(str(int(namori.same_branch(u, v))))
            elif op == 'ANC':
                out.append(str(int(namori.is_ancestor_in_branch(u, v))))
            elif op == 'LCA':
                out.append(str(namori.branch_lca(u, v)))
            elif op == 'SEG':
                segments = namori.branch_path_ranges(u, v)
                if segments is None:
                    out.append('None')
                else:
                    nodes = sorted(namori.branch_hld_rev[i] for l, r in segments for i in range(l, r))
                    out.append(' '.join(map(str, nodes)))
            elif op == 'ESEG':
                segments = namori.branch_path_ranges(u, v, edge_query=True)
                if segments is None:
                    out.append('None')
                else:
                    nodes = sorted(namori.branch_hld_rev[i] for l, r in segments for i in range(l, r))
                    out.append(' '.join(map(str, nodes)))
            elif op == 'D':
                out.append(str(namori.hops(u, v)))
            elif op == 'WD':
                out.append(str(namori.dist(u, v)))
            elif op == 'PL':
                out.append('%d %d' % namori.path_length(u, v))
            elif op == 'WPL':
                out.append('%d %d' % namori.weighted_path_length(u, v))
            elif op == 'CD':
                out.append(str(namori.cycle_hops(u, v)))
            else:
                out.append(str(namori.cycle_dist(u, v)))
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
