from __future__ import annotations

from dataclasses import dataclass
import random

from config import M_MAX, N_MAX, WEIGHT_MAX


@dataclass(frozen=True, slots=True)
class Case:
    vertex_count: int
    edges: tuple[tuple[int, int, int], ...]


def generate_case(rng: random.Random) -> Case:
    vertex_count = rng.randint(2, N_MAX)
    max_edges = min(M_MAX, vertex_count * (vertex_count - 1) // 2)
    edge_count = rng.randint(1, max_edges)
    pairs = [(u, v) for u in range(vertex_count) for v in range(u + 1, vertex_count)]
    chosen_pairs = rng.sample(pairs, edge_count)
    edges = tuple(
        (u, v, rng.randint(1, WEIGHT_MAX))
        for u, v in chosen_pairs
    )
    return Case(vertex_count=vertex_count, edges=edges)
