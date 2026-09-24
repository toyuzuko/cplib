#!/usr/bin/env python3

from __future__ import annotations

from typing import Generic, cast

from cplib.tools.type import T


class DoublyLinkedList(Generic[T]):
    """
    Doubly linked list with O(1) end operations and node-handle operations.

    This structure is optimized for workloads where new values are inserted at
    the front and the first occurrence of a value from the front is deleted.
    It also supports cursor-style insertion and deletion through node handles.
    Values must be hashable and keep stable equality and hashes while stored.
    None is a valid value. Handles are positive integers local to this list;
    erased handles are invalid and never reused. The sentinel handle is 0.

    Space Complexity:
        O(m), where m is the total number of insertions, including erased nodes.
    """
    def __init__(self) -> None:
        """
        Initialize an empty list.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._values: list[T | None] = [None]
        self._prev = [0]
        self._next = [0]
        self._active = [False]
        self._occurrence: dict[T, list[int]] = {}
        self._front_insert_only = True
        self._size = 0

    def __len__(self) -> int:
        """
        Return the number of active nodes.

        Returns:
            Number of values in the list.

        Time Complexity:
            O(1)
        """
        return self._size

    def size(self) -> int:
        """
        Return the number of active nodes.

        Returns:
            Number of values in the list.

        Time Complexity:
            O(1)
        """
        return len(self)

    def _insert_after(self, pos: int, node: int) -> None:
        nxt = self._next[pos]
        self._prev[node] = pos
        self._next[node] = nxt
        self._next[pos] = node
        self._prev[nxt] = node

    def _new_node(self, value: T) -> int:
        nodes = self._occurrence.setdefault(value, [])
        node = len(self._values)
        self._values.append(value)
        self._prev.append(0)
        self._next.append(0)
        self._active.append(True)
        nodes.append(node)
        self._size += 1
        return node

    def _erase_node(self, node: int) -> T:
        if not 0 < node < len(self._active) or not self._active[node]:
            raise ValueError('node is not active')
        prv = self._prev[node]
        nxt = self._next[node]
        self._next[prv] = nxt
        self._prev[nxt] = prv
        self._active[node] = False
        self._size -= 1
        return cast(T, self._values[node])

    def insert_front(self, value: T) -> None:
        """
        Insert value at the front.

        Args:
            value: Value to insert.

        Raises:
            TypeError: If value is not hashable.

        Returns:
            None.

        Time Complexity:
            Average amortized O(1), assuming O(1) hashing and equality.
        """
        node = self._new_node(value)
        self._insert_after(0, node)

    def append(self, value: T) -> int:
        """
        Insert value at the back and return its node handle.

        Args:
            value: Value to insert.

        Raises:
            TypeError: If value is not hashable.

        Returns:
            Node handle of the inserted value.

        Time Complexity:
            Average amortized O(1), assuming O(1) hashing and equality.
        """
        return self.insert_before(0, value)

    def insert_before(self, pos: int, value: T) -> int:
        """
        Insert value just before a node handle.

        Args:
            pos: Node handle before which the value is inserted. Use ``0`` for
                the end sentinel.
            value: Value to insert.

        Raises:
            TypeError: If value is not hashable.
            ValueError: If pos is neither 0 nor an active handle.

        Returns:
            Node handle of the inserted value.

        Time Complexity:
            Average amortized O(1), assuming O(1) hashing and equality.
        """
        if not 0 <= pos < len(self._active) or (pos != 0 and not self._active[pos]):
            raise ValueError('pos is not active')
        node = self._new_node(value)
        self._front_insert_only = False
        self._insert_after(self._prev[pos], node)
        return node

    def erase(self, node: int) -> tuple[T, int]:
        """
        Remove a node and return its value and the next node handle.

        Args:
            node: Active node handle to remove.

        Returns:
            Removed value and the following node handle, or ``0`` if it was the
            last node.

        Raises:
            ValueError: If the handle is invalid or erased (0 is invalid).

        Time Complexity:
            O(1)
        """
        value = self._erase_node(node)
        return value, self._next[node]

    def value(self, node: int) -> T:
        """
        Return the value stored at a node handle.

        Args:
            node: Active node handle.

        Returns:
            Stored value.

        Raises:
            ValueError: If the handle is invalid or erased (0 is invalid).

        Time Complexity:
            O(1)
        """
        if not 0 < node < len(self._active) or not self._active[node]:
            raise ValueError('node is not active')
        return cast(T, self._values[node])

    def next_node(self, node: int) -> int:
        """
        Return the next node handle.

        Args:
            node: Node handle, or ``0`` for the end sentinel.

        Returns:
            Next node handle, or ``0`` at the end. For node=0, the front
            handle is returned (0 if empty).

        Raises:
            ValueError: If the handle is invalid or erased (0 is allowed).

        Time Complexity:
            O(1)
        """
        if not 0 <= node < len(self._active) or (node != 0 and not self._active[node]):
            raise ValueError('node is not active')
        return self._next[node]

    def prev_node(self, node: int) -> int:
        """
        Return the previous node handle.

        Args:
            node: Node handle, or ``0`` for the end sentinel.

        Returns:
            Previous node handle, or ``0`` before the front. For node=0,
            the back handle is returned (0 if empty).

        Raises:
            ValueError: If the handle is invalid or erased (0 is allowed).

        Time Complexity:
            O(1)
        """
        if not 0 <= node < len(self._active) or (node != 0 and not self._active[node]):
            raise ValueError('node is not active')
        return self._prev[node]

    def front_node(self) -> int:
        """
        Return the front node handle.

        Returns:
            Front node handle, or ``0`` if the list is empty.

        Time Complexity:
            O(1)
        """
        return self._next[0]

    def back_node(self) -> int:
        """
        Return the back node handle.

        Returns:
            Back node handle, or ``0`` if the list is empty.

        Time Complexity:
            O(1)
        """
        return self._prev[0]

    def pop_front(self) -> T:
        """
        Remove and return the front value.

        Returns:
            Front value.

        Raises:
            IndexError: If the list is empty.

        Time Complexity:
            O(1)
        """
        if self._size == 0:
            raise IndexError('pop from an empty DoublyLinkedList')
        return self._erase_node(self._next[0])

    def pop_back(self) -> T:
        """
        Remove and return the back value.

        Returns:
            Back value.

        Raises:
            IndexError: If the list is empty.

        Time Complexity:
            O(1)
        """
        if self._size == 0:
            raise IndexError('pop from an empty DoublyLinkedList')
        return self._erase_node(self._prev[0])

    def discard_first(self, value: T) -> bool:
        """
        Remove the first occurrence of value from the front.

        Args:
            value: Value to delete.

        Returns:
            ``True`` if a value was removed, otherwise ``False``.

        Time Complexity:
            Average amortized O(1) if insert_front is the only insertion method
            used so far. After append or insert_before, O(n) for n active nodes.
        """
        if not self._front_insert_only:
            node = self._next[0]
            while node != 0:
                if self._active[node] and self._values[node] == value:
                    self._erase_node(node)
                    return True
                node = self._next[node]
            return False
        nodes = self._occurrence.get(value)
        if nodes is None:
            return False
        while nodes and not self._active[nodes[-1]]:
            nodes.pop()
        if not nodes:
            return False
        self._erase_node(nodes.pop())
        return True

    def to_list(self) -> list[T]:
        """
        Return all values from front to back.

        Returns:
            Values in list order.

        Time Complexity:
            O(n)
        """
        res: list[T] = []
        node = self._next[0]
        while node != 0:
            res.append(cast(T, self._values[node]))
            node = self._next[node]
        return res


class SpliceableLinkedLists(Generic[T]):
    """
    Collection of singly linked lists with O(1) append and splice-to-back.

    Node handles are managed internally. The structure is useful when many
    lists are concatenated repeatedly and elements must not be copied during
    concatenation.

    Space Complexity:
        O(number of inserted values + number of lists)
    """
    def __init__(self, n: int) -> None:
        """
        Initialize ``n`` empty lists.

        Args:
            n: Number of lists to manage.

        Returns:
            None.

        Raises:
            ValueError: If n is negative.

        Time Complexity:
            O(n)
        """
        if n < 0:
            raise ValueError('number of lists must be nonnegative')
        self.n = n
        self.head = [0] * n
        self.tail = [0] * n
        self.next = [0]
        self.values: list[T | None] = [None]
        self.sizes = [0] * n

    def __len__(self) -> int:
        """
        Return the total number of stored values.

        Returns:
            Total number of values in all lists.

        Time Complexity:
            O(1)
        """
        return len(self.values) - 1

    def list_size(self, index: int) -> int:
        """
        Return the size of one list.

        Args:
            index: List index.

        Returns:
            Number of values in the list.

        Raises:
            IndexError: If a list index is outside [0, n).

        Time Complexity:
            O(1)
        """
        if not 0 <= index < self.n:
            raise IndexError('list index out of range')
        return self.sizes[index]

    def append(self, index: int, value: T) -> int:
        """
        Append value to the back of one list.

        Args:
            index: List index.
            value: Value to append.

        Returns:
            Node handle of the inserted value.

        Raises:
            IndexError: If a list index is outside [0, n).

        Time Complexity:
            Amortized O(1)
        """
        if not 0 <= index < self.n:
            raise IndexError('list index out of range')
        node = len(self.values)
        self.values.append(value)
        self.next.append(0)
        if self.head[index] == 0:
            self.head[index] = node
        else:
            self.next[self.tail[index]] = node
        self.tail[index] = node
        self.sizes[index] += 1
        return node

    def splice_back(self, source: int, target: int) -> None:
        """
        Move all values of one list to the back of another list.

        Args:
            source: Source list index. It becomes empty after the operation,
                except when source == target, which leaves the list unchanged.
            target: Target list index.

        Returns:
            None.

        Raises:
            IndexError: If a list index is outside [0, n).

        Time Complexity:
            O(1)
        """
        if not 0 <= source < self.n or not 0 <= target < self.n:
            raise IndexError('list index out of range')
        if source == target or self.head[source] == 0:
            return
        if self.head[target] == 0:
            self.head[target] = self.head[source]
        else:
            self.next[self.tail[target]] = self.head[source]
        self.tail[target] = self.tail[source]
        self.sizes[target] += self.sizes[source]
        self.head[source] = 0
        self.tail[source] = 0
        self.sizes[source] = 0

    def to_list(self, index: int) -> list[T]:
        """
        Return values of one list from front to back.

        Args:
            index: List index.

        Returns:
            Values in the list order.

        Raises:
            IndexError: If a list index is outside [0, n).

        Time Complexity:
            O(k), where ``k`` is the list size.
        """
        if not 0 <= index < self.n:
            raise IndexError('list index out of range')
        res: list[T] = []
        node = self.head[index]
        while node != 0:
            res.append(cast(T, self.values[node]))
            node = self.next[node]
        return res
