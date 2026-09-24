from cplib.datastructure.intervalset import IntervalSet


def format_interval(interval: tuple[int, int] | None) -> str:
    if interval is None:
        return 'None'
    return f'{interval[0]} {interval[1]}'


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    q = int(lines[0])
    intervals = IntervalSet()
    out: list[str] = []
    for line in lines[1:1 + q]:
        parts = line.split()
        op = parts[0]
        if op == 'ADD':
            intervals.add(int(parts[1]), int(parts[2]))
        elif op == 'REM':
            intervals.remove(int(parts[1]), int(parts[2]))
        elif op == 'CON':
            out.append(str(int(intervals.contains(int(parts[1])))))
        elif op == 'FIND':
            out.append(str(intervals.find_point(int(parts[1]))))
        elif op == 'LEN':
            out.append(str(len(intervals)))
        elif op == 'COV':
            out.append(str(intervals.covered_count()))
        elif op == 'GET':
            out.append(format_interval(intervals.get(int(parts[1]))))
        elif op == 'DIS':
            out.append(str(int(intervals.is_disjoint(int(parts[1]), int(parts[2])))))
        else:
            out.append(str(intervals.mex(int(parts[1]))))
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
