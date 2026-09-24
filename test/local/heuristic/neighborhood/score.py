from __future__ import annotations

from scenario import Case, SwapOp, UndoOp


def total_score(values: list[int]) -> int:
    return sum(abs(values[i] - values[i + 1]) for i in range(len(values) - 1))


def solve_case(case: Case) -> list[int]:
    state = list(case.values)
    history: list[tuple[int, int]] = []
    outputs: list[int] = []

    for op in case.operations:
        if isinstance(op, SwapOp):
            state[op.left], state[op.right] = state[op.right], state[op.left]
            history.append((op.left, op.right))
        elif isinstance(op, UndoOp):
            left, right = history.pop()
            state[left], state[right] = state[right], state[left]
        else:
            outputs.append(total_score(state))

    return outputs
