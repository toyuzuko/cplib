from cplib.string.hashing import DynamicRollingHashMersenneMod


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, q = map(int, lines[0].split())
    s = lines[1].strip()
    rh = DynamicRollingHashMersenneMod(s, base=3)
    out: list[str] = []
    for line in lines[2:2 + q]:
        parts = line.split()
        if parts[0] == 'SET':
            rh.set_char(int(parts[1]), parts[2])
        elif parts[0] == 'HASH':
            out.append(str(rh.get_hash(int(parts[1]), int(parts[2]))))
        else:
            out.append(str(rh.search_substring(parts[1], int(parts[2]), int(parts[3]))))
    assert len(s) == n
    return '\n'.join(out) + ('\n' if out else '')


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
