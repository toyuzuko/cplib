# cplib.algorithm

`cplib.algorithm` contains common competitive-programming algorithms.

## Modules

### `bisearch.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `binary_search` | function | `binary_search(ng: int, ok: int, check: Callable[[int], bool]) -> int` | Find the boundary of a monotone integer predicate. | Time: ``O(log(abs(ok - ng)))`` predicate evaluations. |
| `float_binary_search` | function | `float_binary_search(ng: float, ok: float, check: Callable[[float], bool], iterations: int = 80)…` | Find an approximate boundary of a monotone real predicate. | Time: ``O(iterations)`` predicate evaluations. |
| `bisect_left` | function | `bisect_left(arr: Sequence[KeyT], x: KeyT) -> int` | Return the first index ``i`` such that ``arr[i] >= x``. | Time: ``O(log n)`` |
| `bisect_right` | function | `bisect_right(arr: Sequence[KeyT], x: KeyT) -> int` | Return the first index ``i`` such that ``arr[i] > x``. | Time: ``O(log n)`` |
| `ParallelBinarySearch` | class | `ParallelBinarySearch(steps: int)` | Schedule multiple first-true searches on a growing prefix. | Space: ``O(q)`` |

### `dp.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `fibonacci_number` | function | `fibonacci_number(n: int, f0: int = 0, f1: int = 1) -> int` | Return the n-th term of a Fibonacci-type sequence. | Time: O(log(n + 1)) arithmetic operations. Integer arithmetic is not constant-time for large terms. |
| `minimum_coin_count` | function | `minimum_coin_count(coins: Sequence[int], amount: int) -> int` | Return the minimum number of unlimited coins needed to make ``amount``. | Time: O(amount * n), where ``n`` is ``len(coins)``. |
| `matrix_chain_multiplication_cost` | function | `matrix_chain_multiplication_cost(dimensions: Sequence[tuple[int, int]]) -> int` | Return the minimum scalar multiplication count for a matrix chain. | Time: O(n^3), where ``n = len(dimensions)``. |
| `optimal_binary_search_tree_cost` | function | `optimal_binary_search_tree_cost(p: Sequence[float], q: Sequence[float]) -> float` | Return the minimum expected search cost of an optimal binary search tree. | Time: O(n^2), where ``n = len(p)``. |

### `greedy.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `maximum_profit` | function | `maximum_profit(prices: Sequence[int]) -> int` | Return the maximum difference ``prices[j] - prices[i]`` for ``i < j``. | Time: O(n), where ``n = len(prices)``. |
| `greedy_coin_count` | function | `greedy_coin_count(coins: Sequence[int], amount: int) -> int` | Return the number of coins chosen by the standard greedy algorithm. | Time: O(n log n), where ``n = len(coins)``. |
| `fractional_knapsack` | function | `fractional_knapsack(items: Sequence[tuple[int, int]], capacity: int) -> float` | Return the maximum value obtainable when items can be split. | Time: O(n log n), where ``n = len(items)``. |
| `max_non_overlapping_intervals` | function | `max_non_overlapping_intervals(intervals: Sequence[tuple[int, int]], *, allow_touch: bool = True…` | Return the maximum number of non-overlapping intervals. | Time: O(n log n), where ``n = len(intervals)``. |
| `huffman_encoded_length` | function | `huffman_encoded_length(frequencies: Sequence[int]) -> int` | Return the minimum encoded length for Huffman coding. | Time: O(n log n), where ``n = len(frequencies)``. |

### `knapsack.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `SubsetSumResult` | class | `SubsetSumResult(...)` | Result of a subset-sum style meet-in-the-middle query. | Space: O(k), where ``k`` is the number of selected values. |
| `subset_sum_meet_in_the_middle` | function | `subset_sum_meet_in_the_middle(values: Sequence[int], target: int) -> SubsetSumResult \| None` | Find one subset whose sum is exactly ``target``. | Time: O(n 2^(n/2)) |
| `maximum_subset_sum_at_most_meet_in_the_middle` | function | `maximum_subset_sum_at_most_meet_in_the_middle(values: Sequence[int], limit: int) -> SubsetSumRe…` | Find a maximum-sum subset whose sum is at most ``limit``. | Time: O(n 2^(n/2)) |
| `KnapsackItem` | class | `KnapsackItem(...)` | One item description for unified knapsack solving. | Space: ``O(1)`` |
| `KnapsackResult` | class | `KnapsackResult(...)` | Result of a knapsack query with reconstruction. | Space: ``O(n)``, where ``n`` is the number of original items. |
| `bounded_knapsack_small_values` | function | `bounded_knapsack_small_values(items: Sequence[KnapsackItem], capacity: int, *, window: int \| No…` | Return the bounded-knapsack optimum for small item values. | Time: O(n log n + n * (window + 1) + sum(item.value)) for retained items, where ``n`` is ``len(items)``. Integer arithmetic is treated as O(1). |
| `knapsack` | function | `knapsack(items: Sequence[KnapsackItem], capacity: int, *, restore: bool = False, mitm_threshold…` | Return the maximum obtainable value under a weight limit. | Time: Meet-in-the-middle branch: ``O(m 2^(m/2))`` where ``m`` is the expanded 0/1 item count. DP branches take ``O(m * min(capacity, total_value))``. |

### `mo.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `hilbert_order` | function | `hilbert_order(x: int, y: int, power: int) -> int` | Return the Hilbert-curve index of a point in a square grid. | Time: O(power) integer operations. |
| `Mo` | class | `Mo(n: int, block_size: int \| None = None)` | Standard Mo's algorithm scheduler for half-open range queries. | Space: ``O(q)`` |
| `HilbertMo` | class | `HilbertMo(n: int)` | Mo's algorithm variant that sorts queries by Hilbert order. | Space: ``O(q)`` |
| `RollbackMo` | class | `RollbackMo(n: int, block_size: int \| None = None)` | Rollback Mo's algorithm for data structures without deletions. | Space: ``O(q)`` plus the underlying rollback structure |

### `sat.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `TwoSatResult` | class | `TwoSatResult(...)` | Result of 2-SAT solving. | Space: ``O(n)`` when an assignment is present. |
| `TwoSatSolver` | class | `TwoSatSolver(n: int)` | 2-SAT solver based on strongly connected components. | Space: ``O(n + m)`` |
| `ThreeSatResult` | class | `ThreeSatResult(...)` | Result of 3-SAT solving. | Space: ``O(n)`` when an assignment is present. |
| `CnfSatResult` | class | `CnfSatResult(...)` | Result of general CNF-SAT solving via reduction to 3-SAT. | Space: ``O(n)`` when an assignment is present. |
| `ThreeSatSolver` | class | `ThreeSatSolver(n: int)` | 3-SAT solver using iterative backtracking with propagation. | Space: ``O(n + m)`` |
| `CnfSatSolver` | class | `CnfSatSolver(n: int)` | General CNF-SAT solver via Tseitin-style reduction to 3-SAT. | Space: ``O(n + L)``, where ``L`` is the total number of stored literals. |

### `search.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `solve_n_queens` | function | `solve_n_queens(n: int, fixed: Sequence[tuple[int, int]] = ()) -> tuple[int, ...] \| None` | Return one N-Queens placement satisfying fixed queens. | Time: Exponential in ``n`` in the worst case. |
| `sliding_puzzle_distance` | function | `sliding_puzzle_distance(board: Sequence[int], height: int, width: int, target: Sequence[int] \|…` | Return the shortest solution length of a rectangular sliding puzzle. | Time: Exponential in the solution length in the worst case. |

### `sort.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `insertion_sort` | function | `insertion_sort(values: Sequence[T], key: Callable[[T], KeyT] \| None = None, gap: int = 1) -> li…` | Return a copy sorted within each gap-spaced subsequence by insertion sort. | Time: O(n + n^2 / gap) in the worst case, including the input copy. |
| `bubble_sort` | function | `bubble_sort(values: Sequence[T], key: Callable[[T], KeyT] \| None = None) -> list[T]` | Return a stably sorted copy using bubble sort. | Time: O(n^2) |
| `selection_sort` | function | `selection_sort(values: Sequence[T], key: Callable[[T], KeyT] \| None = None) -> list[T]` | Return a sorted copy using selection sort. | Time: O(n^2) |
| `shell_sort` | function | `shell_sort(values: Sequence[T], key: Callable[[T], KeyT] \| None = None, gaps: Sequence[int] \| N…` | Return a sorted copy using shell sort. | Time: O(n^2) for the default gaps. For custom gaps, a general upper bound is O(sum(n + n^2 / gap)), including the final gap-1 pass. |
| `merge_sort` | function | `merge_sort(arr: list[T], cmp: Callable[[T, T], bool], threshold: int = 3) -> list[T]` | Return a stably sorted copy of ``arr`` using the given comparator. | Time: ``O(n log n)`` for a fixed threshold. In general, ``O(n log n + n * min(n, 2**threshold))``. |
| `intro_sort` | function | `intro_sort(values: Sequence[T], cmp: Callable[[T, T], bool], threshold: int = 16) -> list[T]` | Return a sorted copy using introsort with the given comparator. | Time: O(n log n) for a fixed threshold, where ``n = len(values)``. In general, O(n log n + n * min(n, threshold)). |
| `includes_sorted` | function | `includes_sorted(values: Sequence[KeyT], targets: Sequence[KeyT]) -> bool` | Return whether sorted ``values`` contains all sorted ``targets``. | Time: O(n + m), where ``n = len(values)`` and ``m = len(targets)``. |
| `sorted_set_union` | function | `sorted_set_union(a: Sequence[KeyT], b: Sequence[KeyT]) -> list[KeyT]` | Return the union of two sorted unique sequences. | Time: O(n + m), where ``n = len(a)`` and ``m = len(b)``. |
| `sorted_set_intersection` | function | `sorted_set_intersection(a: Sequence[KeyT], b: Sequence[KeyT]) -> list[KeyT]` | Return the intersection of two sorted unique sequences. | Time: O(n + m), where ``n = len(a)`` and ``m = len(b)``. |
| `sorted_set_difference` | function | `sorted_set_difference(a: Sequence[KeyT], b: Sequence[KeyT]) -> list[KeyT]` | Return the sorted set difference ``a - b``. | Time: O(n + m), where ``n = len(a)`` and ``m = len(b)``. |
| `sorted_set_symmetric_difference` | function | `sorted_set_symmetric_difference(a: Sequence[KeyT], b: Sequence[KeyT]) -> list[KeyT]` | Return the symmetric difference of two sorted unique sequences. | Time: O(n + m), where ``n = len(a)`` and ``m = len(b)``. |
| `counting_sort` | function | `counting_sort(values: Sequence[int], max_value: int \| None = None, min_value: int = 0) -> list[…` | Return the sorted values using counting sort. | Time: O(n + U), where ``U = max_value - min_value + 1``. |
| `partition` | function | `partition(values: Sequence[T], key: Callable[[T], KeyT] \| None = None, left: int = 0, right: in…` | Return a copy partitioned by the last element as pivot. | Time: O(len(values)), including the full input copy. |
| `quick_sort` | function | `quick_sort(values: Sequence[T], key: Callable[[T], KeyT] \| None = None) -> list[T]` | Return a sorted copy using iterative Lomuto quicksort. | Time: Average O(n log n), worst-case O(n^2). |
| `minimum_cost_sort` | function | `minimum_cost_sort(values: Sequence[int]) -> int` | Return the minimum swap cost needed to sort values in ascending order. | Time: O(n log n), where ``n = len(values)``. |
