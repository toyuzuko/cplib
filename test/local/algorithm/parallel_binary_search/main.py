from cplib.algorithm.bisearch import ParallelBinarySearch


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

    values = [0] * n
    pbs = ParallelBinarySearch(m)
    for _ in range(q):
        pbs.add_query()

    def reset() -> None:
        for i in range(n):
            values[i] = 0

    def apply(index: int) -> None:
        position, delta = updates[index]
        values[position] += delta

    def check(query_index: int) -> bool:
        left, right, target = queries[query_index]
        return sum(values[left:right]) >= target

    answers = pbs.run(reset=reset, apply=apply, check=check)
    return " ".join(map(str, answers)) + "\n"


if __name__ == "__main__":
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
