from __future__ import annotations

from dataclasses import dataclass
import random

from config import C_MAX, N_MAX, SCORE_MAX


@dataclass(frozen=True, slots=True)
class Case:
    length: int
    color_count: int
    position_scores: tuple[tuple[int, ...], ...]
    transition_scores: tuple[tuple[int, ...], ...]


def generate_case(rng: random.Random) -> Case:
    length = rng.randint(1, N_MAX)
    color_count = rng.randint(2, C_MAX)
    position_scores = tuple(
        tuple(rng.randint(0, SCORE_MAX) for _ in range(color_count))
        for _ in range(length)
    )
    transition_scores = tuple(
        tuple(rng.randint(0, SCORE_MAX) for _ in range(color_count))
        for _ in range(color_count)
    )
    return Case(
        length=length,
        color_count=color_count,
        position_scores=position_scores,
        transition_scores=transition_scores,
    )
