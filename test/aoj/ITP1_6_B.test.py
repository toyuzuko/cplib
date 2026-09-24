# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/6/ITP1_6_B

from cplib.tools.fastio import FastIO


n = FastIO.read_int()
cards: set[tuple[str, int]] = set()
for _ in range(n):
    suit = FastIO.read()
    rank = FastIO.read_int()
    cards.add((suit, rank))

for suit in ('S', 'H', 'C', 'D'):
    for rank in range(1, 14):
        if (suit, rank) not in cards:
            FastIO.writeln(f'{suit} {rank}')
