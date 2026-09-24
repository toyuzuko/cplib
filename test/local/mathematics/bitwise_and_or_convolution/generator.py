from __future__ import annotations

import random

from config import N_MAX, VALUE_MAX


def generate_testcase() -> str:
    n = random.randint(0, N_MAX)
    size = 1 << n
    a = [random.randint(0, VALUE_MAX) for _ in range(size)]
    b = [random.randint(0, VALUE_MAX) for _ in range(size)]
    return '\n'.join((str(n), ' '.join(map(str, a)), ' '.join(map(str, b)))) + '\n'
