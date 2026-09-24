# verification-helper: PROBLEM https://judge.yosupo.jp/problem/kth_term_of_linearly_recurrent_sequence

from cplib.mathematics.recurrence import evaluate_linear_recurrence


D, K = map(int, input().split())
A = list(map(int, input().split()))
C = list(map(int, input().split()))

print(evaluate_linear_recurrence(C, A, K))
