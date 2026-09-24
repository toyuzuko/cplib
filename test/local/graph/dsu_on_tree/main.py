from cplib.graph.base import Node
from cplib.graph.treequery import DSUOnTree
from cplib.graph import Tree


def solve(inp: str) -> str:
    lines = inp.splitlines()
    n = int(lines[0])
    parents = [] if n == 1 else list(map(int, lines[1].split()))
    colors = list(map(int, lines[2 if n > 1 else 1].split()))

    tree = Tree(n)
    for v in range(1, n):
        tree.add_edge(Node(parents[v - 1]), Node(v))
    tree.build(Node(0))

    freq: dict[int, int] = {}

    def add(v: Node) -> None:
        color = colors[v]
        freq[color] = freq.get(color, 0) + 1

    def remove(v: Node) -> None:
        color = colors[v]
        freq[color] -= 1
        if freq[color] == 0:
            del freq[color]

    def answer(_: Node) -> int:
        return len(freq)

    ans = DSUOnTree[int](tree).run(add=add, remove=remove, answer=answer)
    return " ".join(map(str, ans)) + "\n"


if __name__ == "__main__":
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
