# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/11/ITP1_11_D

from cplib.tools.fastio import FastIO


def roll(dice: tuple[int, ...], op: str) -> tuple[int, ...]:
    a = list(dice)
    if op == 'N':
        a[0], a[1], a[5], a[4] = a[1], a[5], a[4], a[0]
    elif op == 'S':
        a[0], a[1], a[5], a[4] = a[4], a[0], a[1], a[5]
    elif op == 'E':
        a[0], a[2], a[5], a[3] = a[3], a[0], a[2], a[5]
    else:
        a[0], a[2], a[5], a[3] = a[2], a[5], a[3], a[0]
    return tuple(a)


def canonical(dice: tuple[int, ...]) -> tuple[int, ...]:
    seen: set[tuple[int, ...]] = set()
    stack = [dice]
    best = dice
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        if cur < best:
            best = cur
        for op in 'NSEW':
            stack.append(roll(cur, op))
    return best


n = FastIO.read_int()
seen: set[tuple[int, ...]] = set()
ok = True
for _ in range(n):
    key = canonical(tuple(FastIO.read_ints(6)))
    if key in seen:
        ok = False
    seen.add(key)
FastIO.writeln('Yes' if ok else 'No')
