"""Template for custom judging logic.

Choose one of the two sections below and remove or comment the other.

Non-interactive checker:
    Define ``is_accepted(input_data, output, expected) -> bool``.

Interactive judge:
    Define ``InteractiveJudge`` using the API described below.
"""

from __future__ import annotations
import random


# =============================================================================
# A) Non-interactive checker (keep if the problem is NOT interactive)
# =============================================================================
def is_accepted(input_data: str, output: str, expected: str) -> bool:
    """
    Decide whether `output` is correct for *input_data*.

    Adapt when multiple outputs are possible, whitespace differences
    are irrelevant, etc.

    Args:
        input_data: Complete testcase input; unused by this exact checker.
        output: Contestant output.
        expected: Reference output.

    Returns:
        Whether the two output strings match exactly.

    Time Complexity:
        O(L), where L is the shorter output length.

    Space Complexity:
        O(1) auxiliary space.
    """
    return output == expected


# =============================================================================
# B) Interactive judge (keep if the problem IS interactive)
# =============================================================================
class InteractiveJudge:
    """
    Skeleton for writing an interactive judge.

    Attributes:
        init_input: First block sent to the contestant.
        finished: Set to **True** when no further interaction is necessary.
        accepted: Set to **True** if the contestant ultimately solves the task.

    Methods:
        next_input(output): Called each time the contestant outputs a line and
            returns the next line for the contestant, including its newline.
            The final reply is sent even when finished becomes True. Solver
            stdin is then closed. EOF before finished is a wrong answer.
            Callbacks must terminate; their time counts toward the dialogue
            deadline but the tester cannot preempt callback execution.
    """

    # ------------------------------------------------------------------
    def __init__(self) -> None:
        """Start the example game with numbers from 1 through 2*N+1.

        Returns:
            None. N is sampled uniformly from 1 through 1000.

        Time Complexity:
            O(N).

        Space Complexity:
            O(N).
        """
        # ---------------------- EXAMPLE GAME --------------------------
        # Generate parameters that satisfy the constraints
        self.N = random.randint(1, 1000)
        self.limit = 2 * self.N + 1

        # ----------- Initialize the first input line -------------------
        self.init_input: str = f"{self.N}\n"

        # Internal state
        self.finished: bool = False
        self.accepted: bool = False
        self._used = [False] * (self.limit + 1)

    # ------------------------------------------------------------------
    def next_input(self, output: str) -> str:
        """
        Process one contestant line and return the judge's reply.

        Args:
            output: One decimal integer naming an unused number in
                [1, 2*N+1]. Call only while finished is false.

        Returns:
            The smallest remaining number followed by a newline. Returns
            zero followed by a newline and sets finished on an invalid move or when no numbers
            remain. accepted is true only when the contestant wins.

        Time Complexity:
            O(N + L), where L is the output line length, plus the cost of
            converting the decimal integer.

        Space Complexity:
            O(L) for the stripped line and integer conversion.
        """
        # ----------- simple validity checks --------------------------
        s = output.strip()
        try:
            x = int(s) if s.isdecimal() else 0
        except ValueError:
            # Exceeding the interpreter's digit limit is an invalid move too.
            x = 0
        if not (1 <= x <= self.limit) or self._used[x]:
            self.finished = True
            self.accepted = False
            return "0\n"

        self._used[x] = True

        # Judge (Aoki) picks the smallest remaining number
        for y in range(1, self.limit + 1):
            if not self._used[y]:
                self._used[y] = True
                return f"{y}\n"

        # Aoki cannot move → contestant wins
        self.finished = True
        self.accepted = True
        return "0\n"
