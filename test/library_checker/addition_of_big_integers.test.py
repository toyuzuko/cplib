# verification-helper: PROBLEM https://judge.yosupo.jp/problem/addition_of_big_integers

from cplib.mathematics.bigint import BigInt
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    a = BigInt(FastIO.read())
    b = BigInt(FastIO.read())
    c = a + b
    FastIO.writeln(f'{c}')
