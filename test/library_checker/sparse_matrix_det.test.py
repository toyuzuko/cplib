# verification-helper: PROBLEM https://judge.yosupo.jp/problem/sparse_matrix_det

from cplib.mathematics.matrix import SparseMatrixMod
from cplib.tools.fastio import FastIO


N, K = FastIO.read_ints(2)

entries: list[tuple[int, int, int]] = []

for _ in range(K):
    r, c, v = FastIO.read_ints(3)
    entries.append((r, c, v))

A = SparseMatrixMod.from_edges(N, N, entries)

FastIO.writeln(f'{A.determinant()}')
