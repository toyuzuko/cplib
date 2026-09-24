# verification-helper: PROBLEM https://judge.yosupo.jp/problem/find_linear_recurrence

from cplib.mathematics.recurrence import find_linear_recurrence


N = int(input())
A = list(map(int, input().split()))

C = find_linear_recurrence(A)

print(len(C))
print(' '.join(map(str, C)))
