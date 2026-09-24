# verification-helper: PROBLEM https://judge.yosupo.jp/problem/longest_increasing_subsequence

from cplib.sequence.subseq import longest_increasing_subsequence
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = list(FastIO.read_ints(N))

indices = longest_increasing_subsequence(A, return_idx=True)

FastIO.writeln(f'{len(indices)}')
FastIO.writeln(' '.join(map(str, indices)))
