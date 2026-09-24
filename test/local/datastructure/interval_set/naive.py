from __future__ import annotations


def sorted_intervals(values: set[int]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for x in sorted(values):
        if not result or result[-1][1] != x:
            result.append((x, x + 1))
        else:
            l, _ = result[-1]
            result[-1] = (l, x + 1)
    return result


def find_point(values: set[int], p: int) -> int:
    for i, (l, r) in enumerate(sorted_intervals(values)):
        if l <= p < r:
            return i
    return -1


def mex(values: set[int], p: int) -> int:
    while p in values:
        p += 1
    return p


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    q = int(lines[0])
    values: set[int] = set()
    out: list[str] = []
    for line in lines[1:1 + q]:
        parts = line.split()
        op = parts[0]
        if op == 'ADD':
            l = int(parts[1])
            r = int(parts[2])
            for x in range(l, r):
                values.add(x)
        elif op == 'REM':
            l = int(parts[1])
            r = int(parts[2])
            for x in range(l, r):
                values.discard(x)
        elif op == 'CON':
            out.append(str(int(int(parts[1]) in values)))
        elif op == 'FIND':
            out.append(str(find_point(values, int(parts[1]))))
        elif op == 'LEN':
            out.append(str(len(sorted_intervals(values))))
        elif op == 'COV':
            out.append(str(len(values)))
        elif op == 'GET':
            i = int(parts[1])
            intervals = sorted_intervals(values)
            if 0 <= i < len(intervals):
                l, r = intervals[i]
                out.append(f'{l} {r}')
            else:
                out.append('None')
        elif op == 'DIS':
            l = int(parts[1])
            r = int(parts[2])
            out.append(str(int(all(x not in values for x in range(l, r)))))
        else:
            out.append(str(mex(values, int(parts[1]))))
    return '\n'.join(out) + '\n'
