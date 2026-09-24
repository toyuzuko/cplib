#!/usr/bin/env python3

from __future__ import annotations

from typing import Generic
from collections.abc import Sequence, Callable

from cplib.datastructure.segtree import SegmentTree
from cplib.datastructure.fenwicktree import FenwickTree
from cplib.tools.type import ValueT


class BinaryTrie:
    """
    Binary trie data structure for integer set operations.

    A trie-based data structure that stores integers as binary sequences,
    supporting efficient insertion, deletion, and order statistics queries.
    Supports global XOR operation on all elements.

    Examples:
        >>> trie = BinaryTrie(20)  # Support integers up to 2^20-1
        >>> trie.add(5)
        True
        >>> trie.add(3)
        True
        >>> trie.add(7)
        True
        >>> trie[1]  # Get 2nd smallest element (0-indexed)
        5
        >>> trie.all_xor(2)  # XOR all elements with 2
        >>> trie.min()  # Now minimum is 3^2 = 1
        1

    Notes:
        The trie maintains elements in sorted order and supports
        efficient order statistics through subtree size tracking.

    Space Complexity:
        O(k * bitlen), where k is the number of distinct stored bit patterns
        ever inserted. Deletion does not release trie nodes.
    """
    def __init__(self, bitlen: int) -> None:
        """
        Initialize a BinaryTrie with a specified bit length.

        Args:
            bitlen (int): The bit length of the integers to be stored in the trie.

        Time Complexity:
            O(1)
        Raises:
            ValueError: If bitlen is negative. A bit length of zero allows only key 0.

        Returns:
            None.

        """
        if bitlen < 0:
            raise ValueError('bitlen must be non-negative')
        self.bitlen = bitlen
        self.root = 1
        self.xor = 0
        self.ptr = [0, 0, 0, 0, 0, 0]
        self.cnt = [0, 0]

    def _newnode(self, par: int) -> int:
        self.ptr.extend([0, 0, par])
        self.cnt.append(0)
        return len(self.ptr) // 3 - 1

    def add(self, x: int) -> bool:
        """
        Add an integer to the trie.

        Args:
            x: The integer to add (must be in [0, 2^bitlen))

        Returns:
            True if the integer was added, False if it already existed

        Raises:
            ValueError: If x is out of range [0, 2^bitlen)

        Examples:
            >>> trie = BinaryTrie(10)
            >>> trie.add(42)
            True
            >>> trie.add(42)  # Already exists
            False

        Time Complexity:
            O(bitlen)

        """
        if x < 0 or x >= 1 << self.bitlen:
            raise ValueError("x is out of range")
        x ^= self.xor
        v = self.root
        for i in range(self.bitlen - 1, -1, -1):
            if (x >> i) & 1:
                if not self.ptr[v * 3 + 1]:
                    self.ptr[3 * v + 1] = self._newnode(v)
                v = self.ptr[3 * v + 1]
            else:
                if not self.ptr[3 * v + 0]:
                    self.ptr[3 * v + 0] = self._newnode(v)
                v = self.ptr[3 * v + 0]
        if self.cnt[v]:
            return False
        while v:
            self.cnt[v] += 1
            v = self.ptr[3 * v + 2]
        return True

    def discard(self, x: int) -> bool:
        """
        Remove the specified value if present.

        Args:
            x: Value to remove.

        Returns:
            True if removed, otherwise False.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(bitlen).
        """
        if x < 0 or x >= 1 << self.bitlen:
            return False
        x ^= self.xor
        v = self.root
        for i in range(self.bitlen - 1, -1, -1):
            if (x >> i) & 1:
                if not self.ptr[3 * v + 1]:
                    return False
                v = self.ptr[3 * v + 1]
            else:
                if not self.ptr[3 * v + 0]:
                    return False
                v = self.ptr[3 * v + 0]
        if self.cnt[v] == 0:
            return False
        while v:
            self.cnt[v] -= 1
            v = self.ptr[3 * v + 2]
        return True

    def remove(self, x: int) -> None:
        """
        Remove the specified value.

        Args:
            x: Value to remove.

        Returns:
            None.

        Raises:
            KeyError: If the value is absent.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(bitlen).
        """
        if not self.discard(x):
            raise KeyError(x)

    def __contains__(self, x: int) -> bool:
        """
        Check if an integer is contained in the trie.

        Time Complexity: O(bitlen)

        Args:
            x: The integer to check; values outside the storage range are absent.

        Returns:
            True if the integer is in the trie, False otherwise

        Examples:
            >>> trie = BinaryTrie(10)
            >>> trie.add(42)
            True
            >>> 42 in trie
            True
            >>> 43 in trie
            False
        """
        if x < 0 or x >= 1 << self.bitlen:
            return False
        x ^= self.xor
        v = self.root
        for i in range(self.bitlen - 1, -1, -1):
            if (x >> i) & 1:
                if not self.ptr[3 * v + 1]:
                    return False
                v = self.ptr[3 * v + 1]
            else:
                if not self.ptr[3 * v + 0]:
                    return False
                v = self.ptr[3 * v + 0]
        return self.cnt[v] > 0

    def __len__(self) -> int:
        """
        Get the number of elements in the trie.

        Time Complexity: O(1)

        Returns:
            The number of elements in the trie
        """
        return self.cnt[self.root]

    def all_xor(self, x: int) -> None:
        """
        Apply XOR to all elements in the trie.

        This operation is performed lazily by storing a global XOR value,
        so the actual elements in the trie are not modified until accessed.

        Args:
            x: The value to XOR with all elements

        Examples:
            >>> trie = BinaryTrie(10)
            >>> trie.add(5)  # Binary: 101
            True
            >>> trie.add(3)  # Binary: 011
            True
            >>> trie.all_xor(6)  # XOR with 110
            >>> trie.min()  # 3^6 = 5, 5^6 = 3, so min is 3
            3

        Time Complexity:
            O(1)
        Raises:
            ValueError: If x is outside [0, 2**bitlen); the trie is unchanged.

        Returns:
            None.

        """
        if not 0 <= x < 1 << self.bitlen:
            raise ValueError('xor mask is out of range')
        self.xor ^= x

    def min(self) -> int:
        """
        Get the minimum element in the trie.

        Returns:
            The minimum element

        Time Complexity:
            O(bitlen)
        Raises:
            IndexError: If the trie is empty.

        """
        return self[0]

    def max(self) -> int:
        """
        Get the maximum element in the trie.

        Returns:
            The maximum element

        Time Complexity:
            O(bitlen)
        Raises:
            IndexError: If the trie is empty.

        """
        return self[len(self) - 1]

    def __getitem__(self, k: int) -> int:
        """
        Get the k-th smallest element in the trie.

        Time Complexity: O(bitlen)

        Args:
            k: The index (0-based) of the element to retrieve

        Returns:
            The k-th smallest element

        Raises:
            IndexError: If k is out of range [0, len(trie))

        Examples:
            >>> trie = BinaryTrie(10)
            >>> for x in [5, 3, 7, 1]: _ = trie.add(x)
            >>> trie[0]  # Smallest element
            1
            >>> trie[2]  # 3rd smallest element
            5
        """
        if k < 0 or k >= len(self):
            raise IndexError('k is out of range')
        x = self.xor
        v = self.root
        res = 0
        for i in range(self.bitlen - 1, -1, -1):
            lv, rv = self.ptr[3 * v + 0], self.ptr[3 * v + 1]
            if not lv or self.cnt[lv] == 0:
                v = rv
                res |= 1 << i
            elif not rv or self.cnt[rv] == 0:
                v = lv
            else:
                if (x >> i) & 1:
                    if self.cnt[rv] <= k:
                        k -= self.cnt[rv]
                        v = lv
                    else:
                        v = rv
                        res |= 1 << i
                else:
                    if self.cnt[lv] <= k:
                        k -= self.cnt[lv]
                        v = rv
                        res |= 1 << i
                    else:
                        v = lv
        return res ^ x

    def index(self, x: int) -> int:
        """
        Return the first sorted index of ``x``.

        Args:
            x: Search value.

        Returns:
            Zero-based index of the first occurrence.

        Raises:
            ValueError: If the value is absent.

        Examples:
            >>> trie = BinaryTrie(4)
            >>> for value in (1, 3, 5, 7): _ = trie.add(value)
            >>> trie.index(5)
            2
            >>> trie.index(4)
            Traceback (most recent call last):
                ...
            ValueError: given value is not contained

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(bitlen).
        """
        if x < 0 or x >= 1 << self.bitlen:
            raise ValueError("x is out of range")
        v = self.root
        res = 0
        for i in range(self.bitlen - 1, -1, -1):
            xor_bit = (self.xor >> i) & 1
            bit = (x >> i) & 1
            if bit:
                res += self.cnt[self.ptr[3 * v + xor_bit]]
            v = self.ptr[3 * v + (bit ^ xor_bit)]
            if not v or self.cnt[v] == 0:
                raise ValueError('given value is not contained')
        if not self.cnt[v]:
            raise ValueError('given value is not contained')
        return res

    def bisect_left(self, x: int) -> int:
        """
        Return the number of elements strictly less than ``x``.

        Args:
            x: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Examples:
            >>> trie = BinaryTrie(4)
            >>> for value in (1, 3, 5, 7): _ = trie.add(value)
            >>> trie.bisect_left(5), trie.bisect_right(5)
            (2, 3)
            >>> trie.bisect_left(-1), trie.bisect_right(100)
            (0, 4)

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(bitlen).
        """
        if x <= 0:
            return 0
        if x >= 1 << self.bitlen:
            return self.cnt[self.root]
        v = self.root
        res = 0
        for i in range(self.bitlen - 1, -1, -1):
            xor_bit = (self.xor >> i) & 1
            bit = (x >> i) & 1
            if bit:
                res += self.cnt[self.ptr[3 * v + xor_bit]]
            v = self.ptr[3 * v + (bit ^ xor_bit)]
            if not v or self.cnt[v] == 0:
                return res
        return res

    def bisect_right(self, x: int) -> int:
        """
        Return the number of elements less than or equal to ``x``.

        Args:
            x: Search value, including values outside the storage range.

        Returns:
            Insertion index in ``[0, len(self)]``.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(bitlen).
        """
        return self.bisect_left(x + 1)

    def successor(self, x: int, inclusive: bool = True) -> int | None:
        """Return the smallest stored key greater than or equal to ``x``.

        Args:
            x: Search key; it may be absent or outside [0, 2**bitlen).
            inclusive: If False, require a key strictly greater than x.

        Returns:
            Matching stored key, or None if no such key exists.

        Time Complexity:
            O(bitlen).

        Space Complexity:
            O(1) auxiliary space.
        """
        index = self.bisect_left(x) if inclusive else self.bisect_right(x)
        if index == len(self):
            return None
        return self[index]

    def predecessor(self, x: int, inclusive: bool = True) -> int | None:
        """Return the largest stored key less than or equal to ``x``.

        Args:
            x: Search key; it may be absent or outside [0, 2**bitlen).
            inclusive: If False, require a key strictly less than x.

        Returns:
            Matching stored key, or None if no such key exists.

        Time Complexity:
            O(bitlen).

        Space Complexity:
            O(1) auxiliary space.
        """
        index = (self.bisect_right(x) if inclusive else self.bisect_left(x)) - 1
        if index < 0:
            return None
        return self[index]


class MergeableBinaryTrie(Generic[ValueT]):
    """
    Mergeable binary trie data structure supporting multiple tries with associative operations.

    A binary trie implementation that supports multiple independent tries that can be
    merged and split. Each leaf stores a value of type ValueT, and the trie maintains
    associative products over subtrees. Supports both forward and reverse product
    computation for non-commutative operations.

    Attributes:
        bitlen: Maximum bit length of integers (supports [0, 2^bitlen))
        op: Associative binary operation on type ValueT
        e: Identity element for the operation
        calc_reverse: Whether to store reverse products as well as forward products.
        ptr: List storing child pointers and parent pointers for all nodes
        cnt_type: List storing node counts and type flags (root/leaf) for all nodes
        sum: List storing subtree products for all nodes (forward and reverse if calc_reverse is True)
        free_nodes: List of indices of nodes that have been marked for reuse after deletion

    Time Complexities:
        - new_trie: O(1)
        - add/discard/contains: O(bitlen)
        - index/bisect_left: O(bitlen)
        - size: O(1)
        - __len__: O(P), where P is the number of allocated node slots
        - get: O(bitlen)
        - prod: O(1)
        - merge: O(v), where v is the number of overlapping node pairs
        - split: O(bitlen)

    Args:
        bitlen: Maximum bit length of integers (supports [0, 2^bitlen))
        op: Associative binary operation on type ValueT
        e: Identity element for the operation
        calc_reverse: Whether to store reverse products as well as forward products.

    Examples:
        >>> trie = MergeableBinaryTrie(20, lambda x, y: x + y, 0, calc_reverse=True)
        >>> root1 = trie.new_trie()
        >>> trie.add(root1, 5, 10)  # key=5, value=10
        True
        >>> trie.add(root1, 3, 20)  # key=3, value=20
        True
        >>> trie.prod(root1)  # (forward_sum, reverse_sum)
        (30, 30)
        >>> root2 = trie.new_trie()
        >>> trie.add(root2, 7, 15)
        True
        >>> merged = trie.merge(root1, root2)  # Merge tries
        >>> trie.size(merged)
        3

    Notes:
        Each trie maintains elements in sorted order by key and supports
        efficient merge/split operations. Forward products follow increasing key order. Reverse products are
        maintained only when calc_reverse=True; otherwise prod returns e
        as its second component.

    Space Complexity:
        O(P), where P is the number of allocated node slots. Overlapping
        nodes are recycled on merge, but discard does not release paths.
        Each add or split can allocate O(bitlen) nodes.
    """
    def __init__(self, bitlen: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, calc_reverse: bool = False) -> None:
        """
        Initialize a MergeableBinaryTrie with specified parameters.

        Time Complexity: O(1)

        Args:
            bitlen (int): The bit length of integers to be stored (supports [0, 2^bitlen))
            op (Callable[[ValueT, ValueT], ValueT]): Associative binary operation on type ValueT
            e (ValueT): Identity element for the operation (op(e, x) = op(x, e) = x)
            calc_reverse: If True, also maintain products in decreasing key order.

        Returns:
            None. Initializes storage for independently rooted tries.
        Raises:
            ValueError: If bitlen is negative. A bit length of zero allows only key 0.

        """
        if bitlen < 0:
            raise ValueError('bitlen must be non-negative')
        self.bitlen = bitlen
        self.ptr: list[int] = [0, 0, 0] # [left, right, parent]
        self.cnt_type: list[int] = [0] # node count of subtree. root: + 1 << 29, leaf: + 1 << 30
        self.calc_reverse = calc_reverse
        if calc_reverse:
            self.sum: list[ValueT] = [e, e] # [sum, rev_sum]
        else:
            self.sum: list[ValueT] = [e]
        self.e = e
        self.op = op
        self.free_nodes: list[int] = []  # Pool of reusable node indices

    def _mark_for_reuse(self, v: int) -> None:
        """Mark a node and its subtree for potential reuse."""
        if v == 0 or self._is_root(v): return
        self.free_nodes.append(v)

    def _count(self, v: int) -> int:
        return self.cnt_type[v] & ((1 << 29) - 1)

    def _set_count(self, v: int, cnt: int) -> None:
        is_root = self._is_root(v)
        is_leaf = self._is_leaf(v)
        self.cnt_type[v] = cnt
        if is_root: self.cnt_type[v] |= 1 << 29
        if is_leaf: self.cnt_type[v] |= 1 << 30

    def _is_root(self, v: int) -> bool:
        return self.cnt_type[v] & (1 << 29) != 0

    def _is_leaf(self, v: int) -> bool:
        return self.cnt_type[v] & (1 << 30) != 0

    def _new_node(self, par: int) -> int:
        if self.free_nodes:
            # Reuse a freed node
            v = self.free_nodes.pop()
            self.ptr[v * 3] = 0
            self.ptr[v * 3 + 1] = 0
            self.ptr[v * 3 + 2] = par
            self.cnt_type[v] = 0
            if self.calc_reverse:
                self.sum[v * 2] = self.e
                self.sum[v * 2 + 1] = self.e
            else:
                self.sum[v] = self.e
            return v
        else:
            # Create new node
            self.ptr.append(0)
            self.ptr.append(0)
            self.ptr.append(par)
            self.cnt_type.append(0)
            if self.calc_reverse:
                self.sum.append(self.e)
                self.sum.append(self.e)
            else:
                self.sum.append(self.e)
            return len(self.ptr) // 3 - 1

    def new_trie(self) -> int:
        """
        Create a new empty trie and return its root index.

        Returns:
            int: The root index of the newly created trie

        Examples:
            >>> trie = MergeableBinaryTrie(10, lambda x, y: x + y, 0)
            >>> root = trie.new_trie()
            >>> trie.size(root)
            0

        Time Complexity:
            O(1)
        """
        v = self._new_node(0)
        self.cnt_type[v] |= 1 << 29
        if self.bitlen == 0:
            self.cnt_type[v] |= 1 << 30
        return v

    def add(self, root: int, x: int, val: ValueT, update: bool = False) -> bool:
        """
        Add an integer with associated value to the specified trie.

        Args:
            root (int): The root index of the target trie
            x (int): The integer key to add (must be in [0, 2^bitlen))
            val (ValueT): The value to associate with the key
            update (bool): If True, update the value if the key already exists

        Returns:
            True if a new key was added, False if it already existed, including value updates.

        Raises:
            ValueError: If x is out of range or root is not a valid root

        Examples:
            >>> trie = MergeableBinaryTrie(10, lambda x, y: x + y, 0)
            >>> root = trie.new_trie()
            >>> trie.add(root, 42, 100)
            True
            >>> trie.add(root, 42, 200)  # Already exists
            False
            >>> trie.add(root, 42, 300, update=True)  # Update value
            False

        Time Complexity:
            O(bitlen)
        """
        if x < 0 or x >= 1 << self.bitlen:
            raise ValueError("x must be in [0, 2^bitlen)")
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError("given index is not root")
        v = root
        for i in range(self.bitlen - 1, -1, -1):
            if x >> i & 1:
                if not self.ptr[v * 3 + 1]:
                    self.ptr[v * 3 + 1] = self._new_node(v)
                v = self.ptr[v * 3 + 1]
            else:
                if not self.ptr[v * 3]:
                    self.ptr[v * 3] = self._new_node(v)
                v = self.ptr[v * 3]
        added = self._count(v) == 0
        if not added and not update: return False
        self._set_count(v, 1)
        self.cnt_type[v] |= 1 << 30 # leaf
        if self.calc_reverse:
            self.sum[v * 2 + 0] = val
            self.sum[v * 2 + 1] = val
        else:
            self.sum[v] = val
        while v:
            if not self._is_leaf(v):
                if self.calc_reverse:
                    self.sum[v * 2 + 0] = self.op(self.sum[self.ptr[v * 3] * 2 + 0], self.sum[self.ptr[v * 3 + 1] * 2 + 0])
                    self.sum[v * 2 + 1] = self.op(self.sum[self.ptr[v * 3 + 1] * 2 + 1], self.sum[self.ptr[v * 3] * 2 + 1])
                else:
                    self.sum[v] = self.op(self.sum[self.ptr[v * 3]], self.sum[self.ptr[v * 3 + 1]])
                self._set_count(v, self._count(self.ptr[v * 3]) + self._count(self.ptr[v * 3 + 1]))
            v = self.ptr[v * 3 + 2]
        return added

    def discard(self, root: int, x: int) -> bool:
        """
        Remove the specified value if present.

        Args:
            root: Valid root of the target trie.
            x: Value to remove.

        Returns:
            True if removed, otherwise False.

        Raises:
            ValueError: If the root is invalid.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(bitlen), assuming the aggregation operation is O(1).
        """
        if not 0 <= root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError('given index is not root')
        if x < 0 or x >= 1 << self.bitlen:
            return False
        v = root
        for i in range(self.bitlen - 1, -1, -1):
            if x >> i & 1:
                if not self.ptr[v * 3 + 1]:
                    return False
                v = self.ptr[v * 3 + 1]
            else:
                if not self.ptr[v * 3]:
                    return False
                v = self.ptr[v * 3]
        if self._count(v) == 0: return False
        self._set_count(v, 0)
        if self.calc_reverse:
            self.sum[v * 2 + 0] = self.e
            self.sum[v * 2 + 1] = self.e
        else:
            self.sum[v] = self.e
        while v:
            if not self._is_leaf(v):
                if self.calc_reverse:
                    self.sum[v * 2 + 0] = self.op(self.sum[self.ptr[v * 3] * 2 + 0], self.sum[self.ptr[v * 3 + 1] * 2 + 0])
                    self.sum[v * 2 + 1] = self.op(self.sum[self.ptr[v * 3 + 1] * 2 + 1], self.sum[self.ptr[v * 3] * 2 + 1])
                else:
                    self.sum[v] = self.op(self.sum[self.ptr[v * 3]], self.sum[self.ptr[v * 3 + 1]])
                self._set_count(v, self._count(self.ptr[v * 3]) + self._count(self.ptr[v * 3 + 1]))
            v = self.ptr[v * 3 + 2]
        return True

    def remove(self, root: int, x: int) -> None:
        """
        Remove the specified value.

        Args:
            root: Valid root of the target trie.
            x: Value to remove.

        Returns:
            None.

        Raises:
            KeyError: If the value is absent.
            ValueError: If the root is invalid.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(bitlen), assuming the aggregation operation is O(1).
        """
        if not self.discard(root, x):
            raise KeyError(x)

    def contains(self, root: int, x: int) -> bool:
        """
        Check if an integer is contained in the specified trie.

        Args:
            root (int): The root index of the target trie
            x (int): The integer key to check; values outside the storage range are absent.

        Returns:
            bool: True if the key is in the trie, False otherwise

        Raises:
            ValueError: If root is not a valid root

        Time Complexity:
            O(bitlen)
        """
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError('given index is not root')
        if x < 0 or x >= 1 << self.bitlen:
            return False
        v = root
        for i in range(self.bitlen - 1, -1, -1):
            if x >> i & 1:
                if not self.ptr[v * 3 + 1]:
                    return False
                v = self.ptr[v * 3 + 1]
            else:
                if not self.ptr[v * 3]:
                    return False
                v = self.ptr[v * 3]
        return self._count(v) > 0

    def __contains__(self, x: int) -> bool:
        """
        Check if an integer is contained in any trie.

        Time Complexity:
            O(P + R * bitlen), where P is allocated node slots and R is active roots

        Args:
            x (int): The integer key to check (must be in [0, 2^bitlen))

        Returns:
            bool: True if the key is in any trie, False otherwise

        Examples:
            >>> trie = MergeableBinaryTrie(10, lambda x, y: x + y, 0)
            >>> root = trie.new_trie()
            >>> trie.add(root, 42, 100)
            True
            >>> 42 in trie
            True
            >>> 43 in trie
            False
        """
        for r in range(len(self.cnt_type)):
            if self._is_root(r) and self.contains(r, x):
                return True
        return False

    def index(self, root: int, x: int) -> int:
        """
        Return the first sorted index of ``x``.

        Args:
            root: Valid root of the target trie.
            x: Search value.

        Returns:
            Zero-based index of the first occurrence.

        Raises:
            ValueError: If the value is absent or the root is invalid.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(bitlen).
        """
        if x < 0 or x >= 1 << self.bitlen:
            raise ValueError("x must be in [0, 2^bitlen)")
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError("given index is not root")
        v = root
        res = 0
        for i in range(self.bitlen - 1, -1, -1):
            if x >> i & 1:
                if not self.ptr[v * 3 + 1] or self._count(self.ptr[v * 3 + 1]) == 0:
                    raise ValueError('given value is not contained')
                res += self._count(v) - self._count(self.ptr[v * 3 + 1])
                v = self.ptr[v * 3 + 1]
            else:
                if not self.ptr[v * 3] or self._count(self.ptr[v * 3]) == 0:
                    raise ValueError('given value is not contained')
                v = self.ptr[v * 3]
        if not self._count(v):
            raise ValueError('given value is not contained')
        return res

    def bisect_left(self, root: int, x: int) -> int:
        """
        Return the number of elements strictly less than ``x``.

        Args:
            root: Valid root of the target trie.
            x: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Raises:
            ValueError: If the root is invalid.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(bitlen).
        """
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError('given index is not root')
        if x <= 0:
            return 0
        if x >= 1 << self.bitlen:
            return self._count(root)
        v = root
        res = 0
        for i in range(self.bitlen - 1, -1, -1):
            if x >> i & 1:
                if not self.ptr[v * 3 + 1] or self._count(self.ptr[v * 3 + 1]) == 0:
                    return res + self._count(v)
                res += self._count(v) - self._count(self.ptr[v * 3 + 1])
                v = self.ptr[v * 3 + 1]
            else:
                if not self.ptr[v * 3] or self._count(self.ptr[v * 3]) == 0:
                    return res
                v = self.ptr[v * 3]
        return res

    def bisect_right(self, root: int, x: int) -> int:
        """
        Return the number of elements less than or equal to ``x``.

        Args:
            root: Valid root of the target trie.
            x: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Raises:
            ValueError: If the root is invalid.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(bitlen).
        """
        return self.bisect_left(root, x + 1)

    def successor(self, root: int, x: int, inclusive: bool = True) -> int | None:
        """Return the smallest stored key greater than or equal to ``x``.

        Args:
            root: Valid root of the target trie.
            x: Search key; it may be absent or outside [0, 2**bitlen).
            inclusive: If False, require a key strictly greater than x.

        Returns:
            Matching stored key, or None if no such key exists.

        Raises:
            ValueError: If the root is invalid.

        Time Complexity:
            O(bitlen).

        Space Complexity:
            O(1) auxiliary space.
        """
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError('given index is not root')
        index = self.bisect_left(root, x) if inclusive else self.bisect_right(root, x)
        if index == self._count(root):
            return None
        return self.get(root, index)[0]

    def predecessor(self, root: int, x: int, inclusive: bool = True) -> int | None:
        """Return the largest stored key less than or equal to ``x``.

        Args:
            root: Valid root of the target trie.
            x: Search key; it may be absent or outside [0, 2**bitlen).
            inclusive: If False, require a key strictly less than x.

        Returns:
            Matching stored key, or None if no such key exists.

        Raises:
            ValueError: If the root is invalid.

        Time Complexity:
            O(bitlen).

        Space Complexity:
            O(1) auxiliary space.
        """
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError('given index is not root')
        index = (self.bisect_right(root, x) if inclusive else self.bisect_left(root, x)) - 1
        if index < 0:
            return None
        return self.get(root, index)[0]

    def size(self, root: int) -> int:
        """
        Get the number of elements in the specified trie.

        Args:
            root (int): The root index of the target trie

        Returns:
            int: The number of elements in the trie

        Raises:
            ValueError: If root is not a valid root

        Time Complexity:
            O(1)
        """
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError("given index is not root")
        return self._count(root)

    def __len__(self) -> int:
        """
        Get the total number of elements across all tries.

        Time Complexity: O(P), where P is the number of allocated node slots

        Returns:
            int: The total number of elements across all tries
        """
        res = 0
        for r in range(len(self.cnt_type)):
            if self._is_root(r):
                res += self.size(r)
        return res

    def merge(self, root1: int, root2: int) -> int:
        """
        Merge two tries into one, combining their elements.

        Args:
            root1 (int): The root index of the first trie (becomes the merged result)
            root2 (int): The root index of the second trie (becomes invalid after merge)

        Returns:
            int: The root index of the merged trie (same as root1)

        Raises:
            ValueError: If either root is invalid or both roots are the same.

        Examples:
            >>> trie = MergeableBinaryTrie(10, lambda x, y: x + y, 0)
            >>> root1 = trie.new_trie()
            >>> root2 = trie.new_trie()
            >>> trie.add(root1, 3, 10)
            True
            >>> trie.add(root2, 5, 20)
            True
            >>> merged = trie.merge(root1, root2)
            >>> trie.size(merged)
            2

        Time Complexity:
            O(v), where v is the number of overlapping node pairs visited.
            Each visit releases one node from root2, so the total merge work
            is O(A + M) across M merges and A node allocations, counting reuse.

        Notes:
            If a key is present in both tries, the value from root1 is retained.
            A previously deleted key is absent and does not override root2.
            Root handles consumed by a merge must not be used again; their
            integer slots may later be reused.

        """
        if not 0 < root1 < len(self.cnt_type) or not self._is_root(root1):
            raise ValueError('first index is not a valid root')
        if not 0 < root2 < len(self.cnt_type) or not self._is_root(root2):
            raise ValueError('second index is not a valid root')
        if root1 == root2:
            raise ValueError('cannot merge a trie with itself')
        stack = [(root1, root2)]
        order: list[int] = []
        while stack:
            v1, v2 = stack.pop()
            order.append(v1)
            self._mark_for_reuse(v2)
            if self._is_leaf(v1) and self._is_leaf(v2):
                if self._count(v1) == 0:
                    if self.calc_reverse:
                        self.sum[v1 * 2] = self.sum[v2 * 2]
                        self.sum[v1 * 2 + 1] = self.sum[v2 * 2 + 1]
                    else:
                        self.sum[v1] = self.sum[v2]
                self._set_count(v1, self._count(v1) | self._count(v2))
                continue
            if self.ptr[v1 * 3 + 0]:
                if self.ptr[v2 * 3 + 0]:
                    stack.append((self.ptr[v1 * 3 + 0], self.ptr[v2 * 3 + 0]))
            else:
                if self.ptr[v2 * 3 + 0]:
                    self.ptr[v1 * 3 + 0] = self.ptr[v2 * 3 + 0]
                    self.ptr[self.ptr[v1 * 3 + 0] * 3 + 2] = v1
            if self.ptr[v1 * 3 + 1]:
                if self.ptr[v2 * 3 + 1]:
                    stack.append((self.ptr[v1 * 3 + 1], self.ptr[v2 * 3 + 1]))
            else:
                if self.ptr[v2 * 3 + 1]:
                    self.ptr[v1 * 3 + 1] = self.ptr[v2 * 3 + 1]
                    self.ptr[self.ptr[v1 * 3 + 1] * 3 + 2] = v1
        for v in order[::-1]:
            if self._is_leaf(v): continue
            if self.calc_reverse:
                self.sum[v * 2 + 0] = self.op(self.sum[self.ptr[v * 3] * 2 + 0], self.sum[self.ptr[v * 3 + 1] * 2 + 0])
                self.sum[v * 2 + 1] = self.op(self.sum[self.ptr[v * 3 + 1] * 2 + 1], self.sum[self.ptr[v * 3] * 2 + 1])
            else:
                self.sum[v] = self.op(self.sum[self.ptr[v * 3]], self.sum[self.ptr[v * 3 + 1]])
            self._set_count(v, self._count(self.ptr[v * 3]) + self._count(self.ptr[v * 3 + 1]))
        self.cnt_type[root2] &= ~(1 << 29)  # Remove root flag
        self._mark_for_reuse(root2)  # Mark root2 for potential reuse
        return root1

    def split(self, root: int, x: int) -> tuple[int, int]:
        """
        Split a trie into two tries: one containing keys [0, x) and another containing [x, 2^bitlen).

        WARNING: The behavior is undefined when x does not exist in the trie and is not at a
        valid split boundary. For safe splitting with arbitrary x values, use safe_split() instead.

        The operation is destructive. Continue with the returned roots instead
        of treating the input root as an unchanged snapshot.

        Args:
            root (int): The root index of the trie to split
            x (int): The split point (must be in [0, 2^bitlen])

        Returns:
            tuple[int, int]: (left_root, right_root) where left contains [0, x) and right contains [x, 2^bitlen)

        Raises:
            ValueError: If x is out of range or root is not a valid root

        Examples:
            >>> trie = MergeableBinaryTrie(10, lambda x, y: x + y, 0)
            >>> root = trie.new_trie()
            >>> for i in [1, 3, 5, 7]: _ = trie.add(root, i, i * 10)
            >>> left, right = trie.split(root, 5)  # Split at an existing key
            >>> trie.size(left)  # Contains 1, 3
            2
            >>> trie.size(right)  # Contains 5, 7
            2

        Notes:
            This method works correctly when x is a key that exists in the trie or when
            splitting at boundaries where the trie structure naturally divides. For arbitrary
            split points, consider using safe_split() which handles all cases correctly.

        Time Complexity:
            O(bitlen)
        """
        if x < 0 or x > 1 << self.bitlen:
            raise ValueError('split key must be in [0, 2^bitlen]')
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError("given index is not root")
        if x == 0:
            n = self.new_trie()
            return n, root
        if x == 1 << self.bitlen:
            n = self.new_trie()
            return root, n
        v = root
        for i in range(self.bitlen - 1, -1, -1):
            if x >> i & 1:
                if not self.ptr[v * 3 + 1]: break
                v = self.ptr[v * 3 + 1]
            else:
                if not self.ptr[v * 3]: break
                v = self.ptr[v * 3]
        update = False
        nv = np = 0
        while self.ptr[v * 3 + 2]:
            p = self.ptr[v * 3 + 2]
            if not update:
                if self.ptr[p * 3 + 1] == v and self.ptr[p * 3]:
                    pl = self.ptr[p * 3]
                    update = True
                    np = self._new_node(0)
                    self.ptr[np * 3 + 0] = pl
                    self.ptr[pl * 3 + 2] = np
                    self.ptr[p * 3] = 0
            else:
                if self.ptr[p * 3] == v:
                    np = self._new_node(0)
                    self.ptr[np * 3] = nv
                    self.ptr[np * 3 + 1] = 0
                    self.ptr[nv * 3 + 2] = np
                else:
                    np = self._new_node(0)
                    self.ptr[np * 3 + 0] = self.ptr[p * 3 + 0]
                    if self.ptr[p * 3]:
                        self.ptr[self.ptr[p * 3] * 3 + 2] = np
                    self.ptr[p * 3 + 0] = 0
                    self.ptr[np * 3 + 1] = nv
                    self.ptr[nv * 3 + 2] = np
            self._set_count(p, self._count(self.ptr[p * 3]) + self._count(self.ptr[p * 3 + 1]))
            if self.calc_reverse:
                self.sum[p * 2 + 0] = self.op(self.sum[self.ptr[p * 3 + 0] * 2 + 0], self.sum[self.ptr[p * 3 + 1] * 2 + 0])
                self.sum[p * 2 + 1] = self.op(self.sum[self.ptr[p * 3 + 1] * 2 + 1], self.sum[self.ptr[p * 3 + 0] * 2 + 1])
            else:
                self.sum[p] = self.op(self.sum[self.ptr[p * 3]], self.sum[self.ptr[p * 3 + 1]])
            if update:
                self._set_count(np, self._count(self.ptr[np * 3]) + self._count(self.ptr[np * 3 + 1]))
                if self.calc_reverse:
                    self.sum[np * 2 + 0] = self.op(self.sum[self.ptr[np * 3 + 0] * 2 + 0], self.sum[self.ptr[np * 3 + 1] * 2 + 0])
                    self.sum[np * 2 + 1] = self.op(self.sum[self.ptr[np * 3 + 1] * 2 + 1], self.sum[self.ptr[np * 3 + 0] * 2 + 1])
                else:
                    self.sum[np] = self.op(self.sum[self.ptr[np * 3]], self.sum[self.ptr[np * 3 + 1]])
            v = p
            nv = np
        if nv == 0:
            nv = self.new_trie()
        self.cnt_type[nv] |= (1 << 29)
        return nv, v

    def get(self, root: int, k: int) -> tuple[int, ValueT]:
        """
        Get the k-th smallest element and its value from the specified trie.

        Args:
            root (int): The root index of the target trie
            k (int): The index (0-based) of the element to retrieve

        Returns:
            tuple[int, ValueT]: (key, value) of the k-th smallest element

        Raises:
            ValueError: If root is not a valid root.
            IndexError: If k is outside [0, size(root)).

        Examples:
            >>> trie = MergeableBinaryTrie(10, lambda x, y: x + y, 0)
            >>> root = trie.new_trie()
            >>> trie.add(root, 5, 50)
            True
            >>> trie.add(root, 3, 30)
            True
            >>> trie.get(root, 0)  # Smallest element
            (3, 30)
            >>> trie.get(root, 1)  # Second smallest
            (5, 50)

        Time Complexity:
            O(bitlen)
        """
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError("given index is not root")
        if k < 0 or k >= self.size(root):
            raise IndexError('this trie has no k-th element')
        v = root
        key = 0
        for i in range(self.bitlen - 1, -1, -1):
            lv, rv = self.ptr[3 * v + 0], self.ptr[3 * v + 1]
            if not lv or self._count(lv) == 0:
                v = rv
                key |= 1 << i
            elif not rv or self._count(rv) == 0:
                v = lv
            else:
                if self._count(lv) <= k:
                    k -= self._count(lv)
                    v = rv
                    key |= 1 << i
                else:
                    v = lv
        return key, self.sum[v] if not self.calc_reverse else self.sum[v * 2 + 0]

    def prod(self, root: int) -> tuple[ValueT, ValueT]:
        """
        Get the product of all values in the specified trie.

        Args:
            root (int): The root index of the target trie

        Returns:
            tuple[ValueT, ValueT]: (forward_product, reverse_product) where forward is computed
                        in increasing key order. The reverse product uses decreasing key
                        order when calc_reverse=True, and equals e otherwise.

        Raises:
            ValueError: If root is not a valid root

        Examples:
            >>> trie = MergeableBinaryTrie(10, lambda x, y: x + y, 0)
            >>> root = trie.new_trie()
            >>> trie.add(root, 3, 10)
            True
            >>> trie.add(root, 5, 20)
            True
            >>> trie.prod(root)  # Sum of values: 10 + 20 = 30
            (30, 0)

        Time Complexity:
            O(1)
        """
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError("given index is not root")
        return (self.sum[root], self.e) if not self.calc_reverse else (self.sum[root * 2 + 0], self.sum[root * 2 + 1])

    def safe_split(self, root: int, x: int) -> tuple[int, int]:
        """
        Safely split a trie at any point x, handling cases where x may not exist in the trie.

        This method provides a safe wrapper around split() that handles all edge cases correctly,
        including when x does not exist in the trie. It finds the appropriate split point using
        bisect_left to ensure a valid split operation.

        This operation is destructive, like split. Use the returned roots
        for subsequent operations.

        Args:
            root (int): The root index of the trie to split
            x (int): The split point (must be in [0, 2^bitlen])

        Returns:
            tuple[int, int]: (left_root, right_root) where left contains all keys < x
                           and right contains all keys >= x

        Raises:
            ValueError: If x is out of range or root is not a valid root

        Examples:
            >>> trie = MergeableBinaryTrie(10, lambda x, y: x + y, 0)
            >>> root = trie.new_trie()
            >>> for i in [0, 1, 5, 7]: _ = trie.add(root, i, i * 10)
            >>> left, right = trie.safe_split(root, 2)  # Split at 2 (doesn't exist)
            >>> trie.size(left)  # Contains 0, 1
            2
            >>> trie.size(right)  # Contains 5, 7
            2
            >>> root = trie.merge(left, right)  # Restore the full set before splitting again.
            >>> left2, right2 = trie.safe_split(root, 5)  # Split at 5 (exists)
            >>> trie.size(left2)  # Contains 0, 1
            2
            >>> trie.size(right2)  # Contains 5, 7
            2

        Time Complexity:
            O(bitlen)
        """
        if x < 0 or x > 1 << self.bitlen:
            raise ValueError("split key must be in [0, 2^bitlen]")
        if not 0 < root < len(self.cnt_type) or not self._is_root(root):
            raise ValueError("given index is not root")
        if x == 0:
            return self.new_trie(), root
        if x == 1 << self.bitlen:
            return root, self.new_trie()
        if self.size(root) == 0:
            return self.new_trie(), root
        lb = self.bisect_left(root, x)
        if lb == 0:
            return self.new_trie(), root
        elif lb == self.size(root):
            return root, self.new_trie()
        else:
            key, _ = self.get(root, lb)
            return self.split(root, key)


class RangeSortRangeProd(Generic[ValueT]):
    """
    Range sorting and ordered products for sequences with distinct integer keys.

    A data structure that supports range sorting and range product queries on sequences.
    Maintains an array where each position has a key and a value, supporting efficient
    range sorting operations and range product queries over values.

    Args:
        n: Length of the sequence
        keys: Initial keys, all distinct across the entire sequence
        vals: Initial values for each position
        bitlen: Maximum bit length of keys (supports [0, 2^bitlen))
        op: Associative binary operation on type ValueT
        e: Identity element for the operation

    Examples:
        >>> # Create a range sort range product structure
        >>> keys = [3, 1, 4, 2]
        >>> vals = [10, 20, 30, 40]
        >>> rsrp = RangeSortRangeProd(4, keys, vals, 10, lambda x, y: x + y, 0)
        >>> rsrp.prod(1, 3)  # Sum of values at positions 1-2
        50
        >>> rsrp.sort(0, 4)  # Sort entire range by keys
        >>> rsrp.get(0)  # Now smallest key (1) is at position 0
        (1, 20)
        >>> rsrp.prod(0, 2)  # Sum of first 2 values after sorting
        60

    Notes:
        Keys must remain globally distinct after every set operation.
        Complexity bounds assume O(1) monoid operations and fixed-size values.
        The structure maintains correspondence between keys and values through
        sorting operations. Range products are computed over the current values
        in the specified range, regardless of sorting history.

    Space Complexity:
        O(n + P), where P is the number of allocated trie node slots.
        Each set or nonempty range query can allocate O(bitlen) nodes, and
        merged or replaced nodes are reused. Deleted paths left by splits
        may remain allocated, so P is not bounded by the current key count alone.
    """
    def __init__(self, n: int, keys: Sequence[int], vals: Sequence[ValueT], bitlen: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT) -> None:
        """
        Initialize a RangeSortRangeProd with given keys and values.

        Time Complexity: O((n + 1) * (bitlen + 1))

        Args:
            n (int): Length of the sequence
            keys (Sequence[int]): Exactly n distinct keys, each in [0, 2^bitlen)
            vals (Sequence[ValueT]): Exactly n values, one for each key
            bitlen (int): Maximum bit length of keys
            op (Callable[[ValueT, ValueT], ValueT]): Associative binary operation on type ValueT
            e (ValueT): Identity element for the operation
        Raises:
            ValueError: If n or bitlen is negative, lengths differ from n,
                keys are outside the supported range, or keys are duplicated.

        Returns:
            None.

        """
        if n < 0 or bitlen < 0:
            raise ValueError('n and bitlen must be non-negative')
        if len(keys) != n or len(vals) != n:
            raise ValueError('keys and vals must have length n')
        if any(key < 0 or key >= 1 << bitlen for key in keys):
            raise ValueError('keys must be in [0, 2**bitlen)')
        self._keys = set(keys)
        if len(self._keys) != n:
            raise ValueError('keys must be distinct')
        self.trie = MergeableBinaryTrie(bitlen, op, e, calc_reverse=True)
        self.root = [0] * (n + 1)
        self.rev = [False] * (n + 1)
        self.bit = FenwickTree(n)
        self.bit.build([1] * n)
        self.seg = SegmentTree(n, op, e)
        self.seg.build(vals)
        for i, key in enumerate(keys):
            self.root[i] = self.trie.new_trie()
            self.trie.add(self.root[i], key, vals[i])
        self.root[n] = self.trie.new_trie()
        self.trie.add(self.root[n], (1 << bitlen) - 1, e)
        self.n = n
        self.bitlen = bitlen
        self.e = e
        self.op = op

    def _search_trie(self, i: int) -> int:
        return self.bit.bisect_left(i + 1) - 1

    def _split_trie(self, i: int) -> None:
        idx = self._search_trie(i)
        sz = self.trie.size(self.root[idx])
        if sz <= 1: return
        if i == idx: return
        if self.rev[idx]:
            x = self.trie.get(self.root[idx], sz - i + idx)[0]
            rt, lt = self.trie.split(self.root[idx], x)
        else:
            x = self.trie.get(self.root[idx], i - idx)[0]
            lt, rt = self.trie.split(self.root[idx], x)
        if not lt:
            self.root[idx] = rt
            return
        if not rt:
            self.root[idx] = lt
            return
        self.root[idx] = lt
        self.root[i] = rt
        self.rev[i] = self.rev[idx]
        self.seg.set(idx, self.trie.prod(self.root[idx])[self.rev[i]])
        self.seg.set(i, self.trie.prod(self.root[i])[self.rev[i]])
        self.bit.set(idx, self.trie.size(self.root[idx]))
        self.bit.set(i, self.trie.size(self.root[i]))

    def set(self, i: int, key: int, val: ValueT) -> None:
        """
        Set the key and value at position i.

        Args:
            i (int): Position to update (must be in [0, n))
            key (int): New key in [0, 2^bitlen), unused at any other position
            val (ValueT): New value

        Examples:
            >>> rsrp = RangeSortRangeProd(3, [1, 2, 3], [10, 20, 30], 10, lambda x, y: x + y, 0)
            >>> rsrp.set(1, 5, 50)  # Set position 1 to key=5, value=50
            >>> rsrp.get(1)
            (5, 50)

        Raises:
            AssertionError: If ``0 <= i < n`` is false.
            ValueError: If key is out of range or used at another position.
                These checks happen before modifying the structure.

        Time Complexity:
            O(bitlen + log(n + 1) + v), where v is the number of old trie nodes
            released when replacing the key. Each released node can be charged
            to its earlier allocation. Updating only the value has v = 0.
        Notes:
            The current key may be reused to update only the value.
            Replaced keys become available for later set operations.

        Returns:
            None.

        """
        assert 0 <= i < self.n
        if not 0 <= key < 1 << self.bitlen:
            raise ValueError('key must be in [0, 2**bitlen)')
        old_key, _ = self.get(i)
        if key != old_key and key in self._keys:
            raise ValueError('key is already used at another position')
        if key == old_key:
            idx = self._search_trie(i)
            self.trie.add(self.root[idx], key, val, update=True)
            self.seg.set(idx, self.trie.prod(self.root[idx])[self.rev[idx]])
            return
        self._split_trie(i)
        self._split_trie(i + 1)
        idx = self._search_trie(i)
        root = self.root[idx]
        trie = self.trie
        stack = [root]
        while stack:
            node = stack.pop()
            left, right = trie.ptr[node * 3], trie.ptr[node * 3 + 1]
            if left:
                stack.append(left)
            if right:
                stack.append(right)
            if node != root:
                trie.free_nodes.append(node)
        trie.ptr[root * 3] = trie.ptr[root * 3 + 1] = 0
        trie.cnt_type[root] = 1 << 29  # Empty root; changing the key requires bitlen > 0.
        trie.sum[root * 2] = trie.sum[root * 2 + 1] = self.e
        trie.add(root, key, val)
        self._keys.remove(old_key)
        self._keys.add(key)
        self.rev[idx] = False
        self.seg.set(idx, val)
        self.bit.set(idx, 1)

    def get(self, i: int) -> tuple[int, ValueT]:
        """
        Get the key and value at position i.

        Args:
            i (int): Position to query (must be in [0, n))

        Returns:
            tuple[int, ValueT]: (key, value) at position i

        Examples:
            >>> rsrp = RangeSortRangeProd(3, [1, 2, 3], [10, 20, 30], 10, lambda x, y: x + y, 0)
            >>> rsrp.get(1)
            (2, 20)

        Raises:
            AssertionError: If ``0 <= i < n`` is false.

        Time Complexity:
            O(bitlen + log(n + 1))
        """
        assert 0 <= i < self.n
        idx = self._search_trie(i)
        rank = i - idx
        if self.rev[idx]:
            rank = self.trie.size(self.root[idx]) - 1 - rank
        return self.trie.get(self.root[idx], rank)

    def sort(self, l: int, r: int, reverse: bool = False) -> None:
        """
        Sort the range [l, r) by keys.

        Args:
            l (int): Left boundary of range (inclusive)
            r (int): Right boundary of range (exclusive)
            reverse (bool): If True, sort in descending order; otherwise ascending

        Examples:
            >>> rsrp = RangeSortRangeProd(4, [3, 1, 4, 2], [30, 10, 40, 20], 10, lambda x, y: x + y, 0)
            >>> rsrp.sort(0, 4)  # Sort entire array by keys
            >>> [rsrp.get(i)[0] for i in range(4)]  # Keys are now sorted
            [1, 2, 3, 4]
            >>> rsrp.sort(0, 4, reverse=True)  # Sort in descending order
            >>> [rsrp.get(i)[0] for i in range(4)]
            [4, 3, 2, 1]

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(bitlen + (k + 1) * log(n + 1) + v), where k is the number of
            blocks merged and v is the number of overlapping trie nodes visited.
            Merged blocks and released nodes are charged to earlier creation;
            total work over q updates/queries is O((n + q) * (bitlen + log(n + 1))).
        Returns:
            None.

        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return
        self._split_trie(l)
        self._split_trie(r)
        lidx = self._search_trie(l)
        ridx = self._search_trie(r)
        cur = self.bit.bisect_left(self.bit.sum(lidx + 1) + 1) - 1
        while cur < ridx:
            self.root[lidx] = self.trie.merge(self.root[lidx], self.root[cur])
            self.root[cur] = 0
            self.bit.set(cur, 0)
            self.seg.set(cur, self.e)
            self.rev[cur] = False
            cur = self.bit.bisect_left(self.bit.sum(cur + 1) + 1) - 1
        self.rev[lidx] = reverse
        self.seg.set(lidx, self.trie.prod(self.root[lidx])[reverse])
        self.bit.set(lidx, self.trie.size(self.root[lidx]))

    def prod(self, l: int, r: int) -> ValueT:
        """
        Compute the product of values in range [l, r).

        Args:
            l (int): Left boundary of range (inclusive)
            r (int): Right boundary of range (exclusive)

        Returns:
            ValueT: Product of values in the specified range

        Examples:
            >>> rsrp = RangeSortRangeProd(4, [3, 1, 4, 2], [30, 10, 40, 20], 10, lambda x, y: x + y, 0)
            >>> rsrp.prod(1, 3)  # Sum of values at positions 1-2
            50
            >>> rsrp.sort(0, 4)  # Sort by keys
            >>> rsrp.prod(0, 2)  # Sum of first 2 values after sorting
            30

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(bitlen + log(n + 1)); O(1) for an empty range.
        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return self.e
        self._split_trie(l)
        self._split_trie(r)
        lidx = self._search_trie(l)
        ridx = self._search_trie(r)
        return self.seg.prod(lidx, ridx)

    def all_prod(self) -> ValueT:
        """
        Compute the product of all values in the sequence.

        Returns:
            ValueT: Product of all values

        Examples:
            >>> rsrp = RangeSortRangeProd(4, [3, 1, 4, 2], [30, 10, 40, 20], 10, lambda x, y: x + y, 0)
            >>> rsrp.all_prod()  # Sum of all values
            100

        Time Complexity:
            O(1)
        """
        return self.seg.all_prod()
