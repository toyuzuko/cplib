# cplib.sequence

`cplib.sequence` contains sequence, range-query, and permutation algorithms.

## Modules

### `alignment.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `edit_distance` | function | `edit_distance(s: Sequence[object], t: Sequence[object], insert_cost: int = 1, delete_cost: int…` | Return the weighted edit distance between two sequences. | Time: O(nm), where ``n = len(s)`` and ``m = len(t)``. |
| `longest_common_subsequence_length` | function | `longest_common_subsequence_length(s: Sequence[object], t: Sequence[object]) -> int` | Return the length of the longest common subsequence of two sequences. | Time: O(nm), where ``n = len(s)`` and ``m = len(t)``. |

### `cartesian.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `cartesian_tree` | function | `cartesian_tree(arr: Sequence[KeyT]) -> Tree` | Build a Cartesian tree from the given sequence of comparable elements. | Time: O(n) |

### `grid.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `largest_square_area_in_grid` | function | `largest_square_area_in_grid(grid: Sequence[Sequence[int]], available_value: int = 0) -> int` | Return the largest square area consisting only of one cell value. | Time: O(hw), where ``h`` and ``w`` are grid dimensions. |
| `count_squares_in_grid` | function | `count_squares_in_grid(grid: Sequence[Sequence[int]], available_value: int = 0) -> int` | Count square subgrids consisting only of one cell value. | Time: O(hw), where ``h`` and ``w`` are grid dimensions. |
| `largest_rectangle_area_in_grid` | function | `largest_rectangle_area_in_grid(grid: Sequence[Sequence[int]], available_value: int = 0) -> int` | Return the largest rectangle area consisting only of one cell value. | Time: O(hw), where ``h`` and ``w`` are grid dimensions. |
| `count_rectangles_in_grid` | function | `count_rectangles_in_grid(grid: Sequence[Sequence[int]], available_value: int = 0) -> int` | Count rectangular subgrids consisting only of one cell value. | Time: O(hw), where ``h`` and ``w`` are grid dimensions. |

### `histogram.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `largest_rectangle_area` | function | `largest_rectangle_area(histogram: Sequence[int]) -> int` | Return the largest rectangle area in a histogram. | Time: O(n), where ``n`` is ``len(histogram)``. |

### `permutation.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `next_permutation` | function | `next_permutation(perm: list[int]) -> bool` | Find the next lexicographically greater permutation of a sequence. | Time: O(n) |
| `prev_permutation` | function | `prev_permutation(perm: list[int]) -> bool` | Find the previous lexicographically smaller permutation of a sequence. | Time: O(n) |
| `count_inversions` | function | `count_inversions(arr: Sequence[KeyT]) -> int` | Count inversions in a sequence. | Time: O(n log n), where ``n = len(arr)``. |

### `rangestat.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `StaticRangeOrderQuery` | class | `StaticRangeOrderQuery(arr: Sequence[int], log: int \| None = None)` | Static order-statistics queries on a non-negative integer array. | Space: O(n log V) |
| `StaticRangeCountDistinctQuery` | class | `StaticRangeCountDistinctQuery(arr: Sequence[int])` | Static range distinct-count queries. | Space: O(n log n) |
| `static_range_count_distinct` | function | `static_range_count_distinct(arr: Sequence[int], queries: Sequence[tuple[int, int]]) -> list[int]` | Answer static range distinct-count queries. | Time: O(n log n + q log n) |
| `StaticRangeMajorityQuery` | class | `StaticRangeMajorityQuery(arr: Sequence[int])` | Static range strict-majority queries. | Space: O(n) |
| `StaticRangeModeQuery` | class | `StaticRangeModeQuery(n: int, arr: Sequence[int])` | Static range mode query with sqrt decomposition. | Space: O(n + num_blocks^2) |
| `StaticRangeLISQuery` | class | `StaticRangeLISQuery(p: Sequence[int])` | Static range LIS queries on a permutation. | Space: O(n log n) |
| `static_range_lis` | function | `static_range_lis(p: Sequence[int], queries: Sequence[tuple[int, int]]) -> list[int]` | Answer static range LIS queries on a permutation. | Time: O(n log^2 n + q log n) |
| `OfflineStaticRangeInversionsQuery` | class | `OfflineStaticRangeInversionsQuery(arr: Sequence[int], block_size: int \| None = None)` | Offline static range inversion-count queries. | Space: O(n + q) |
| `offline_static_range_inversions` | function | `offline_static_range_inversions(arr: Sequence[int], queries: Sequence[tuple[int, int]]) -> list…` | Answer static range inversion-count queries offline. | Time: O((n + q) sqrt(n) log n) with the standard Mo ordering |
| `OfflineStaticRangeMexQuery` | class | `OfflineStaticRangeMexQuery(n: int, arr: Sequence[int])` | Offline static range mex queries on an immutable integer array. | Space: O(n + q) |
| `offline_static_range_mex` | function | `offline_static_range_mex(arr: Sequence[int], queries: Sequence[tuple[int, int]]) -> list[int]` | Answer static range mex queries offline on an immutable integer array. | Time: O((n + q) log n) |

### `stack.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `matched_interval_areas` | function | `matched_interval_areas(text: str, open_char: str = '(', close_char: str = ')', area_func: Calla…` | Compute merged areas for matched character intervals. | Time: O(n) |

### `subseq.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `longest_increasing_subsequence` | function | `longest_increasing_subsequence(arr: list[int], return_idx: bool = False) -> list[int]` | Return one longest increasing subsequence. | Time: ``O(n log n)`` |
| `number_of_subsequences` | function | `number_of_subsequences(arr: list[int], mod: int) -> int` | Count distinct subsequences modulo ``mod``. | Time: ``O(n)`` |

### `window.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `count_subarrays_with_sum` | function | `count_subarrays_with_sum(arr: Sequence[int], target: int) -> int` | Count non-empty contiguous subarrays whose sum is exactly ``target``. | Time: O(n), where ``n`` is ``len(arr)``. |
| `count_subarrays_with_sum_at_most_nonnegative` | function | `count_subarrays_with_sum_at_most_nonnegative(arr: Sequence[int], upper: int) -> int` | Count non-empty contiguous subarrays whose sum is at most ``upper``. | Time: O(n), where ``n`` is ``len(arr)``. |
| `minimum_subarray_length_with_sum_at_least_nonnegative` | function | `minimum_subarray_length_with_sum_at_least_nonnegative(arr: Sequence[int], lower: int) -> int` | Return the shortest length of a subarray whose sum is at least ``lower``. | Time: O(n), where ``n`` is ``len(arr)``. |
| `minimum_window_covering_multiset` | function | `minimum_window_covering_multiset(arr: Sequence[HashableT], required: Iterable[HashableT]) -> int` | Return the shortest contiguous window covering a required multiset. | Time: O(n + k), where ``n`` is ``len(arr)`` and ``k`` is the number of required elements including multiplicities. |
