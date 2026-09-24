from __future__ import annotations

import random
from config import ALPHABET, LENGTH_MAX, SPECIAL_CASES, SPECIAL_CASE_RATE


def generate_testcase() -> str:
    if random.random() < SPECIAL_CASE_RATE:
        return random.choice(SPECIAL_CASES) + "\n"
    length = random.randint(0, LENGTH_MAX)
    s = "".join(random.choice(ALPHABET) for _ in range(length))
    return s + "\n"
