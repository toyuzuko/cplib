# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/11/ITP2_11_B

from cplib.mathematics import bitmask_from_indices, bitmask_indices, enumerate_supersets
from cplib.tools.fastio import FastIO


n = FastIO.read_int()
k = FastIO.read_int()
base = bitmask_from_indices(FastIO.read_int() for _ in range(k))
for mask in enumerate_supersets(base, n):
    elems = ' '.join(str(i) for i in bitmask_indices(mask))
    FastIO.writeln(f'{mask}: {elems}' if elems else f'{mask}:')
