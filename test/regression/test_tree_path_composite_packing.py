import os
from pathlib import Path
import random
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOLVER = ROOT / 'test/library_checker/point_set_tree_path_composite_sum.test.py'
TOPTREE_SOLVER = ROOT / 'test/library_checker/point_set_tree_path_composite_sum.toptree.test.py'
MOD = 998244353


class TreePathCompositePackingTest(unittest.TestCase):
    def test_updates_and_roots_against_naive_tree_dp(self) -> None:
        for seed in range(8):
            rng = random.Random(seed)
            n, q = (1, 2, 7, 20)[seed % 4], 100
            values = [rng.choice((0, 1, MOD - 1)) for _ in range(n)]
            lines = [f'{n} {q}', ' '.join(map(str, values))]
            adjacency: list[list[tuple[int, int]]] = [[] for _ in range(n)]
            edges: list[tuple[int, int]] = []
            for v in range(1, n):
                u = rng.randrange(v)
                b, c = rng.choice((1, MOD - 1)), rng.choice((0, MOD - 1))
                edges.append((b, c))
                adjacency[u].append((v, v - 1))
                adjacency[v].append((u, v - 1))
                lines.append(f'{u} {v} {b} {c}')
            expected: list[int] = []
            for step in range(q):
                root = rng.randrange(n)
                if n == 1 or step % 2 == 0:
                    v = rng.randrange(n)
                    value = rng.randrange(MOD) if step % 3 else rng.choice((0, MOD - 1))
                    values[v] = value
                    lines.append(f'0 {v} {value} {root}')
                else:
                    edge = rng.randrange(n - 1)
                    b = rng.randrange(1, MOD) if step % 3 else MOD - 1
                    c = rng.randrange(MOD) if step % 3 else MOD - 1
                    edges[edge] = b, c
                    lines.append(f'1 {edge} {b} {c} {root}')
                parent = [-1] * n
                order = [root]
                for u in order:
                    for v, _ in adjacency[u]:
                        if v != parent[u]:
                            parent[v] = u
                            order.append(v)
                sums, sizes = values[:], [1] * n
                for u in reversed(order):
                    for v, edge in adjacency[u]:
                        if parent[v] == u:
                            b, c = edges[edge]
                            sums[u] = (sums[u] + b * sums[v] + c * sizes[v]) % MOD
                            sizes[u] += sizes[v]
                expected.append(sums[root])
            for solver in (SOLVER, TOPTREE_SOLVER):
                with self.subTest(seed=seed, solver=solver.name):
                    result = subprocess.run([sys.executable, str(solver)], input='\n'.join(lines) + '\n', capture_output=True, text=True, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT)), timeout=20)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(list(map(int, result.stdout.split())), expected)


if __name__ == '__main__':
    unittest.main()
