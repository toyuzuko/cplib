# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/7/ITP1_7_B

from cplib.tools.fastio import FastIO


while True:
    n, x = FastIO.read_ints(2)
    if n == 0 and x == 0:
        break
    ans = 0
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            k = x - i - j
            if j < k <= n:
                ans += 1
    FastIO.writeln(f'{ans}')
