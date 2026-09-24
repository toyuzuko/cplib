from __future__ import annotations

from dataclasses import dataclass
import random

from config import N_MAX, Q_MAX, VALUE_ABS_MAX


@dataclass(frozen=True, slots=True)
class SwapOp:
    left: int
    right: int


@dataclass(frozen=True, slots=True)
class UndoOp:
    pass


@dataclass(frozen=True, slots=True)
class QueryOp:
    pass


Operation = SwapOp | UndoOp | QueryOp


@dataclass(frozen=True, slots=True)
class Case:
    values: tuple[int, ...]
    operations: tuple[Operation, ...]


def _random_swap(rng: random.Random, n: int) -> SwapOp:
    left, right = sorted(rng.sample(range(n), 2))
    return SwapOp(left, right)


def generate_case(rng: random.Random) -> Case:
    n = rng.randint(2, N_MAX)
    q = rng.randint(3, Q_MAX)
    values = tuple(rng.randint(-VALUE_ABS_MAX, VALUE_ABS_MAX) for _ in range(n))

    operations: list[Operation] = [_random_swap(rng, n), UndoOp(), QueryOp()]
    depth = 0
    for op in operations:
        if isinstance(op, SwapOp):
            depth += 1
        elif isinstance(op, UndoOp):
            depth -= 1

    while len(operations) < q:
        if depth == 0:
            kind = rng.random()
            if kind < 0.6:
                op = _random_swap(rng, n)
                depth += 1
            else:
                op = QueryOp()
        else:
            kind = rng.random()
            if kind < 0.45:
                op = _random_swap(rng, n)
                depth += 1
            elif kind < 0.70:
                op = UndoOp()
                depth -= 1
            else:
                op = QueryOp()
        operations.append(op)

    return Case(values=values, operations=tuple(operations))
