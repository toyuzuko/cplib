from __future__ import annotations


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    arr = list(map(int, lines[1].split())) if n else []

    answers: list[str] = []
    for line in lines[2:2 + q]:
        l, r = map(int, line.split())
        values = set(arr[l:r])
        mex = 0
        while mex in values:
            mex += 1
        answers.append(str(mex))
    return '\n'.join(answers) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
