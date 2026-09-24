# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/1/ALDS1_1_B

from math import gcd

from cplib.tools.fastio import FastIO


x, y = FastIO.read_ints(2)
FastIO.writeln(f'{gcd(x, y)}')
