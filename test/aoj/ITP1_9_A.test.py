# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/9/ITP1_9_A

from cplib.tools.fastio import FastIO


W = FastIO.read().lower()
ans = 0
while True:
    word = FastIO.read()
    if word == 'END_OF_TEXT':
        break
    if word.lower() == W:
        ans += 1
FastIO.writeln(f'{ans}')
