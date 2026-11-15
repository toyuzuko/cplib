import random
import unittest

from cplib.graph import Graph, dijkstra, zero_one_bfs, zero_one_bfs_with_prev


class ZeroOneBFSTest(unittest.TestCase):
    def test_random_vs_dijkstra_and_predecessors(self):
        rng = random.Random(7102026)
        for directed in (False, True):
            for n in range(1, 18):
                for _ in range(25):
                    g = Graph(n, is_directed=directed)
                    for _ in range(rng.randrange(n * n + 1)):
                        g.add_edge(rng.randrange(n), rng.randrange(n), rng.randrange(2))
                    source = rng.randrange(n)
                    dst, prev = zero_one_bfs_with_prev(g, source)
                    self.assertEqual(dst, dijkstra(g, source))
                    self.assertEqual(zero_one_bfs(g, source), dst)
                    self.assertEqual(prev[source], -1)
                    for v in range(n):
                        if v == source or dst[v] == Graph.dst_inf:
                            self.assertEqual(prev[v], -1)
                            continue
                        u = prev[v]
                        self.assertTrue(any(w == v and dst[u] + g.wt[e] == dst[v] for w, e in g.graph[u]))
                        seen = set()
                        while v != source:
                            self.assertNotIn(v, seen)
                            seen.add(v)
                            v = prev[v]
                            self.assertGreaterEqual(v, 0)

    def test_invalid_and_empty(self):
        for source in (-1, 0, 1):
            with self.assertRaises(IndexError):
                zero_one_bfs(Graph(0), source)
        for weight in (-1, 2, 10**30):
            g = Graph(3, is_directed=True)
            g.add_edge(1, 2, weight)
            with self.assertRaises(ValueError):
                zero_one_bfs(g, 0)
        for source in (-1, 3):
            with self.assertRaises(IndexError):
                zero_one_bfs(Graph(3), source)

    def test_stale_candidate_and_zero_cycle(self):
        g = Graph(5, is_directed=True)
        for u, v, w in [(0, 1, 1), (0, 2, 0), (2, 1, 0), (1, 2, 0), (1, 3, 1)]:
            g.add_edge(u, v, w)
        self.assertEqual(zero_one_bfs(g, 0), [0, 0, 0, 1, Graph.dst_inf])


if __name__ == '__main__':
    unittest.main()
