# verification-helper: PROBLEM https://judge.yosupo.jp/problem/enumerate_palindromes

from cplib.string.palindrome import manacher

S = input()
palindromes = manacher(S)

print(' '.join(map(str, palindromes)))