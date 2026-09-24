# verification-helper: PROBLEM https://judge.yosupo.jp/problem/nim_product_64

from cplib.mathematics.arithmetic import NimProduct64
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    A, B = FastIO.read_ints(2)
    FastIO.writeln(f'{NimProduct64.multiply(A, B)}')
