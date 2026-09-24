# verification-helper: PROBLEM https://judge.yosupo.jp/problem/shift_of_sampling_points_of_polynomial

from cplib.mathematics.polynomial import polynomial_shift_sampling


N, M, C = map(int, input().split())
F = list(map(int, input().split()))

result = polynomial_shift_sampling(N, M, F, C)

print(' '.join(map(str, result)))