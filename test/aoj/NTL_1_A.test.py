# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/6/NTL/1/NTL_1_A

from cplib.mathematics.factorization import PrimeFactor
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
factors = PrimeFactor.factorize(N)

FastIO.writeln(f'{N}: {" ".join(map(str, factors))}')
