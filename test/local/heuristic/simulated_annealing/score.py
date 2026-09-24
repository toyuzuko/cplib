from __future__ import annotations

from scenario import Case


def validate_and_score(case: Case, solution: list[int]) -> int:
    if len(solution) != case.vertex_count:
        raise ValueError('solution length does not match N')
    if any(value not in (0, 1) for value in solution):
        raise ValueError('solution must be a 0/1 assignment')

    total = 0
    for u, v, weight in case.edges:
        if solution[u] != solution[v]:
            total += weight
    return total


def total_weight(case: Case) -> int:
    return sum(weight for _, _, weight in case.edges)
