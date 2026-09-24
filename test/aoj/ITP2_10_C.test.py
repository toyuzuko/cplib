# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/10/ITP2_10_C

from cplib.mathematics import BitFlagSet
from cplib.tools.fastio import FastIO


q = FastIO.read_int()
flags = BitFlagSet(64)
for _ in range(q):
    op = FastIO.read_int()
    if op == 0:
        i = FastIO.read_int()
        FastIO.writeln('1' if flags.test(i) else '0')
    elif op == 1:
        flags.set_bit(FastIO.read_int())
    elif op == 2:
        flags.clear_bit(FastIO.read_int())
    elif op == 3:
        flags.flip_bit(FastIO.read_int())
    elif op == 4:
        FastIO.writeln('1' if flags.all() else '0')
    elif op == 5:
        FastIO.writeln('1' if flags.any() else '0')
    elif op == 6:
        FastIO.writeln('1' if flags.none() else '0')
    elif op == 7:
        FastIO.writeln(str(flags.count()))
    else:
        FastIO.writeln(str(flags.val()))
