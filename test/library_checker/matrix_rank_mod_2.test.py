# verification-helper: PROBLEM https://judge.yosupo.jp/problem/matrix_rank_mod_2

from cplib.mathematics.matrix import MatrixBit, BitSet
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
FastIO.read_line() # Skip the first nextline.

if N < M:
    bitsets = [BitSet(M) for _ in range(N)]
    for i in range(N):
        bits = FastIO.read_line()
        for j in range(M):
            if bits[j] == '1':
                bitsets[i].add(j)
    a = MatrixBit.from_bitset(N, M, bitsets)
else:
    bitsets = [BitSet(N) for _ in range(M)]
    for i in range(N):
        bits = FastIO.read_line()
        for j in range(M):
            if bits[j] == '1':
                bitsets[j].add(i)
    a = MatrixBit.from_bitset(M, N, bitsets)

FastIO.writeln(f'{a.rank()}')