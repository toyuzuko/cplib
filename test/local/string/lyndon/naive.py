from __future__ import annotations


def parse_input(inp: str) -> str:
    return inp.rstrip("\n")


def is_lyndon(word: str) -> bool:
    if not word:
        return False
    return all(word < word[i:] for i in range(1, len(word)))


def brute_factorization(s: str) -> list[int]:
    if not s:
        return [0]

    answer: list[int] | None = None

    def dfs(pos: int, parts: list[str], boundaries: list[int]) -> None:
        nonlocal answer
        if answer is not None:
            return
        if pos == len(s):
            if all(parts[i] >= parts[i + 1] for i in range(len(parts) - 1)):
                answer = boundaries + [len(s)]
            return
        for nxt in range(pos + 1, len(s) + 1):
            part = s[pos:nxt]
            if not is_lyndon(part):
                continue
            if parts and parts[-1] < part:
                continue
            dfs(nxt, parts + [part], boundaries + [pos])

    dfs(0, [], [])
    assert answer is not None
    return answer


def brute_minimum_representation(s: str) -> int:
    if not s:
        return 0
    rotations = [s[i:] + s[:i] for i in range(len(s))]
    best = min(rotations)
    for i, rotation in enumerate(rotations):
        if rotation == best:
            return i
    raise AssertionError("unreachable")


def solve(inp: str) -> str:
    s: str = parse_input(inp)
    boundaries: list[int] = brute_factorization(s)
    rotation: int = brute_minimum_representation(s)
    return " ".join(str(value) for value in boundaries) + "\n" + str(rotation) + "\n"
