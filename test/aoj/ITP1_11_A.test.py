# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/11/ITP1_11_A

from cplib.tools.fastio import FastIO


dice = list(FastIO.read_ints(6))
for op in FastIO.read():
    if op == 'N':
        dice[0], dice[1], dice[5], dice[4] = dice[1], dice[5], dice[4], dice[0]
    elif op == 'S':
        dice[0], dice[1], dice[5], dice[4] = dice[4], dice[0], dice[1], dice[5]
    elif op == 'E':
        dice[0], dice[2], dice[5], dice[3] = dice[3], dice[0], dice[2], dice[5]
    else:
        dice[0], dice[2], dice[5], dice[3] = dice[2], dice[5], dice[3], dice[0]
FastIO.writeln(f'{dice[0]}')
