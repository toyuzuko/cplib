#!/usr/bin/env python3

from cplib.datastructure.dsu import DSUOnlyPathHalving
from cplib.datastructure.queue import PriorityQueue
from cplib.graph.base import Node as Node
from cplib.graph.core import Graph, Tree
from cplib.graph.walk import cycle_detection

def optimal_scheduling_on_tree(tree: Tree, proc_time: list[int], weight: list[int]):
    """
    Find an optimal scheduling order for jobs whose precedence constraints form a rooted tree.

    Each vertex is a job. The rooted tree expresses parent-before-child
    precedence constraints: a child can be scheduled only after its parent.
    Among all valid orders, the returned order minimizes the total weighted
    completion time ``sum(weight[v] * completion_time[v])``.

    The returned ``acc`` is the weighted waiting-time part
    ``sum(weight[v] * (completion_time[v] - proc_time[v]))``. The full weighted
    completion time is ``acc + sum(weight[v] * proc_time[v] for v in range(n))``.

    The algorithm uses a greedy approach based on Smith's ratio (weight/processing_time)
    and merges jobs in order of their priority while respecting tree constraints.

    Args:
        tree (Tree): A Tree object representing the job precedence constraints.
                     Must be already built (tree.build() called).
        proc_time (list[int]): Processing time for each job. proc_time[i] is the
                               time required to complete job i.
        weight (list[int]): Weight (importance) of each job. weight[i] is the
                           penalty coefficient for job i's completion time.

    Returns:
        tuple[int, list[int]]: A tuple containing:
            - acc (int): The minimum total weighted waiting time
            - order (list[int]): The optimal scheduling order of jobs (node indices)

    Raises:
        ValueError: If the tree has not been built yet (tree.root == -1)

    Examples:
        A release pipeline has to run the root setup job before package jobs,
        and each package before its own checks. The order minimizes weighted
        completion time while respecting those dependencies.

        >>> tree = Tree(6)
        >>> tree.add_edge(Node(0), Node(1))
        >>> tree.add_edge(Node(0), Node(2))
        >>> tree.add_edge(Node(1), Node(3))
        >>> tree.add_edge(Node(1), Node(4))
        >>> tree.add_edge(Node(2), Node(5))
        >>> tree.build(Node(0))
        >>> proc_time = [3, 2, 4, 1, 2, 1]
        >>> weight = [4, 8, 3, 6, 2, 5]
        >>> cost, order = optimal_scheduling_on_tree(tree, proc_time, weight)
        >>> cost
        144
        >>> order
        [0, 1, 3, 2, 5, 4]
        >>> cost + sum(t * w for t, w in zip(proc_time, weight))
        199

    Notes:
        The algorithm uses a priority queue to greedily merge jobs based on their
        weight-to-processing-time ratio while maintaining the tree structure constraints.

    Time Complexity:
        O(n^2) in the size of the processed input or stored data

    Space Complexity:
        O(n) in the size of newly allocated output or auxiliary storage
    """

    class Job:
        def __init__(self, c: int, t: int, idx: int, qid: int):
            self.c = c
            self.t = t
            self.idx = idx
            self.qid = qid

        def __lt__(self, other: 'Job') -> bool:
            if self.t == 0 and other.t == 0:
                return self.c > other.c
            if self.t == 0:
                return True
            if other.t == 0:
                return False
            lhs = self.c * other.t
            rhs = self.t * other.c
            return lhs > rhs

    if tree.root == -1:
        raise ValueError('This tree has not been built yet')
    n = tree.n
    weight = weight.copy()
    proc_time = proc_time.copy()

    acc = 0
    dsu = DSUOnlyPathHalving(n)
    ids = [0] * n

    pq = PriorityQueue[Job]()
    pq.build([Job(weight[v], proc_time[v], v, ids[v]) for v in range(n) if v != tree.root])
    seen = [-1] * n
    done = 0

    while pq:
        job = pq.pop()
        if job.qid != ids[job.idx]:
            continue
        v = job.idx
        seen[v] = done
        done += 1
        dsu.link(v, tree.par_v[v])
        r = dsu.leader(v)
        acc += proc_time[r] * weight[v]
        weight[r] += weight[v]
        proc_time[r] += proc_time[v]
        ids[r] += 1
        if r != tree.root:
            pq.push(Job(weight[r], proc_time[r], r, ids[r]))

    order: list[int] = []
    ready = PriorityQueue[tuple[int, int]]()
    ready.build([(-1, int(tree.root))])

    while ready:
        _, v = ready.pop()
        order.append(v)
        for u, _ in tree.tree[v]:
            if tree.par_v[v] == u: continue
            ready.push((seen[u], u))

    return acc, order


def optimal_scheduling_on_dag(g: Graph, proc_time: list[int], weight: list[int]) -> tuple[int, list[int]]:
    """
    Finds the optimal scheduling order for jobs on a DAG with precedence constraints.

    Solves the single-machine weighted completion time minimization problem
    (1 | prec(DAG) | Σ w_j C_j) using subset dynamic programming.
    Time complexity: O(2^n * n^2), Space complexity: O(2^n).

    Args:
        g (Graph): Directed acyclic graph representing job precedence constraints.
                   Must have g.n == len(proc_time) == len(weight).
        proc_time (list[int]): Processing time for each job. proc_time[i] is the
                               time required to complete job i.
        weight (list[int]): Weight (importance) of each job. weight[i] is the
                           penalty coefficient for job i's completion time.

    Returns:
        tuple[int, list[int]]: A tuple containing:
            - Minimum total weighted completion time (Σ w_j C_j)
            - Optimal scheduling order of jobs (list of job indices)

    Raises:
        AssertionError: If graph is not directed or input sizes don't match.
        ValueError: If graph contains a cycle (not a DAG).

    Examples:
        A build graph has two independent source-generation jobs. Both must
        finish before packaging, and the final publish job waits for packaging
        and documentation.

        >>> g = Graph(5, is_directed=True)
        >>> g.add_edge(Node(0), Node(2))  # generate API before package
        >>> g.add_edge(Node(1), Node(2))  # compile assets before package
        >>> g.add_edge(Node(1), Node(3))  # compile assets before docs
        >>> g.add_edge(Node(2), Node(4))  # package before publish
        >>> g.add_edge(Node(3), Node(4))  # docs before publish
        >>> proc_time = [3, 1, 2, 4, 2]
        >>> weight = [4, 6, 5, 2, 8]
        >>> cost, order = optimal_scheduling_on_dag(g, proc_time, weight)
        >>> cost
        168
        >>> order
        [1, 0, 2, 3, 4]

    Time Complexity:
        O(n^2 2^n)

    Space Complexity:
        O(2^n)
    """
    n = g.n
    assert g.is_directed, "Graph must be directed"
    assert n == len(proc_time) == len(weight)

    cycle_check = cycle_detection(g)
    if cycle_check.found is True:
        raise ValueError("Graph is not a DAG (contains a cycle)")

    pred_mask = [0] * n
    for u, v in g.edges:
        pred_mask[v] |= 1 << u
    proc_sum = [0] * (1 << n)
    for mask in range(1, 1 << n):
        b = mask & -mask
        i = (b.bit_length() - 1)
        proc_sum[mask] = proc_sum[mask ^ b] + proc_time[i]
    INF = sum(map(abs, proc_time)) * sum(map(abs, weight)) + 1
    dp   = [INF] * (1 << n)
    prev = [-1]  * (1 << n)
    dp[0] = 0

    for mask in range(1 << n):
        cur_time = proc_sum[mask]
        base = dp[mask]
        if base == INF:
            continue
        avail = (~mask) & ((1 << n) - 1)
        v = avail
        while v:
            b = v & -v
            idx = b.bit_length() - 1
            v ^= b
            if pred_mask[idx] & ~mask:
                continue
            nxt = mask | b
            finish_time = cur_time + proc_time[idx]
            cost = base + weight[idx] * finish_time
            if cost < dp[nxt]:
                dp[nxt]  = cost
                prev[nxt] = idx

    full_mask = (1 << n) - 1
    opt_cost  = dp[full_mask]

    order: list[int] = []
    mask = full_mask
    while mask:
        j = prev[mask]
        order.append(j)
        mask ^= 1 << j
    order.reverse()

    return opt_cost, order


__all__ = ['optimal_scheduling_on_tree', 'optimal_scheduling_on_dag']
