from __future__ import annotations

import random

from config import (
    OP_TYPE_MAX,
    Q_MAX,
    VALUE_ABS_MAX,
    WINDOW_LEFT_MAX,
    WINDOW_LEFT_MIN,
    WINDOW_RIGHT_MAX,
)


def generate_testcase() -> str:
    q = random.randint(1, Q_MAX)
    lines = [str(q)]
    for _ in range(q):
        typ = random.randint(0, OP_TYPE_MAX)
        if typ <= 3:
            lines.append(f"{typ} {random.randint(-VALUE_ABS_MAX, VALUE_ABS_MAX)}")
        elif typ == 4:
            left = random.randint(WINDOW_LEFT_MIN, WINDOW_LEFT_MAX)
            right = random.randint(left, WINDOW_RIGHT_MAX)
            lines.append(f"{typ} {left} {right}")
        elif typ <= 6:
            lines.append(str(typ))
        else:
            lines.append(f"{typ} {random.randint(-VALUE_ABS_MAX, VALUE_ABS_MAX)}")
    return "\n".join(lines) + "\n"


def generate_max_testcase() -> str:
    """
    Generate a maximum-query stress testcase.

    Returns:
        Input text with exactly ``Q_MAX`` operations.

    Time Complexity:
        O(Q_MAX).

    Space Complexity:
        O(Q_MAX).
    """
    q = Q_MAX
    lines = [str(q)]
    for i in range(q):
        typ = i % (OP_TYPE_MAX + 1)
        if typ <= 3:
            value = random.choice((-VALUE_ABS_MAX, VALUE_ABS_MAX))
            lines.append(f"{typ} {value}")
        elif typ == 4:
            lines.append(f"{typ} {WINDOW_LEFT_MIN} {WINDOW_RIGHT_MAX}")
        elif typ <= 6:
            lines.append(str(typ))
        else:
            value = random.choice((-VALUE_ABS_MAX, VALUE_ABS_MAX))
            lines.append(f"{typ} {value}")
    return "\n".join(lines) + "\n"
