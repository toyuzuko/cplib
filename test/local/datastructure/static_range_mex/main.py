from __future__ import annotations

from cplib.sequence.rangestat import OfflineStaticRangeMexQuery


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    arr = list(map(int, lines[1].split())) if n else []
    queries = [tuple(map(int, line.split())) for line in lines[2:2 + q]]

    solver = OfflineStaticRangeMexQuery(n, arr)
    return '\n'.join(map(str, solver.solve(queries))) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
