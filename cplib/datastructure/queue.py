#!/usr/bin/env python3

import heapq
from collections.abc import Sequence
from typing import Generic
from cplib.tools.type import T, KeyT


def heapify(values: Sequence[KeyT], ascending: bool = True) -> list[KeyT]:
    """
    Return a heapified copy of values.

    Args:
        values: Input values.
        ascending: If True, build a min-heap. Otherwise build a max-heap.

    Returns:
        Heap array representation.

    Time Complexity:
        O(n)

    Space Complexity:
        O(n)
    """
    heap = list(values)
    if ascending:
        heapq.heapify(heap)
    else:
        # Python 3.11's private max-heap functions have incomplete stubs.
        heapq._heapify_max(heap)  # pyright: ignore[reportPrivateUsage, reportArgumentType]
    return heap


def worst_case_heap_for_heapsort(values: Sequence[KeyT]) -> list[KeyT]:
    """
    Return a max-heap causing many swaps in the sort phase of heapsort.

    The returned permutation is constructed by reversing the standard 1-indexed
    heapsort deletion process and choosing the deepest rightmost path at each
    step. Values should be distinct when an exact worst-case permutation is
    required.

    Args:
        values: Values to permute.

    Returns:
        A max-heap permutation of the input values.

    Time Complexity:
        O(n log n), where ``n = len(values)``.

    Space Complexity:
        O(n)
    """
    sorted_values = sorted(values)
    if not sorted_values:
        return []
    heap = [sorted_values[0]]
    for value in sorted_values[1:]:
        node = len(heap)
        moved = heap[node - 1]
        heap.append(moved)
        while node > 1:
            parent = node >> 1
            heap[node - 1] = heap[parent - 1]
            node = parent
        heap[0] = value
    return heap


class PriorityQueue(Generic[KeyT]):
    """
    Priority queue implementation supporting both min-heap and max-heap.

    A generic priority queue that can operate as either a min-heap (ascending=True)
    or max-heap (ascending=False). Uses Python's heapq module internally.

    Time Complexities:
        - push: O(log n)
        - pop: O(log n)
        - build: O(n)

    Space Complexity:
        O(n)

    Attributes:
        _ascending: If True, operates as min-heap; if False, as max-heap.
        _heap: Internal heap array.

    Examples:
        >>> # Min-heap example
        >>> pq = PriorityQueue[int](ascending=True)
        >>> pq.push(3)
        >>> pq.push(1)
        >>> pq.push(4)
        >>> print(pq.pop())  # 1
        1

        >>> # Max-heap example
        >>> pq = PriorityQueue[int](ascending=False)
        >>> pq.build([3, 1, 4, 1, 5])
        >>> print(pq.pop())  # 5
        5

    Args:
        ascending: If True, use ascending order; otherwise use descending order.

    """
    def __init__(self, ascending: bool = True) -> None:
        """Initialize priority queue.

        Args:
            ascending: If True, min-heap; if False, max-heap. Defaults to True.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._ascending = ascending
        self._heap: list[KeyT] = []

    def __len__(self) -> int:
        """
        Return the number of elements in the queue.

        Returns:
            Number of stored elements.

        Time Complexity:
            O(1)
        """
        return len(self._heap)

    def size(self) -> int:
        """
        Return the number of elements in the queue.

        Returns:
            Number of stored elements.

        Time Complexity:
            O(1)
        """
        return len(self)

    def build(self, arr: list[KeyT]) -> None:
        """
        Build heap from array in O(n) time.

        Args:
            arr: Array to build heap from.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self._heap = heapify(arr, self._ascending)

    def push(self, val: KeyT) -> None:
        """
        Push value onto heap.

        Args:
            val: Value to push.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        if self._ascending:
            heapq.heappush(self._heap, val)
        else:
            self._heap.append(val)
            heapq._siftdown_max(self._heap, 0, len(self._heap) - 1)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    def pop(self) -> KeyT:
        """
        Pop and return top element from heap.

        Returns:
            Top element (minimum if ascending, maximum if descending).

        Raises:
            IndexError: If heap is empty.

        Time Complexity:
            O(log n)
        """
        if len(self._heap) == 0:
            raise IndexError('pop from an empty PriorityQueue')
        if self._ascending:
            return heapq.heappop(self._heap)
        else:
            return heapq._heappop_max(self._heap)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]

    def top(self) -> KeyT:
        """
        Return the top element without removing it.

        Returns:
            Top element (minimum if ascending, maximum if descending).

        Raises:
            IndexError: If heap is empty.

        Time Complexity:
            O(1)
        """
        if len(self._heap) == 0:
            raise IndexError('top from an empty PriorityQueue')
        return self._heap[0]

    @property
    def ascending(self) -> bool:
        """
        Return whether this priority queue is a min-heap.

        Returns:
            True if smaller values are popped first, otherwise False.

        Time Complexity:
            O(1)
        """
        return self._ascending


class RadixHeap(Generic[T]):
    """
    Radix heap for monotone non-negative integer keys.

    This priority queue supports ``push(key, value)`` and ``pop()`` when popped
    keys are non-decreasing. It is useful for Dijkstra's algorithm on graphs
    with non-negative integer edge weights.

    Space Complexity:
        O(n + B), where ``B`` is the largest key bit length seen so far.
    """

    def __init__(self, last: int = 0) -> None:
        """
        Initialize an empty radix heap.

        Args:
            last: Initial lower bound of keys. Every pushed key must be at least
                this value.

        Raises:
            ValueError: If ``last`` is negative.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        if last < 0:
            raise ValueError('last must be non-negative')
        self._last = last
        self._size = 0
        self._buckets: list[list[tuple[int, T]]] = [[] for _ in range(1)]

    def __len__(self) -> int:
        """
        Return the number of stored items.

        Returns:
            Number of items.

        Time Complexity:
            O(1)
        """
        return self._size

    def size(self) -> int:
        """
        Return the number of stored items.

        Returns:
            Number of items.

        Time Complexity:
            O(1)
        """
        return len(self)

    def last(self) -> int:
        """
        Return the last popped key.

        Returns:
            Last popped key, or the initial lower bound if no item was popped.

        Time Complexity:
            O(1)
        """
        return self._last

    def push(self, key: int, value: T) -> None:
        """
        Push an item with a monotone integer key.

        Args:
            key: Non-negative integer key. It must be at least ``last()``.
            value: Associated value.

        Raises:
            ValueError: If ``key`` is negative or smaller than ``last()``.

        Returns:
            None.

        Time Complexity:
            O(1) plus any newly allocated buckets; at most B buckets are
            allocated over the lifetime of the heap, where B is the maximum
            key bit length. Integer operations are treated as constant time.
        """
        if key < self._last:
            raise ValueError('key must be at least the last popped key')
        bucket = (key ^ self._last).bit_length()
        while bucket >= len(self._buckets):
            self._buckets.append([])
        self._buckets[bucket].append((key, value))
        self._size += 1

    def pop(self) -> tuple[int, T]:
        """
        Pop and return the item with the minimum key.

        Returns:
            Pair ``(key, value)`` with the minimum key.

        Raises:
            IndexError: If the heap is empty.

        Time Complexity:
            O(B) amortized, where B is the maximum key bit length. Integer
            operations are treated as constant time.
        """
        if self._size == 0:
            raise IndexError('pop from an empty RadixHeap')
        if not self._buckets[0]:
            bucket = 1
            while bucket < len(self._buckets) and not self._buckets[bucket]:
                bucket += 1
            new_last = min(key for key, _ in self._buckets[bucket])
            self._last = new_last
            items = self._buckets[bucket]
            self._buckets[bucket] = []
            for key, value in items:
                self._buckets[(key ^ self._last).bit_length()].append((key, value))
        self._size -= 1
        return self._buckets[0].pop()


class DoubleEndedPriorityQueue(Generic[KeyT]):
    """
    Double-ended priority queue supporting both min and max operations.

    Maintains both a min-heap and max-heap internally with lazy deletion
    to support efficient access to both minimum and maximum elements.

    Values must be hashable as well as comparable. Lazy deletion retains
    some removed entries. In the bounds below, n counts all values passed to
    the most recent build plus subsequent pushes, including deleted values.

    Time Complexities:
        - push: O(log n)
        - pop_min: O(log n) amortized
        - pop_max: O(log n) amortized
        - build: O(n)

    Space Complexity:
        O(n)

    Attributes:
        _max_heap: Max-heap for maximum operations.
        _min_heap: Min-heap for minimum operations.
        _max_deleted: Values popped from max-heap, pending removal from min-heap.
        _min_deleted: Values popped from min-heap, pending removal from max-heap.
        _size: Current number of elements.

    Examples:
        >>> depq = DoubleEndedPriorityQueue[int]()
        >>> depq.build([3, 1, 4, 1, 5, 9])
        >>> print(depq.pop_min())
        1
        >>> print(depq.pop_max())  # 9
        9
        >>> depq.push(2)
        >>> print(depq.pop_min())
        1

    """
    def __init__(self) -> None:
        """
        Initialize an empty double-ended priority queue.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._max_heap = PriorityQueue[KeyT](ascending=False)
        self._min_heap = PriorityQueue[KeyT](ascending=True)
        self._max_deleted: dict[KeyT, int] = dict()
        self._min_deleted: dict[KeyT, int] = dict()
        self._size = 0

    def __len__(self) -> int:
        """
        Return the number of elements in the queue.

        Returns:
            Number of stored elements.

        Time Complexity:
            O(1)
        """
        return self._size

    def size(self) -> int:
        """
        Return the number of elements in the queue.

        Returns:
            Number of stored elements.

        Time Complexity:
            O(1)
        """
        return len(self)

    def build(self, arr: list[KeyT]) -> None:
        """
        Replace all contents with the array and clear pending deletions.

        Args:
            arr: Array to build from.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self._size = len(arr)
        self._min_heap.build(arr)
        self._max_heap.build(arr)
        self._min_deleted.clear()
        self._max_deleted.clear()

    def pop_min(self) -> KeyT:
        """
        Pop and return minimum element.

        Returns:
            Minimum element in the queue.

        Raises:
            IndexError: If queue is empty.

        Notes:
            Uses lazy deletion to handle elements already popped from max-heap.

        Time Complexity:
            O(log n) amortized
        """
        if self._size == 0:
            raise IndexError('pop from an empty DoubleEndedPriorityQueue')
        while True:
            v = self._min_heap.pop()
            if self._max_deleted.get(v, 0):
                self._max_deleted[v] -= 1
            else:
                self._size -= 1
                self._min_deleted[v] = self._min_deleted.get(v, 0) + 1
                return v

    def pop_max(self) -> KeyT:
        """
        Pop and return maximum element.

        Returns:
            Maximum element in the queue.

        Raises:
            IndexError: If queue is empty.

        Notes:
            Uses lazy deletion to handle elements already popped from min-heap.

        Time Complexity:
            O(log n) amortized
        """
        if self._size == 0:
            raise IndexError('pop from an empty DoubleEndedPriorityQueue')
        while True:
            v = self._max_heap.pop()
            if self._min_deleted.get(v, 0):
                self._min_deleted[v] -= 1
            else:
                self._size -= 1
                self._max_deleted[v] = self._max_deleted.get(v, 0) + 1
                return v

    def push(self, val: KeyT) -> None:
        """
        Push value into double-ended priority queue.

        Args:
            val: Value to push.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        self._size += 1
        self._min_heap.push(val)
        self._max_heap.push(val)

class DoubleEndedQueue(Generic[T]):
    """
    Double-ended queue (deque) with O(1) amortized operations at both ends.

    A double-ended queue implementation using two stacks (lists) to achieve
    O(1) amortized time complexity for append/pop operations at both ends.
    Also supports O(1) random access to elements.

    This implementation is particularly useful when collections.deque cannot
    be used (e.g., in some competitive programming environments) or when
    O(1) random access is needed alongside deque operations.

    Time Complexities:
        - append: O(1)
        - appendleft: O(1)
        - pop: O(1) amortized
        - popleft: O(1) amortized
        - get: O(1)
        - len: O(1)

    Space Complexity:
        O(n)

    Attributes:
        lt: Left stack storing elements in reverse order.
        rt: Right stack storing elements in normal order.

    Examples:
        >>> dq = DoubleEndedQueue[int]()
        >>> dq.append(1)
        >>> dq.append(2)
        >>> dq.appendleft(0)
        >>> print(dq[0])
        0
        >>> print(dq[1])
        1
        >>> print(dq[2])
        2
        >>> print(dq.popleft())  # 0
        0
        >>> print(dq.pop())  # 2
        2

        >>> # Building a deque from both ends
        >>> dq = DoubleEndedQueue[str]()
        >>> for i in range(3):
        ...     dq.append(f"right_{i}")
        ...     dq.appendleft(f"left_{i}")
        >>> print(len(dq))  # 6
        6

    Notes:
        The internal representation uses two stacks to maintain balance.
        When one stack is empty during pop operations, elements are
        redistributed from the other stack to maintain amortized O(1) complexity.

    """
    def __init__(self) -> None:
        """Initialize an empty double-ended queue.

        Creates two empty stacks to represent left and right sides of the deque.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.lt: list[T] = []
        self.rt: list[T] = []

    def __len__(self) -> int:
        """Return the number of elements in the deque.

        Time Complexity: O(1)

        Returns:
            Total number of elements in both stacks.
        """
        return len(self.lt) + len(self.rt)

    def append(self, val: T) -> None:
        """
        Add an element to the right end of the deque.

        Args:
            val: Value to append to the right end.

        Returns:
            None.

        Time Complexity:
            O(1) amortized
        """
        self.rt.append(val)

    def appendleft(self, val: T) -> None:
        """
        Add an element to the left end of the deque.

        Args:
            val: Value to append to the left end.

        Returns:
            None.

        Time Complexity:
            O(1) amortized
        """
        self.lt.append(val)

    def pop(self) -> T:
        """
        Remove and return an element from the right end of the deque.

        Returns:
            The rightmost element.

        Raises:
            IndexError: If deque is empty.

        Notes:
            If right stack is empty, redistributes elements from left stack
            to maintain balance and amortized O(1) complexity.

        Time Complexity:
            O(1) amortized
        """
        if len(self) == 0:
            raise IndexError('pop from an empty DoubleEndedQueue')
        if not self.rt:
            i = (len(self.lt) + 1) // 2
            self.rt = self.lt[:i][::-1]
            self.lt = self.lt[i:]
        return self.rt.pop()

    def popleft(self) -> T:
        """
        Remove and return an element from the left end of the deque.

        Returns:
            The leftmost element.

        Raises:
            IndexError: If deque is empty.

        Notes:
            If left stack is empty, redistributes elements from right stack
            to maintain balance and amortized O(1) complexity.

        Time Complexity:
            O(1) amortized
        """
        if len(self) == 0:
            raise IndexError('popleft from an empty DoubleEndedQueue')
        if not self.lt:
            i = (len(self.rt) + 1) // 2
            self.lt = self.rt[:i][::-1]
            self.rt = self.rt[i:]
        return self.lt.pop()

    def __getitem__(self, i: int) -> T:
        """Get element at index i without removing it.

        Time Complexity: O(1)

        Args:
            i: Index of element to retrieve (0-based from left).

        Returns:
            Element at index i.

        Raises:
            IndexError: If index is out of range.

        Notes:
            Elements in left stack are stored in reverse order,
            so ~i (bitwise NOT) is used to access them correctly.
        """
        if i < 0 or i >= len(self):
            raise IndexError('get index out of range')
        if i < len(self.lt):
            return self.lt[~i]
        return self.rt[i - len(self.lt)]


class DeletablePriorityQueue(Generic[KeyT]):
    """
    Priority queue with arbitrary-value removal via ``remove``.

    Wraps PriorityQueue with the ability to remove arbitrary elements
    using lazy deletion with a counter dictionary.

    Values must be hashable as well as comparable. Lazy deletion retains
    some removed entries. In the bounds below, n counts all values passed to
    the most recent build plus subsequent pushes, including deleted values.

    Time Complexities:
        - push: O(log n)
        - pop: O(log n) amortized
        - remove: O(1)
        - build: O(n)

    Attributes:
        _ascending: If True, min-heap; if False, max-heap.
        _heap: Internal priority queue.
        _cnt: Number of active occurrences of each value.
        _size: Current number of elements.

    Examples:
        >>> dpq = DeletablePriorityQueue[int](ascending=True)
        >>> dpq.build([3, 1, 4, 1, 5])
        >>> dpq.remove(1)
        >>> print(dpq.pop())  # 1 (only one instance deleted)
        1
        >>> dpq.remove(3)
        >>> print(dpq.pop())  # 4
        4

    Args:
        ascending: If True, use ascending order; otherwise use descending order.

    Space Complexity:
        O(n)
    """
    def __init__(self, ascending: bool = True) -> None:
        """Initialize deletable priority queue.

        Args:
            ascending: If True, min-heap; if False, max-heap. Defaults to True.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._ascending = ascending
        self._heap = PriorityQueue[KeyT](ascending)
        self._cnt: dict[KeyT, int] = dict()
        self._size = 0

    def __len__(self) -> int:
        """
        Return the number of active elements in the queue.

        Returns:
            Number of non-deleted elements.

        Time Complexity:
            O(1)
        """
        return self._size

    def size(self) -> int:
        """
        Return the number of active elements in the queue.

        Returns:
            Number of non-deleted elements.

        Time Complexity:
            O(1)
        """
        return len(self)

    def build(self, arr: list[KeyT]) -> None:
        """
        Replace all contents and occurrence counts with the array.

        Args:
            arr: Array to build heap from.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self._size = len(arr)
        self._heap.build(arr)
        self._cnt.clear()
        for v in arr:
            self._cnt[v] = self._cnt.get(v, 0) + 1

    def remove(self, val: KeyT) -> None:
        """
        Delete one instance of value from heap.

        Args:
            val: Value to delete.

        Raises:
            KeyError: If value is not in the queue; the contents are unchanged.

        Notes:
            Uses lazy deletion - actual removal happens during pop operations.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        if self._cnt.get(val, 0) == 0:
            raise KeyError(val)
        self._cnt[val] -= 1
        self._size -= 1

    def push(self, val: KeyT) -> None:
        """
        Push value onto heap.

        Args:
            val: Value to push.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        self._size += 1
        self._heap.push(val)
        self._cnt[val] = self._cnt.get(val, 0) + 1

    def pop(self) -> KeyT:
        """
        Pop and return top element from heap.

        Returns:
            Top element (minimum if ascending, maximum if descending).

        Raises:
            IndexError: If heap is empty.

        Notes:
            Skips lazily deleted elements.

        Time Complexity:
            amortized O(log n)
        """
        if self._size == 0:
            raise IndexError('pop from an empty DeletablePriorityQueue')
        self._size -= 1
        while True:
            v = self._heap.pop()
            if self._cnt[v] == 0:
                continue
            self._cnt[v] -= 1
            return v


class OffsetPriorityQueue:
    """
    Priority queue with global offset support for all elements.

    A specialized priority queue that maintains a global offset value that is
    applied to all elements. This is useful for problems where you need to
    add/subtract a constant value to all elements in the queue efficiently.

    The offset is applied lazily - stored values remain unchanged, but the
    offset is added when retrieving values via pop() or top().

    Time Complexities:
        - push: O(log n)
        - pop: O(log n)
        - top: O(1)
        - add_offset: O(1)
        - meld: O(min(n, m) log(n + m)) for a single meld
        - build: O(n)

    Notes:
        When merging multiple heaps with total N elements, the overall
        time complexity is O(N (log N)²) due to repeated melding.

    Attributes:
        _pq: Internal priority queue storing actual values.
        _lazy: Global offset to be added to all elements.

    Examples:
        >>> # Min-heap with offset
        >>> opq = OffsetPriorityQueue(ascending=True)
        >>> opq.push(5)
        >>> opq.push(3)
        >>> opq.add_offset(10)  # Add 10 to all elements
        >>> print(opq.pop())  # 13 (was 3, now 3+10)
        13
        >>> print(opq.pop())  # 15 (was 5, now 5+10)
        15

        >>> # Max-heap with offset
        >>> opq = OffsetPriorityQueue(ascending=False)
        >>> opq.build([1, 2, 3, 4, 5])
        >>> opq.add_offset(-2)  # Subtract 2 from all elements
        >>> print(opq.pop())  # 3 (was 5, now 5-2)
        3

    Notes:
        Only supports integer values due to offset arithmetic.

    Args:
        ascending: If True, use ascending order; otherwise use descending order.

    Space Complexity:
        O(n)
    """
    def __init__(self, ascending: bool = True) -> None:
        """Initialize offset priority queue.

        Args:
            ascending: If True, min-heap; if False, max-heap. Defaults to True.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._pq = PriorityQueue[int](ascending)
        self._lazy = 0

    def __len__(self) -> int:
        """
        Return the number of elements in the queue.

        Returns:
            Number of stored elements.

        Time Complexity:
            O(1)
        """
        return len(self._pq)

    def size(self) -> int:
        """
        Return the number of elements in the queue.

        Returns:
            Number of stored elements.

        Time Complexity:
            O(1)
        """
        return len(self)

    def build(self, arr: list[int]) -> None:
        """
        Replace all contents with the array and reset the offset to zero.

        Args:
            arr: Array of integers to build heap from.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self._pq.build(arr)
        self._lazy = 0

    def push(self, val: int) -> None:
        """
        Push value onto heap, adjusting for current offset.

        Args:
            val: Value to push (offset will be subtracted internally).

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        val -= self._lazy
        self._pq.push(val)

    def pop(self) -> int:
        """
        Pop and return top element with offset applied.

        Returns:
            Top element with the current offset added.

        Raises:
            IndexError: If queue is empty.

        Time Complexity:
            O(log n)
        """
        if len(self._pq) == 0:
            raise IndexError('pop from an empty OffsetPriorityQueue')
        ret = self._pq.pop()
        ret += self._lazy
        return ret

    def top(self) -> int:
        """
        Return top element with offset applied without removing it.

        Returns:
            Top element with the current offset added.

        Raises:
            IndexError: If queue is empty.

        Time Complexity:
            O(1)
        """
        if len(self._pq) == 0:
            raise IndexError('top from an empty OffsetPriorityQueue')
        ret = self._pq.top()
        ret += self._lazy
        return ret

    def add_offset(self, offset: int) -> None:
        """
        Add offset to all elements in the queue.

        Args:
            offset: Value to add to all elements.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._lazy += offset

    def meld(self, other: 'OffsetPriorityQueue') -> None:
        """
        Merge another OffsetPriorityQueue into this one.

        Args:
            other: Another OffsetPriorityQueue to merge.

        Raises:
            ValueError: If ``other is self`` or the queues have different ordering.

        Notes:
            The other queue will be emptied after this operation.
            Swaps internal structures if other queue is larger for efficiency.

        Returns:
            None.

        Time Complexity:
            O(min(n, m) * log(n + m)) for a single meld, where m is the size of the other queue
        """
        if other is self:
            raise ValueError('cannot meld a queue into itself')
        if self._pq.ascending != other._pq.ascending:
            raise ValueError('Cannot meld queues with different orderings')
        if self.size() < other.size():
            self._pq, other._pq = other._pq, self._pq
            self._lazy, other._lazy = other._lazy, self._lazy
        while len(other._pq) > 0:
            self.push(other.pop())


class PersistentLeftistHeap(Generic[KeyT]):
    """
    Persistent meldable heap implemented as a leftist heap.

    The heap is represented by integer roots. Each update returns a new root
    and leaves the previous version usable. This is suitable when many heaps
    share structure through repeated meld and pop operations.

    Time Complexities:
        - ``singleton`` / ``top`` / ``is_empty``: ``O(1)``
        - ``meld`` / ``push`` / ``pop``: ``O(log n)`` amortized

    Space Complexity:
        - ``O(m)`` where ``m`` is the number of created heap nodes
    """

    def __init__(self) -> None:
        """
        Initialize an empty node pool for persistent heaps.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.value: list[KeyT] = []
        self.left: list[int] = []
        self.right: list[int] = []
        self.rank: list[int] = []

    @staticmethod
    def empty() -> int:
        """
        Return the empty-heap root.

        Returns:
            The root handle for an empty heap.

        Time Complexity:
            O(1)
        """
        return -1

    @staticmethod
    def is_empty(root: int) -> bool:
        """
        Return whether ``root`` is the empty heap.

        Args:
            root: Heap root returned by this instance, or -1 for the empty heap.

        Returns:
            True if ``root`` is the empty heap.

        Time Complexity:
            O(1)
        """
        return root == -1

    def singleton(self, value: KeyT) -> int:
        """
        Create a heap consisting of one element.

        Args:
            value: Stored value or update value.

        Returns:
            Root handle of the singleton heap.

        Time Complexity:
            O(1)
        """
        node = len(self.value)
        self.value.append(value)
        self.left.append(-1)
        self.right.append(-1)
        self.rank.append(1)
        return node

    def _clone(self, node: int) -> int:
        new = len(self.value)
        self.value.append(self.value[node])
        self.left.append(self.left[node])
        self.right.append(self.right[node])
        self.rank.append(self.rank[node])
        return new

    def _rank(self, node: int) -> int:
        return 0 if node == -1 else self.rank[node]

    def meld(self, a: int, b: int) -> int:
        """
        Return the meld of two heaps.

        Args:
            a: Root of the first heap.
            b: Root of the second heap.

        Returns:
            Root handle of the melded heap.

        Time Complexity:
            O(log n)
        """
        if a == -1:
            return b
        if b == -1:
            return a
        if self.value[a] > self.value[b]:
            a, b = b, a
        node = self._clone(a)
        self.right[node] = self.meld(self.right[node], b)
        if self._rank(self.left[node]) < self._rank(self.right[node]):
            self.left[node], self.right[node] = self.right[node], self.left[node]
        self.rank[node] = self._rank(self.right[node]) + 1
        return node

    def push(self, root: int, value: KeyT) -> int:
        """
        Return a new heap formed by inserting ``value`` into ``root``.

        Args:
            root: Heap root returned by this instance, or -1 for the empty heap.
            value: Stored value or update value.

        Returns:
            Root handle of the new heap.

        Time Complexity:
            O(log n)
        """
        return self.meld(root, self.singleton(value))

    def top(self, root: int) -> KeyT:
        """
        Return the minimum element of ``root`` without removing it.

        Args:
            root: Heap root returned by this instance, or -1 for the empty heap.

        Returns:
            Minimum element of the heap.

        Raises:
            IndexError: If ``root`` is empty.

        Time Complexity:
            O(1)
        """
        if root == -1:
            raise IndexError('top from an empty PersistentLeftistHeap')
        return self.value[root]

    def pop(self, root: int) -> tuple[KeyT, int]:
        """
        Return ``(minimum, new_root)`` after removing the top element.

        Args:
            root: Heap root returned by this instance, or -1 for the empty heap.

        Returns:
            Pair of the removed minimum element and the new root handle.

        Raises:
            IndexError: If ``root`` is empty.

        Time Complexity:
            O(log n)
        """
        if root == -1:
            raise IndexError('pop from an empty PersistentLeftistHeap')
        return self.value[root], self.meld(self.left[root], self.right[root])
