# verification-helper: PROBLEM https://judge.yosupo.jp/problem/montmort_number_mod

from cplib.mathematics.combinatorics import enumerate_montmort_number


N, M = map(int, input().split())

print(*enumerate_montmort_number(N, M)[1:])