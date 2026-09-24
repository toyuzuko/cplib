#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Callable, Sequence
from operator import sub
from typing import Generic, Literal, TypeAlias, cast

from cplib.graph.eulertourtree import EulerTourTree
from cplib.tools.type import ValueT, AggregateT, ActionT, VertexValueT


QueryPayload: TypeAlias = object


class UndoableDSUWithComponentAggregate(Generic[ValueT]):
    """
    Undoable Disjoint Set Union with component aggregate support.

    This DSU maintains an aggregate for each connected component and supports
    undoing merge operations. The aggregate must form a commutative group so
    that merged components can be separated again after later vertex updates.

    Attributes:
        n: Number of elements.
        par_size: Parent and size array (negative values represent size for roots).
        his: History stack for undo operations.
        comp_agg: Aggregate value of each rooted component.

    Examples:
        >>> dsu = UndoableDSUWithComponentAggregate(5, lambda a, b: a + b, lambda x: -x, 0)
        >>> dsu.vertex_apply(0, 10)
        >>> dsu.vertex_apply(2, 20)
        >>> dsu.merge(0, 2)
        True
        >>> print(dsu.component_aggregate(0))  # 30
        30
        >>> dsu.undo()
        >>> print(dsu.component_aggregate(0))  # 10
        10

    Complexity Notation:
        n: Number of elements.
        h: Number of stored history entries.

    Space Complexity:
        O(n + h)

    """

    def __init__(self, n: int, op: Callable[[ValueT, ValueT], ValueT], inv: Callable[[ValueT], ValueT], e: ValueT) -> None:
        """Initialize DSU with n elements.

        Args:
            n: Number of elements (0-indexed).
            op: Binary operation on component aggregates.
            inv: Inverse operation for the component aggregate group.
            e: Identity element of the component aggregate group.

        Returns:
            ``None``.

        Time Complexity:
            ``O(n)``

        """
        self.n = n
        self.op = op
        self.inv = inv
        self.e = e
        self.par_size = [-1] * n
        self.his: list[tuple[int, int]] = []
        self.comp_agg = [e for _ in range(n)]

    def leader(self, a: int) -> int:
        """
        Find the leader (root) of element a.

        Args:
            a: Element to find leader for.

        Returns:
            Leader element of the component containing a.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.
        Time Complexity:
            ``O(log n)``

        """
        assert 0 <= a < self.n
        x = a
        while self.par_size[x] >= 0:
            x = self.par_size[x]
        return x

    def same(self, a: int, b: int) -> bool:
        """
        same API.

        Args:
            a: First operand, coefficient, or endpoint depending on the method.
            b: Second operand, coefficient, or endpoint depending on the method.

        Returns:
            ``True`` if ``a`` and ``b`` are in the same component.

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        return self.leader(a) == self.leader(b)

    def merge(self, a: int, b: int) -> bool:
        """
        Merge components containing elements a and b.

        Args:
            a: First element.
            b: Second element.

        Returns:
            True if components were merged, False if already in same component.

        Notes:
            Uses union by size heuristic. History is recorded for undo.

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.
        Time Complexity:
            ``O(log n)``

        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        x = self.leader(a)
        y = self.leader(b)
        if -self.par_size[x] < -self.par_size[y]:
            x, y = y, x
        self.his.append((x, self.par_size[x]))
        self.his.append((y, self.par_size[y]))
        if x == y:
            return False
        self.par_size[x] += self.par_size[y]
        self.par_size[y] = x
        self.comp_agg[x] = self.op(self.comp_agg[x], self.comp_agg[y])
        return True

    def size(self, a: int) -> int:
        """
        Return the size of the component containing ``a``.

        Args:
            a: First operand, coefficient, or endpoint depending on the method.

        Returns:
            Number of elements in the component containing ``a``.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        return -self.par_size[self.leader(a)]

    def undo(self) -> None:
        """
        Undo the last merge operation.

        Raises:
            ValueError: If no history to undo.

        Returns:
            ``None``.

        Notes:
            Each merge operation creates 2 history entries.
        Time Complexity:
            O(1)

        """
        if not self.his:
            raise ValueError('no history to undo')
        y, par_size_y = self.his.pop()
        x, par_size_x = self.his.pop()
        if self.par_size[x] != par_size_x:
            self.comp_agg[x] = self.op(self.comp_agg[x], self.inv(self.comp_agg[y]))
        self.par_size[x] = par_size_x
        self.par_size[y] = par_size_y

    def snapshot(self) -> int:
        """
        Take a snapshot of current state.

        Returns:
            Snapshot identifier for rollback.

        Time Complexity:
            O(1)
        """
        return len(self.his)

    def rollback(self, snap: int) -> None:
        """
        Rollback to a previous snapshot.

        Args:
            snap: Snapshot identifier from snapshot().

        Returns:
            ``None``.

        Raises:
            ValueError: If snapshot number is invalid.
        Time Complexity:
            ``O(|history| - snap)``

        """
        if snap < 0 or snap > len(self.his):
            raise ValueError('invalid snapshot number')
        while snap < len(self.his):
            self.undo()

    def component_aggregate(self, a: int) -> ValueT:
        """
        Return the aggregate of the component containing a.

        Args:
            a: First operand, coefficient, or endpoint depending on the method.

        Returns:
            Aggregate value of the component containing ``a``.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        return self.comp_agg[self.leader(a)]

    def vertex_apply(self, a: int, x: ValueT) -> None:
        """
        Apply a vertex contribution to the component aggregate.

        Args:
            a: Vertex to update.
            x: Contribution to add into the component aggregate group.

        Returns:
            ``None``.

        Notes:
            The contribution is applied to all ancestors up to the current root
            so that later undo operations keep component aggregates consistent.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.
        Time Complexity:
            ``O(log n)``

        """
        assert 0 <= a < self.n
        while a >= 0:
            self.comp_agg[a] = self.op(self.comp_agg[a], x)
            a = self.par_size[a]


class UndoableDSUWithLazyAggregate(Generic[VertexValueT, AggregateT, ActionT]):
    """
    Undoable DSU supporting vertex updates and component lazy updates.

    This structure supports:

    - per-vertex updates on values of type `VertexValueT`
    - per-component lazy updates of type `ActionT`
    - per-component aggregates of type `AggregateT`

    To make `undo()` work after both `merge()` and later updates, the supplied
    operations must satisfy a few algebraic requirements.

    Requirements:
        `op` / `agg_inv` / `agg_e`:
            `AggregateT` must behave as a commutative group. `op` combines component
            aggregates, `agg_e` is its identity, and `agg_inv` removes a child
            component from a merged parent during `undo()`.
        `composition` / `difference` / `lazy_id`:
            Lazy tags of type `ActionT` must form a group under composition.
            `composition(f, g)` means "apply `g`, then apply `f`". `difference`
            must satisfy `composition(difference(f, g), g) == f`. Thus
            `difference(lazy_id, g)` gives the inverse of `g`. Composition
            need not be commutative.
        `mapping_value` / `mapping_aggregate`:
            They must describe the same update on a single value and on an
            aggregate. In particular, applying `f` to every vertex in a
            component of size `sz` must match `mapping_aggregate(f, agg, sz)`.
            Mapping must respect action composition and aggregation over disjoint
            components, using the sum of their sizes. Callbacks must not mutate
            their arguments.
        `value_to_aggregate`:
            Converts one vertex value into the corresponding singleton
            aggregate. A per-vertex update uses this to compute the aggregate
            delta that has to be pushed to ancestors.

    Notes:
        Undo and rollback reverse merges only. Vertex and component updates
        remain applied to every vertex they affected, even after a split.

    Complexity Notation:
        n: Number of vertices.
        h: Number of stored history entries.

    Space Complexity:
        O(n + h)

    """

    def __init__(
        self,
        values: list[VertexValueT],
        op: Callable[[AggregateT, AggregateT], AggregateT],
        agg_inv: Callable[[AggregateT], AggregateT],
        agg_e: AggregateT,
        mapping_value: Callable[[ActionT, VertexValueT], VertexValueT],
        mapping_aggregate: Callable[[ActionT, AggregateT, int], AggregateT],
        composition: Callable[[ActionT, ActionT], ActionT],
        difference: Callable[[ActionT, ActionT], ActionT],
        lazy_id: ActionT,
        value_to_aggregate: Callable[[VertexValueT], AggregateT],
    ) -> None:
        """Initialize the DSU.

        Args:
            values: Initial vertex values.
            op: Binary operation on component aggregates. It should be
                commutative, because component order is irrelevant.
            agg_inv: Inverse operation for the aggregate group. This is used to
                subtract a child component from a merged parent during `undo()`.
            agg_e: Identity element of the aggregate group.
            mapping_value: Applies one lazy tag to one vertex value.
            mapping_aggregate: Applies one lazy tag to a whole component
                aggregate. The third argument is the component size, because
                many aggregates need it. For example, for integer sum with
                range-add, `mapping_aggregate(f, s, sz) = s + f * sz`.
            composition: Composes lazy actions as `f after g`.
            difference: Returns `d` satisfying `composition(d, g) == f`. This
                is needed to recover the part of a lazy tag that was added after
                a merge happened.
            lazy_id: Identity lazy action.
            value_to_aggregate: Lifts one vertex value into a singleton
                aggregate.

        Typical examples:
            Integer add / sum:
                `VertexValueT = AggregateT = ActionT = int`,
                `op = +`,
                `agg_inv(x) = -x`,
                `mapping_value(f, x) = x + f`,
                `mapping_aggregate(f, s, sz) = s + f * sz`.
            XOR update / XOR aggregate:
                `VertexValueT = AggregateT = ActionT = int`,
                `op = xor`,
                `agg_inv(x) = x`,
                `mapping_value(f, x) = x ^ f`,
                `mapping_aggregate(f, s, sz) = s ^ (f if sz & 1 else 0)`.

        Returns:
            ``None``.

        Time Complexity:
            ``O(n)``

        """
        self.n = len(values)
        self.op = op
        self.agg_inv = agg_inv
        self.agg_e = agg_e
        self.mapping_value = mapping_value
        self.mapping_aggregate = mapping_aggregate
        self.composition = composition
        self.difference = difference
        self.lazy_id = lazy_id
        self.value_to_aggregate = value_to_aggregate
        self.par_size = [-1] * self.n
        self.tag = [lazy_id for _ in range(self.n)]
        self.value = values[:]
        self.sub_agg = [value_to_aggregate(v) for v in values]
        self.his: list[tuple[bool, int, int, int, int]] = []

    def leader(self, a: int) -> int:
        """
        Find the leader (root) of element a.

        Args:
            a: Vertex index.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Returns:
            Leader of the component containing ``a``.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        x = a
        while self.par_size[x] >= 0:
            x = self.par_size[x]
        return x

    def same(self, a: int, b: int) -> bool:
        """
        Return whether a and b are in the same component.

        Args:
            a: Vertex index.
            b: Second vertex index.

        Returns:
            ``True`` if ``a`` and ``b`` are in the same component.

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        return self.leader(a) == self.leader(b)

    def size(self, a: int) -> int:
        """
        Return the size of the component containing a.

        Args:
            a: Vertex index.

        Returns:
            Number of vertices in the component containing ``a``.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        return -self.par_size[self.leader(a)]

    def merge(self, a: int, b: int) -> bool:
        """
        Merge components containing a and b.

        Args:
            a: Vertex index.
            b: Second vertex index.

        Returns:
            ``True`` if two components were merged, otherwise ``False``.

        Raises:
            AssertionError: If any of ``0 <= a < n``, ``0 <= b < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        assert 0 <= b < self.n
        x = self.leader(a)
        y = self.leader(b)
        if x == y:
            self.his.append((False, x, 0, y, 0))
            return False
        if -self.par_size[x] < -self.par_size[y]:
            x, y = y, x
        size_y = -self.par_size[y]
        self.his.append((True, x, self.par_size[x], y, self.par_size[y]))
        self.par_size[x] += self.par_size[y]
        self.par_size[y] = x
        self.sub_agg[x] = self.op(self.sub_agg[x], self.sub_agg[y])
        # Store the attached component in the parent tag's coordinate system.
        inverse = self.difference(self.lazy_id, self.tag[x])
        self.tag[y] = self.composition(inverse, self.tag[y])
        self.sub_agg[y] = self.mapping_aggregate(inverse, self.sub_agg[y], size_y)
        return True

    def undo(self) -> None:
        """
        Undo the last merge operation.

        Raises:
            ValueError: If no history to undo.

        Returns:
            ``None``.

        Time Complexity:
            O(1)
        """
        if not self.his:
            raise ValueError('no history to undo')
        merged, x, par_size_x, y, par_size_y = self.his.pop()
        if not merged:
            return
        size_y = -par_size_y
        restored_y = self.mapping_aggregate(self.tag[x], self.sub_agg[y], size_y)
        self.par_size[x] = par_size_x
        self.par_size[y] = par_size_y
        self.sub_agg[x] = self.op(self.sub_agg[x], self.agg_inv(restored_y))
        self.sub_agg[y] = restored_y
        self.tag[y] = self.composition(self.tag[x], self.tag[y])

    def snapshot(self) -> int:
        """
        Take a snapshot of current state.

        Returns:
            Snapshot identifier for rollback.

        Time Complexity:
            O(1)
        """
        return len(self.his)

    def rollback(self, snap: int) -> None:
        """
        Rollback to a previous snapshot.

        Args:
            snap: Snapshot identifier from ``snapshot()``.

        Raises:
            ValueError: If ``snap`` is outside the valid history range.

        Returns:
            ``None``.

        Time Complexity:
            ``O(|history| - snap)``
        """
        if snap < 0 or snap > len(self.his):
            raise ValueError('invalid snapshot number')
        while snap < len(self.his):
            self.undo()

    def vertex_apply(self, a: int, f: ActionT) -> None:
        """
        Apply a lazy action to a single vertex.

        Args:
            a: Vertex to update.
            f: Lazy action applied to the current value of ``a``.

        Returns:
            ``None``.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        path: list[int] = []
        tag = self.lazy_id
        v = a
        while v >= 0:
            path.append(v)
            tag = self.composition(self.tag[v], tag)
            v = self.par_size[v]
        old = self.value[a]
        current = self.mapping_value(tag, old)
        updated = self.mapping_value(f, current)
        new = self.mapping_value(self.difference(self.lazy_id, tag), updated)
        self.value[a] = new
        for v in path:
            old = self.mapping_value(self.tag[v], old)
            new = self.mapping_value(self.tag[v], new)
            delta = self.op(self.value_to_aggregate(new), self.agg_inv(self.value_to_aggregate(old)))
            self.sub_agg[v] = self.op(self.sub_agg[v], delta)

    def component_apply(self, a: int, f: ActionT) -> None:
        """
        Apply a lazy action to the whole component containing a.

        Args:
            a: Vertex identifying the target component.
            f: Mapping function or lazy tag.

        Returns:
            ``None``.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        r = self.leader(a)
        self.tag[r] = self.composition(f, self.tag[r])
        self.sub_agg[r] = self.mapping_aggregate(f, self.sub_agg[r], -self.par_size[r])

    def vertex_get(self, a: int) -> VertexValueT:
        """
        Return the current value of vertex a.

        Args:
            a: Vertex to query.

        Returns:
            Current value stored at ``a`` after all pending component updates.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        tag = self.lazy_id
        v = a
        while v >= 0:
            tag = self.composition(self.tag[v], tag)
            v = self.par_size[v]
        return self.mapping_value(tag, self.value[a])

    def component_aggregate(self, a: int) -> AggregateT:
        """
        Return the aggregate of the component containing a.

        Args:
            a: Vertex identifying the target component.

        Returns:
            Aggregate of the connected component containing ``a``.

        Raises:
            AssertionError: If ``0 <= a < n`` is false.

        Time Complexity:
            ``O(log n)``
        """
        assert 0 <= a < self.n
        return self.sub_agg[self.leader(a)]


class OfflineDynamicConnectivity(Generic[VertexValueT, AggregateT, ActionT]):
    """
    Offline dynamic connectivity with queries.

    Handles edge insertions/deletions and connectivity queries offline.
    Supports vertex and component updates together with connectivity queries.
    Uses segment tree of time intervals with undoable DSU.

    Attributes:
        n: Number of vertices.
        time_max: Number of allowed timestamps (constructor limit plus one).
        dsu: Undoable DSU structure.
        seg: Segment tree for time intervals.
        queries: List of queries at each time.

    Examples:
        >>> dc = OfflineDynamicConnectivity(4, 5)
        >>> dc.insert_edge(0, 1, 0)
        >>> dc.erase_edge(0, 1, 3)
        >>> dc.set_query_is_same(0, 1, 2)
        >>> results = dc.run()

    Space Complexity:
        O(n + time_max + q + k log time_max), where ``q`` is the number of stored point queries and ``k`` is the number of edge-active intervals

    """
    def __init__(
        self,
        n: int,
        time_max: int,
        values: list[VertexValueT] | None = None,
        op: Callable[[AggregateT, AggregateT], AggregateT] | None = None,
        agg_inv: Callable[[AggregateT], AggregateT] | None = None,
        agg_e: AggregateT | None = None,
        mapping_value: Callable[[ActionT, VertexValueT], VertexValueT] | None = None,
        mapping_aggregate: Callable[[ActionT, AggregateT, int], AggregateT] | None = None,
        composition: Callable[[ActionT, ActionT], ActionT] | None = None,
        difference: Callable[[ActionT, ActionT], ActionT] | None = None,
        lazy_id: ActionT | None = None,
        value_to_aggregate: Callable[[VertexValueT], AggregateT] | None = None,
        value_difference: Callable[[VertexValueT, VertexValueT], ActionT] | None = None,
    ) -> None:
        """Initialize offline dynamic connectivity.

        Args:
            n: Number of vertices (0-indexed).
            time_max: Last allowed timestamp, inclusive. Timestamps run from
                ``0`` through ``time_max``.
            values: Initial vertex values. In the default integer add/sum
                mode, omitted values are initialized to zero.
            op: Binary operation on component aggregates.
            agg_inv: Inverse operation for the aggregate group.
            agg_e: Identity element of the aggregate group.
            mapping_value: Applies a lazy action to a single vertex value.
            mapping_aggregate: Applies a lazy action to a component aggregate.
                It receives the component size as the third argument for the
                same reason as in `UndoableDSUWithLazyAggregate`.
            composition: Composes lazy actions as `f after g`.
            difference: Returns `d` satisfying `composition(d, g) == f`.
            lazy_id: Identity lazy action.
            value_to_aggregate: Lifts a vertex value to an aggregate.
            value_difference: Difference on vertex values used to implement
                `vertex_set`. When omitted, `vertex_set` is unavailable.

        Notes:
            These operations must satisfy the same requirements as
            `UndoableDSUWithLazyAggregate`, because this class internally builds
            that DSU.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``n`` or ``time_max`` is negative, ``values`` has
                the wrong length, or generic initialization omits required
                callbacks or values.

        Time Complexity:
            ``O(n + time_max)``

        """
        if n < 0 or time_max < 0:
            raise ValueError('n and time_max must be non-negative')
        if values is not None and len(values) != n:
            raise ValueError('values length must match n')
        self.n = n
        self.time_max = time_max + 1
        self.log = (self.time_max - 1).bit_length()
        self.size = 1 << self.log
        self.edges: list[tuple[int, int, int]] = []  # (l, r, edge)
        self.insert_times: dict[int, int] = {}
        self.unerased_edges: set[int] = set()
        self.value_difference: Callable[[VertexValueT, VertexValueT], ActionT] | None
        self.dsu: UndoableDSUWithLazyAggregate[VertexValueT, AggregateT, ActionT]
        if op is None: # default to add-sum instance
            self.dsu = cast(UndoableDSUWithLazyAggregate[VertexValueT, AggregateT, ActionT], UndoableDSUWithLazyAggregate(
                cast(list[int], values) if values is not None else [0] * n,
                lambda a, b: a + b, # op
                lambda x: -x, # agg_inv
                0, # agg_e
                lambda f, x: x + f, # mapping_value
                lambda f, s, sz: s + f * sz, # mapping_aggregate
                lambda f, g: f + g, # composition
                lambda f, g: f - g, # difference
                0, # lazy_id
                lambda x: x, # value_to_aggregate
            ))
            self.value_difference = cast(Callable[[VertexValueT, VertexValueT], ActionT], sub)
        else:
            if (
                values is None
                or agg_inv is None
                or agg_e is None
                or mapping_value is None
                or mapping_aggregate is None
                or composition is None
                or difference is None
                or lazy_id is None
                or value_to_aggregate is None
            ):
                raise ValueError('generic initialization requires all operations and initial values')
            self.dsu = UndoableDSUWithLazyAggregate(
                values,
                op,
                agg_inv,
                agg_e,
                mapping_value,
                mapping_aggregate,
                composition,
                difference,
                lazy_id,
                value_to_aggregate,
            )
            self.value_difference = value_difference
        self._initial_values = self.dsu.value[:]
        self.seg: list[list[int]] = [[] for _ in range(2 * self.size)]
        self.queries: list[list[
            tuple[Literal[0, 3], int, ActionT]
            | tuple[Literal[1], int, VertexValueT]
            | tuple[Literal[2, 4], int, None]
            | tuple[Literal[5], int, int]
        ]] = [[] for _ in range(self.time_max + 1)]


    def insert_edge(self, u: int, v: int, t: int) -> None:
        """
        Insert an edge at time t.

        Args:
            u: First vertex.
            v: Second vertex.
            t: Time of insertion. Register changes to each edge in
                nondecreasing timestamp order.

        Returns:
            ``None``.

        Raises:
            AssertionError: If any of ``0 <= u < n``, ``0 <= v < n``, ``0 <= t < self.time_max`` is false.
            ValueError: If the edge is already active or its timestamp
                precedes the previous change to that edge.

        Time Complexity:
            O(1)
        """
        assert 0 <= u < self.n
        assert 0 <= v < self.n
        assert 0 <= t < self.time_max
        if u > v: u, v = v, u
        edge = u * self.n + v
        if edge in self.unerased_edges:
            raise ValueError('edge already exists')
        if t < self.insert_times.get(edge, 0):
            raise ValueError('edge changes must be registered in timestamp order')
        self.unerased_edges.add(edge)
        self.insert_times[edge] = t

    def erase_edge(self, u: int, v: int, t: int) -> None:
        """
        Erase an edge at time t.

        Args:
            u: First vertex.
            v: Second vertex.
            t: Time of erasure.

        Returns:
            ``None``.

        Notes:
            Edge must have been inserted before erasure.

        Raises:
            AssertionError: If any of ``0 <= u < n``, ``0 <= v < n``, ``0 <= t < self.time_max`` is false.
            ValueError: If the edge is not active or erasure precedes insertion.

        Time Complexity:
            O(1)
        """
        assert 0 <= u < self.n
        assert 0 <= v < self.n
        assert 0 <= t < self.time_max
        if u > v: u, v = v, u
        edge = u * self.n + v
        if edge not in self.unerased_edges:
            raise ValueError('edge does not exist')
        if t < self.insert_times[edge]:
            raise ValueError('erasure must not precede insertion')
        self.edges.append((self.insert_times[edge], t, edge))
        self.unerased_edges.remove(edge)
        self.insert_times[edge] = t

    def set_query_vertex_apply(self, v: int, f: ActionT, t: int) -> None:
        """
        Apply a lazy action to vertex v at time t.

        Args:
            v: Vertex to update.
            f: Mapping function or lazy tag.
            t: Query time.

        Returns:
            ``None``.

        Raises:
            AssertionError: If any of ``0 <= v < n``, ``0 <= t < self.time_max`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= v < self.n
        assert 0 <= t < self.time_max
        self.queries[t].append((0, v, f))

    def set_query_vertex_add(self, v: int, x: ActionT, t: int) -> None:
        """
        Add value to vertex at time t.

        Args:
            v: Vertex to add value to.
            x: Value to add.
            t: Time of query.

        Returns:
            ``None``.

        Time Complexity:
            O(1)
        """
        self.set_query_vertex_apply(v, x, t)

    def set_query_vertex_set(self, v: int, x: VertexValueT, t: int) -> None:
        """
        Set the value of vertex v to x at time t.

        Args:
            v: Vertex to update.
            x: Target value of the vertex.
            t: Time of query.

        Returns:
            ``None``.

        Raises:
            AssertionError: If any of ``0 <= v < n``, ``0 <= t < self.time_max`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= v < self.n
        assert 0 <= t < self.time_max
        self.queries[t].append((1, v, x))

    def set_query_vertex_get(self, v: int, t: int) -> None:
        """
        Query the current value of vertex v at time t.

        Args:
            v: Vertex to query.
            t: Time of query.

        Returns:
            ``None``.

        Raises:
            AssertionError: If any of ``0 <= v < n``, ``0 <= t < self.time_max`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= v < self.n
        assert 0 <= t < self.time_max
        self.queries[t].append((2, v, None))

    def set_query_component_apply(self, v: int, f: ActionT, t: int) -> None:
        """
        Apply a lazy action to the whole component of v at time t.

        Args:
            v: Vertex identifying the target component.
            f: Mapping function or lazy tag.
            t: Query time.

        Returns:
            ``None``.

        Raises:
            AssertionError: If any of ``0 <= v < n``, ``0 <= t < self.time_max`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= v < self.n
        assert 0 <= t < self.time_max
        self.queries[t].append((3, v, f))

    def set_query_component_add(self, v: int, x: ActionT, t: int) -> None:
        """
        Add x to every vertex in the component of v at time t.

        Args:
            v: Vertex identifying the component.
            x: Value to add.
            t: Time of query.

        Returns:
            ``None``.

        Time Complexity:
            O(1)
        """
        self.set_query_component_apply(v, x, t)

    def set_query_component_aggregate(self, v: int, t: int) -> None:
        """
        Query the aggregate of the component containing v at time t.

        Args:
            v: Vertex in the component.
            t: Time of query.

        Returns:
            ``None``.

        Notes:
            Result will be in the list returned by run().

        Raises:
            AssertionError: If any of ``0 <= v < n``, ``0 <= t < self.time_max`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= v < self.n
        assert 0 <= t < self.time_max
        self.queries[t].append((4, v, None))

    def set_query_component_sum(self, v: int, t: int) -> None:
        """
        Alias of set_query_component_aggregate for the add-sum instance.

        Args:
            v: Vertex in the component.
            t: Query time.

        Returns:
            ``None``.

        Time Complexity:
            O(1)
        """
        self.set_query_component_aggregate(v, t)

    def set_query_is_same(self, u: int, v: int, t: int) -> None:
        """
        Query if two vertices are connected at time t.

        Args:
            u: First vertex.
            v: Second vertex.
            t: Time of query.

        Returns:
            ``None``.

        Notes:
            Result will be in the list returned by run().

        Raises:
            AssertionError: If any of ``0 <= u < n``, ``0 <= v < n``, ``0 <= t < self.time_max`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= u < self.n
        assert 0 <= v < self.n
        assert 0 <= t < self.time_max
        self.queries[t].append((5, u, v))

    def run(self) -> list[VertexValueT | AggregateT | int]:
        """
        Execute all queries and return results.

        Returns:
            List of query results in timestamp order. Queries at the same
            timestamp are processed in registration order.
            Vertex queries return `VertexValueT`, component aggregate queries return `AggregateT`,
            and connectivity queries return `0` or `1`.

        Notes:
            Each call starts from the constructor's initial values and replays
            all currently registered events. More events may be registered
            between calls. Edge intervals include the insertion timestamp and
            exclude the erasure timestamp; connectivity at each timestamp is
            determined before processing that timestamp's queries.

        Time Complexity:
            ``O(n + time_max + (k log time_max + q) log n + k log time_max)``, where ``k`` is the number of edge-active intervals and ``q`` is the number of submitted queries
        """
        dsu = self.dsu
        dsu.par_size = [-1] * self.n
        dsu.tag = [dsu.lazy_id for _ in range(self.n)]
        dsu.value = self._initial_values[:]
        dsu.sub_agg = [dsu.value_to_aggregate(v) for v in dsu.value]
        dsu.his = []
        self.seg = [[] for _ in range(2 * self.size)]
        intervals = self.edges + [(self.insert_times[e], self.time_max, e) for e in self.unerased_edges]
        for l, r, e in intervals:
            l += self.size
            r += self.size
            while l < r:
                if l & 1:
                    self.seg[l].append(e)
                    l += 1
                if r & 1:
                    r -= 1
                    self.seg[r].append(e)
                l >>= 1
                r >>= 1
        return self._dfs()

    def _dfs(self) -> list[VertexValueT | AggregateT | int]:
        stack = [1]
        res: list[VertexValueT | AggregateT | int] = []
        while stack:
            k = stack.pop()
            if k >= 0:
                if self.size + self.time_max <= k:
                    continue
                stack.append(~k)
                for e in self.seg[k]:
                    self.dsu.merge(e // self.n, e % self.n)
                if self.size <= k:
                    for query in self.queries[k - self.size]:
                        if query[0] == 0:
                            self.dsu.vertex_apply(query[1], query[2])
                        elif query[0] == 1:
                            if self.value_difference is None:
                                raise ValueError('vertex_set requires value_difference')
                            cur = self.dsu.vertex_get(query[1])
                            self.dsu.vertex_apply(query[1], self.value_difference(query[2], cur))
                        elif query[0] == 2:
                            res.append(self.dsu.vertex_get(query[1]))
                        elif query[0] == 3:
                            self.dsu.component_apply(query[1], query[2])
                        elif query[0] == 4:
                            res.append(self.dsu.component_aggregate(query[1]))
                        elif query[0] == 5:
                            res.append(int(self.dsu.same(query[1], query[2])))
                else:
                    stack.append(k << 1 | 1)
                    stack.append(k << 1)
            else:
                k = ~k
                for e in self.seg[k]:
                    self.dsu.undo()
        return res


class SimpleOnlineDynamicConnectivity(Generic[ValueT]):
    """
    Simple online dynamic connectivity with component aggregates.

    This structure maintains one spanning forest with :class:`EulerTourTree`
    and keeps every non-tree edge in ordinary adjacency sets. When a tree edge
    is deleted, it scans the smaller side of the cut to find one replacement
    non-tree edge.

    The implementation is online and simple, but it is not the Holm-de
    Lichtenberg-Thorup polylogarithmic structure. Insertions and queries are
    fast, while deleting a tree edge costs time proportional to the smaller
    component and its non-tree boundary.

    Complexity Notation:
        n: Number of vertices.
        m: Number of currently stored edges.
        k: Size of the smaller side of a deleted tree edge cut.
        b: Number of non-tree incidences scanned while searching for a replacement.

    Space Complexity:
        O(n + m)

    """

    __slots__ = ('n', 'e', 'op', 'forest', 'edge_tree', 'non_tree_adj', 'mark', 'stamp')

    def __init__(self, n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT], values: Sequence[ValueT] | None = None) -> None:
        """
        Initialize the connectivity structure.

        Args:
            n: Number of vertices.
            e: Identity element of ``op``.
            op: Commutative associative operation for component aggregates.
            values: Initial vertex values. When omitted, all vertices are initialized with ``e``.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``values`` does not have length ``n``.

        Time Complexity:
            ``O(n)``

        """
        self.n = n
        self.e = e
        self.op = op
        base_values = list(values) if values is not None else [e] * n
        if len(base_values) != n:
            raise ValueError('values length must match n')
        self.forest = EulerTourTree(n, e, op)
        self.forest.build(base_values)
        self.edge_tree: dict[tuple[int, int], bool] = {}
        self.non_tree_adj: list[set[int]] = [set() for _ in range(n)]
        self.mark = [0] * n
        self.stamp = 1

    def _normalize(self, u: int, v: int) -> tuple[int, int]:
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise ValueError('vertex index out of range')
        if u == v:
            raise ValueError('self-loop is not supported')
        return (u, v) if u < v else (v, u)

    def _remove_non_tree_edge(self, u: int, v: int) -> None:
        self.non_tree_adj[u].remove(v)
        self.non_tree_adj[v].remove(u)

    def _find_replacement(self, u: int, v: int) -> bool:
        if self.forest.component_size(u) > self.forest.component_size(v):
            u, v = v, u
        vertices = self.forest.component_vertices(u)
        stamp = self.stamp
        self.stamp += 1
        for x in vertices:
            self.mark[x] = stamp
        for x in vertices:
            for y in tuple(self.non_tree_adj[x]):
                if self.mark[y] == stamp:
                    continue
                key = (x, y) if x < y else (y, x)
                self._remove_non_tree_edge(key[0], key[1])
                self.edge_tree[key] = True
                self.forest.link(key[0], key[1])
                return True
        return False

    def insert_edge(self, u: int, v: int) -> bool:
        """
        Insert edge ``(u, v)``.

        Args:
            u: First endpoint.
            v: Second endpoint.

        Returns:
            ``True`` if the inserted edge becomes a tree edge, otherwise ``False``.

        Raises:
            ValueError: If the edge already exists or is a self-loop.

        Time Complexity:
            ``O(log n)`` expected.

        """
        key = self._normalize(u, v)
        if key in self.edge_tree:
            raise ValueError('edge already exists')
        if self.forest.same(key[0], key[1]):
            self.edge_tree[key] = False
            self.non_tree_adj[key[0]].add(key[1])
            self.non_tree_adj[key[1]].add(key[0])
            return False
        self.edge_tree[key] = True
        self.forest.link(key[0], key[1])
        return True

    def erase_edge(self, u: int, v: int) -> bool:
        """
        Erase edge ``(u, v)``.

        Args:
            u: First endpoint.
            v: Second endpoint.

        Returns:
            ``True`` if the erased edge was a tree edge, otherwise ``False``.

        Raises:
            ValueError: If the edge does not exist or is a self-loop.

        Time Complexity:
            Non-tree edge deletion is ``O(1)``. Tree edge deletion is ``O(log n + k + b)``, where ``k`` is the size of the smaller side of the cut and ``b`` is the number of non-tree incidences scanned there.

        """
        key = self._normalize(u, v)
        is_tree = self.edge_tree.pop(key, None)
        if is_tree is None:
            raise ValueError('edge does not exist')
        if not is_tree:
            self._remove_non_tree_edge(key[0], key[1])
            return False
        self.forest.cut(key[0], key[1])
        self._find_replacement(key[0], key[1])
        return True

    def same(self, u: int, v: int) -> bool:
        """
        Return whether ``u`` and ``v`` are connected.

        Args:
            u: First vertex.
            v: Second vertex.

        Returns:
            ``True`` if the two vertices are in the same connected component, otherwise ``False``.

        Raises:
            ValueError: If either vertex index is out of range.

        Time Complexity:
            ``O(log n)`` expected.

        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise ValueError('vertex index out of range')
        if u == v:
            return True
        return self.forest.same(u, v)

    def set(self, v: int, value: ValueT) -> None:
        """
        Overwrite the payload of vertex ``v``.

        Args:
            v: Target vertex.
            value: New payload value.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``v`` is out of range.

        Time Complexity:
            ``O(log n)`` expected.

        """
        if not (0 <= v < self.n):
            raise ValueError('vertex index out of range')
        self.forest.set(v, value)

    def get(self, v: int) -> ValueT:
        """
        Return the payload of vertex ``v``.

        Args:
            v: Target vertex.

        Returns:
            Current payload stored at ``v``.

        Raises:
            ValueError: If ``v`` is out of range.

        Time Complexity:
            ``O(1)``.

        """
        if not (0 <= v < self.n):
            raise ValueError('vertex index out of range')
        return self.forest.get(v)

    def component_aggregate(self, v: int) -> ValueT:
        """
        Return the aggregate of the component containing ``v``.

        Args:
            v: Any vertex in the target component.

        Returns:
            Aggregate of the connected component containing ``v``.

        Raises:
            ValueError: If ``v`` is out of range.

        Time Complexity:
            ``O(log n)`` expected.

        """
        if not (0 <= v < self.n):
            raise ValueError('vertex index out of range')
        return self.forest.component_aggregate(v)

    def component_size(self, v: int) -> int:
        """
        Return the size of the component containing ``v``.

        Args:
            v: Any vertex in the target component.

        Returns:
            Number of vertices in the connected component containing ``v``.

        Raises:
            ValueError: If ``v`` is out of range.

        Time Complexity:
            ``O(log n)`` expected.

        """
        if not (0 <= v < self.n):
            raise ValueError('vertex index out of range')
        return self.forest.component_size(v)


class HDLTOnlineDynamicConnectivity(SimpleOnlineDynamicConnectivity[ValueT]):
    """
    HDLT-style online dynamic connectivity with component aggregates.

    This implementation keeps exact edge levels and a forest for every level.
    It follows the standard Holm-de Lichtenberg-Thorup replacement strategy:
    when a tree edge of level ``i`` is deleted, it scans the smaller side in
    each forest ``F_i, F_{i-1}, ..., F_0``; internal level-``i`` edges are
    promoted to ``i + 1`` and the first crossing non-tree edge becomes the
    replacement tree edge.

    Complexity Notation:
        n: Number of vertices.
        m: Number of edge records ever inserted and still retained internally.

    Space Complexity:
        O((n + m) log n)

    """

    __slots__ = ('n', 'e', 'op', 'levels', 'forest', 'edge_u', 'edge_v', 'edge_level', 'edge_is_tree', 'edge_tree_mask', 'edge_alive', 'edge_id', 'incident', 'incident_count', 'mark', 'stamp')

    def __init__(self, n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT], values: Sequence[ValueT] | None = None) -> None:
        """
        Initialize the HDLT connectivity structure.

        Args:
            n: Number of vertices.
            e: Identity element of ``op``.
            op: Commutative associative operation for component aggregates.
            values: Initial vertex values. When omitted, all vertices are initialized with ``e``.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``values`` does not have length ``n``.

        Time Complexity:
            ``O(n log n)``

        """
        self.n = n
        self.e = e
        self.op = op
        self.levels = max(1, n.bit_length())
        base_values = list(values) if values is not None else [e] * n
        if len(base_values) != n:
            raise ValueError('values length must match n')
        self.forest = [EulerTourTree(n, e, op) for _ in range(self.levels)]
        for ett in self.forest:
            ett.build(base_values)
        self.edge_u: list[int] = []
        self.edge_v: list[int] = []
        self.edge_level: list[int] = []
        self.edge_is_tree: list[bool] = []
        self.edge_tree_mask: list[int] = []
        self.edge_alive: list[bool] = []
        self.edge_id: dict[tuple[int, int], int] = {}
        self.incident: list[list[list[int]]] = [[[ ] for _ in range(n)] for _ in range(self.levels)]
        self.incident_count = [[0] * n for _ in range(self.levels)]
        self.mark = [0] * n
        self.stamp = 1

    def _normalize(self, u: int, v: int) -> tuple[int, int]:
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise ValueError('vertex index out of range')
        if u == v:
            raise ValueError('self-loop is not supported')
        return (u, v) if u < v else (v, u)

    def _forest0(self) -> EulerTourTree[ValueT]:
        return self.forest[0]

    def _add_incident(self, level: int, vertex: int, edge_id: int) -> None:
        self.incident[level][vertex].append(edge_id)
        self.incident_count[level][vertex] += 1
        if self.incident_count[level][vertex] == 1:
            self.forest[level].set_mark(vertex, 1)

    def _remove_incident(self, level: int, vertex: int, edge_id: int) -> None:
        self.incident_count[level][vertex] -= 1
        if self.incident_count[level][vertex] == 0:
            self.forest[level].set_mark(vertex, 0)

    def _promote_edge(self, edge_id: int, level: int) -> None:
        if level + 1 >= self.levels:
            return
        u = self.edge_u[edge_id]
        v = self.edge_v[edge_id]
        self.edge_level[edge_id] = level + 1
        self._add_incident(level + 1, u, edge_id)
        self._add_incident(level + 1, v, edge_id)
        if self.edge_is_tree[edge_id] and ((self.edge_tree_mask[edge_id] >> level) & 1) and not self.forest[level + 1].same(u, v):
            self.forest[level + 1].link(u, v)
            self.edge_tree_mask[edge_id] |= 1 << (level + 1)

    def _link_tree_edge(self, edge_id: int) -> bool:
        u = self.edge_u[edge_id]
        v = self.edge_v[edge_id]
        hi = self.edge_level[edge_id]
        mask = 0
        for level in range(hi + 1):
            if self.forest[level].same(u, v):
                continue
            self.forest[level].link(u, v)
            mask |= 1 << level
        if mask == 0:
            return False
        self.edge_is_tree[edge_id] = True
        self.edge_tree_mask[edge_id] = mask
        return True

    def _cut_tree_edge(self, edge_id: int) -> None:
        u = self.edge_u[edge_id]
        v = self.edge_v[edge_id]
        mask = self.edge_tree_mask[edge_id]
        level = 0
        while mask:
            if mask & 1:
                self.forest[level].cut(u, v)
            mask >>= 1
            level += 1
        self.edge_is_tree[edge_id] = False
        self.edge_tree_mask[edge_id] = 0

    def _replace(self, max_level: int, u: int, v: int) -> bool:
        for level in range(max_level, -1, -1):
            if self.forest[level].component_size(u) > self.forest[level].component_size(v):
                u, v = v, u
            vertices = self.forest[level].component_vertices(u)
            stamp = self.stamp
            self.stamp += 1
            for x in vertices:
                self.mark[x] = stamp
            suppressed: list[int] = []
            seen: set[int] = set()
            while self.forest[level].component_has_marked(u):
                x = self.forest[level].find_marked(u)
                if x < 0 or self.mark[x] != stamp:
                    break
                self.forest[level].set_mark(x, 0)
                suppressed.append(x)
                for edge_id in self.incident[level][x]:
                    if edge_id in seen or not self.edge_alive[edge_id] or self.edge_level[edge_id] < level:
                        continue
                    seen.add(edge_id)
                    a = self.edge_u[edge_id]
                    b = self.edge_v[edge_id]
                    if self.edge_is_tree[edge_id] and not ((self.edge_tree_mask[edge_id] >> level) & 1):
                        continue
                    if self.mark[a] == stamp and self.mark[b] == stamp:
                        if self.edge_level[edge_id] == level:
                            self._promote_edge(edge_id, level)
                        continue
                    if self.edge_is_tree[edge_id]:
                        continue
                    if self.forest[0].same(a, b):
                        continue
                    if not self._link_tree_edge(edge_id):
                        continue
                    for y in suppressed:
                        if self.incident_count[level][y] > 0:
                            self.forest[level].set_mark(y, 1)
                    return True
            for x in suppressed:
                if self.incident_count[level][x] > 0:
                    self.forest[level].set_mark(x, 1)
        return False

    def insert_edge(self, u: int, v: int) -> bool:
        """
        Insert edge ``(u, v)``.

        Args:
            u: First endpoint.
            v: Second endpoint.

        Returns:
            ``True`` if the inserted edge becomes a tree edge, otherwise ``False``.

        Raises:
            ValueError: If the edge already exists or is a self-loop.

        Time Complexity:
            ``O(log^2 n)`` amortized expected.

        """
        key = self._normalize(u, v)
        if key in self.edge_id and self.edge_alive[self.edge_id[key]]:
            raise ValueError('edge already exists')
        edge_id = len(self.edge_u)
        self.edge_u.append(key[0])
        self.edge_v.append(key[1])
        self.edge_level.append(0)
        self.edge_is_tree.append(False)
        self.edge_tree_mask.append(0)
        self.edge_alive.append(True)
        self.edge_id[key] = edge_id
        for level in range(self.edge_level[edge_id] + 1):
            self._add_incident(level, key[0], edge_id)
            self._add_incident(level, key[1], edge_id)
        if not self._forest0().same(key[0], key[1]):
            self._link_tree_edge(edge_id)
            return True
        return False

    def erase_edge(self, u: int, v: int) -> bool:
        """
        Erase edge ``(u, v)``.

        Args:
            u: First endpoint.
            v: Second endpoint.

        Returns:
            ``True`` if the erased edge was a tree edge, otherwise ``False``.

        Raises:
            ValueError: If the edge does not exist or is a self-loop.

        Time Complexity:
            ``O(log^2 n)`` amortized expected.

        """
        key = self._normalize(u, v)
        edge_id = self.edge_id.get(key)
        if edge_id is None or not self.edge_alive[edge_id]:
            raise ValueError('edge does not exist')
        self.edge_alive[edge_id] = False
        del self.edge_id[key]
        level = self.edge_level[edge_id]
        for current_level in range(level + 1):
            self._remove_incident(current_level, key[0], edge_id)
            self._remove_incident(current_level, key[1], edge_id)
        if not self.edge_is_tree[edge_id]:
            return False
        cut_level = self.edge_tree_mask[edge_id].bit_length() - 1
        self._cut_tree_edge(edge_id)
        self._replace(cut_level, key[0], key[1])
        return True

    def same(self, u: int, v: int) -> bool:
        """
        Return whether ``u`` and ``v`` are connected.

        Args:
            u: First vertex.
            v: Second vertex.

        Returns:
            ``True`` if the two vertices are in the same connected component, otherwise ``False``.

        Raises:
            ValueError: If either vertex index is out of range.

        Time Complexity:
            ``O(log n)`` expected.

        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise ValueError('vertex index out of range')
        if u == v:
            return True
        return self._forest0().same(u, v)

    def set(self, v: int, value: ValueT) -> None:
        """
        Overwrite the payload of vertex ``v``.

        Args:
            v: Target vertex.
            value: New payload value.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``v`` is out of range.

        Time Complexity:
            ``O(log^2 n)`` expected.

        """
        if not (0 <= v < self.n):
            raise ValueError('vertex index out of range')
        for forest in self.forest:
            forest.set(v, value)

    def get(self, v: int) -> ValueT:
        """
        Return the payload of vertex ``v``.

        Args:
            v: Target vertex.

        Returns:
            Current payload stored at ``v``.

        Raises:
            ValueError: If ``v`` is out of range.

        Time Complexity:
            ``O(1)``.

        """
        if not (0 <= v < self.n):
            raise ValueError('vertex index out of range')
        return self._forest0().get(v)

    def component_aggregate(self, v: int) -> ValueT:
        """
        Return the aggregate of the component containing ``v``.

        Args:
            v: Any vertex in the target component.

        Returns:
            Aggregate of the connected component containing ``v``.

        Raises:
            ValueError: If ``v`` is out of range.

        Time Complexity:
            ``O(log n)`` expected.

        """
        if not (0 <= v < self.n):
            raise ValueError('vertex index out of range')
        return self._forest0().component_aggregate(v)

    def component_size(self, v: int) -> int:
        """
        Return the size of the component containing ``v``.

        Args:
            v: Any vertex in the target component.

        Returns:
            Number of vertices in the connected component containing ``v``.

        Raises:
            ValueError: If ``v`` is out of range.

        Time Complexity:
            ``O(log n)`` expected.

        """
        if not (0 <= v < self.n):
            raise ValueError('vertex index out of range')
        return self._forest0().component_size(v)


OnlineDynamicConnectivity = SimpleOnlineDynamicConnectivity
