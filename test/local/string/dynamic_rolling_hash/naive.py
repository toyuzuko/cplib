from __future__ import annotations

MOD = 2 ** 61 - 1
BASE = 3


def calc_hash(chars: list[str], l: int, r: int) -> int:
    value = 0
    power = 1
    for i in range(l, r):
        value = (value + power * ord(chars[i])) % MOD
        power = power * BASE % MOD
    return value


def find_pattern(chars: list[str], pattern: str, l: int, r: int) -> int:
    m = len(pattern)
    if r - l < m:
        return -1
    target = list(pattern)
    for i in range(l, r - m + 1):
        if chars[i:i + m] == target:
            return i
    return -1


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    chars = list(lines[1].strip())
    out: list[str] = []
    for line in lines[2:2 + q]:
        parts = line.split()
        if parts[0] == 'SET':
            chars[int(parts[1])] = parts[2]
        elif parts[0] == 'HASH':
            out.append(str(calc_hash(chars, int(parts[1]), int(parts[2]))))
        else:
            out.append(str(find_pattern(chars, parts[1], int(parts[2]), int(parts[3]))))
    assert len(chars) == n
    return '\n'.join(out) + ('\n' if out else '')
