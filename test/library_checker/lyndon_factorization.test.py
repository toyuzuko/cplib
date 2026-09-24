# verification-helper: PROBLEM https://judge.yosupo.jp/problem/lyndon_factorization

from cplib.string.period import duval


S = input()

boundaries = [left for left, _ in duval(S)]
boundaries.append(len(S))

print(" ".join(map(str, boundaries)))
