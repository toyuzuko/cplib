# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/7/ITP1_7_C

from cplib.tools.fastio import FastIO


r, c = FastIO.read_ints(2)
col_sum = [0] * c
total = 0
for _ in range(r):
    row = list(FastIO.read_ints(c))
    row_sum = sum(row)
    for j, x in enumerate(row):
        col_sum[j] += x
    total += row_sum
    FastIO.writeln(' '.join(map(str, row + [row_sum])))
FastIO.writeln(' '.join(map(str, col_sum + [total])))
