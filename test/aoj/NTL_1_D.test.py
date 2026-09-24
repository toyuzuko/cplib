# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/6/NTL/1/NTL_1_D

from cplib.mathematics.factorization import PrimeFactor
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

FastIO.writeln(f'{PrimeFactor.totient(N)}')
