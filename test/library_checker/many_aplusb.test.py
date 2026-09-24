# verification-helper: PROBLEM https://judge.yosupo.jp/problem/many_aplusb

from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    a = FastIO.read_int()
    b = FastIO.read_int()
    FastIO.writeln(f'{a + b}')
