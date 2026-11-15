# verification-helper: PROBLEM https://atcoder.jp/contests/abc464/tasks/abc464_g

from cplib.sequence import minimum_non_adjacent_sums
from cplib.tools.fastio import FastIO


for _ in range(FastIO.read_int()):
    n = FastIO.read_int()
    weather = 'S' + FastIO.read() + 'R'
    equal_edges = [i for i in range(n + 1) if weather[i] == weather[i + 1]]
    gaps = [equal_edges[i + 1] - equal_edges[i] for i in range(len(equal_edges) - 1)]
    required = minimum_non_adjacent_sums(gaps)
    base = (n - len(equal_edges)) // 2
    extra = 0
    answers: list[str] = []
    for budget in range(n + 1):
        if extra + 1 < len(required) and required[extra + 1] <= budget:
            extra += 1
        answers.append(f'{base + extra}')
    FastIO.writeln(' '.join(answers))
