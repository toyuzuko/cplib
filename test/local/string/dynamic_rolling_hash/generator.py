from __future__ import annotations

import random

from config import ALPHABET, N_MAX, Q_MAX, SPECIAL_CASE_RATE


def add_set(chars: list[str], queries: list[str], i: int, c: str) -> None:
    chars[i] = c
    queries.append(f'SET {i} {c}')


def add_last_match_case(chars: list[str], queries: list[str]) -> None:
    n = len(chars)
    m = random.randint(1, min(4, n))
    l = random.randint(0, n - m)
    r = random.randint(l + m, n)
    start = r - m
    pattern = 'b' if m == 1 else 'b' + 'c' * (m - 1)
    for i in range(l, r):
        add_set(chars, queries, i, 'a')
    for j, c in enumerate(pattern):
        add_set(chars, queries, start + j, c)
    queries.append(f'FIND {pattern} {l} {r}')


def add_no_match_case(queries: list[str], n: int) -> None:
    if n == 0:
        return
    l = random.randint(0, n - 1)
    r = random.randint(l + 1, n)
    pattern = random.choice(('z', 'zz', 'az'))
    queries.append(f'FIND {pattern} {l} {r}')


def generate_testcase() -> str:
    n = random.randint(1, N_MAX)
    chars = [random.choice(ALPHABET) for _ in range(n)]
    initial = ''.join(chars)
    queries: list[str] = []

    add_last_match_case(chars, queries)
    add_no_match_case(queries, n)

    while len(queries) < Q_MAX:
        roll = random.random()
        if roll < SPECIAL_CASE_RATE:
            add_last_match_case(chars, queries)
        elif roll < SPECIAL_CASE_RATE * 2:
            add_no_match_case(queries, n)
        elif roll < 0.6:
            i = random.randrange(n)
            c = random.choice(ALPHABET)
            add_set(chars, queries, i, c)
        elif roll < 0.8:
            l = random.randint(0, n)
            r = random.randint(l, n)
            queries.append(f'HASH {l} {r}')
        else:
            m = random.randint(1, min(5, n))
            l = random.randint(0, n - m)
            r = random.randint(l + m, n)
            if random.random() < 0.5:
                start = random.randint(l, r - m)
                pattern = ''.join(chars[start:start + m])
            else:
                pattern = ''.join(random.choice(ALPHABET) for _ in range(m))
            queries.append(f'FIND {pattern} {l} {r}')

    lines = [f'{n} {len(queries)}', initial]
    lines.extend(queries)
    return '\n'.join(lines) + '\n'
