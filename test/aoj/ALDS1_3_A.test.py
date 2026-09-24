# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/3/ALDS1_3_A

import sys

from cplib.tools.fastio import FastIO


stack: list[int] = []

for token in sys.stdin.buffer.read().split():
    if token == b'+':
        b = stack.pop()
        a = stack.pop()
        stack.append(a + b)
    elif token == b'-':
        b = stack.pop()
        a = stack.pop()
        stack.append(a - b)
    elif token == b'*':
        b = stack.pop()
        a = stack.pop()
        stack.append(a * b)
    else:
        stack.append(int(token))

FastIO.writeln(f'{stack[-1]}')
