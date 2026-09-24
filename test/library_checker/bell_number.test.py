# verification-helper: PROBLEM https://judge.yosupo.jp/problem/bell_number

from cplib.mathematics.combinatorics import enumerate_bell_number


N = int(input())

result = enumerate_bell_number(N)

print(' '.join(map(str, result)))