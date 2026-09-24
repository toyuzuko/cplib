from __future__ import annotations

from collections import deque


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n, m, q = map(int, lines[0].split())
    graph = [[] for _ in range(n)]
    for line in lines[1:1 + m]:
        u, v = map(int, line.split())
        graph[u].append(v)

    out: list[str] = []
    for line in lines[1 + m:1 + m + q]:
        s, t = map(int, line.split())
        seen = [False] * n
        seen[s] = True
        que = deque([s])
        while que:
            v = que.popleft()
            for u in graph[v]:
                if not seen[u]:
                    seen[u] = True
                    que.append(u)
        out.append(str(int(seen[t])))
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
