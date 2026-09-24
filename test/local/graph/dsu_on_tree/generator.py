from __future__ import annotations

import random

from config import COLOR_MAX, N_MAX


def generate_testcase() -> str:
    n = random.randint(1, N_MAX)
    parents = [random.randrange(v) for v in range(1, n)]
    colors = [random.randint(0, COLOR_MAX) for _ in range(n)]
    lines = [str(n)]
    if n > 1:
        lines.append(" ".join(map(str, parents)))
    lines.append(" ".join(map(str, colors)))
    return "\n".join(lines) + "\n"
