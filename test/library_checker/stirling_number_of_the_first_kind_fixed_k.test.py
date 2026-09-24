# verification-helper: PROBLEM https://judge.yosupo.jp/problem/stirling_number_of_the_first_kind_fixed_k

from cplib.mathematics.combinatorics import enumerate_stirling_number_first


N, K = map(int, input().split())
result = enumerate_stirling_number_first(N, K)
print(' '.join(map(str, result[K:])))