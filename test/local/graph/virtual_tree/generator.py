from __future__ import annotations

import random

from config import K_MAX, N_MAX


def generate_testcase() -> str:
    n = random.randint(1, N_MAX)
    parents = [random.randrange(v) for v in range(1, n)]
    k = random.randint(0, min(n, K_MAX))
    vertices = random.sample(range(n), k)
    lines = [f"{n} {k}"]
    if n > 1:
        lines.append(" ".join(map(str, parents)))
    lines.append(" ".join(map(str, vertices)))
    return "\n".join(lines) + "\n"
