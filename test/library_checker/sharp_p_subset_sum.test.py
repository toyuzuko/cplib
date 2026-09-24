# verification-helper: PROBLEM https://judge.yosupo.jp/problem/sharp_p_subset_sum

from cplib.mathematics.combinatorics import count_all_subset_sums


N, T = map(int, input().split())
S = list(map(int, input().split()))

result = count_all_subset_sums(S, T)

print(' '.join(map(str, result[1:])))