# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/11/ITP1_11_B

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


def orientations(dice: tuple[int, ...]) -> set[tuple[int, ...]]:
    res: set[tuple[int, ...]] = set()
    stack = [dice]
    while stack:
        cur = stack.pop()
        if cur in res:
            continue
        res.add(cur)
        for op in 'NSEW':
            stack.append(roll(cur, op))
    return res


dice = tuple(FastIO.read_ints(6))
q = FastIO.read_int()
for _ in range(q):
    top, front = FastIO.read_ints(2)
    for cur in orientations(dice):
        if cur[0] == top and cur[1] == front:
            FastIO.writeln(f'{cur[2]}')
            break
