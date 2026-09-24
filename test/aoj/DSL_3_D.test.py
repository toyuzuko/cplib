# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/3/DSL_3_D

from cplib.datastructure.swag import SlidingWindowAggregation
from cplib.tools.fastio import FastIO


N, L = FastIO.read_ints(2)
A = FastIO.read_ints(N)

swag = SlidingWindowAggregation(min)
answers: list[str] = []

for i, a in enumerate(A):
    swag.push_back(a)
    if i >= L:
        swag.pop_front()
    if i + 1 >= L:
        answers.append(str(swag.all_prod()))

FastIO.writeln(' '.join(answers))
