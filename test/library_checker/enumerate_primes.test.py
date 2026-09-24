# verification-helper: PROBLEM https://judge.yosupo.jp/problem/enumerate_primes

from cplib.mathematics.sieve import enumerate_primes_by_index
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_int()
B = FastIO.read_int()

count, primes = enumerate_primes_by_index(N, A, B)

FastIO.writeln(f'{count} {len(primes)}')
FastIO.writeln(' '.join(map(str, primes)))
