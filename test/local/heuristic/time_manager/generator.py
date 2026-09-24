from __future__ import annotations

import random

from config import Q_MAX, START_MAX, TIME_MAX, TIMEOUT_MAX


def generate_testcase() -> str:
    q = random.randint(1, Q_MAX)
    start = random.randint(0, START_MAX)
    timeout = random.randint(0, TIMEOUT_MAX)
    observations = sorted(random.randint(start, TIME_MAX) for _ in range(q))
    lines = [str(q), f"{start} {timeout}", " ".join(map(str, observations))]
    return "\n".join(lines) + "\n"
