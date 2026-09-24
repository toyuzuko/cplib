# verification-helper: PROBLEM https://judge.yosupo.jp/problem/polynomial_interpolation

from cplib.mathematics.polynomial import polynomial_interpolation


N = map(int, input().split())

X = list(map(int, input().split()))
Y = list(map(int, input().split()))

print(polynomial_interpolation(X, Y))