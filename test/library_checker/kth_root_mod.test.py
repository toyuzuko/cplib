# verification-helper: PROBLEM https://judge.yosupo.jp/problem/kth_root_mod

from cplib.mathematics.modular import kth_root_mod
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    K, Y, P = FastIO.read_ints(3)
    FastIO.writeln(f'{kth_root_mod(K, Y, P)}')
