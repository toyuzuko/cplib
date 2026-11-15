'''Minimize finite integer unary and submodular pairwise costs by minimum cut.'''

from typing import NamedTuple

from cplib.graph.base import Capacity, Node
from cplib.graph.flow import MaximumFlow


class BinarySubmodularResult(NamedTuple):
    '''Minimum cost and one attaining assignment of bits.

    Attributes:
        cost: Minimum total cost (possibly negative).
        assignment: Bits (0 or 1) in variable-index order. Ties are unspecified.

    Space Complexity:
        O(n)
    '''
    cost: int
    assignment: list[int]


class BinarySubmodularMinimizer:
    '''Minimize a sum of finite signed integer costs over binary variables.

    Unary costs are unrestricted. Each pairwise table on distinct variables
    must satisfy ``c00 + c11 <= c01 + c10`` in the chosen bit labeling.
    If the condition fails, a problem-specific relabeling may help; this
    class does not search for one. Terms on the same variables are additive.
    For hard implications and integer profits, see ``maximum_weight_closure``.

    Args:
        n: Number of binary variables, indexed from zero.

    Space Complexity:
        O(n + m), where m is the number of pairwise terms.

    Examples:
        >>> solver = BinarySubmodularMinimizer(2)
        >>> solver.add_unary(Node(0), 0, -4)
        >>> solver.add_unary(Node(1), 0, 2)
        >>> solver.add_pairwise(Node(0), Node(1), 0, 0, 5, 0)
        >>> solver.solve()
        BinarySubmodularResult(cost=-2, assignment=[1, 1])
    '''

    def __init__(self, n: int) -> None:
        '''Create a model with no cost terms.

        Args:
            n: Number of variables.

        Raises:
            ValueError: If n is negative.

        Time Complexity:
            O(n)
        '''
        if n < 0:
            raise ValueError('n must be non-negative')
        self._linear = [0] * n
        self._constant = 0
        self._edges: list[tuple[Node, Node, Capacity]] = []

    def _check_index(self, v: Node) -> None:
        if not 0 <= v < len(self._linear):
            raise IndexError('variable index must be within [0, n)')

    def add_unary(self, v: Node, c0: int, c1: int) -> None:
        '''Add a cost depending on one bit.

        Args:
            v: Variable index.
            c0: Cost for bit zero.
            c1: Cost for bit one.

        Raises:
            IndexError: If v is outside the variable range.

        Time Complexity:
            O(1)
        '''
        self._check_index(v)
        self._constant += c0
        self._linear[v] += c1 - c0

    def add_pairwise(
        self, u: Node, v: Node, c00: int, c01: int, c10: int, c11: int,
    ) -> None:
        '''Add a submodular cost table in (u, v) order.

        Args:
            u: Index of the first variable (row).
            v: Index of the second variable (column).
            c00: Cost for bits (0, 0).
            c01: Cost for bits (0, 1).
            c10: Cost for bits (1, 0).
            c11: Cost for bits (1, 1).

        Raises:
            IndexError: If either variable is outside the variable range.
            ValueError: If distinct variables have c00 + c11 > c01 + c10.

        Notes:
            If u equals v, only c00 and c11 can occur, so the term is unary
            and the unused off-diagonal entries are ignored.

        Time Complexity:
            O(1) amortized.
        '''
        self._check_index(u)
        self._check_index(v)
        if u == v:
            self.add_unary(u, c00, c11)
            return
        capacity = c01 + c10 - c00 - c11
        if capacity < 0:
            raise ValueError('pairwise term must satisfy c00 + c11 <= c01 + c10')
        # c00 + (c10 - c00)*x + (c11 - c10)*y + capacity*[x == 0 and y == 1].
        self._constant += c00
        self._linear[u] += c10 - c00
        self._linear[v] += c11 - c10
        if capacity:
            self._edges.append((u, v, Capacity(capacity)))

    def solve(self) -> BinarySubmodularResult:
        '''Return a minimum cost and an attaining bit assignment.

        Returns:
            Minimum total cost and the assignment in index order.

        Notes:
            Each solve builds a fresh network. Adding terms and solving again
            is supported, and previously returned assignments are independent.
            Integer costs are unbounded; no fixed infinity is used.

        Time Complexity:
            O((n + 2)**2 * (n + m) + n), using Dinic maximum flow.
        '''
        n = len(self._linear)
        source, sink = Node(n), Node(n + 1)
        network = MaximumFlow(n + 2)
        for u, v, cap in self._edges:
            network.add_edge(u, v, cap)
        offset = self._constant
        source_capacity = 0
        for v, d in enumerate(self._linear):
            if d > 0:
                network.add_edge(source, Node(v), Capacity(d))
                source_capacity += d
            elif d < 0:
                network.add_edge(Node(v), sink, Capacity(-d))
                offset += d
        result = network.solve(source, sink, Capacity(source_capacity))

        residual: list[list[Node]] = [[] for _ in range(n + 2)]
        for u, v, capacity, flow in result.edges:
            if flow < capacity:
                residual[u].append(v)
            if flow > 0:
                residual[v].append(u)
        assignment = [1] * (n + 2)
        assignment[source] = 0
        stack = [source]
        while stack:
            u = stack.pop()
            for v in residual[u]:
                if assignment[v]:
                    assignment[v] = 0
                    stack.append(v)
        return BinarySubmodularResult(offset + result.flow, assignment[:n])
