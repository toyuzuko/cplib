#!/usr/bin/env python3

from typing import Generic, Callable
from bisect import bisect_right
from cplib.tools.type import ValueT, AggregateT

class DisjointSetUnion:
    """Disjoint Set Union (Union-Find) data structure.

    A data structure that keeps track of a set of elements partitioned into
    disjoint (non-overlapping) subsets. Supports efficient union and find operations.

    Attributes:
        n: Number of elements, vertices, or rows handled by the structure.
        par_size: List where par_size[i] is the parent of i if par_size[i] >= 0, otherwise -size of the set for which i is the representative.

    Time Complexities:
        - leader: O(α(n)) amortized, where α is the inverse Ackermann function
        - merge: O(α(n)) amortized
        - same: O(α(n)) amortized
        - size: O(α(n)) amortized
        - is_root: O(1)
        - roots: O(n)
        - groups: O(n)

    Examples:
        >>> dsu = DisjointSetUnion(5)
        >>> dsu.merge(0, 1)
        True
        >>> dsu.merge(2, 3)
        True
        >>> dsu.same(0, 1)
        True
        >>> dsu.same(0, 2)
        False
        >>> dsu.merge(1, 3)
        True
        >>> dsu.groups()
        [[0, 1, 2, 3], [4]]

    Notes:
        Uses path compression and union by size for optimal performance.
        The inverse Ackermann function α(n) is effectively constant for all practical values of n.

    Args:
        n: Number of elements, vertices, or rows handled by the structure.

    Space Complexity:
        O(n) in the constructor input size or configured capacity
    """
    def __init__(self, n: int) -> None:
        """Initialize a disjoint-set data structure with `n` singleton sets.

        Args:
            n (int): The number of singleton sets.

        Time Complexity:
            O(n)

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.par_size = [-1] * n

    def leader(self, a: int) -> int:
        """
        Find the representative of the set that element a is part of.

        Args:
            a (int): The element to find the representative of

        Returns:
            int: The representative of the set

        Raises:
            AssertionError: If a is out of range [0, n)

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        x = a
        while self.par_size[x] >= 0:
            x = self.par_size[x]
        while self.par_size[a] >= 0:
            parent = self.par_size[a]
            self.par_size[a] = x
            a = parent
        return x

    def same(self, a: int, b: int) -> bool:
        """
        Check if elements a and b are part of the same set.

        Args:
            a (int): The first element
            b (int): The second element

        Returns:
            bool: True if a and b are part of the same set, False otherwise

        Raises:
            AssertionError: If a or b is out of range [0, n)

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        return self.leader(a) == self.leader(b)

    def merge(self, a: int, b: int) -> bool:
        """
        Merge the sets that a and b are part of.

        Args:
            a (int): The first element
            b (int): The second element

        Returns:
            bool: True if the merge was successful, False if a and b were already part of the same set

        Raises:
            AssertionError: If a or b is out of range [0, n)

        Notes:
            Uses union by size heuristic to keep the tree balanced.

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        x = self.leader(a)
        y = self.leader(b)
        if x == y: return False
        if -self.par_size[x] < -self.par_size[y]: x, y = y, x
        self.par_size[x] += self.par_size[y]
        self.par_size[y] = x
        return True

    def size(self, a: int) -> int:
        """
        Get the size of the set that a is part of.

        Args:
            a (int): The element

        Returns:
            int: The size of the set

        Raises:
            AssertionError: If a is out of range [0, n)

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        return -self.par_size[self.leader(a)]

    def is_root(self, a: int) -> bool:
        """Check if a is the representative of its set.

        Args:
            a (int): The element to check

        Returns:
            bool: True if a is the representative of its set, False otherwise

        Raises:
            AssertionError: If a is out of range [0, n)

        Time Complexity:
            O(1)
        """
        assert 0 <= a < self.n
        return self.par_size[a] < 0

    def roots(self) -> list[int]:
        """Get a list of all set representatives.

        Returns:
            list[int]: The list of representatives

        Time Complexity:
            O(n)
        """
        res = [i for i in range(self.n) if self.par_size[i] < 0]
        return res

    def groups(self) -> list[list[int]]:
        """Get a list of all sets. Each set is represented as a list of its elements.

        Returns:
            list[list[int]]: The list of sets

        Examples:
            >>> dsu = DisjointSetUnion(5)
            >>> dsu.merge(0, 1)
            True
            >>> dsu.merge(2, 3)
            True
            >>> dsu.groups()
            [[0, 1], [2, 3], [4]]

        Time Complexity:
            O(n)
        """
        res: list[list[int]] = [[] for _ in range(self.n)]
        for i in range(self.n):
            res[self.leader(i)].append(i)
        res = [res[i] for i in range(self.n) if res[i]]
        return res

class WeightedDSU:
    """Weighted Disjoint Set Union data structure.

    A variant of the disjoint set union that maintains weights between elements.
    Supports finding the relative weight/distance between elements in the same connected component.

    Attributes:
        n: Number of elements, vertices, or rows handled by the structure.
        par_size: List where par_size[i] is the parent of i if par_size[i] >= 0, otherwise -size of the set for which i is the representative.
        wt: List where wt[i] is the weight from element i to its parent (if par_size[i] >= 0) or 0 if i is a representative.

    Time Complexities:
        - leader: O(α(n)) amortized, where α is the inverse Ackermann function
        - merge: O(α(n)) amortized
        - same: O(α(n)) amortized
        - size: O(α(n)) amortized
        - diff: O(α(n)) amortized

    Examples:
        >>> wdsu = WeightedDSU(4)
        >>> wdsu.merge(0, 1, 5)  # distance from 0 to 1 is 5
        True
        >>> wdsu.merge(1, 2, 3)  # distance from 1 to 2 is 3
        True
        >>> wdsu.diff(0, 2)  # distance from 0 to 2 is 5 + 3 = 8
        8
        >>> wdsu.same(0, 2)
        True
        >>> wdsu.same(0, 3)
        False

    Notes:
        Uses path compression with weight updates to maintain relative distances.
        Weights represent the cumulative distance/difference from each element to its root.

    Args:
        n: Number of elements, vertices, or rows handled by the structure.

    Space Complexity:
        O(n) in the constructor input size or configured capacity

    Potential Convention:
        merge(a, b, w) enforces potential[b] - potential[a] = w, and diff(a, b)
        returns that difference. DSUWithPotential uses inv(potential[b]) *
        potential[a], so for addition its difference has the opposite sign.
    """
    def __init__(self, n: int) -> None:
        """Initialize a weighted disjoint-set data structure with `n` singleton sets.

        Args:
            n (int): The number of singleton sets.

        Time Complexity:
            O(n)

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.par_size = [-1] * n
        self.wt = [0] * n

    def leader(self, a: int) -> int:
        """
        Find the representative of the set that element `a` is part of, while updating the weights.

        Args:
            a (int): The element to find the representative of.

        Returns:
            int: The representative of the set.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        x = a
        order: list[int] = []
        while self.par_size[x] >= 0:
            order.append(x)
            x = self.par_size[x]
        for s in reversed(order):
            self.wt[s] += self.wt[self.par_size[s]]
            self.par_size[s] = x
        return x

    def merge(self, a: int, b: int, w: int = 0) -> bool:
        """
        Merge the sets that `a` and `b` are part of, while accounting for weights.

        Args:
            a (int): The first element.
            b (int): The second element.
            w (int): Required potential[b] - potential[a].

        Returns:
            bool: True if two components were joined; False if already joined
                with a consistent difference. Contradictions raise ValueError.

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.
            ValueError: If the requested weight contradicts existing constraints.

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        x = self.leader(a)
        y = self.leader(b)
        w += self.wt[a] - self.wt[b]
        if x == y:
            if w:
                raise ValueError("given weight is inconsistent with the existing weight")
            else:
                return False
        if -self.par_size[x] < -self.par_size[y]:
            x, y = y, x
            w = -w
        self.par_size[x] += self.par_size[y]
        self.par_size[y] = x
        self.wt[y] = w
        return True

    def same(self, a: int, b: int) -> bool:
        """
        Check if elements `a` and `b` are part of the same set.

        Args:
            a (int): The first element.
            b (int): The second element.

        Returns:
            bool: True if `a` and `b` are part of the same set, False otherwise.

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        return self.leader(a) == self.leader(b)

    def weight(self, a: int) -> int:
        """
        Get the weight of the element `a`.

        Args:
            a (int): The element.

        Returns:
            int: potential[a] - potential[leader(a)]. The component reference
                may change after a merge.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        self.leader(a)
        return self.wt[a]

    def diff(self, a: int, b: int) -> int:
        """
        Calculate the weight difference between elements `a` and `b`.

        Args:
            a (int): The first element.
            b (int): The second element.

        Returns:
            int: potential[b] - potential[a].

        Raises:
            ValueError: If `a` and `b` are not in the same set.

        Time Complexity:
            O(α(n)) amortized, where α is the inverse Ackermann function
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        if self.leader(a) == self.leader(b):
            return self.wt[b] - self.wt[a]
        else:
            raise ValueError("elements are not in the same set")

    def size(self, a: int) -> int:
        """Get the size of the set that `a` is part of.

        Args:
            a (int): The element.

        Returns:
            int: The size of the set.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            O(α(n)) amortized
        """
        assert 0 <= a < self.n
        return -self.par_size[self.leader(a)]


class DSUWithPotential(Generic[ValueT]):
    """Disjoint Set Union with potential/weight for general group operations.

    A generalized version of weighted DSU that supports arbitrary group operations
    instead of just integer addition. Maintains potential values for elements and
    supports queries for the group operation result between any two elements in
    the same component.

    Mathematical Model:
        - For each element, maintains a potential value in group (ValueT, •, e, inv)
        - merge(u, v, w) ensures: inv(potential[v]) • potential[u] = w
        - diff(u, v) returns: inv(potential[v]) • potential[u]

    Requirements:
        - (ValueT, mul_func, e) forms a group with identity e
        - inv_func(x) returns the inverse of x
        - mul_func must be associative: mul_func(mul_func(a, b), c) = mul_func(a, mul_func(b, c))
        - Identity: mul_func(e, x) = mul_func(x, e) = x
        - Inverse: mul_func(x, inv_func(x)) = mul_func(inv_func(x), x) = e

    Attributes:
        n: Number of elements, vertices, or rows handled by the structure.
        par_size: List where par_size[i] is the parent of i if par_size[i] >= 0, otherwise -size of the set for which i is the representative.
        potential: Relative group value inv(P[parent[i]]) * P[i], or e at a root.
            Path compression changes the reference parent but preserves differences.
        mul: Group operation function (associative, has identity, has inverse).
        inv: Group inverse function.
        e: Identity element of the group.

    Time Complexities:
        - __init__: O(n)
        - leader: O(α(n)) amortized
        - merge: O(α(n)) amortized
        - same: O(α(n)) amortized
        - diff: O(α(n)) amortized
        - size: O(α(n)) amortized

    Examples:
        >>> # Integer addition group
        >>> dsu = DSUWithPotential(5, lambda x, y: x + y, lambda x: -x, 0)
        >>> dsu.merge(0, 1, 3)  # potential[0] - potential[1] = 3
        True
        >>> dsu.merge(1, 2, 5)  # potential[1] - potential[2] = 5
        True
        >>> dsu.diff(0, 2)  # potential[0] - potential[2] = 8
        8

        >>> # Permutations form a non-commutative group.
        >>> def compose(p, q): return tuple(p[q[i]] for i in range(3))
        >>> def inverse(p): return tuple(p.index(i) for i in range(3))
        >>> dsu = DSUWithPotential(3, compose, inverse, (0, 1, 2))
        >>> dsu.merge(0, 1, (1, 0, 2))
        True
        >>> dsu.merge(1, 2, (0, 2, 1))
        True
        >>> dsu.diff(0, 2) == compose((0, 2, 1), (1, 0, 2))
        True

    Notes:
        This data structure is particularly useful for problems involving:
        - Coordinate transformations
        - Matrix equations
        - Modular arithmetic relations
        - Any constraint satisfaction problems over groups

    Space Complexity:
        O(n) in the constructor input size or configured capacity

    Callback Contract:
        Group operations must not mutate shared inputs. Bounds assume O(1)
        operations and fixed-size group values. Commutativity is not required.
    """
    def __init__(self, n: int, mul_func: Callable[[ValueT, ValueT], ValueT], inv_func: Callable[[ValueT], ValueT], e: ValueT) -> None:
        """Initialize a DSU with potential for n elements.

        Args:
            n (int): Number of elements (indexed 0 to n-1)
            mul_func (Callable[[ValueT, ValueT], ValueT]): Group operation function
            inv_func (Callable[[ValueT], ValueT]): Group inverse function
            e (ValueT): Identity element of the group

        Time Complexity:
            O(n)

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.par_size = [-1] * n
        self.potential = [e] * n
        self.mul = mul_func
        self.inv = inv_func
        self.e = e

    def leader(self, a: int) -> int:
        """
        Find the representative of the set containing element a.

        Performs path compression while updating potential values correctly.

        Args:
            a (int): Element to find the leader of (must be in [0, n))

        Returns:
            int: Representative of the set containing a

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            O(α(n)) amortized
        """
        assert 0 <= a < self.n
        x = a
        order: list[int] = []
        while self.par_size[x] >= 0:
            order.append(x)
            x = self.par_size[x]
        for s in reversed(order):
            self.potential[s] = self.mul(self.potential[self.par_size[s]], self.potential[s])
            self.par_size[s] = x
        return x

    def merge(self, a: int, b: int, w: ValueT) -> bool:
        """
        Merge the sets containing a and b with constraint w.

        Establishes the relation: inv(potential[b]) • potential[a] = w

        Args:
            a (int): First element (must be in [0, n))
            b (int): Second element (must be in [0, n))
            w (ValueT): Constraint value for the relation

        Returns:
            bool: True if merge was successful, False if already in same set

        Raises:
            ValueError: If the constraint is inconsistent with existing relations

        Examples:
            >>> dsu = DSUWithPotential(3, lambda x, y: x + y, lambda x: -x, 0)
            >>> dsu.merge(0, 1, 5)  # potential[0] - potential[1] = 5
            True
            >>> dsu.merge(1, 2, 3)  # potential[1] - potential[2] = 3
            True
            >>> dsu.merge(0, 2, 7)  # Inconsistent: should be 8, not 7
            Traceback (most recent call last):
                ...
            ValueError: given weight is inconsistent with the existing weight

        Time Complexity:
            O(α(n)) amortized
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        x = self.leader(a)
        y = self.leader(b)
        if x == y:
            if w != self.mul(self.inv(self.potential[b]), self.potential[a]):
                raise ValueError("given weight is inconsistent with the existing weight")
            else:
                return False
        if -self.par_size[x] < -self.par_size[y]:
            self.par_size[y] += self.par_size[x]
            self.par_size[x] = y
            self.potential[x] = self.mul(self.potential[b], self.mul(w, self.inv(self.potential[a])))
        else:
            self.par_size[x] += self.par_size[y]
            self.par_size[y] = x
            self.potential[y] = self.mul(self.potential[a], self.mul(self.inv(w), self.inv(self.potential[b])))
        return True

    def same(self, a: int, b: int) -> bool:
        """
        Check if elements a and b are in the same connected component.

        Args:
            a (int): First element (must be in [0, n))
            b (int): Second element (must be in [0, n))

        Returns:
            bool: True if a and b are in the same component, False otherwise

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.

        Time Complexity:
            O(α(n)) amortized
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        return self.leader(a) == self.leader(b)

    def diff(self, a: int, b: int) -> ValueT:
        """
        Calculate the group operation result between potentials of a and b.

        Returns inv(potential[b]) • potential[a], which represents the
        "difference" between a and b in the group.

        Args:
            a (int): First element (must be in [0, n))
            b (int): Second element (must be in [0, n))

        Returns:
            ValueT: The group operation result inv(potential[b]) • potential[a]

        Raises:
            ValueError: If a and b are not in the same connected component

        Examples:
            >>> dsu = DSUWithPotential(3, lambda x, y: x + y, lambda x: -x, 0)
            >>> dsu.merge(0, 1, 5)  # potential[0] - potential[1] = 5
            True
            >>> dsu.merge(1, 2, 3)  # potential[1] - potential[2] = 3
            True
            >>> dsu.diff(0, 2)  # potential[0] - potential[2] = 8
            8
            >>> dsu.diff(2, 0)  # potential[2] - potential[0] = -8
            -8

        Time Complexity:
            O(α(n)) amortized
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        if self.leader(a) == self.leader(b):
            return self.mul(self.inv(self.potential[b]), self.potential[a])
        else:
            raise ValueError("elements are not in the same set")

    def size(self, a: int) -> int:
        """
        Get the size of the connected component containing element a.

        Args:
            a (int): Element to query (must be in [0, n))

        Returns:
            int: Size of the component containing a

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            O(α(n)) amortized
        """
        assert 0 <= a < self.n
        return -self.par_size[self.leader(a)]

class PartiallyPersistentDSU:
    """Partially persistent disjoint-set union.

    The structure supports union operations on the latest version and
    connectivity queries against any past time step.

    Attributes:
        n: Number of elements, vertices, or rows handled by the structure.
        par_size: Current parent or negative current component size at a root.
        time: Time at which a node was joined to its parent; -1 for current roots.
        t: Current time step, incremented with each merge.

    Time Complexities:
        - ``leader`` / ``same`` / ``size`` / ``merge``: ``O(log n)``

    Space Complexity:
        - ``O(n)``

    Examples:
        >>> dsu = PartiallyPersistentDSU(3)
        >>> dsu.merge(0, 1)
        True
        >>> dsu.same(0, 1, 0)
        True

    Notes:
        Initial time is -1. Every valid merge attempt advances time, including
        attempts within one component. Queries accept -1 <= t <= self.t.
        Size histories grow only on successful merges, at most n - 1 times.
    """

    def __init__(self, n: int) -> None:
        """Initialize a partially persistent disjoint-set data structure with `n` singleton sets.
        A partially persistent DSU supports queries to past versions of the data structure.

        Args:
            n (int): The number of singleton sets.

        Time Complexity:
            O(n) in the constructor input size or configured capacity

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.par_size = [-1] * n
        self.t = -1
        self.time = [-1] * n
        self._size_history: list[list[tuple[int, int]]] = [[(-1, 1)] for _ in range(n)]

    def leader(self, a: int, t: int) -> int:
        """Find the representative of the set that element `a` is part of at time `t`.

        Args:
            a (int): The element to find the representative of.
            t (int): The time version of the DSU to query.

        Returns:
            int: The representative of the set at time `t`.

        Raises:
            AssertionError: If a is outside [0, n) or t is outside [-1, self.t].

        Time Complexity:
            O(log n)
        """
        assert 0 <= a < self.n
        assert -1 <= t <= self.t
        x = a
        while self.par_size[x] >= 0 and self.time[x] <= t:
            x = self.par_size[x]
        return x

    def same(self, a: int, b: int, t: int) -> bool:
        """Check if elements `a` and `b` are part of the same set at time `t`.

        Args:
            a (int): The first element.
            b (int): The second element.
            t (int): The time version of the DSU to query.

        Returns:
            bool: True if `a` and `b` are part of the same set at time `t`, False otherwise.

        Raises:
            AssertionError: If an element is outside [0, n) or t is outside [-1, self.t].

        Time Complexity:
            O(log n)
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        return self.leader(a, t) == self.leader(b, t)

    def merge(self, a: int, b: int) -> bool:
        """Merge the sets that `a` and `b` are part of at the current time. The time counter advances before recording each valid attempt, including already-connected pairs.

        Args:
            a (int): The first element.
            b (int): The second element.

        Returns:
            bool: True if the merge was successful, False if `a` and `b` were already part of the same set.

        Time Complexity:
            O(log n)

        Raises:
            AssertionError: If a or b is outside [0, n). The time is not advanced.
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        self.t += 1
        x = self.leader(a, self.t)
        y = self.leader(b, self.t)
        if x == y: return False
        if -self.par_size[x] < -self.par_size[y]: x, y = y, x
        self.par_size[x] += self.par_size[y]
        self.par_size[y] = x
        self.time[y] = self.t
        self._size_history[x].append((self.t, -self.par_size[x]))
        return True

    def size(self, a: int, t: int) -> int:
        """Get the size of the set that `a` is part of at time `t`.

        Args:
            a (int): The element.
            t (int): The time version of the DSU to query.

        Returns:
            int: The size of the set at time `t`.

        Raises:
            AssertionError: If a is outside [0, n) or t is outside [-1, self.t].

        Time Complexity:
            O(log n)
        """
        assert 0 <= a < self.n
        root = self.leader(a, t)
        history = self._size_history[root]
        index = bisect_right(history, (t, self.n + 1)) - 1
        return history[index][1]

class UndoableDSU:
    """Disjoint-set union with rollback support.

    Merge operations are recorded on a history stack and can be reverted in
    LIFO order with ``undo``.

    Attributes:
        n: Number of elements, vertices, or rows handled by the structure.
        par_size: List where par_size[i] is the parent of i if par_size[i] >= 0, otherwise -size of the set for which i is the representative.
        his: History stack recording the state of merged elements for undo operations.

    Time Complexities:
        - ``leader`` / ``same`` / ``size`` / ``merge``: ``O(log n)``
        - ``undo`` / ``snapshot``: ``O(1)``
        - ``rollback``: ``O(k + 1)`` to undo k merge attempts

    Space Complexity:
        - ``O(n + q)``, where ``q`` is the number of recorded merges

    Examples:
        >>> dsu = UndoableDSU(3)
        >>> dsu.merge(0, 1)
        True
        >>> dsu.undo()
        >>> dsu.same(0, 1)
        False

    Notes:
        Every merge attempt records one undo step, including already-connected
        pairs. Snapshot integers are history positions, not merge counts.
    """

    def __init__(self, n: int) -> None:
        """Initialize a undo-able disjoint-set data structure with `n` singleton sets.

        This DSU allows to undo merge operations.

        Args:
            n (int): The number of singleton sets.

        Time Complexity:
            O(n)

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.par_size = [-1] * n
        self.his: list[tuple[int, int]] = []

    def leader(self, a: int) -> int:
        """
        Find the representative of the set that element `a` is part of.

        Args:
            a (int): The element to find the representative of.

        Returns:
            int: The representative of the set.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= a < self.n
        x = a
        while self.par_size[x] >= 0:
            x = self.par_size[x]
        return x

    def same(self, a: int, b: int) -> bool:
        """
        Check if elements `a` and `b` are part of the same set.

        Args:
            a (int): The first element.
            b (int): The second element.

        Returns:
            bool: True if `a` and `b` are part of the same set, False otherwise.

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        return self.leader(a) == self.leader(b)

    def merge(self, a: int, b: int) -> bool:
        """
        Merge the sets that `a` and `b` are part of.

        Args:
            a (int): The first element.
            b (int): The second element.

        Returns:
            bool: True if the merge was successful, False if `a` and `b` were already part of the same set.

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        x = self.leader(a)
        y = self.leader(b)
        self.his.append((x, self.par_size[x]))
        self.his.append((y, self.par_size[y]))
        if x == y: return False
        if -self.par_size[x] < -self.par_size[y]: x, y = y, x
        self.par_size[x] += self.par_size[y]
        self.par_size[y] = x
        return True

    def size(self, a: int) -> int:
        """
        Get the size of the set that `a` is part of.

        Args:
            a (int): The element.

        Returns:
            int: The size of the set.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= a < self.n
        return -self.par_size[self.leader(a)]

    def undo(self) -> None:
        """Revert the most recent merge operation.

        Raises:
            ValueError: If there's no history to undo.

        Time Complexity:
            O(1)

        Returns:
            None.
        """
        if not self.his:
            raise ValueError("no history to undo")
        y, par_size_y = self.his.pop()
        x, par_size_x = self.his.pop()
        self.par_size[x] = par_size_x
        self.par_size[y] = par_size_y

    def snapshot(self) -> int:
        """Return a token identifying the current history position.

        Returns:
            int: Token to pass to rollback; not the number of merge attempts.

        Time Complexity:
            O(1)
        """
        return len(self.his)

    def rollback(self, snap: int) -> None:
        """Rollback the DSU to a previous state represented by the snapshot number.

        Args:
            snap (int): The snapshot number to rollback to.

        Raises:
            ValueError: If snap is negative, exceeds the current token, or is not a merge boundary.

        Time Complexity:
            O(k + 1), where k merge attempts are undone.

        Returns:
            None.
        """
        if snap < 0 or snap > len(self.his) or snap % 2:
            raise ValueError("invalid snapshot number")
        while snap < len(self.his):
            self.undo()


class RangeParallelDSU(Generic[ValueT, AggregateT]):
    """A DSU (Disjoint Set Union) structure that supports merging two equal-length
    intervals in parallel, while maintaining an accumulated “pair‐contribution” sum.

    Each base element (0 ≤ i < n) has a weight of type ValueT. Whenever two components
    with weights (w1, w2) are first merged at the base level (individual elements),
    we compute a contribution of type AggregateT via `pair_contribution(w1, w2)` and add it
    into a running total of type AggregateT using `add_sum(...)`. After merging, the new
    component’s weight is computed via `merge_value(w1, w2)`.

    Internally, there are floor(log₂(n)) + 1 levels of DSU.
    Level k manages intervals of length 2ᵏ for 0 ≤ k ≤ floor(log₂ n).  Merging two intervals [l, l+2ᵏ) and [r, r+2ᵏ)
    in level k implies that all pairs of size-2ᵏ subintervals are “joined” at once.
    If level-k DSU.merge(l, r) actually unites two distinct sets, we then recursively
    merge the two halves (of length 2ᵏ⁻¹ each) at level k-1, and so on, until base-level
    merges (k=0), where we update both the pair‐contribution sum and component weights.

    Already-connected blocks are skipped. A first merge can still process every
    element of the intervals; the benefit is amortized over repeated operations.
    Each level k stores n - 2^k + 1 interval starts, for O(n log(n + 1)) total nodes.

    Attributes:
        n (int): Number of base elements.
        merge_value (Callable[[ValueT, ValueT], ValueT]): How to combine two component weights.
        pair_contribution (Callable[[ValueT, ValueT], AggregateT]): Contribution to add when two ValueT-weights merge.
        add_sum (Callable[[AggregateT, AggregateT], AggregateT]): How to add two AggregateT-values together.
        total_sum (AggregateT): Accumulated sum of all prior pair‐contributions.
        vals (List[ValueT]): Current weight of each component, stored at its representative.
        ufs (List[DisjointSetUnion]): A list of DSU structures, one per level k.

    Examples:
        >>> # Suppose we want to keep integer weights and sums mod 1000000007:
        >>> MOD = 10**9 + 7
        >>> def merge_value(a: int, b: int) -> int:
        ...     return (a + b) % MOD
        >>> def pair_contribution(a: int, b: int) -> int:
        ...     return (a * b) % MOD
        >>> def add_sum(x: int, y: int) -> int:
        ...     return (x + y) % MOD
        >>>
        >>> weights = [2, 3, 5, 7, 11, 13, 17, 19]
        >>> rpd = RangeParallelDSU(
        ...     n=8,
        ...     initial_weights=weights,
        ...     merge_value=merge_value,
        ...     pair_contribution=pair_contribution,
        ...     add_sum=add_sum,
        ...     sum_identity=0
        ... )
        >>> # Merge intervals [1,4) and [4,7): pairs (1,4), (2,5), (3,6)
        >>> rpd.range_merge(3, 1, 4)
        >>> # pair_sum = 3*11 + 5*13 + 7*17 = 33 + 65 + 119 = 217 mod MOD
        >>> print(rpd.pair_sum())
        217
        >>> # Check connectivity at base level
        >>> print(rpd.same(2, 5), rpd.same(0, 1))
        True False
        >>> # Element 2 belongs to the component containing weights 5 and 13.
        >>> # (5 + 13 mod MOD)
        >>> print(rpd.comp_weight(2))
        18

    Raises:
        ValueError: If n <= 0 or initial_weights does not contain n entries.

    Space Complexity:
        O(n log n) in the constructor input size or configured capacity

    Callback Contract:
        Callbacks must not mutate their inputs. Merge order follows internal
        block traversal and union by size, not left-to-right element order.
        Use associative, commutative merge_value when component weights must
        depend only on their members. An arbitrary pair_contribution records
        contributions in the actual merge order; it is not necessarily a sum
        over all pairs of original elements.
    """

    def __init__(
        self,
        n: int,
        initial_weights: list[ValueT],
        merge_value: Callable[[ValueT, ValueT], ValueT],
        pair_contribution: Callable[[ValueT, ValueT], AggregateT],
        add_sum: Callable[[AggregateT, AggregateT], AggregateT],
        sum_identity: AggregateT,
    ) -> None:
        """Initialize the RangeParallelDSU for `n` elements with given operations.

        Args:
            n (int): Number of base elements.
            initial_weights (list[ValueT]): length-n list of each element’s initial weight.
            merge_value (Callable[[ValueT, ValueT], ValueT]): Function to combine two component weights.
            pair_contribution (Callable[[ValueT, ValueT], AggregateT]): Function to compute AggregateT-contribution when merging weights.
            add_sum (Callable[[AggregateT, AggregateT], AggregateT]): Function to add two AggregateT-values for the running sum.
            sum_identity (AggregateT): Identity element for the accumulated sum of type AggregateT.

        Raises:
            ValueError: If n ≤ 0 or len(initial_weights) ≠ n.

        Time Complexity:
            O(n log(n + 1)) to initialize all interval starts at every level.

        Returns:
            None.
        """
        if n <= 0:
            raise ValueError("n must be positive")
        if len(initial_weights) != n:
            raise ValueError(
                f"Expected {n} initial weights, got {len(initial_weights)}"
            )

        self.n = n
        self.merge_value = merge_value
        self.pair_contribution = pair_contribution
        self.add_sum = add_sum
        self.total_sum: AggregateT = sum_identity
        self.vals: list[ValueT] = list(initial_weights)
        self.log = self.n.bit_length()

        # Build one DSU per level k, each of size (n - 2^k + 1).
        # Level k manages intervals of length 2^k;
        # an index i in DSU[k] represents the interval [i, i + 2^k).
        self.ufs: list[DisjointSetUnion] = []
        for k in range(self.log):
            length = self.n - (1 << k) + 1
            self.ufs.append(DisjointSetUnion(length))

    def same(self, u: int, v: int) -> bool:
        """
        Check if elements u and v belong to the same connected component
        at the base (k=0) level.

        Args:
            u: First base-level index to compare.
            v: Second base-level index to compare.

        Returns:
            bool: True if they share the same component, False otherwise.

        Time Complexity:
            O(α(n)), where α is the inverse Ackermann function.
        """
        return self.ufs[0].same(u, v)

    def comp_weight(self, u: int) -> ValueT:
        """
        Get the current component-weight (type ValueT) for the component containing u.

        Args:
            u (int): A base‐level index (0 ≤ u < n).

        Returns:
            ValueT: The weight stored at the representative of u’s component.

        Time Complexity:
            O(α(n)).
        """
        root = self.ufs[0].leader(u)
        return self.vals[root]

    def pair_sum(self) -> AggregateT:
        """
        Return the accumulated sum (type AggregateT) of all pair‐contributions so far.

        Each time two base‐level components with weights (w1, w2) merge for
        the first time, we add `pair_contribution(w1, w2)` to this running total.

        Returns:
            AggregateT: The current total of pair‐contributions.

        Time Complexity:
            O(1).
        """
        return self.total_sum

    def range_merge(self, length: int, start1: int, start2: int) -> None:
        """
        Merge the interval [start1, start1+length) with [start2, start2+length) in parallel.

        For each i in [0..length-1], elements start1+i and start2+i become
        connected (in the same component). Internally, this is done by:
          1. Decompose `length` into powers of two: length = ∑ (2^b_i).
          2. For each block of size 2^b, at level b we attempt DSU[b].merge(i1, i2).
             If that succeeds, we recursively (iteratively) merge the two halves
             of size 2^(b-1) at level (b-1), and so on down to level 0.
          3. At level 0 (single indices), when two distinct roots ru, rv merge,
             we compute `pair_contribution(vals[ru], vals[rv])` and add it to
             `total_sum = add_sum(total_sum, contrib)`, then update the new
             component’s weight as `merge_value(vals[new_root], vals[old_root])`.

        Args:
            length (int): The size of each interval to merge (must be non-negative).
            start1 (int): Starting index of the first interval (0 ≤ start1 ≤ n).
            start2 (int): Starting index of the second interval (0 ≤ start2 ≤ n).

        Returns:
            None. Updates connectivity, component weights, and the pair sum.

        Raises:
            AssertionError: If length is negative or either interval lies
                outside [0, n).

        Time Complexity:
            O((length + 1) log(n + 1)) for a single call in the worst case.
            Across q calls, O((n + q) log(n + 1) α(n)) total DSU work,
            because each successful block union is expanded only once.
            These bounds assume O(1) callback operations.

        Space Complexity:
            O(log(n + 1)) auxiliary stack space.

        """
        assert length >= 0  # non-negative range length
        assert 0 <= start1 <= self.n and 0 <= start2 <= self.n  # interval starts
        assert start1 + length <= self.n and start2 + length <= self.n  # interval ends

        stack: list[tuple[int, int, int]] = []
        i1, i2 = start1, start2
        rem = length
        while rem > 0:
            b = rem.bit_length() - 1  # largest b s.t. 2^b ≤ rem
            block_size = 1 << b
            stack.append((b, i1, i2))
            i1 += block_size
            i2 += block_size
            rem -= block_size

        while stack:
            level, a1, a2 = stack.pop()
            dsu = self.ufs[level]
            if level == 0:
                ru = dsu.leader(a1)
                rv = dsu.leader(a2)
                if ru != rv:
                    self.total_sum = self.add_sum(self.total_sum, self.pair_contribution(self.vals[ru], self.vals[rv]))
                    dsu.merge(ru, rv)
                    new_root = dsu.leader(ru)
                    old_root = rv if new_root == ru else ru
                    self.vals[new_root] = self.merge_value(self.vals[new_root], self.vals[old_root])
            else:
                if not dsu.merge(a1, a2): continue # Already connected under this level.
                half = 1 << (level - 1)
                stack.append((level - 1, a1 + half, a2 + half))
                stack.append((level - 1, a1, a2))


class QueryDSU(Generic[ValueT]):
    """
    Query-based Disjoint Set Union with path optimization based on a custom function.

    A specialized DSU that maintains an additional value m[v] for each node v, which
    represents an "optimal" element in the path from v to its root according to a
    user-defined function f and comparison operator op.

    This data structure is particularly useful in algorithms where you need to:
    - Find the minimum/maximum element on a path to the root
    - Track specific properties along paths in a forest
    - Implement path queries in algorithms like dominator tree construction

    Mathematical Model:
        - Each node v has a parent par[v] and a stored index m[v]
        - f(m[v]) represents the "value" of the element stored at v
        - During path compression, m[v] is updated to the "best" element on the path
          from v to root according to the operator op

    Time Complexities:
        - __init__: O(n)
        - leader: O(log n) amortized; O(n) for one call
        - eval: O(log n) amortized; O(n) for one call
        - link: O(log n) amortized; O(n) for one call

    Attributes:
        n: Number of elements
        par: Parent array where par[v] is the parent of v
        m: Array where m[v] stores the "optimal" element index on the path
        f: Function that maps element indices to comparable values of type ValueT
        op: Binary operator that selects the "better" of two ValueT values
            (typically min or max)

    Examples:
        >>> # Find minimum value on path to root
        >>> values = [10, 5, 8, 3, 12, 7, 9, 2]
        >>> dsu = QueryDSU(8, lambda x: values[x], min)
        >>>
        >>> # Build a tree: 0 -> 1 -> 2 -> 3
        >>> dsu.link(3, 2)
        >>> dsu.link(2, 1)
        >>> dsu.link(1, 0)
        >>>
        >>> # eval(3) returns the index with minimum value on path 3->2->1->0
        >>> best_idx = dsu.eval(3)
        >>> print(best_idx)  # 3 (has value 3, which is minimum on path)
        3

        For dominator-tree construction, the callback can instead map each
        vertex to the DFS index of its semidominator.

    Notes:
        The operator op should be:
        - Associative and commutative for correctness
        - Selective: op(x, y) must equal x or y, since eval returns an index
        - Common choices: min or max; gcd/lcm are not valid in general
        - Ties select the closest matching ancestor to the root
        The callback f should normally return fixed values. If values change,
        the caller must ensure that previously discarded candidates never
        become preferable to retained candidates. This is not a structure
        for arbitrary point updates to path minima/maxima.
        Complexity bounds assume O(1) callbacks. Path compression is iterative;
        a single call may use O(n) temporary stack space.

    Space Complexity:
        O(n) in the constructor input size or configured capacity
    """
    def __init__(self, n: int, f: Callable[[int], ValueT], op: Callable[[ValueT, ValueT], ValueT]) -> None:
        """Initialize QueryDSU with n singleton sets.

        Time Complexity: O(n)

        Args:
            n: Number of elements (must be nonnegative)
            f: Function mapping indices to values of type ValueT
            op: Binary operator for comparing/selecting ValueT values

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.par = [i for i in range(n)]
        self.m = [i for i in range(n)]
        self.f = f
        self.op = op

    def leader(self, v: int) -> int:
        """Find the root of the tree containing v with path compression.

        During path compression, updates m[v] to store the "best" element
        on the path from v to root according to the operator op.

        Args:
            v: Element to find the root of (must be in [0, n))

        Returns:
            int: Root of the tree containing v

        Time Complexity:
            O(log n) amortized; O(n) for one call

        Raises:
            AssertionError: If an element is outside [0, n).
        """
        assert 0 <= v < self.n
        path: list[int] = []
        root = v
        while self.par[root] != root:
            path.append(root)
            root = self.par[root]
        for node in reversed(path):
            parent = self.par[node]
            fv = self.f(self.m[node])
            fp = self.f(self.m[parent])
            if self.op(fv, fp) == fp:
                self.m[node] = self.m[parent]
            self.par[node] = root
        return root

    def eval(self, v: int) -> int:
        """Get the optimal element index on the path from v to its root.

        Returns the index of the element with the "best" value according to
        the operator op among all elements on the path from v to the root.

        Args:
            v: Element to evaluate (must be in [0, n))

        Returns:
            int: Index of the optimal element on the path to root

        Examples:
            >>> values = [10, 5, 8, 3]
            >>> dsu = QueryDSU(4, lambda x: values[x], min)
            >>> dsu.link(3, 2)
            >>> dsu.link(2, 1)
            >>> dsu.link(1, 0)
            >>> print(dsu.eval(3))  # Returns 3 (has minimum value 3)
            3

        Time Complexity:
            O(log n) amortized; O(n) for one call

        Raises:
            AssertionError: If an element is outside [0, n).
        """
        self.leader(v)
        return self.m[v]

    def link(self, child: int, parent: int) -> None:
        """Make parent the parent of child in the forest structure.

        IMPORTANT CONDITIONS:
        1. child must be a root (i.e., par[child] == child) before calling link
        2. child and parent must be in different trees
        3. The link operation is performed directly without union-by-rank

        This is a low-level operation typically used in algorithms that build
        specific tree structures (like dominator trees) where the parent-child
        relationships are predetermined.

        Args:
            child: Node to be linked (must be a root, i.e., par[child] == child)
            parent: Node that will become the parent of child

        Raises:
            AssertionError: If an element is outside [0, n).
            ValueError: If child is not a root
            ValueError: If child and parent are already in the same connected component

        Examples:
            >>> dsu = QueryDSU(4, lambda x: x, min)
            >>> # Build tree: 0 <- 1 <- 2 <- 3
            >>> dsu.link(1, 0)  # Make 0 parent of 1
            >>> dsu.link(2, 1)  # Make 1 parent of 2
            >>> dsu.link(3, 2)  # Make 2 parent of 3
            >>>
            >>> # Error cases:
            >>> dsu.link(1, 3)  # 1 is not a root.
            Traceback (most recent call last):
                ...
            ValueError: Node 1 is not a root (par[1] = 0)
            >>> dsu.link(0, 2)  # Both vertices have root 0.
            Traceback (most recent call last):
                ...
            ValueError: Nodes 0 and 2 are already in the same connected component

        Time Complexity:
            O(log n) amortized; O(n) for one call

        Returns:
            None.
        """
        assert 0 <= child < self.n
        assert 0 <= parent < self.n
        if self.par[child] != child:
            raise ValueError(f"Node {child} is not a root (par[{child}] = {self.par[child]})")
        if self.leader(child) == self.leader(parent):
            raise ValueError(f"Nodes {child} and {parent} are already in the same connected component")
        self.par[child] = parent


class DSUOnlyPathHalving:
    """
    Disjoint Set Union with only path halving optimization and explicit parent-child relationships.

    Links choose the parent explicitly instead of using union by size or rank.
    Path halving preserves component roots but rewrites parent pointers, so
    this structure does not retain the original tree's ancestor relationships.
    ``same`` tests component membership, not ancestry. A single leader lookup
    can take O(n) time before paths have been shortened.

    Attributes:
        n: Number of elements
        par: Parent array where par[v] is the parent of v (par[v] == v if v is a root)

    Time Complexities:
        - leader: O(log n) amortized
        - same: O(log n) amortized
        - link: O(log n) amortized

    Space Complexity:
        O(n) in the constructor input size or configured capacity

    Examples:
        >>> dsu = DSUOnlyPathHalving(5)
        >>> dsu.link(1, 0)  # Make 0 the parent of 1
        >>> dsu.link(2, 0)  # Make 0 the parent of 2
        >>> dsu.link(3, 1)  # Attach 3 to the component containing 1 (root 0)
        >>> dsu.link(4, 1)  # Attach 4 to the same component
        >>> dsu.same(3, 4)  # True, both are in the component with root 0
        True
        >>> dsu.same(2, 3)  # Both have root 0; this does not test ancestry.
        True
    """
    def __init__(self, n: int) -> None:
        """Initialize a DSU with path halving optimization.

        Args:
            n (int): Number of elements (indexed 0 to n-1)

        Time Complexity: O(n)

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.par = [i for i in range(n)]

    def leader(self, a: int) -> int:
        """
        Find the root of the tree containing element a.

        Args:
            a (int): Element to find the leader of (must be in [0, n))

        Returns:
            int: Root of the tree containing element a

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            O(log n) amortized
        """
        assert 0 <= a < self.n
        v = a
        while self.par[v] != v:
            self.par[v] = self.par[self.par[v]]
            v = self.par[v]
        return v

    def same(self, a: int, b: int) -> bool:
        """
        Check if elements a and b are in the same connected component.

        Args:
            a (int): First element (must be in [0, n))
            b (int): Second element (must be in [0, n))

        Returns:
            bool: True if a and b are in the same component, False otherwise

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.

        Time Complexity:
            O(log n) amortized
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        return self.leader(a) == self.leader(b)

    def link(self, child: int, parent: int) -> None:
        """Attach the component root of child to the component root of parent.

        child need not itself be a root. Original tree edges are not retained.

        Args:
            child (int): Child element (must be in [0, n))
            parent (int): Parent element (must be in [0, n))

        Raises:
            ValueError: If parent and child are already in the same component

        Time Complexity:
            O(log n) amortized

        Returns:
            None.
        """
        assert 0 <= child < self.n
        assert 0 <= parent < self.n
        child_root = self.leader(child)
        parent_root = self.leader(parent)
        if child_root == parent_root:
            raise ValueError(f"Elements {parent} and {child} are already in the same component")
        self.par[child_root] = parent_root
