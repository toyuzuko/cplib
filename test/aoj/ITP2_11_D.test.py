# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/11/ITP2_11_D

from cplib.mathematics import bitmask_indices, enumerate_combinations
from cplib.tools.fastio import FastIO


n = FastIO.read_int()
k = FastIO.read_int()
for mask in enumerate_combinations(n, k):
    elems = ' '.join(str(i) for i in bitmask_indices(mask))
    FastIO.writeln(f'{mask}: {elems}' if elems else f'{mask}:')
