# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/9/ALDS1_9_A

from cplib.tools.fastio import FastIO


H = FastIO.read_int()
A = FastIO.read_ints(H)

for i in range(1, H + 1):
    parts = [f'node {i}: key = {A[i - 1]},']
    if i // 2 >= 1:
        parts.append(f'parent key = {A[i // 2 - 1]},')
    if i * 2 <= H:
        parts.append(f'left key = {A[i * 2 - 1]},')
    if i * 2 + 1 <= H:
        parts.append(f'right key = {A[i * 2]},')
    FastIO.writeln(' '.join(parts) + ' ')
