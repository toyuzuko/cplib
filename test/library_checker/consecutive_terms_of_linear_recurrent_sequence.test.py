# verification-helper: PROBLEM https://judge.yosupo.jp/problem/consecutive_terms_of_linear_recurrent_sequence

from cplib.mathematics.recurrence import enumerate_linear_recurrence
from cplib.tools.fastio import FastIO


D, K, M = FastIO.read_ints(3)
A = list(FastIO.read_ints(D))
C = list(FastIO.read_ints(D))

FastIO.writeln(' '.join(map(str, enumerate_linear_recurrence(C, A, K, M))))
