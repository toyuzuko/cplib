from __future__ import annotations

import random

from config import DELTA_MAX, M_MAX, N_MAX, Q_MAX, TARGET_PADDING


def generate_testcase() -> str:
    n = random.randint(1, N_MAX)
    m = random.randint(1, M_MAX)
    q = random.randint(1, Q_MAX)
    updates = [(random.randrange(n), random.randint(0, DELTA_MAX)) for _ in range(m)]
    lines = [f"{n} {m} {q}"]
    lines.extend(f"{index} {delta}" for index, delta in updates)

    total = [0] * n
    for index, delta in updates:
        total[index] += delta

    for _ in range(q):
        left = random.randrange(n)
        right = random.randint(left + 1, n)
        baseline = sum(total[left:right])
        target = random.randint(0, baseline + TARGET_PADDING)
        lines.append(f"{left} {right} {target}")
    return "\n".join(lines) + "\n"
