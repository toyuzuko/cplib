from __future__ import annotations

from dataclasses import dataclass

from cplib.heuristic.neighborhood import Move, Neighborhood

from scenario import Case, SwapOp, UndoOp
from score import total_score


def _swap_delta(values: list[int], left: int, right: int) -> float:
    if left > right:
        left, right = right, left

    n = len(values)
    old_score = 0
    new_score = 0
    affected = {left - 1, left, right - 1, right}
    swapped_left = values[right]
    swapped_right = values[left]
    for index in affected:
        if 0 <= index < n - 1:
            old_score += abs(values[index] - values[index + 1])
            left_value = swapped_left if index == left else swapped_right if index == right else values[index]
            right_value = (
                swapped_left
                if index + 1 == left
                else swapped_right
                if index + 1 == right
                else values[index + 1]
            )
            new_score += abs(left_value - right_value)
    return float(new_score - old_score)


@dataclass(slots=True)
class SwapMove:
    left: int
    right: int
    delta: float

    def apply(self, state: list[int]) -> None:
        state[self.left], state[self.right] = state[self.right], state[self.left]

    def revert(self, state: list[int]) -> None:
        state[self.left], state[self.right] = state[self.right], state[self.left]

    def score_delta(self) -> float:
        return self.delta


def solve_case(case: Case) -> list[int]:
    state = list(case.values)
    neighborhood = Neighborhood(state, float(total_score(state)))
    history: list[SwapMove] = []
    outputs: list[int] = []

    for op in case.operations:
        if isinstance(op, SwapOp):
            move = SwapMove(op.left, op.right, _swap_delta(state, op.left, op.right))
            assert isinstance(move, Move)
            neighborhood.apply(move)
            history.append(move)
        elif isinstance(op, UndoOp):
            move = history.pop()
            neighborhood.revert(move)
        else:
            outputs.append(int(neighborhood.score))

    return outputs
