from cplib.graph.families import FunctionalGraph


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    to = list(map(int, lines[1].split()))
    vertex_values = list(map(int, lines[2].split()))
    edge_values = list(map(int, lines[3].split()))
    fg = FunctionalGraph(to)
    vertex_fg = FunctionalGraph.from_vertex_values(to, vertex_values, lambda a, b: a + b, 0)
    edge_fg = FunctionalGraph.from_edge_values(to, edge_values, lambda a, b: a + b, 0)
    out: list[str] = []
    for line in lines[4:4 + q]:
        parts = line.split()
        op = parts[0]
        v = int(parts[1])
        if op == 'J':
            out.append(str(fg.jump(v, int(parts[2]))))
        elif op == 'G':
            out.append(str(fg.get(v, int(parts[2]))))
        elif op == 'PV':
            out.append(str(vertex_fg.prod(v, int(parts[2]))))
        elif op == 'PE':
            out.append(str(edge_fg.prod(v, int(parts[2]))))
        elif op == 'CID':
            out.append(str(fg.cycle_id(v)))
        elif op == 'CLEN':
            out.append(str(fg.cycle_length(v)))
        elif op == 'DIST':
            out.append(str(fg.hops_to_cycle(v)))
        elif op == 'ON':
            out.append(str(int(fg.is_on_cycle(v))))
        else:
            out.append(str(fg.cycle_entry(v)))
    assert len(to) == n
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
