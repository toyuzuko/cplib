from __future__ import annotations

import random
from config import ALPHABET, LENGTH_MAX


def generate_testcase() -> str:
    length = random.randint(0, LENGTH_MAX)
    s = "".join(random.choice(ALPHABET) for _ in range(length))
    return s + "\n"
