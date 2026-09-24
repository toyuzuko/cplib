from __future__ import annotations

from cplib.heuristic.time_manager import TimeManager


def solve(inp: str) -> str:
    lines = inp.splitlines()
    q = int(lines[0])
    start, timeout = map(int, lines[1].split())
    observations = list(map(int, lines[2].split()))

    current_time = start

    def clock() -> float:
        return float(current_time)

    manager = TimeManager(float(timeout), start_time=float(start), clock=clock)
    out: list[str] = []
    for i in range(q):
        current_time = observations[i]
        out.append(
            f"{int(manager.elapsed())} {int(manager.remaining())} {int(manager.is_timeout())}"
        )
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
