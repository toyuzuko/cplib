# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/2/ALDS1_2_C

from cplib.algorithm.sort import bubble_sort, selection_sort
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
cards = [FastIO.read() for _ in range(N)]

stable = sorted(cards, key=lambda card: int(card[1:]))
bubble = bubble_sort(cards, key=lambda card: int(card[1:]))
selection = selection_sort(cards, key=lambda card: int(card[1:]))

FastIO.writeln(' '.join(bubble))
FastIO.writeln('Stable' if bubble == stable else 'Not stable')
FastIO.writeln(' '.join(selection))
FastIO.writeln('Stable' if selection == stable else 'Not stable')
