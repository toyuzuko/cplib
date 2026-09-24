# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/15/ALDS1_15_D

from cplib.algorithm.greedy import huffman_encoded_length
from cplib.tools.fastio import FastIO


S = FastIO.read()
counts = [0] * 26
for c in S:
    counts[ord(c) - ord('a')] += 1

FastIO.writeln(f'{huffman_encoded_length(counts)}')
