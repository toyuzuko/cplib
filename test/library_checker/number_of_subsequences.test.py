# verification-helper: PROBLEM https://judge.yosupo.jp/problem/number_of_subsequences

from cplib.sequence.subseq import number_of_subsequences


MOD = 998244353

N = int(input())
A = list(map(int, input().split()))

result = number_of_subsequences(A, MOD)
result = (result - 1) % MOD  # Exclude the empty subsequence

print(result)
