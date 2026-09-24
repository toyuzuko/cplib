from cplib.datastructure.avltree import PersistentImplicitAVLTree
from cplib.tools.fastio import FastIO


BIT = 20
MASK = (1 << BIT) - 1
REBUILD_NODE_THRESHOLD = 2_000_000


def op(a: int, b: int) -> int:
    return (((a >> BIT) + (b >> BIT)) << BIT) + ((a & MASK) + (b & MASK))


def mapping(x: int, a: int) -> int:
    length = a & MASK
    return (((a >> BIT) + x * length) << BIT) + length


def composition(x: int, y: int) -> int:
    return x + y


N, Q = FastIO.read_ints(2)
A = [(a << BIT) + 1 for a in FastIO.read_ints(N)]

seq = PersistentImplicitAVLTree(op, 0, mapping, composition, 0, commutative=True)
root = seq.new_root(A)
del A

for _ in range(Q):
    t = FastIO.read_int()
    if t == 1:
        a, b, v = FastIO.read_ints(3)
        root = seq.range_apply(root, a - 1, b, v)
    elif t == 2:
        a, b, c, d = FastIO.read_ints(4)
        _, rest = seq.split(root, c - 1)
        copied, _ = seq.split(rest, d - c + 1)
        left, rest = seq.split(root, a - 1)
        _, right = seq.split(rest, b - a + 1)
        root = seq.merge(left, seq.merge(copied, right))
    else:
        a, b = FastIO.read_ints(2)
        result, root = seq.prod(root, a - 1, b)
        FastIO.writeln(f'{result >> BIT}')
    if len(seq.val) > REBUILD_NODE_THRESHOLD:
        values = seq.to_list(root)
        seq = PersistentImplicitAVLTree(op, 0, mapping, composition, 0, commutative=True)
        root = seq.new_root(values)
        del values
