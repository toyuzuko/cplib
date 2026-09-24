# verification-helper: PROBLEM https://judge.yosupo.jp/problem/suffixarray

from cplib.string.suffix import SuffixArray


S = input()
suffix_array = SuffixArray(S)

print(' '.join(map(str, suffix_array.arr)))