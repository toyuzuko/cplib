from __future__ import annotations

from cplib.sequence.rangestat import StaticRangeMajorityQuery


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    arr = list(map(int, lines[1].split()))
    solver = StaticRangeMajorityQuery(arr)

    answers: list[str] = []
    for line in lines[2:2 + q]:
        l, r = map(int, line.split())
        value = solver.range_majority(l, r)
        answers.append('NONE' if value is None else str(value))
    return '\n'.join(answers) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
