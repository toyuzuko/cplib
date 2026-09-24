# verification-helper: PROBLEM https://judge.yosupo.jp/problem/factorial

from cplib.mathematics.factorial import LargeFactorialMod
from cplib.tools.fastio import FastIO


T = FastIO.read_int()
N = [FastIO.read_int() for _ in range(T)]

factorial = LargeFactorialMod()
for ans in factorial.factorials(N):
    FastIO.writeln(f'{ans}')
