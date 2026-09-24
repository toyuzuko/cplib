"""Reference solution template.

Usage patterns:
    Import mode: The tester imports this file and calls ``solve()``.
    Script mode: Run the tester with ``--naive-script`` so the ``__main__``
        block is executed as a standalone program.
"""

from __future__ import annotations
import sys


# ------------------------------------------------------------------ import-mode
def solve(input_data: str) -> str:
    """
    Compute the correct answer for *input_data*.

    Args:
        input_data: Exactly what would appear on STDIN for one case.

    Returns:
        This echo example returns input_data unchanged, preserving any trailing
        newline. Replace it with the output format required by your problem.

    Time Complexity:
        O(1) for this echo example.

    Space Complexity:
        O(1) auxiliary space for this echo example.
    """
    # -------------- EXAMPLE: echo input -------------------------------
    return input_data

    # TODO: Implement real solution here.


# ------------------------------------------------------------------ script-mode
def _main_script() -> None:
    """Entrypoint when executed as `python naive.py`."""
    data = sys.stdin.read()
    sys.stdout.write(solve(data))

if __name__ == "__main__":
    _main_script()
