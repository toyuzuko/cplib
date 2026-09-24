# verification-helper: PROBLEM https://judge.yosupo.jp/problem/stirling_number_of_the_first_kind

from cplib.mathematics.combinatorics import enumerate_stirling_number_first


N = int(input())
result = enumerate_stirling_number_first(N, None)
print(' '.join(map(str, result)))
