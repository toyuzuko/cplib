# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/2/ITP1_2_A

from cplib.tools.fastio import FastIO


a, b = FastIO.read_ints(2)
if a < b:
    op = '<'
elif a > b:
    op = '>'
else:
    op = '=='
FastIO.writeln(f'a {op} b')
