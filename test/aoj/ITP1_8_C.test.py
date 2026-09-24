# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/8/ITP1_8_C

import sys


counts = [0] * 26
for ch in sys.stdin.read().lower():
    if 'a' <= ch <= 'z':
        counts[ord(ch) - ord('a')] += 1

for i, count in enumerate(counts):
    print(f'{chr(ord("a") + i)} : {count}')
