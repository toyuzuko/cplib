# verification-helper: PROBLEM https://judge.yosupo.jp/problem/stirling_number_of_the_second_kind_fixed_k

from cplib.mathematics.combinatorics import enumerate_stirling_number_second


N, K = map(int, input().split())
result = enumerate_stirling_number_second(N, K)
print(' '.join(map(str, result[K:])))