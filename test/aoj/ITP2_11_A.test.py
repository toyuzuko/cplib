# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/11/ITP2_11_A

from cplib.mathematics import bitmask_indices, enumerate_bitmasks
from cplib.tools.fastio import FastIO


n = FastIO.read_int()
for mask in enumerate_bitmasks(n):
    elems = ' '.join(str(i) for i in bitmask_indices(mask))
    FastIO.writeln(f'{mask}: {elems}' if elems else f'{mask}:')
