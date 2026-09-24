# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/6/ALDS1_6_C

from cplib.algorithm.sort import quick_sort
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
cards: list[tuple[int, str]] = []

for _ in range(N):
    suit = FastIO.read()
    value = FastIO.read_int()
    cards.append((value, suit))

sorted_cards = quick_sort(cards, key=lambda card: card[0])
stable_cards = sorted(cards, key=lambda card: card[0])

FastIO.writeln('Stable' if sorted_cards == stable_cards else 'Not stable')
for value, suit in sorted_cards:
    FastIO.writeln(f'{suit} {value}')
