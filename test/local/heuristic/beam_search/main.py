from __future__ import annotations

from dataclasses import dataclass

import config
from cplib.heuristic.beam_search import BeamSearch
from scenario import Case


@dataclass(frozen=True, slots=True)
class State:
    sequence: tuple[int, ...]
    score: int
    last_color: int


def solve_case(case: Case) -> list[int]:
    sentinel = case.color_count

    def expand(state: State):
        index = len(state.sequence)
        for color in range(case.color_count):
            gain = case.position_scores[index][color]
            if state.last_color != sentinel:
                gain += case.transition_scores[state.last_color][color]
            yield State(state.sequence + (color,), state.score + gain, color)

    def evaluate(state: State) -> float:
        return float(state.score)

    solver = BeamSearch[State](
        expand=expand,
        evaluate=evaluate,
        beam_width=config.BEAM_WIDTH,
    )
    result = solver.search(
        initial_states=[State((), 0, sentinel)],
        max_depth=case.length,
        is_goal=lambda state: len(state.sequence) == case.length,
    )
    return list(result.best_state.sequence)


def solve(inp: str) -> str:
    tokens = list(map(int, inp.split()))
    position = 0
    length = tokens[position]
    position += 1
    color_count = tokens[position]
    position += 1
    position_scores: list[tuple[int, ...]] = []
    for _ in range(length):
        row = tuple(tokens[position : position + color_count])
        position += color_count
        position_scores.append(row)
    transition_scores: list[tuple[int, ...]] = []
    for _ in range(color_count):
        row = tuple(tokens[position : position + color_count])
        position += color_count
        transition_scores.append(row)
    case = Case(
        length=length,
        color_count=color_count,
        position_scores=tuple(position_scores),
        transition_scores=tuple(transition_scores),
    )
    answer = solve_case(case)
    return ' '.join(map(str, answer)) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
