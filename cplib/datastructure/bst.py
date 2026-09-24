#!/usr/bin/env python3

from __future__ import annotations

from typing import Generic
from cplib.tools.type import KeyT


class BinarySearchTree(Generic[KeyT]):
    """
    Plain unbalanced binary search tree.

    This tree preserves the shape determined only by insertion and deletion
    order, so it is useful when traversal order of a standard BST matters.

    Space Complexity:
        O(m), where m is the maximum number of simultaneously stored values.

    Notes:
        Deleted node slots are reused on insertion. Their old key references
        remain until the slots are reused. The tree is not balanced; its
        height can be linear in the number of stored values.
    """
    def __init__(self) -> None:
        """
        Initialize an empty binary search tree.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._root = -1
        self._values: list[KeyT] = []
        self._left: list[int] = []
        self._right: list[int] = []
        self._parent: list[int] = []
        self._free_nodes: list[int] = []
        self._size = 0

    def __len__(self) -> int:
        """
        Return the number of values in the tree.

        Returns:
            Number of stored values.

        Time Complexity:
            O(1)
        """
        return self._size

    def size(self) -> int:
        """
        Return the number of values in the tree.

        Returns:
            Number of stored values.

        Time Complexity:
            O(1)
        """
        return len(self)

    def _find_node(self, value: KeyT) -> int:
        v = self._root
        values, left, right = self._values, self._left, self._right
        while v != -1:
            cur = values[v]
            if value < cur:
                v = left[v]
            elif cur < value:
                v = right[v]
            else:
                return v
        return -1

    def contains(self, value: KeyT) -> bool:
        """
        Check whether value is stored in the tree.

        Args:
            value: Value to search.

        Returns:
            Whether ``value`` exists.

        Time Complexity:
            O(h), where h is the tree height.
        """
        return self._find_node(value) != -1

    def add(self, value: KeyT) -> bool:
        """
        Insert value if it is not already present.

        Args:
            value: Value to insert.

        Returns:
            ``True`` if inserted, otherwise ``False``.

        Time Complexity:
            O(h), where h is the tree height.
        """
        parent = -1
        v = self._root
        go_left = False
        values, left, right = self._values, self._left, self._right
        while v != -1:
            parent = v
            cur = values[v]
            if value < cur:
                v = left[v]
                go_left = True
            elif cur < value:
                v = right[v]
                go_left = False
            else:
                return False

        if self._free_nodes:
            idx = self._free_nodes.pop()
            values[idx] = value
            left[idx] = right[idx] = -1
            self._parent[idx] = parent
        else:
            idx = len(values)
            values.append(value)
            left.append(-1)
            right.append(-1)
            self._parent.append(parent)
        if parent == -1:
            self._root = idx
        elif go_left:
            left[parent] = idx
        else:
            right[parent] = idx
        self._size += 1
        return True

    def _minimum_node(self, v: int) -> int:
        left = self._left
        while left[v] != -1:
            v = left[v]
        return v

    def _transplant(self, u: int, v: int) -> None:
        parent = self._parent[u]
        if parent == -1:
            self._root = v
        elif u == self._left[parent]:
            self._left[parent] = v
        else:
            self._right[parent] = v
        if v != -1:
            self._parent[v] = parent

    def discard(self, value: KeyT) -> bool:
        """
        Remove value from the tree if it exists.

        Args:
            value: Value to remove.

        Returns:
            ``True`` if removed, otherwise ``False``.

        Time Complexity:
            O(h), where h is the tree height.
        """
        z = self._find_node(value)
        if z == -1:
            return False
        if self._left[z] == -1:
            self._transplant(z, self._right[z])
        elif self._right[z] == -1:
            self._transplant(z, self._left[z])
        else:
            y = self._minimum_node(self._right[z])
            if self._parent[y] != z:
                self._transplant(y, self._right[y])
                self._right[y] = self._right[z]
                self._parent[self._right[y]] = y
            self._transplant(z, y)
            self._left[y] = self._left[z]
            self._parent[self._left[y]] = y
        self._size -= 1
        self._free_nodes.append(z)
        return True

    def remove(self, value: KeyT) -> None:
        """
        Remove value from the tree.

        Args:
            value: Value to remove.

        Returns:
            None.

        Raises:
            KeyError: If ``value`` does not exist.

        Time Complexity:
            O(h), where h is the tree height.
        """
        if not self.discard(value):
            raise KeyError(value)

    def inorder(self) -> list[KeyT]:
        """
        Return values in inorder traversal.

        Returns:
            Values visited by left-root-right traversal.

        Time Complexity:
            O(n)
        """
        res: list[KeyT] = []
        stack: list[int] = []
        v = self._root
        values, left, right = self._values, self._left, self._right
        while v != -1 or stack:
            while v != -1:
                stack.append(v)
                v = left[v]
            v = stack.pop()
            res.append(values[v])
            v = right[v]
        return res

    def preorder(self) -> list[KeyT]:
        """
        Return values in preorder traversal.

        Returns:
            Values visited by root-left-right traversal.

        Time Complexity:
            O(n)
        """
        if self._root == -1:
            return []
        res: list[KeyT] = []
        stack = [self._root]
        values, left, right = self._values, self._left, self._right
        while stack:
            v = stack.pop()
            res.append(values[v])
            if right[v] != -1:
                stack.append(right[v])
            if left[v] != -1:
                stack.append(left[v])
        return res

    def postorder(self) -> list[KeyT]:
        """
        Return values in postorder traversal.

        Returns:
            Values visited by left-right-root traversal.

        Time Complexity:
            O(n)
        """
        res: list[KeyT] = []
        stack: list[tuple[int, bool]] = []
        values, left, right = self._values, self._left, self._right
        if self._root != -1:
            stack.append((self._root, False))
        while stack:
            v, visited = stack.pop()
            if visited:
                res.append(values[v])
                continue
            stack.append((v, True))
            if right[v] != -1:
                stack.append((right[v], False))
            if left[v] != -1:
                stack.append((left[v], False))
        return res
