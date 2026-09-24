# verification-helper: PROBLEM https://judge.yosupo.jp/problem/stern_brocot_tree

from cplib.mathematics.rational import SternBrocotTree
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    op = FastIO.read()
    if op == 'ENCODE_PATH':
        a = FastIO.read_int()
        b = FastIO.read_int()
        path = SternBrocotTree(a, b).path()
        FastIO.write(f'{len(path)}')
        for direction, count in path:
            FastIO.write(f' {direction} {count}')
        FastIO.write('\n')

    elif op == 'DECODE_PATH':
        k = FastIO.read_int()
        path: list[tuple[str, int]] = []
        for _ in range(k):
            direction = FastIO.read()
            count = FastIO.read_int()
            path.append((direction, count))
        value = SternBrocotTree.from_path(path).value()
        FastIO.writeln(f'{value.num} {value.den}')

    elif op == 'LCA':
        a = FastIO.read_int()
        b = FastIO.read_int()
        c = FastIO.read_int()
        d = FastIO.read_int()
        value = SternBrocotTree.lca(SternBrocotTree(a, b), SternBrocotTree(c, d)).value()
        FastIO.writeln(f'{value.num} {value.den}')

    elif op == 'ANCESTOR':
        k = FastIO.read_int()
        a = FastIO.read_int()
        b = FastIO.read_int()
        ancestor = SternBrocotTree(a, b).ancestor(k)
        if ancestor is None:
            FastIO.writeln('-1')
        else:
            value = ancestor.value()
            FastIO.writeln(f'{value.num} {value.den}')

    else:
        a = FastIO.read_int()
        b = FastIO.read_int()
        lower, upper = SternBrocotTree(a, b).range()
        FastIO.writeln(f'{lower.num} {lower.den} {upper.num} {upper.den}')
