"""Default exact-output checker."""

from __future__ import annotations

from config import SAMPLE_LEFT, SAMPLE_RIGHT

VALUES_PER_LINE = SAMPLE_RIGHT - SAMPLE_LEFT + 2


def is_valid(inp: str, out: str) -> bool:
    """
    Check that stress-mode output has the expected slope-trick dump shape.

    Args:
        inp: Input text.
        out: Output text from ``main.py``.

    Returns:
        True when the output has one integer row per state and the expected
        number of values per row.

    Time Complexity:
        O(Q * W), where Q is the number of operations and W is the number of
        sampled values per output row.

    Space Complexity:
        O(Q * W) for split output tokens.
    """
    lines = inp.splitlines()
    if not lines:
        return out == ''
    try:
        q = int(lines[0])
    except ValueError:
        return False
    out_lines = out.splitlines()
    if len(out_lines) != q + 1:
        return False
    for line in out_lines:
        parts = line.split()
        if len(parts) != VALUES_PER_LINE:
            return False
        try:
            for part in parts:
                int(part)
        except ValueError:
            return False
    return True
