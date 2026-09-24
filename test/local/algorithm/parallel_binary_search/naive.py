from __future__ import annotations


def _parse_update(line: str) -> tuple[int, int]:
    position_str, delta_str = line.split()
    return int(position_str), int(delta_str)


def _parse_query(line: str) -> tuple[int, int, int]:
    left_str, right_str, target_str = line.split()
    return int(left_str), int(right_str), int(target_str)


def solve(inp: str) -> str:
    lines = inp.splitlines()
    n, m, q = map(int, lines[0].split())
    updates: list[tuple[int, int]] = [_parse_update(lines[i]) for i in range(1, m + 1)]
    queries: list[tuple[int, int, int]] = [
        _parse_query(lines[i]) for i in range(m + 1, m + q + 1)
    ]

    answers: list[int] = []
    for left, right, target in queries:
        values = [0] * n
        answer = m + 1
        if sum(values[left:right]) >= target:
            answers.append(0)
            continue
        for step, (index, delta) in enumerate(updates, 1):
            values[index] += delta
            if sum(values[left:right]) >= target:
                answer = step
                break
        answers.append(answer)
    return " ".join(map(str, answers)) + "\n"
