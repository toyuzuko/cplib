# verification-helper: PROBLEM https://judge.yosupo.jp/problem/counting_squarefrees

from cplib.mathematics.summatory import count_squarefrees
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

FastIO.writeln(f'{count_squarefrees(N)}')
