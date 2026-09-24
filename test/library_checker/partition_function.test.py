# verification-helper: PROBLEM https://judge.yosupo.jp/problem/partition_function

from cplib.mathematics.combinatorics import enumerate_partition_number


N = int(input())

print(*enumerate_partition_number(N))