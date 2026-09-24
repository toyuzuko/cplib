# verification-helper: PROBLEM https://judge.yosupo.jp/problem/two_square_sum

from cplib.mathematics.arithmetic import two_square_sum
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    N = FastIO.read_int()
    ans = two_square_sum(N)
    FastIO.writeln(f'{len(ans)}')
    for x, y in ans:
        FastIO.writeln(f'{x} {y}')
