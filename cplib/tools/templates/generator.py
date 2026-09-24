"""Random testcase generator template for non-interactive tasks.

Edit ``generate_testcase()`` to follow the exact input format and constraints
of your problem.
"""

from __future__ import annotations
import random


def generate_testcase() -> str:
    """
    Create ONE random input and return it as a string.

    Returns:
        Complete input including trailing newline.

    Time Complexity:
        O(1) for this single-integer example with a fixed upper bound.

    Space Complexity:
        O(1) for this example.
    """
    # ---------- EXAMPLE: single integer --------------------------------
    n = random.randint(1, 1000)
    return f"{n}\n"

    # TODO: Replace example with real generator logic.
