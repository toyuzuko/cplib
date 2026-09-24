#!/usr/bin/env python3

from collections.abc import Sequence

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.tools.type import KeyT


def cartesian_tree(arr: Sequence[KeyT]) -> Tree:
    """
    Build a Cartesian tree from the given sequence of comparable elements.

    Args:
        arr: Non-empty sequence of mutually comparable elements.

    Returns:
        Built min-Cartesian tree with original indices as vertices. In-order
        traversal visits indices in their original order. Equal minima choose
        the leftmost index as their ancestor.

    Raises:
        ValueError: If ``arr`` is empty.

    Time Complexity:
        O(n)

    Space Complexity:
        O(n)
    """
    n = len(arr)
    if n == 0:
        raise ValueError('arr must be non-empty')
    stack: list[tuple[int, KeyT]] = []
    par = [Node(-1)] * n
    for i in range(n):
        c = -1
        p = -1
        while stack:
            p, val = stack[-1]
            if arr[i] < val:
                c, _ = stack.pop()
            else:
                break
        if stack:
            par[i] = Node(p)
        if c != -1:
            par[c] = Node(i)
        stack.append((i, arr[i]))
    tree = Tree(n)
    root = -1
    for u, v in enumerate(par):
        if v != -1:
            tree.add_edge(Node(v), Node(u))
        else:
            root = u
    tree.build(Node(root))
    return tree
