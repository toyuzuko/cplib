from __future__ import annotations


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    arr = list(map(int, lines[1].split()))

    answers: list[str] = []
    for line in lines[2:2 + q]:
        l, r = map(int, line.split())
        freq: dict[int, int] = {}
        majority: int | None = None
        for value in arr[l:r]:
            freq[value] = freq.get(value, 0) + 1
            if freq[value] > (r - l) // 2:
                majority = value
        answers.append('NONE' if majority is None else str(majority))
    return '\n'.join(answers) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
