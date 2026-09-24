from cplib.graph.core import Graph
from cplib.graph.families import CactusGraph


def format_blocks(blocks: list[list[int]]) -> str:
    normalized = [tuple(sorted(block)) for block in blocks]
    normalized.sort()
    return '|'.join(' '.join(map(str, block)) for block in normalized)


def common_cycle_block(cactus: CactusGraph, u: int, v: int) -> int:
    blocks = set(cactus.blocks_of(u))
    for block in cactus.blocks_of(v):
        if block in blocks and cactus.is_cycle_block(block):
            return block
    raise AssertionError('no common cycle block')


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, m, q = map(int, lines[0].split())
    graph = Graph(n)
    for line in lines[1:1 + m]:
        u, v, w = map(int, line.split())
        graph.add_edge(u, v, w)
    cactus = CactusGraph(graph)
    out: list[str] = []
    for line in lines[1 + m:1 + m + q]:
        parts = line.split()
        op = parts[0]
        if op == 'BV':
            blocks = [cactus.block_vertices[block] for block in cactus.blocks_of(int(parts[1]))]
            out.append(format_blocks(blocks))
        elif op == 'BE':
            block = cactus.block_of_edge(int(parts[1]))
            out.append(format_blocks([cactus.block_vertices[block]]))
        elif op == 'ART':
            out.append(str(int(cactus.is_articulation(int(parts[1])))))
        elif op == 'ON':
            out.append(str(int(cactus.is_on_cycle(int(parts[1])))))
        elif op == 'SAME':
            out.append(str(int(cactus.same_block(int(parts[1]), int(parts[2])))))
        else:
            u = int(parts[1])
            v = int(parts[2])
            block = common_cycle_block(cactus, u, v)
            out.append(f'{cactus.cycle_hops(block, u, v)} {cactus.cycle_dist(block, u, v)}')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
