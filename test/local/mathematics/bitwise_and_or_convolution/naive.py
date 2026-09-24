from __future__ import annotations

from config import MOD


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n = int(lines[0])
    a = list(map(int, lines[1].split()))
    b = list(map(int, lines[2].split()))
    size = 1 << n
    and_conv = [0] * size
    or_conv = [0] * size
    for i in range(size):
        for j in range(size):
            value = a[i] * b[j]
            and_conv[i & j] = (and_conv[i & j] + value) % MOD
            or_conv[i | j] = (or_conv[i | j] + value) % MOD
    return ' '.join(map(str, and_conv)) + '\n' + ' '.join(map(str, or_conv)) + '\n'
