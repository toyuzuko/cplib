# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/10/ITP2_10_D

from cplib.mathematics import BitFlagSet, bitmask_from_indices
from cplib.tools.fastio import FastIO


n = FastIO.read_int()
masks: list[int] = []
for _ in range(n):
    k = FastIO.read_int()
    masks.append(bitmask_from_indices(FastIO.read_int() for _ in range(k)))

q = FastIO.read_int()
flags = BitFlagSet(64)
for _ in range(q):
    op = FastIO.read_int()
    x = FastIO.read_int()
    if op == 0:
        FastIO.writeln('1' if flags.test(x) else '0')
        continue
    mask = masks[x]
    if op == 1:
        flags.set_mask(mask)
    elif op == 2:
        flags.clear_mask(mask)
    elif op == 3:
        flags.flip_mask(mask)
    elif op == 4:
        FastIO.writeln('1' if flags.all(mask) else '0')
    elif op == 5:
        FastIO.writeln('1' if flags.any(mask) else '0')
    elif op == 6:
        FastIO.writeln('1' if flags.none(mask) else '0')
    elif op == 7:
        FastIO.writeln(str(flags.count(mask)))
    else:
        FastIO.writeln(str(flags.val(mask)))
