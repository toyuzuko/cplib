from __future__ import annotations

from cplib.datastructure.slopetrick import SlopeTrick
from config import SAMPLE_LEFT, SAMPLE_RIGHT

SAMPLE_POINTS: tuple[int, ...] = tuple(range(SAMPLE_LEFT, SAMPLE_RIGHT + 1))


def parse_query(line: str) -> tuple[int, ...]:
    """Parse one operation line into a tuple of integers."""
    parts: list[str] = line.split()
    return tuple(int(part) for part in parts)


def dump_state(st: SlopeTrick) -> str:
    values = " ".join(str(st.evaluate(x)) for x in SAMPLE_POINTS)
    return f"{st.minimum()} {values}"


def solve(inp: str) -> str:
    lines: list[str] = inp.splitlines()
    q = int(lines[0])
    st = SlopeTrick()
    out: list[str] = [dump_state(st)]
    for i in range(1, q + 1):
        query = parse_query(lines[i])
        typ = query[0]
        if typ == 0:
            st.add_x_minus_a(query[1])
        elif typ == 1:
            st.add_a_minus_x(query[1])
        elif typ == 2:
            st.add_abs(query[1])
        elif typ == 3:
            st.shift(query[1])
        elif typ == 4:
            st.sliding_window_min(query[1], query[2])
        elif typ == 5:
            st.prefix_min()
        elif typ == 6:
            st.suffix_min()
        else:
            st.add_const(query[1])
        out.append(dump_state(st))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
