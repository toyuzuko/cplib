# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/7/ITP1_7_A

from cplib.tools.fastio import FastIO


while True:
    m, f, r = FastIO.read_ints(3)
    if m == -1 and f == -1 and r == -1:
        break
    score = m + f
    if m == -1 or f == -1 or score < 30:
        grade = 'F'
    elif score >= 80:
        grade = 'A'
    elif score >= 65:
        grade = 'B'
    elif score >= 50 or r >= 50:
        grade = 'C'
    else:
        grade = 'D'
    FastIO.writeln(grade)
