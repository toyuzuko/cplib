from __future__ import annotations

from config import BRUTE_BOUND, SAMPLE_LEFT, SAMPLE_RIGHT

INF: int = 10**18
POINTS: tuple[int, ...] = tuple(range(-BRUTE_BOUND, BRUTE_BOUND + 1))
SAMPLE_POINTS: tuple[int, ...] = tuple(range(SAMPLE_LEFT, SAMPLE_RIGHT + 1))


def parse_query(line: str) -> tuple[int, ...]:
    """Parse one operation line into a tuple of integers."""
    parts: list[str] = line.split()
    return tuple(int(part) for part in parts)


def dump_state(values: list[int]) -> str:
    minimum = min(values)
    sample = " ".join(str(values[x + BRUTE_BOUND]) for x in SAMPLE_POINTS)
    return f"{minimum} {sample}"


def shift_values(values: list[int], delta: int) -> list[int]:
    moved = [0] * len(values)
    for i, x in enumerate(POINTS):
        src = x - delta
        if -BRUTE_BOUND <= src <= BRUTE_BOUND:
            moved[i] = values[src + BRUTE_BOUND]
        else:
            moved[i] = INF
    return moved


def sliding_window_min(values: list[int], left: int, right: int) -> list[int]:
    moved = [0] * len(values)
    for i, x in enumerate(POINTS):
        start = max(x - right, -BRUTE_BOUND)
        end = min(x - left, BRUTE_BOUND)
        best = INF
        for y in range(start, end + 1):
            best = min(best, values[y + BRUTE_BOUND])
        moved[i] = best
    return moved


def prefix_min(values: list[int]) -> list[int]:
    moved = values[:]
    for i in range(1, len(moved)):
        moved[i] = min(moved[i], moved[i - 1])
    return moved


def suffix_min(values: list[int]) -> list[int]:
    moved = values[:]
    for i in range(len(moved) - 2, -1, -1):
        moved[i] = min(moved[i], moved[i + 1])
    return moved


def solve(inp: str) -> str:
    lines: list[str] = inp.splitlines()
    q = int(lines[0])
    values: list[int] = [0] * len(POINTS)
    out: list[str] = [dump_state(values)]
    for i in range(1, q + 1):
        query = parse_query(lines[i])
        typ = query[0]
        if typ == 0:
            values = [value + max(x - query[1], 0) for x, value in zip(POINTS, values)]
        elif typ == 1:
            values = [value + max(query[1] - x, 0) for x, value in zip(POINTS, values)]
        elif typ == 2:
            values = [value + abs(x - query[1]) for x, value in zip(POINTS, values)]
        elif typ == 3:
            values = shift_values(values, query[1])
        elif typ == 4:
            values = sliding_window_min(values, query[1], query[2])
        elif typ == 5:
            values = prefix_min(values)
        elif typ == 6:
            values = suffix_min(values)
        else:
            values = [value + query[1] for value in values]
        out.append(dump_state(values))
    return "\n".join(out) + "\n"
