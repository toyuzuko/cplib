from __future__ import annotations

import config
from cplib.heuristic.random import XorShift
from cplib.heuristic.simulated_annealing import (
    AnnealingRng,
    AnnealingSchedule,
    SimulatedAnnealing,
)
from scenario import Case


def _score(case: Case, assignment: list[int]) -> float:
    total = 0
    for u, v, weight in case.edges:
        if assignment[u] != assignment[v]:
            total += weight
    return float(total)


def _copy_assignment(assignment: list[int]) -> list[int]:
    return assignment.copy()


def solve_case(case: Case) -> list[int]:
    rng = XorShift(case.vertex_count + len(case.edges))
    initial_state = [rng.randrange(2) for _ in range(case.vertex_count)]

    def generate_neighbor(state: list[int], annealing_rng: AnnealingRng) -> list[int]:
        index = annealing_rng.randrange(case.vertex_count)
        state[index] ^= 1
        if case.vertex_count >= 2 and annealing_rng.random() < 0.2:
            other = annealing_rng.randrange(case.vertex_count - 1)
            if other >= index:
                other += 1
            state[other] ^= 1
        return state

    solver = SimulatedAnnealing[list[int]](
        evaluate=lambda assignment: _score(case, assignment),
        generate_neighbor=generate_neighbor,
        schedule=AnnealingSchedule(
            start_temp=config.START_TEMP,
            end_temp=config.END_TEMP,
        ),
        rng=rng,
        copy_state=_copy_assignment,
    )
    result = solver.run(
        initial_state=initial_state,
        iterations=max(1, config.ITERATIONS_PER_VERTEX * case.vertex_count),
    )
    return result.best_state


def solve(inp: str) -> str:
    tokens = list(map(int, inp.split()))
    position = 0
    vertex_count = tokens[position]
    position += 1
    edge_count = tokens[position]
    position += 1
    edges: list[tuple[int, int, int]] = []
    for _ in range(edge_count):
        u = tokens[position] - 1
        v = tokens[position + 1] - 1
        weight = tokens[position + 2]
        position += 3
        edges.append((u, v, weight))
    case = Case(vertex_count=vertex_count, edges=tuple(edges))
    answer = solve_case(case)
    return ' '.join(map(str, answer)) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
