from __future__ import annotations


def solve(inp: str) -> str:
    lines = inp.splitlines()
    q = int(lines[0])
    start, timeout = map(int, lines[1].split())
    observations = list(map(int, lines[2].split()))

    out: list[str] = []
    for i in range(q):
        elapsed = observations[i] - start
        remaining = max(0, timeout - elapsed)
        timeout_flag = 1 if elapsed >= timeout else 0
        out.append(f"{elapsed} {remaining} {timeout_flag}")
    return "\n".join(out) + "\n"
