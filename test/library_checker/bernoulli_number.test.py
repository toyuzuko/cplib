# verification-helper: PROBLEM https://judge.yosupo.jp/problem/bernoulli_number

from cplib.mathematics.combinatorics import enumerate_bernoulli_number


N = int(input())

result = enumerate_bernoulli_number(N)

print(' '.join(map(str, result)))