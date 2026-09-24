# cplib.datastructure

`cplib.datastructure` contains data structure implementations.

## Modules

### `avltree.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `AVLTree` | class | `AVLTree()` | AVL tree implementation for ordered set operations. | Space: O(m + 1), where m is the maximum size since the most recent build. Deleted node slots are retained for reuse. |
| `ImplicitAVLTree` | class | `ImplicitAVLTree(op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[[ActionT,…` | Implicit AVL tree with lazy propagation for sequence operations. | Space: O(m), where m is the maximum size since the last build. Deleted slots are reused. |
| `PersistentImplicitAVLTree` | class | `PersistentImplicitAVLTree(op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[…` | Fully persistent implicit AVL tree with lazy propagation. | Space: O(N) |

### `binarytrie.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `BinaryTrie` | class | `BinaryTrie(bitlen: int)` | Binary trie data structure for integer set operations. | Space: O(k * bitlen), where k is the number of distinct stored bit patterns ever inserted. Deletion does not release trie nodes. |
| `MergeableBinaryTrie` | class | `MergeableBinaryTrie(bitlen: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, calc_revers…` | Mergeable binary trie data structure supporting multiple tries with associative operations. | Space: O(P), where P is the number of allocated node slots. Overlapping nodes are recycled on merge, but discard does not release paths. Each add or split can allocate O(bitlen) nodes. |
| `RangeSortRangeProd` | class | `RangeSortRangeProd(n: int, keys: Sequence[int], vals: Sequence[ValueT], bitlen: int, op: Callab…` | Range sorting and ordered products for sequences with distinct integer keys. | Space: O(n + P), where P is the number of allocated trie node slots. Each set or nonempty range query can allocate O(bitlen) nodes, and merged or replaced nodes are reused. Deleted paths left by splits may remain allocated, so P is not bounded by the current key count alone. |

### `bst.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `BinarySearchTree` | class | `BinarySearchTree()` | Plain unbalanced binary search tree. | Space: O(m), where m is the maximum number of simultaneously stored values. |

### `convex.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `LiChaoTree` | class | `LiChaoTree(variables: list[int])` | Li Chao tree for minimum queries on affine functions. | Space: O(n) |
| `MonotoneConvexHullTrick` | class | `MonotoneConvexHullTrick(slope_increasing: bool = False, query_increasing: bool = True)` | Deque-based convex hull trick for monotone slopes and monotone queries. | Space: O(n) |

### `cumulative.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Cumulative` | class | `Cumulative(n: int, init: ValueT, op: Callable[[ValueT, ValueT], ValueT], inv_op: Callable[[Valu…` | Prefix-aggregate structure for static range queries. | Space: O(n) |
| `CumulativeSum2D` | class | `CumulativeSum2D(h: int, w: int)` | 2D cumulative sums with constant-time ``rectangle_sum`` queries. | Space: O(h * w) |
| `Imos1D` | class | `Imos1D(n: int)` | 1D difference-array helper for offline range additions. | Space: O(n) |
| `Imos2D` | class | `Imos2D(h: int, w: int)` | 2D difference-array helper for offline rectangle additions. | Space: O(h * w) |

### `dsu.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `DisjointSetUnion` | class | `DisjointSetUnion(n: int)` | Disjoint Set Union (Union-Find) data structure. | Space: O(n) in the constructor input size or configured capacity |
| `WeightedDSU` | class | `WeightedDSU(n: int)` | Weighted Disjoint Set Union data structure. | Space: O(n) in the constructor input size or configured capacity |
| `DSUWithPotential` | class | `DSUWithPotential(n: int, mul_func: Callable[[ValueT, ValueT], ValueT], inv_func: Callable[[Valu…` | Disjoint Set Union with potential/weight for general group operations. | Space: O(n) in the constructor input size or configured capacity |
| `PartiallyPersistentDSU` | class | `PartiallyPersistentDSU(n: int)` | Partially persistent disjoint-set union. | Space: ``O(n)`` |
| `UndoableDSU` | class | `UndoableDSU(n: int)` | Disjoint-set union with rollback support. | Space: ``O(n + q)``, where ``q`` is the number of recorded merges |
| `RangeParallelDSU` | class | `RangeParallelDSU(n: int, initial_weights: list[ValueT], merge_value: Callable[[ValueT, ValueT],…` | A DSU (Disjoint Set Union) structure that supports merging two equal-length | Space: O(n log n) in the constructor input size or configured capacity |
| `QueryDSU` | class | `QueryDSU(n: int, f: Callable[[int], ValueT], op: Callable[[ValueT, ValueT], ValueT])` | Query-based Disjoint Set Union with path optimization based on a custom function. | Space: O(n) in the constructor input size or configured capacity |
| `DSUOnlyPathHalving` | class | `DSUOnlyPathHalving(n: int)` | Disjoint Set Union with only path halving optimization and explicit parent-child relationships. | Space: O(n) in the constructor input size or configured capacity |

### `fenwicktree.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `FenwickTree` | class | `FenwickTree(n: int)` | Fenwick Tree (Binary Indexed Tree) for efficient prefix sum queries. | Space: O(n) |
| `GroupFenwickTree` | class | `GroupFenwickTree(n: int, op: Callable[[ValueT, ValueT], ValueT], inv: Callable[[ValueT], ValueT…` | Fenwick tree over an abelian group. | Space: ``O(n)`` |
| `RangeAddPointGet` | class | `RangeAddPointGet(n: int)` | Range add and point get data structure using Fenwick Tree. | Space: O(n) |
| `GroupRangeAddPointGet` | class | `GroupRangeAddPointGet(n: int, op: Callable[[ValueT, ValueT], ValueT], inv: Callable[[ValueT], V…` | Range add and point get over an abelian group. | Space: ``O(n)`` |
| `RangeSetBIT` | class | `RangeSetBIT(n: int)` | Range-based set data structure using Fenwick Tree for order statistics. | Space: O(n) in the constructor input size or configured capacity |
| `RangeMultisetBIT` | class | `RangeMultisetBIT(n: int)` | Range-based multiset data structure using Fenwick Tree. | Space: O(n) in the constructor input size or configured capacity |
| `SortedSetBIT` | class | `SortedSetBIT(variables: list[KeyT])` | Sorted set data structure for arbitrary comparable elements using Fenwick Tree. | Space: O(n) in the constructor input size or configured capacity |
| `SortedMultisetBIT` | class | `SortedMultisetBIT(variables: list[KeyT])` | Sorted multiset data structure for arbitrary comparable elements using Fenwick Tree. | Space: O(n) in the constructor input size or configured capacity |

### `hash.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `SafeIntegerDict` | class | `SafeIntegerDict(values: Mapping[int, ValueT] \| Iterable[tuple[int, ValueT]] = ())` | Dictionary with collision-resistant storage for integer keys. | Space: O(n) for n bounded-size keys, excluding stored values. |
| `SafeIntegerSet` | class | `SafeIntegerSet(values: Iterable[int] = ())` | Set with collision-resistant storage for integer elements. | Space: O(n) for n bounded-size elements. |

### `intervalset.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `IntervalSet` | class | `IntervalSet()` | Disjoint interval set with add/remove and point queries. | Space: O(m), where m is the maximum number of stored intervals so far. The backing Treap reuses deleted nodes; the endpoint map stores only the currently active intervals. |

### `linkedlist.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `DoublyLinkedList` | class | `DoublyLinkedList()` | Doubly linked list with O(1) end operations and node-handle operations. | Space: O(m), where m is the total number of insertions, including erased nodes. |
| `SpliceableLinkedLists` | class | `SpliceableLinkedLists(n: int)` | Collection of singly linked lists with O(1) append and splice-to-back. | Space: O(number of inserted values + number of lists) |

### `persistent.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `PartiallyPersistentArray` | class | `PartiallyPersistentArray(n: int, auto_update: bool = True, init_val: T \| None = None)` | Partially persistent array with efficient version management. | Space: O(n + q), where q is the number of recorded point updates. |
| `FullyPersistentArray` | class | `FullyPersistentArray(n: int, child_num: int = 64, auto_update: bool = True, init_val: T \| None…` | Fully persistent array supporting updates to any version. | Space: O(P + q * B * (1 + log_B(n + 1)) + v), where B=child_num, P=B**ceil(log_B(max(1, n))), q is the number of point updates, and v is the number of timestamp advancements. For fixed B, this is O(n + q * (1 + log(n + 1)) + v + 1). |
| `FullyPersistentDSU` | class | `FullyPersistentDSU(n: int, auto_update: bool = True)` | Fully persistent disjoint set union (Union-Find) data structure. | Space: O(n + q * (1 + log(n + 1)) + v + 1), where q counts merge attempts and v counts timestamp advancements, including explicit update calls. |
| `FullyPersistentSegmentTree` | class | `FullyPersistentSegmentTree(n: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, auto_upda…` | Fully persistent segment tree without lazy propagation. | Space: O(n + q * (1 + log(n + 1)) + v + 1), where q counts point updates and v counts timestamp advancements, including explicit update calls. |
| `FullyPersistentLazySegmentTree` | class | `FullyPersistentLazySegmentTree(n: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mappi…` | Fully persistent segment tree with lazy propagation. | Space: O(n + q * (1 + log(n + 1)) + v + 1), where q counts range updates and copies and v counts timestamp advancements. Queries do not allocate or mutate tree nodes. |

### `queue.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `heapify` | function | `heapify(values: Sequence[KeyT], ascending: bool = True) -> list[KeyT]` | Return a heapified copy of values. | Time: O(n) |
| `worst_case_heap_for_heapsort` | function | `worst_case_heap_for_heapsort(values: Sequence[KeyT]) -> list[KeyT]` | Return a max-heap causing many swaps in the sort phase of heapsort. | Time: O(n log n), where ``n = len(values)``. |
| `PriorityQueue` | class | `PriorityQueue(ascending: bool = True)` | Priority queue implementation supporting both min-heap and max-heap. | Space: O(n) |
| `RadixHeap` | class | `RadixHeap(last: int = 0)` | Radix heap for monotone non-negative integer keys. | Space: O(n + B), where ``B`` is the largest key bit length seen so far. |
| `DoubleEndedPriorityQueue` | class | `DoubleEndedPriorityQueue()` | Double-ended priority queue supporting both min and max operations. | Space: O(n) |
| `DoubleEndedQueue` | class | `DoubleEndedQueue()` | Double-ended queue (deque) with O(1) amortized operations at both ends. | Space: O(n) |
| `DeletablePriorityQueue` | class | `DeletablePriorityQueue(ascending: bool = True)` | Priority queue with arbitrary-value removal via ``remove``. | Space: O(n) |
| `OffsetPriorityQueue` | class | `OffsetPriorityQueue(ascending: bool = True)` | Priority queue with global offset support for all elements. | Space: O(n) |
| `PersistentLeftistHeap` | class | `PersistentLeftistHeap()` | Persistent meldable heap implemented as a leftist heap. | Space: ``O(m)`` where ``m`` is the number of created heap nodes |

### `range2d.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `CompressedFenwickTree2D` | class | `CompressedFenwickTree2D(points: Iterable[tuple[int, int]])` | Offline 2D Fenwick tree on sparse integer coordinates. | Space: O(k log k) |
| `KDTree2D` | class | `KDTree2D(points: Iterable[tuple[int, int]], values: Iterable[int] \| None = None)` | Static 2D k-d tree with point updates, rectangle-sum queries, and | Space: O(n) |
| `LazyKDTree2D` | class | `LazyKDTree2D(points: Iterable[tuple[int, int]], values: Iterable[ValueT] \| None, op: Callable[[…` | Static 2D k-d tree with lazy rectangle updates and rectangle queries. | Space: O(n) |
| `PointAddRectangleSum` | class | `PointAddRectangleSum(points: Iterable[tuple[int, int]])` | Sparse point-add rectangle-sum data structure. | Space: O(k log k) |
| `RectangleAddPointGet` | class | `RectangleAddPointGet(rectangles: Iterable[tuple[int, int, int, int]])` | Sparse rectangle-add point-get data structure. | Space: O(k log k) |
| `static_rectangle_union_area` | function | `static_rectangle_union_area(rectangles: Iterable[tuple[int, int, int, int]]) -> int` | Return the area covered by at least one half-open rectangle. | Time: O(k + n log(n + 1)), where k is the input rectangle count and n is the number of nonempty rectangles. |
| `static_rectangle_add_rectangle_sum` | function | `static_rectangle_add_rectangle_sum(rectangles: Iterable[tuple[int, int, int, int, int]], querie…` | Solve static rectangle-add rectangle-sum queries offline. | Time: O((n + q) log (n + q)) |

### `segtree.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `SegmentTree` | class | `SegmentTree(n: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT)` | Segment tree for point updates and ordered range products. | Space: O(n + 1). |
| `RangeMinPointSet` | class | `RangeMinPointSet(n: int, inf: int = 1 << 30)` | Segment tree specialized for point updates and range minima. | Space: O(n + 1). See inherited methods for operation costs. |
| `RangeLinearAddRangeMin` | class | `RangeLinearAddRangeMin(values: Sequence[int], block_size: int \| None = None)` | Range linear-add and range-min structure by sqrt decomposition. | Space: ``O(n)`` |
| `SegmentTreeBeats` | class | `SegmentTreeBeats(n: int)` | Segment tree beats for ``chmin/chmax/add/update`` and range statistics. | Space: O(n + 1). Integer arithmetic is counted as O(1). |
| `SegmentTree2D` | class | `SegmentTree2D(n: int, m: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT)` | Dense two-dimensional segment tree for point updates and rectangle products. | Space: O((n + 1) * (m + 1)). |
| `DualSegmentTree` | class | `DualSegmentTree(n: int, op: Callable[[ValueT, ValueT], ValueT], id: ValueT, commutative: bool =…` | Dual segment tree for range updates and point queries. | Space: O(n + 1). |
| `LazySegmentTree` | class | `LazySegmentTree(n: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[[A…` | Lazy segment tree for point/range updates and ordered range products. | Space: O(n + 1). |
| `RangeAffineRangeSum` | class | `RangeAffineRangeSum(n: int, mod: Callable[[], int])` | Range affine updates and modular range sums over an initially zero array. | Space: O(n + 1). |
| `MergeSortTree` | class | `MergeSortTree(n: int, op: Callable[[KeyT, KeyT], KeyT], e: KeyT)` | Static range counts and aggregates of values at most a threshold. | Space: O(n log(n + 1) + 1) after build; O(n + 1) before build. |

### `slopetrick.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `SlopeTrick` | class | `SlopeTrick(minimum: int = 0)` | Maintain a convex piecewise-linear function by slope trick. | Space: O(n) |

### `sparsetable.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `SparseTable` | class | `SparseTable(arr: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT])` | Sparse Table for efficient range queries with idempotent operations. | Space: O(n log(n + 1)) for the precomputed levels. |
| `DisjointSparseTable` | class | `DisjointSparseTable(arr: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT])` | Disjoint sparse table for associative range queries. | Space: O(n log(n + 1)) for the precomputed levels. |

### `swag.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `SlidingWindowAggregation` | class | `SlidingWindowAggregation(op: Callable[[ValueT, ValueT], ValueT])` | Double-ended sliding-window aggregation structure. | Space: O(n) |

### `treap.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `ImplicitTreap` | class | `ImplicitTreap(op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[[ActionT, Va…` | Implicit Treap with lazy propagation for sequence operations. | Space: O(m), where m is the maximum size since the last build. Deleted slots are reused. |
| `Treap` | class | `Treap()` | Treap implementation for ordered set operations. | Space: O(m), where m is the maximum number of stored keys since the last build. Deleted node slots are reused by later insertions. |
| `TreapMultiset` | class | `TreapMultiset()` | Treap implementation for ordered multiset operations. | Space: O(m), where m is the maximum number of distinct keys since the last build. Deleted node slots are reused by later insertions. |
| `SegmentedImplicitTreap` | class | `SegmentedImplicitTreap(op: Callable[[ValueT, ValueT], ValueT], e: ValueT, make_data: Callable[[…` | Implicit treap whose nodes represent constant segments. | Space: O(A), where A is the total number of allocated segment nodes. Nodes from roots abandoned by the caller are not reclaimed. |

### `wavelet.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `FullyIndexableDictionary` | class | `FullyIndexableDictionary(size: int)` | Bit vector packed in 32-bit blocks with rank and select support. | Space: O(n) |
| `WaveletMatrix` | class | `WaveletMatrix(log: int = 32)` | Wavelet matrix for static integer sequences. | Space: O(n log V) |

### `wbtree.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `ImplicitWeightBalancedTree` | class | `ImplicitWeightBalancedTree(op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable…` | Implicit weight-balanced tree with lazy propagation for sequence operations. | Space: O(m), where m is the maximum size since the last build. Deleted slots are reused. |
| `PersistentImplicitWeightBalancedTree` | class | `PersistentImplicitWeightBalancedTree(op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping…` | Fully persistent implicit weight-balanced tree with lazy propagation. | Space: O(N) |
