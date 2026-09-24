def solve(inp: str) -> str:
    s = inp.rstrip("\n")
    counts: dict[str, int] = {}
    for left in range(len(s)):
        for right in range(left, len(s)):
            part = s[left : right + 1]
            if part == part[::-1]:
                counts[part] = counts.get(part, 0) + 1

    longest_suffix = ""
    for i in range(len(s) + 1):
        part = s[i:]
        if part == part[::-1]:
            longest_suffix = part
            break

    items = sorted(counts.items(), key=lambda item: (len(item[0]), item[0]))
    out = [str(len(items)), longest_suffix]
    out.extend(f"{pal} {count}" for pal, count in items)
    return "\n".join(out) + "\n"
