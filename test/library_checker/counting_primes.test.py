# verification-helper: PROBLEM https://judge.yosupo.jp/problem/counting_primes

from cplib.mathematics.summatory import count_primes
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

FastIO.writeln(f'{count_primes(N)}')