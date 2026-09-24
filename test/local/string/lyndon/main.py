from cplib.string.period import duval, minimum_representation


def parse_input(inp: str) -> str:
    return inp.rstrip("\n")


def format_boundaries(boundaries: list[int]) -> str:
    return " ".join(str(value) for value in boundaries)


def solve(inp: str) -> str:
    s: str = parse_input(inp)
    boundaries: list[int] = []
    for left, _ in duval(s):
        boundaries.append(left)
    boundaries.append(len(s))
    return (
        format_boundaries(boundaries)
        + "\n"
        + str(minimum_representation(s))
        + "\n"
    )


if __name__ == "__main__":
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
