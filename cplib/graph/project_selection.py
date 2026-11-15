"""Integer-profit project selection with hard dependency constraints."""

from collections.abc import Sequence
from typing import NamedTuple

from cplib.graph.base import Capacity, Node
from cplib.graph.flow import MaximumFlow


class MaximumWeightClosureResult(NamedTuple):
    """Optimal project selection.

    Attributes:
        profit: Maximum sum of selected profits (at least zero).
        selected: Selected vertex IDs in increasing order. Ties are unspecified.

    Space Complexity:
        O(n)
    """
    profit: int
    selected: list[Node]


def maximum_weight_closure(
    profits: Sequence[int], implications: Sequence[tuple[Node, Node]],
) -> MaximumWeightClosureResult:
    """Maximize selected integer profits subject to hard implications.

    An implication ``(u, v)`` means selecting ``u`` requires selecting ``v``.
    Negative profits represent costs; selecting nothing is always feasible.
    Cycles, self-dependencies and duplicate implications are allowed. This is
    a maximum-weight closure helper, not a general submodular-energy solver.
    Inputs are not modified; each call builds a fresh maximum-flow network.

    Args:
        profits: Signed integer profit for each project.
        implications: Directed dependencies between project indices.

    Returns:
        Optimal profit and one optimal closed set of projects.

    Raises:
        IndexError: If a dependency endpoint is outside ``[0, len(profits))``.

    Notes:
        Integer arithmetic is unbounded. The dependency capacity is one more
        than the total positive profit; no fixed infinity sentinel is used.

    Time Complexity:
        O((n + 2)**2 * (n + m)), using Dinic maximum flow.

    Space Complexity:
        O(n + m)

    Examples:
        >>> maximum_weight_closure([8, -3, -10], [(0, 1)])
        MaximumWeightClosureResult(profit=5, selected=[0, 1])
        >>> maximum_weight_closure([], [])
        MaximumWeightClosureResult(profit=0, selected=[])
    """
    n = len(profits)
    source, target = Node(n), Node(n + 1)
    total = sum(p for p in profits if p > 0)
    network = MaximumFlow(n + 2)
    for u, p in enumerate(profits):
        if p > 0:
            network.add_edge(source, Node(u), Capacity(p))
        elif p < 0:
            network.add_edge(Node(u), target, Capacity(-p))
    for u, v in implications:
        if not 0 <= u < n or not 0 <= v < n:
            raise IndexError('dependency endpoint must be within [0, len(profits))')
        network.add_edge(u, v, Capacity(total + 1))
    result = network.solve(source, target, Capacity(total))
    residual: list[list[Node]] = [[] for _ in range(n + 2)]
    for u, v, capacity, flow in result.edges:
        if flow < capacity:
            residual[u].append(v)
        if flow > 0:
            residual[v].append(u)
    seen = [False] * (n + 2)
    seen[source] = True
    stack = [source]
    while stack:
        u = stack.pop()
        for v in residual[u]:
            if not seen[v]:
                seen[v] = True
                stack.append(v)
    return MaximumWeightClosureResult(total - result.flow, [Node(u) for u in range(n) if seen[u]])
