from cplib.string.palindrome import PalindromicTree


def solve(inp: str) -> str:
    s = inp.rstrip("\n")
    tree = PalindromicTree(s)
    counts = tree.build_occurrence_counts()
    items: list[tuple[str, int]] = []
    for node in range(2, len(tree.length)):
        items.append((tree.palindrome(node), counts[node]))
    items.sort(key=lambda item: (len(item[0]), item[0]))

    out = [str(len(items)), tree.longest_suffix_palindrome()]
    out.extend(f"{pal} {count}" for pal, count in items)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
